import pathlib
import pandas as pd
from pathlib import Path
import typing
import os
from datetime import datetime


def prepend_header_dataframe(
    dataframe: pd.DataFrame, header_dataframe: pd.DataFrame
) -> pd.DataFrame:
    # Prepend header columns
    if len(header_dataframe.columns) > 0:

        # Insert backwards to keep original order
        for column in header_dataframe.columns[::-1]:
            dataframe.insert(0, column, header_dataframe[column])

    return dataframe


def _popup_message(message: str, message_box_title: str = "Error"):
    """ Message to alert user of what is happening, response is not recorded

    Args:
        message (str): Text to display in the body of the popup dialog
        message_box_title (str, optional): Title of popup dialog box. Defaults to "Error".
    """
    import ctypes  # An included library with Python install.

    ctypes.windll.user32.MessageBoxW(
        0, message, message_box_title, 1,
    )


def _export_excel(df: pd.DataFrame, output_file_path: str):
    """ For exporting dataframes to provided paths to xlsx format

    Args:
        df (pd.DataFrame): DataFrame to export
        output_file_path (str): Location to export to
    """
    print(f"Exporting data to {output_file_path}")
    try:
        df.to_excel(output_file_path, index=False)
    except ValueError:
        print(f"Exporting Excel Failed, attemping CSV export")
        new_output_path = _change_extension_on_path(output_file_path, ".csv")
        _export_csv(df, new_output_path)


def _export_csv(df: pd.DataFrame, output_file_path: str):
    """ For exporting dataframes to provided paths to csv format

    Args:
        df (pd.DataFrame): DataFrame to export
        output_file_path (str): Location to export to
    """
    print(f"Exporting data to {output_file_path}")
    df.to_csv(output_file_path, index=False)


def error_printing(error_message: str):
    """ For printing errors such that users see lots of hashtags

    Args:
        error_message (str): Text to include in between 'highlighted' sections
    """
    print(
        f"################################ CHECK THIS ################################"
    )
    print(error_message)
    print(
        f"################################ CHECK THIS ################################"
    )


def gooey_tqdm(iterable: typing.Iterable, *args: int, **kwargs: int) -> typing.Iterable:
    """ Utilise estimated time remaining from TQDM in Gooey

    Args:
        iterable (typing.Iterable): Iterable to be looped over

    Returns:
        typing.Iterable: The original iterable to be looped over
    """
    import io
    import sys
    from contextlib import redirect_stderr
    from tqdm import tqdm

    progress_bar_output = io.StringIO()

    with redirect_stderr(progress_bar_output):
        return tqdm(iterable, file=sys.stdout, *args, **kwargs)


def _convert_path(filepath: str) -> pathlib.Path:
    """ Convert path to patlib via constructor

    Args:
        filepath (str): File path as string

    Returns:
        pathlib.Path: File path as pathlib object
    """
    return Path(filepath)


def separate_header_data(
    dataframe: pd.DataFrame, header_length: int
) -> typing.Tuple[pd.DataFrame, pd.DataFrame]:
    """ For separate header data from dataframe

    Args:
        dataframe (pd.DataFrame): Original dataframe prior to separation
        header_length (int): Length of header to separate

    Returns:
        typing.Tuple[pd.DataFrame, pd.DataFrame]: Returns the header dataframe and the dataframe without header
    """

    dataframe_header = dataframe.iloc[:, :header_length]

    dataframe_without_header = dataframe.iloc[:, header_length:]

    return dataframe_header, dataframe_without_header


def _change_extension_on_path(filepath: str, new_extension: str) -> pathlib.Path:
    """ For changing an extension without altering the path

    Args:
        filepath (str): Path of original file to be changed
        new_extension (str): New extension to be changed to

    Returns:
        pathlib.Path: Original path with file with new extension
    """
    new_path = _convert_path(filepath)

    return new_path.with_suffix(new_extension)


def _read_large_dataset(
    filename: str, chunksize: int = 2000, *args, **kwargs
) -> pd.DataFrame:
    """ Read Large Datasets into pandas DataFrame

    Args:
        filename (str): Path to file to read
        chunksize (int): Number of 'chunks' to read in iteratively

    Returns:
        pd.DataFrame: Complete DataFrame of large dataset
    """
    file_path = _convert_path(filename)
    temp_list = []
    if file_path.suffix == ".xlsx":
        return pd.read_excel(file_path, *args, **kwargs)
    elif file_path.suffix == ".csv":
        for chunk in pd.read_csv(file_path, chunksize=chunksize, *args, **kwargs):
            temp_list.append(chunk)

        return pd.concat(temp_list)

    raise ValueError(f"Unable to read data set found at {file_path}")


