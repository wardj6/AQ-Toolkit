""" Contemporaneous calculations on timeseries, this is for finding where peaks may lie in the background data or in receptors
"""

import pandas as pd
from .File_Utilties import _read_large_dataset, gooey_tqdm


def _get_receptor_slice(
    sliced_dataframe: pd.DataFrame, current_name: str, background_column_name: str
) -> pd.DataFrame:
    """ From the sorted slice retrieve both the index and sum with background

    Args:
        sliced_dataframe (pd.DataFrame): Slice of sorted dataframe, should contain two columns [current receptor, background]
        current_name (str): Name to provide in output column names

    Returns:
        pd.DataFrame: Sliced dataframe with index and sum with background
    """

    # This is done as passing a kwarg to avoid the settingwithoutcopy warning
    # https://stackoverflow.com/questions/12555323/adding-new-column-to-existing-dataframe-in-python-pandas
    # https://stackoverflow.com/questions/39767718/pandas-assign-with-new-column-name-as-string
    new_columns = {
        f"{current_name}_Index": sliced_dataframe.index,
        f"{current_name}_Background_Sum": sliced_dataframe.iloc[:, 0]
        + sliced_dataframe[background_column_name],
        f"{current_name}_Empty_Space": "",
    }
    return sliced_dataframe.assign(**new_columns)


def contemporaneous(
    header_length: int,
    input_path: str,
    input_background_path: str,
    background_column_name: str,
    output_rows: int,
    output_filename: str,
    ascending: bool,
) -> pd.DataFrame:
    """ Contemporaneous calculations for timeseries (this sorts the values by data to get the top N scores)

    Args:
        header_length (int): Number of columns to ignore
        input_path (str): Path to input source data
        input_background_path (str): Path to input background data
        background_column_name (str): Column name containing background data
        output_rows (int): Number of rows (top N scores)
        output_filename (str): Path to file name to write CSV to
        ascending (bool): Whether to sort ascending (True) or descending (False)

    Returns:
        pd.DataFrame: [description]
    """

    header_length = int(header_length)
    output_rows = int(output_rows)

    background = _read_large_dataset(input_background_path)

    data = _read_large_dataset(input_path)

    # Disregard any information (essentially an index)
    data = data.iloc[:, header_length:]

    # Read in background pollutant levels a column in the data
    data[background_column_name] = background[background_column_name]

    # Sum first column for consistent dataframe dimensions
    data["Sum"] = data[data.columns[0]] + data[background_column_name]

    # Write a CSV progressively (row by row)
    f = open(output_filename, "w", newline="")

    # Loop over each column in the data set (representing a receptor)
    # Enumerate must be the last wrapper as it doesn't have a length so the loading bar won't format properly
    # https://github.com/tqdm/tqdm/issues/157
    for column_number, column in enumerate(gooey_tqdm(data.columns[:-2])):

        # Print only every 3rd column number so the progress bar appears
        if column_number % 3 == 0:
            print("")
        # Sort by current receptor
        sorted_data = data.sort_values(by=column, ascending=ascending).head(output_rows)

        receptor_slice = _get_receptor_slice(
            sorted_data.iloc[:, [column_number, -2]], "Receptor", background_column_name
        )

        # Sort by background
        sorted_data = data.sort_values(
            by=background_column_name, ascending=ascending
        ).head(output_rows)
        background_slice = _get_receptor_slice(
            sorted_data.iloc[:, [-2, column_number]],
            background_column_name,
            background_column_name,
        )

        # Sort by sum of current receptor + background
        data["Sum"] = data[column] + data[background_column_name]
        sorted_data = data.sort_values(by="Sum", ascending=ascending).head(output_rows)
        sum_slice = _get_receptor_slice(
            sorted_data.iloc[:, [-1, -2, column_number]], "Sum", background_column_name
        )

        # Remove all indexes from slices
        receptor_slice.reset_index(drop=True, inplace=True)
        background_slice.reset_index(drop=True, inplace=True)
        sum_slice.reset_index(drop=True, inplace=True)

        # Wrap into a single dataframe
        result = pd.concat([receptor_slice, background_slice, sum_slice], axis=1)

        # Write current dataframe into CSV
        result.to_csv(f)
