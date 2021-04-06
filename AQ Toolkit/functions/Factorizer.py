""" Factorizer allows vector datasets to be multiplied over a timeseries dataset. This could be used to scale pollutants for different times of day.

"""

import os
import csv
import pandas as pd

from .File_Utilties import _read_large_dataset, prepend_header_dataframe


def factorizer(
    header_length: int,
    data_df: pd.DataFrame,
    # dataset_filename: str,
    factor_df: pd.DataFrame,
    # factor_filename: str,
    # output_filename: str,
) -> pd.DataFrame:
    """ Function for multiplying timeseries by a vector. Vector must contain same dimensions over index

    Args:
        header_length (int): Number of columns in index to ignore (eg, 3 for year/month/day)
        data_df (pd.DataFrame): Dataframe of input dataset
        factor_df (pd.DataFrame): Dataframe of factors to multiply data by. The last column will be taken as the factors
    
    Returns:
        pd.DataFrame: Factorised dataframe of data_df multiplied element wise by factor_df
    """

    header_length = int(header_length)

    print(f"Running Factoriser tool...")

    if len(factor_df.index) != len(data_df.index):
        raise ValueError("Ensure factors and data share same length in index")

    # Separate header from data
    data_header_df = data_df.iloc[:, :header_length]

    data_df = data_df.iloc[:, header_length:]

    # Multiply all rows by scalar value in factor column
    output_df = pd.DataFrame()
    for column in data_df.columns:
        output_df[column] = data_df[column] * factor_df.iloc[:, -1]

    # Concatenate the header columns back with the updated data
    output_df = prepend_header_dataframe(output_df, data_header_df)

    return output_df
