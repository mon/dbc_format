# DBC Format

An opinionated formatter for Vector DBC files, using the `cantools` library.

## Usage:
```
usage: dbc_format.py [-h] [-o OUTPUT] paths [paths ...]

DBC formatter

positional arguments:
  paths                 Input .dbc file(s) and/or folder(s)

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Specify output path instead of overwriting the original
```

## Support
I consider this tool "finished" as it suits my needs. Issues and pull requests
will be considered, but don't expect much support.

## Formatting

All string sorting is naturally sorted using the `natsort` library, so "Node10"
will be sorted after "Node2".

### Nodes
Sorted alphabetically

Unformatted:
```dbc
BU_: Car Bus Bicycle
```

Formatted:
```dbc
BU_: Bicycle Bus Car
```

### Messages
Sorted by message CAN ID

### Signals
Sorted by unmuxed signals first, then muxed signals, in order of start bit.

Unformatted:
```dbc
BO_ 1111 Voltage: 8 Car
 SG_ Voltage1 m0 : 32|32@1- (1,0) [0|0] "V" Vector__XXX
 SG_ Voltage2 m1 : 32|32@1- (1,0) [0|0] "V" Vector__XXX
 SG_ VoltageMux M : 0|8@1+ (1,0) [0|0] "" Vector__XXX
```

Formatted:
```dbc
BO_ 1111 Voltage: 8 Car
 SG_ VoltageNumber M : 0|8@1+ (1,0) [0|0] "" Vector__XXX
 SG_ Voltage1 m0 : 32|32@1- (1,0) [0|0] "V" Vector__XXX
 SG_ VoltageMux m1 : 32|32@1- (1,0) [0|0] "V" Vector__XXX
```

### Value tables
Sorted by message CAN ID, then signal name, then backwards by value.

Formatted:
```dbc
VAL_ 911 BusMode 3 "RESET" 2 "VOLTAGE" 1 "CURRENT" 0 "IDLE";
```

### Whitespace
* All runs of more than 2 space characters are squashed to 1. Semicolons are put
at the end of their line with no extra space.
* Newlines are Unix (\\n) format.
* All runs of more than 2 newlines are squashed to 1

### Attributes
All definitions first, then defaults, then values. In order of Bus, Node, Signal
attributes, then sorted alphabetically by attribute name, then by Node (for node
attributes), then by CAN ID (if one exists), then by signal name.

Formatted:
```dbc
BA_DEF_ "BusType" STRING;
BA_DEF_ BO_ "IsAlbatross" ENUM "No","Yes";
BA_DEF_ BO_ "IsSane" ENUM "No","Yes";
BA_DEF_ BO_ "NodeAttr" HEX 0 65535;
BA_DEF_ BO_ "timeout" INT 0 60000;
BA_DEF_DEF_ "BusType" "";
BA_DEF_DEF_ "IsAlbatross" "Yes";
BA_DEF_DEF_ "IsSane" "Yes";
BA_DEF_DEF_ "NodeAttr" 0;
BA_DEF_DEF_ "timeout" 1000;
BA_ "BusType" "CAN";
BA_ "NodeAttr" BU_ Bus 555;
BA_ "timeout" BO_ 888 20000;
BA_ "timeout" BO_ 999 20000;
BA_ "IsSane" SG_ 888 InsaneValue 0;
BA_ "IsSane" SG_ 888 InsaneValue2 0;
BA_ "IsAlbatross" SG_ 111 BirdVal 0;
```

### Comments
Sorted by comments for Bus, Node, Message, Signal, then by message CAN
ID (if one exists), then alphabetically.

### Floating point scientific notation
* Lowercase `e` character for exponent
* No 0 padding for exponent

Unformatted:
```dbc
BA_DEF_ SG_ "GenSigStartValue" FLOAT -1E+099 1E+099;
```

Formatted:
```dbc
BA_DEF_ SG_ "GenSigStartValue" FLOAT -1e+99 1e+99;
```

### Long names
Long names and the `SystemSignalLongSymbol` attribute used for them are not
used. All signals use their full length name.
