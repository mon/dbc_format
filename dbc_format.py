#!/usr/bin/env python3

import argparse
import decimal
import os
import re
from pathlib import Path
from typing import List

# this script was written with cantools 38.0.0
import cantools.database.can.formats.dbc as cantools_dbc
from cantools import database
from cantools.database import utils
from cantools.database.can import Database
from cantools.database.can.formats.dbc import _create_GenMsgCycleTime_definition
from natsort import natsort_key, natsorted


def attribute_sorter(attrs: List[utils.type_sort_attribute]):
    def key(item: utils.type_sort_attribute):
        typ, attr, node, msg, signal = item

        # major sort order: dbc/node/message/signal
        attr_name = natsort_key(attr.name.lower())

        if typ == "dbc":
            return ("A", attr_name)
        elif typ == "node":
            return ("B", attr_name, natsort_key(node.name))
        elif typ == "message":
            return ("C", attr_name, msg.frame_id)
        elif typ == "signal":
            return ("D", attr_name, msg.frame_id, natsort_key(signal.name))
        else:
            raise NotImplementedError

    attrs.sort(key=key)
    return attrs


def sort_signals_by_natural_name(signals):
    return natsorted(signals, key=lambda s: s.name.lower())


# Here's the fragile stuff - cantools people aren't super stoked to modify the
# library to support all our formatting, so monkeypatch some internal functions
# and sort those lines afterwards
orig_dump_comments = cantools_dbc._dump_comments
orig_dump_attribute_definition_defaults = (
    cantools_dbc._dump_attribute_definition_defaults
)


def hook_dump_comments(*args, **kwargs):
    lines = orig_dump_comments(*args, **kwargs)

    def sorter(line: str):
        key = natsort_key(line)
        # comments are CM_ XX_ ....
        cm_type = line.split(" ")[1]
        if cm_type[0] == '"':  # bus comment, start of string
            return ("A", *key)
        if cm_type == "BU_":
            return ("B", *key)
        elif cm_type == "BO_":
            return ("C", *key)
        elif cm_type == "SG_":
            return ("D", *key)
        else:  # shouldn't be hit
            return ("Z", *key)

    return sorted(lines, key=sorter)


def hook_dump_attribute_definition_defaults(*args, **kwargs):
    lines = orig_dump_attribute_definition_defaults(*args, **kwargs)

    return sorted(lines, key=lambda s: s.lower())


def dbc_format_to_str(db: Database):
    # remove useless attribute added by CANdb++
    db.dbc.attribute_definitions.pop("SystemSignalLongSymbol", None)

    # cantools adds this anyway, but we need to sort it
    if "GenMsgCycleTime" not in db.dbc.attribute_definitions:
        db.dbc.attribute_definitions[
            "GenMsgCycleTime"
        ] = _create_GenMsgCycleTime_definition()

    def attr_def_sorter(item):
        name_keyed = natsort_key(item[0].lower())
        kind = item[1].kind
        if kind is None:
            return ("A", name_keyed)
        else:
            return ("B", kind, name_keyed)

    db.dbc._attribute_definitions = dict(
        sorted(db.dbc.attribute_definitions.items(), key=attr_def_sorter)
    )

    db._messages.sort(key=lambda m: m.frame_id)
    db._nodes.sort(key=lambda n: natsort_key(n.name))

    # make Decimal format with lowercase e
    caps = decimal.getcontext().capitals
    decimal.getcontext().capitals = False

    # monkeypatch
    cantools_dbc._dump_comments = hook_dump_comments
    cantools_dbc._dump_attribute_definition_defaults = (
        hook_dump_attribute_definition_defaults
    )

    raw = db.as_dbc_string(
        sort_signals=utils.sort_signals_by_start_bit_and_mux,
        sort_attribute_signals=sort_signals_by_natural_name,
        sort_attributes=attribute_sorter,
        sort_choices=utils.sort_choices_by_value_descending,
        shorten_long_names=False,
    )

    # unpatch
    cantools_dbc._dump_comments = orig_dump_comments
    cantools_dbc._dump_attribute_definition_defaults = (
        orig_dump_attribute_definition_defaults
    )

    # restore Decimal formatting
    decimal.getcontext().capitals = caps

    # extra whitespace that cantools uses that we don't care as much for
    raw = raw.replace("  ", " ").replace(" ;", ";")
    # we use Unix line endings
    raw = raw.replace("\r\n", "\n")
    # cantools also creates too much vertical whitespace
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    # final newline
    raw = re.sub(r"\n+$", "\n", raw)

    return raw


def dbc_format(db: Database, out_path: str):
    data = dbc_format_to_str(db)

    with open(out_path, "w", newline="") as f:
        f.write(data)


parser = argparse.ArgumentParser(description="DBC formatter")
parser.add_argument(
    "paths", help="Input .dbc file(s) and/or folder(s)", nargs="+", type=Path
)
parser.add_argument(
    "-o",
    "--output",
    help="Specify output path instead of overwriting the original",
    type=Path,
)

if __name__ == "__main__":
    args = parser.parse_args()

    if args.output and (len(args.paths) > 1 or not os.path.isfile(args.paths[0])):
        print("--output/-o can only be used with 1 input file")
        exit(1)

    files = []
    for path in args.paths:
        if os.path.isfile(path):
            files.append(path)
        elif os.path.isdir(path):
            files.extend(
                [
                    os.path.join(path, f)
                    for f in os.listdir(path)
                    if f.lower().endswith("dbc")
                ]
            )

    for file in files:
        suffix = "" if not args.output else f" to {args.output}"
        print(f"Formatting {file}{suffix}")
        db = database.load_file(file)
        dbc_format(db, args.output or file)
