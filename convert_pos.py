# Based on convert_pos.py code from Github User dronir

# This converts a component placement file in CSV format, produced by KiCad Pcbnew,
# by selecting File / Fabrication Outputs / Footprint position (.pos) file
# into the format expected by the JLCPCB manufacture service.

# In KiCad, use the following options:
#   Format = CSV
#   Units = Millimeters
#   Files = Single file for board
#   Include footprints with SMD pads even if ... = unchecked

# Use this by running the command line: python convert_pos.py inputfile.csv outputfile.csv
# It will overwrite your output file without asking so be careful.

import pandas as pd
from sys import argv, exit
import click

# Select these columns from the input file
FILTER = ["Ref", "PosX", "PosY", "Side", "Rot"]

# Rename the columns based on these rules
JLCPCB_NAMES = {
    "Ref" : "Designator",
    "PosX" : "Mid X",
    "PosY" : "Mid Y",
    "Side" : "Layer",
    "Rot" : "Rotation"
}

@click.command()
@click.option('--filename')
def convert(filename):
    # Read data, filter, rename and write output
    data = pd.read_csv(filename)
    print(data)
    filtered = data[FILTER]
    result = filtered.rename(JLCPCB_NAMES, axis="columns", errors="raise")
    result.to_csv(filename, index=False)

if __name__ == '__main__':
    convert()