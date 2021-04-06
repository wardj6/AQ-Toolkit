import pandas as pd
import numpy as np
from src.functions.File_Utilties import split_df


def timeseries_difference(input_ts: str,
                          subtract_ts: str,
                          output_file: str,
                          cols_to_skip: int,
                          GRAL_header_rows: int,
                          num_receptors: int
                          ):

    type = 'GRAL'
    keep_cols_data = range(0, cols_to_skip + num_receptors)
    keep_cols_header = range(0, cols_to_skip + num_receptors - 1)

    if type == 'GRAL':
        input_type = input_ts.split(".")[-1]
        if input_type == "txt":
            input_df = pd.read_csv(input_ts, delimiter=r"\t", header=None, skiprows=GRAL_header_rows,
                               engine="python", encoding="utf_16", usecols=keep_cols_data)
            inp_header = pd.read_csv(input_ts, delimiter=r"\t", header=None, nrows=GRAL_header_rows,
                               engine="python", encoding="utf_16", usecols=keep_cols_header)
            sub_df = pd.read_csv(subtract_ts, delimiter=r"\t", header=None, skiprows=GRAL_header_rows,
                               engine="python", encoding="utf_16", usecols=keep_cols_data)
        else:
            input_df = pd.read_csv(input_ts, header=None, skiprows=GRAL_header_rows, usecols=keep_cols_data)
            inp_header = pd.read_csv(input_ts, header=None, nrows=GRAL_header_rows, usecols=keep_cols_data)
            sub_df = pd.read_csv(subtract_ts, header=None, skiprows=GRAL_header_rows, usecols=keep_cols_data)

        cols_header_input, input_data = split_df(input_df, cols_to_skip)
        cols_header_sub, sub_data = split_df(sub_df, cols_to_skip)

        diff_data = input_data - sub_data

        # put df back together and export
        output_df = pd.concat([cols_header_input, diff_data], axis=1)
        new_index = np.arange(GRAL_header_rows - 1, output_df.shape[0] + GRAL_header_rows - 1)
        output_df.index = new_index

        output_df = pd.concat([inp_header, output_df])

        output_df.to_csv(output_file, header=False, index=False)
        print(f"\nSaved difference timeseries to {output_file}\n")