def append_to_file_path(file_path: str, suffix: str) -> pathlib.Path:
    """ Append to file name in file path with a suffix (eg 'C:/file.txt', '_Test' will return 'C:/file_Test.txt')

    Args:
        file_path (str): Path to append with suffix
        suffix (str): Suffix to append to file name within path

    Returns:
        pathlib.Path: Appended file name within path
    """
    new_path = _convert_path(file_path)
    return new_path.parent / (new_path.stem + suffix + new_path.suffix)


def _config_template_columns(config_type: str) -> typing.Dict:
    """ Default columns & values for generated configuration files

    Args:
        config_type (str): Type which must be present in template column keys

    Raises:
        ValueError: If config type provided is not in template column keys

    Returns:
        typing.Dict: Column heading: default value in form of dictionary
    """
    template_columns = {
        "stitcher": {"Scale": 1, "Columns to Exclude": 3},
        "factorizer": {"Factor": 1},
        "csv_formatter": {"CALPUFF": 0},
    }
    if config_type not in template_columns.keys():
        raise ValueError(f"Configuration type: {config_type} not supported")
    return template_columns[config_type]


def generate_config(
    folder_path: str,
    config_type: str = None,
    file_extensions: typing.List[str] = None,
    recursive: bool = True,
) -> pd.DataFrame:
    """ Generate configuration files by searching folder structures for files

    Args:
        folder_path (str): Path to parent directory to search within
        config_type (str, optional): Type to input columns & default values in configuration file. Defaults to None.
        file_extensions (typing.List[str], optional): Extensions to limit the search for. Defaults to None.
        recursive (bool, optional): Whether to search recursively (eg within subfolders) or not. Defaults to True.

    Returns:
        pd.DataFrame: Configuration file as a DataFrame to be used elsewhere
    """
    path = _convert_path(folder_path)

    # Initialise DataFrame
    file_df = pd.DataFrame()

    for (dirpath, dirnames, filenames) in gooey_tqdm(os.walk(path)):

        # Loop through all files
        for file_name in filenames:

            # Check file type is provided
            # if file_extensions:
            if file_extensions is not None:

                # Append if file type

                if file_name.lower().endswith(tuple(file_extensions)):
                    row = {}

                    row["Path"] = os.path.abspath(os.path.join(dirpath, file_name))

                    if config_type is not None:
                        if config_type == "csv_formatter":
                            filename_no_ext, _ = os.path.splitext(file_name)
                            formatted_filename = filename_no_ext + ".csv"
                            row["Output"] = os.path.abspath(
                                os.path.join(dirpath, formatted_filename)
                            )

                        elif config_type == "factorizer":
                            filename_no_ext, _ = os.path.splitext(file_name)
                            formatted_filename = filename_no_ext + "_Factorised.csv"
                            row["Output"] = os.path.abspath(
                                os.path.join(dirpath, formatted_filename)
                            )

                        elif config_type == "extract_column_names":
                            row["ids"] = _read_large_dataset(
                                os.path.join(dirpath, file_name)
                            ).columns.tolist()

                    file_df = file_df.append(row, ignore_index=True)

            # If no file type provided, include all files
            else:
                row = {}

                row["Path"] = os.path.abspath(os.path.join(dirpath, file_name))

                file_df = file_df.append(row, ignore_index=True)

        if not recursive:
            break

    # Add column headings as needed
    if config_type is not None:

        # If extract column names is used, expand column of lists into it's own dataframe of vary length and concatenate path back
        # https://stackoverflow.com/questions/44663903/pandas-split-column-of-lists-of-unequal-length-into-multiple-columns
        if config_type == "extract_column_names":
            return pd.concat(
                [file_df["Path"], pd.DataFrame(file_df["ids"].to_list())], axis=1
            )

        default_columns = _config_template_columns(config_type)
        for column_name, default_value in default_columns.items():
            file_df[column_name] = default_value

    return file_df


# A function to split the first date columns from the actual data in a file
def split_df(df, cols_to_skip):
    header_cols_df = df.iloc[:, 0:cols_to_skip]
    data = df.iloc[:, cols_to_skip:]
    # make sure all data columns are numeric
    data = data.apply(pd.to_numeric)
    return header_cols_df, data
