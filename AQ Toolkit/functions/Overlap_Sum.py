""" Overlap Sum is a tool for joining back together multiple data sets that share columns
"""
from .File_Utilties import _read_large_dataset, error_printing, gooey_tqdm

import pandas as pd

import typing


def _rename_columns(
    dataframe: pd.DataFrame, header_columns: typing.List, receptor_id_names: typing.List
) -> pd.DataFrame:
    """ Rename a slice of columns (normally this will raise an error with pandas Index being unmuteable)
        This is completed by appending an 'original' slice of column names with a new column name list, note that this will only work in order

    Args:
        dataframe (pd.DataFrame): DataFrame with columns to be renamed
        header_columns (typing.List): Columns to remain the same
        receptor_id_names (typing.List): New column names

    Returns:
        pd.DataFrame: DataFrame with renamed columns!
    """
    try:
        renamed_df = dataframe.set_axis(
            header_columns + receptor_id_names, axis=1, inplace=False
        )
    except:
        # ValueError is raised when axis' don't match warn user
        error_printing(
            f"Number of columns in data set potentially does not match number of receptor IDs provided"
        )
        raise
    return renamed_df


def _get_row_as_list(
    dataframe: pd.DataFrame, value_to_match_in_index: str
) -> typing.List:
    """ Get the contents of a row (match with value) and return a list

    Args:
        dataframe (pd.DataFrame): DataFrame with data to extract (index must contain value_to_match_in_index)
        value_to_match_in_index (str): Value to be matched in index using `.get_loc`

    Returns:
        typing.List: A list of all the values in that row
    """
    return (
        dataframe.iloc[dataframe.index.get_loc(value_to_match_in_index)]
        .dropna()
        .tolist()
    )


def overlap_sum(
    input_file_list: typing.List,
    id_df: pd.DataFrame,
    header_column_length: int,
    fill_invalid_value: float,
) -> pd.DataFrame:
    """ Overlap summing tool for summing back together multiple dataframes with shared columns

    Args:
        input_file_list (typing.List): List of files to sum by matching columns
        id_df (pd.DataFrame): DataFrame where the index is the file name (as provided in the input_file_list (if Path use `.stem`)) and the remainder of the row is the column names
        header_column_length (int): Number of columns that are shared across all datasets (eg, year, month, day)

    Returns:
        pd.DataFrame: Summed Dataset with all columns provided in id_df
    """
    out_df = _read_large_dataset(input_file_list[0], 2000)

    # Get the contents of the row where the file_name is the index (stem is used to avoid pathing problems) and return a list
    out_df_index = _get_row_as_list(id_df, input_file_list[0].stem)

    # Get header slice (will be prepended later)
    out_df_header = out_df.iloc[:, :header_column_length]

    # Remove header
    out_df = out_df.iloc[:, header_column_length:]

    # Rename the columns in the dataset to match that of what's read in the ID dataframe
    out_df = _rename_columns(out_df, [], out_df_index)

    # Iterate over all files (skipping the first as this was already done)
    for file_name in gooey_tqdm(input_file_list[1:]):
        print(f"Processing {file_name}")

        sum_df = _read_large_dataset(file_name)

        if sum_df.shape[0] != out_df.shape[0]:
            raise ValueError(
                f"Number of rows do not match, ensure data sets have same shape (rows, columns) of data: {sum_df.shape} & {out_df.shape}"
            )

        sum_df_index = _get_row_as_list(id_df, file_name.stem)

        sum_df = sum_df.iloc[:, header_column_length:]

        sum_df = _rename_columns(sum_df, [], sum_df_index)

        out_df = out_df.add(sum_df, axis=1, fill_value=0)

        del sum_df

    # Remove any unnamed columns
    out_df = out_df.loc[:, ~out_df.columns.str.contains("^Unnamed")]

    # Prepend header columns
    if len(out_df_header.columns) > 0:

        # Insert backwards to keep original order
        for column in out_df_header.columns[::-1]:
            out_df.insert(0, column, out_df_header[column])

    return out_df
