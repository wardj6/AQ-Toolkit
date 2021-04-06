""" Apply air quality modelling EPA functions and return statistics for NO2 specifically

Returns:
    [type]: [description]
"""

import pandas as pd

from .File_Utilties import _read_large_dataset, prepend_header_dataframe
import typing


def _compute_statistics(
    dataframe: pd.DataFrame, exceedances: float, percentile: float, window: float
) -> pd.DataFrame:
    outdf = pd.DataFrame(
        {
            "Max of Sensor": dataframe.max(),
            "Average of Sensor": dataframe.mean(),
            "Number of Exceedances": dataframe[dataframe > exceedances].count(),
            "Average Max Column": dataframe.max().mean(),
            "Max Value": dataframe.values.max(),
            f"{percentile * 100}th Percentile of Sensor": dataframe.quantile(
                percentile
            ),
            f"Max of {percentile * 100}th Percentile": dataframe.quantile(
                percentile
            ).max(),
            f"Average {window} Hour Rolling Average of Sensor": dataframe.rolling(
                window=window
            )
            .mean()
            .mean(),
            f"Max {window} Hour Rolling Average of Sensor": dataframe.rolling(
                window=window
            )
            .mean()
            .max(),
            # f"Max {window} Hour Rolling Average": dataframe.rolling(window=window)
            # .mean()
            # .max()
            # .max(),
        }
    )
    outdf.index.name = "Sensor ID"
    outdf.insert(0, "Sensor ID", outdf.index)
    return outdf


def process(
    header_length: int,
    initial: float,
    exceedance: float,
    background_name: str,
    input_data: str,
    ozone_column_name: str,
    fill_invalid_value: float,
    calc_without_background: bool,
    background_column_name: str,
    ozone_scale: float,
    percentile: float,
    window: int,
    top_header_length: int
) -> typing.Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """ Apply EPA modelling functions for NO2 and generate statistics

    Args:
        header_length (int): Number of columns before data starts (eg 3 for year/month/day)
        initial (float): Initial percentage to work with (eg 0.1 = 10%)
        exceedance (float): How many exceedances to compute (eg, compare how many are greater than 246)
        background_name (str): File path to background NO2 data set
        input_data (str): Source data file path
        ozone_column_name (str): Column name of ozone data in background data set
        fill_invalid_value (float): Value to fill any missing values
        calc_without_background (bool): Whether to calculate the same statistics for the data set without the background summed
        background_column_name (str): Column name of background data in background data set (eg, Background NO2)
        ozone_scale (float): Number to scale the ozone values by (default 46/48)
        top_header_length (int): Number of rows to ignore before data begins

    Returns:
        typing.Tuple[pd.DataFrame, pd.DataFrame,pd.DataFrame]: Temporary computed data set, output statistics on computed data, output background statistics
    """

    print(f"Processing NO2 statistics for {input_data}")

    # Read Data
    background = _read_large_dataset(background_name)
    background.dropna(how='all', inplace=True)

    data = _read_large_dataset(input_data)

    data_header = data.iloc[:, :header_length]

    data = data.iloc[:, header_length:]

    data = data[top_header_length - 1:]

    # Multiply background data by provided scalar

    data["background_NO2"] = background[background_column_name]

    data["background_O3"] = background[ozone_column_name]

    print("25%")

    data = data.fillna(fill_invalid_value)


    def olmfunction(row: pd.Series) -> pd.Series:
        """ Compute OLM which is the recorded value multiplied by the initial amount, and add the minimum of (1-iniial)*value or the ozone)

        Args:
            row (pd.Series): Row to be computed where last column is the ozone data scaled

        Returns:
            pd.Series: Computed row
        """
        # Take the ozone value
        ozone_value = float(row.iloc[-1]) * ozone_scale
        background_value = float(row.iloc[-2])
        new_row = []

        # Skip header rows and ignore last 2 values
        for value in row[:-2]:
            value = (float(value) * initial) + min(((1 - initial) * float(value)), ozone_value) + background_value
            new_row.append(value)
        return pd.Series(new_row)

    def backfunction(row: pd.Series) -> pd.Series:
        """ Background function for computing sum of recorded value and background

        Args:
            row (pd.Series): Row to be computed where last column is the background data

        Returns:
            pd.Series: Computed row
        """
        # Take the background value
        background_value = float(row.iloc[-1])
        new_row = []
        for value in row[:-1]:
            value = value - background_value
            new_row.append(value)

        return pd.Series(new_row)


    olm_data = data.apply(olmfunction, axis=1)
    olm_data.columns = data.columns[:-2]
    olm_data_with_background = olm_data.copy()
    olm_data["background"] = list(background[background_column_name])
    olm_data_without_background = olm_data.apply(backfunction, axis=1)
    olm_data_without_background.columns = data.columns[:-2]

    print("50%")
    # Compute statistics
    outdf = _compute_statistics(
        olm_data_with_background, exceedance, percentile, window
    )
    print("75%")
    no_bg_outdf = pd.DataFrame
    if calc_without_background:
        # data["background"] = list(background[background_column_name])
        # bg_data = data.apply(backfunction, axis=1)
        no_bg_outdf = _compute_statistics(
            olm_data_without_background, exceedance, percentile, window
        )

    olm_data_with_background = prepend_header_dataframe(
        olm_data_with_background, data_header
    )
    olm_data_without_background = prepend_header_dataframe(
        olm_data_without_background, data_header
    )

    print("100%")

    return olm_data_with_background, olm_data_without_background, outdf, no_bg_outdf
