"""Stitcher Module - aka batch_sum timeseries element-wise

Raises:
    ValueError: Raises errors on invalid parameters

Returns:
    pd.DataFrame: Summed DataFrame
"""
import os
import pandas as pd
import numpy as np
from .File_Utilties import (
    _read_large_dataset,
    gooey_tqdm,
    separate_header_data,
    prepend_header_dataframe,
)


def _validate_params(row: pd.Series):
    """ Validate Parameters in configuration dataset

    Args:
        row (pd.Series): Row of configuration
    """
    try:
        float(row["Scale"])
    except ValueError:
        print(
            "Invalid Scale for: "
            + row["Path"]
            + " Scale: "
            + row["Scale"]
            + " is not a number"
        )
    try:
        int(row["Columns to Exclude"])
    except ValueError:
        print(
            "Invalid Scale for: "
            + row["Path"]
            + " Ignoring: "
            + row["Columns to Exclude"]
            + " is not a number"
        )


def _clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """ Remove columns with no header and remove invalid rows

    Args:
        df (pd.DataFrame): DataFrame to be cleaned

    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df = df.dropna()
    return df


def stitcher(
    dataframe_1: pd.DataFrame,
    dataframe_2: pd.DataFrame,
    columns_to_exclude_1: int,
    columns_to_exclude_2: int,
) -> pd.DataFrame:

    dataframe_1 = _clean_dataset(dataframe_1)

    dataframe_2 = _clean_dataset(dataframe_2)

    dataframe_header_1, data_1 = separate_header_data(dataframe_1, columns_to_exclude_1)

    _, data_2 = separate_header_data(dataframe_2, columns_to_exclude_2)

    if data_1.empty or data_2.empty:
        import warnings

        warnings.warn("Empty Data detected, check input data sets")
        # print()
        summed_df = data_1.combine(data_2, np.sum)
    else:
        summed_df = data_1 + data_2

    return prepend_header_dataframe(summed_df, dataframe_header_1)


def old_stitcher(config_file_path: str) -> pd.DataFrame:
    """ Stitcher module to batch sum multiple time series datasets element wise

    Args:
        config_file_path (str): File path to configuration file containing details to sum

    Raises:
        ValueError: If invalid oarameters are found

    Returns:
        pd.DataFrame: Summed DataFrame
    """
    config_df = _read_large_dataset(config_file_path)

    config_df = config_df.astype(str)

    dataout = None

    for index, row in gooey_tqdm(config_df.iterrows(), total=config_df.shape[0]):

        print(
            "Processing: "
            + row["Path"]
            + " Scale: "
            + row["Scale"]
            + " Ignoring: "
            + row["Columns to Exclude"]
        )

        _validate_params(row)
        data: pd.DataFrame = _read_large_dataset(row["Path"], 2000)
        data = _clean_dataset(data)

        # Multiply by provided scale before summing
        data.update(
            data.iloc[:, int(row["Columns to Exclude"]) :]
            .astype(float)
            .multiply((float(row["Scale"])))
        )

        # Don't sum anything on first dataset
        if index == 0:
            dataout: pd.DataFrame = data

        else:
            if dataout is None:
                raise IndexError("None error has occured in Stitcher")
            if dataout.shape != data.shape:
                raise ValueError(
                    f"Output dataset dimensions: {dataout.shape} do not match input dataset(s) dimensions: {data.shape}. Potenitally missing hour or day"
                )
            else:
                # Add data past excluded columns
                dataout.update(
                    dataout.iloc[:, int(row["Columns to Exclude"]) :].add(
                        data.iloc[:, int(row["Columns to Exclude"]) :]
                    )
                )
        del data

        print(f"Output Data: {dataout.shape}")

    return dataout
