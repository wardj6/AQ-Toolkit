""" Dat to CSV formatter, currently supports CALPUFF format to export receptor locations as well
"""

import os
import csv
import pandas as pd

from .File_Utilties import append_to_file_path, _popup_message


def _export_calpuff_header(
    source_data_file_path: str, location_output_filename: str, output_filename: str
):
    """ Export CALPUFF dat file to CSV

    Args:
        source_data_file_path (str): Location of source data
        location_output_filename (str): Location to write location data in header 
        output_filename (str): Location to write data
    """
    loc_csv = csv.writer(open(location_output_filename, "w", newline=""))
    out_csv = csv.writer(open(output_filename, "w", newline=""))
    for i, line in enumerate(open(source_data_file_path)):
        if i == 3:
            out_header = ["YYYY", "JDY", "HHMM"]
            loc_header = ["X or Y"]
            for recepternum in range(1, int(line.split()[0]) + 1):
                out_header.append(recepternum)
                loc_header.append(recepternum)
            loc_csv.writerow(loc_header)
            out_csv.writerow(out_header)
        elif i in [9, 10]:
            row = line.split()
            loc_csv.writerow(row)
        elif i > 13:
            row = line.split()
            out_csv.writerow(row)


def csvformatter(filename: str, calpuff_state: bool, output_filename: str):
    """ Format dat files outputted from air quality modelling software to CSV format

    Args:
        filename (str): String of the file path of the source data
        calpuff_state (bool): True if source data is in CALPUFF format (x and y information in header)
        output_filename (str): Output file path to save to
    """

    print(f"Converting {filename}")

    if calpuff_state:
        # Export location data in hearder & data as csv
        location_output_filename = append_to_file_path(output_filename, "_Locations")
        _export_calpuff_header(filename, str(location_output_filename), output_filename)

    else:
        # Read in dat file tab delimited at first
        in_txt = csv.reader(open(filename, "r"), delimiter="\t")
        # Check if Output in first line of dat (typical of CALPUFF)
        if "Output" in next(in_txt)[0]:
            import warnings

            warnings.warn(
                f"{filename} is possibly in OLM format, please ensure this file has no header information"
            )

            _popup_message(
                f"{filename} is possibly in OLM format, please ensure this file has no header information"
            )

        # Determine the delimiter within the dat file
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(next(in_txt)[0])

        # Read in dat file with determined delimiter
        in_txt = csv.reader(open(filename, "r"), delimiter=delimiter.delimiter)

        # Write out to CSV
        out_csv = csv.writer(open(output_filename, "w", newline=""))
        out_csv.writerows(in_txt)


