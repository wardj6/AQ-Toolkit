""" Statistics Generator for Timeseries Datasets

Returns:
    pd.DataFrame: Compiled Statistics Results
"""

import pandas as pd
import typing
from .File_Utilties import _read_large_dataset


def statstics_generator(settings: typing.Dict[str, typing.Any]) -> pd.DataFrame:
    """ Compute variable number of statistics from time series datasets

    Args:
        settings (typing.Dict[str, typing.Any]): Dictionary of settings from user input in Gooey

    Returns:
        pd.DataFrame: Compiled statistics results
    """

    data = _read_large_dataset(settings["path"], 2000)

    data = data.fillna(float(settings["fill_invalid_value"]))

    data = data.iloc[:, int(settings["header_length"]) :]
    data = data[int(settings["top_header_length"]):]
    data.reset_index(inplace=True, drop=True)
    data = data.apply(pd.to_numeric, errors='coerce')

    outdf = pd.DataFrame()

    if settings["enable_sensor_max"]:
        outdf = pd.DataFrame({"Max of Sensor": data.max()})
    if settings["enable_sensor_mean"]:
        temp_df = pd.DataFrame({"Average of Sensor": data.mean()})
        outdf = pd.concat([temp_df, outdf], axis=1, sort=False)
    if settings["percentiles"]:
        percentiles = settings["percentiles"].split(",")
        for percentile in percentiles:
            percentile = float(percentile)
            col_name = str(percentile * 100) + " Percentile of Sensor"
            temp_df = pd.DataFrame({col_name: data.quantile(percentile)})
            outdf = pd.concat([temp_df, outdf], axis=1, sort=False)
    if settings["rolling_mean_window"]:
        col_name = str(settings["rolling_mean_window"]) + " Hour Average of Sensor"
        temp_df = pd.DataFrame(
            {
                f"Average {str(settings['rolling_mean_window'])} Hour Rolling Average of Sensor": data.rolling(
                    window=int(settings["rolling_mean_window"])
                )
                .mean()
                .mean(),
                f"Max {str(settings['rolling_mean_window'])} Hour Rolling Average of Sensor": data.rolling(
                    window=int(settings["rolling_mean_window"])
                )
                .mean()
                .max(),
                # f"Max {str(settings['rolling_mean_window'])} Hour Rolling Average": data.rolling(
                #     window=int(settings["rolling_mean_window"])
                # )
                # .mean()
                # .max()
                # .max(),
            }
        )
        outdf = pd.concat([temp_df, outdf], axis=1, sort=False)
    start_hour = 0
    if settings['start_hour']:
        start_hour = int(settings['start_hour'])
    if settings["custom_hrs_mean"]:
        col_name = "Maximum " + str(settings["custom_hrs_mean"]) + " Hour Average of Sensor"
        resample_period = str(settings["custom_hrs_mean"]) + "H"
        temp_data = data.copy()
        import datetime as dt
        start_date = dt.datetime(year=2021, month=1, day=1, hour=start_hour)
        dates = pd.date_range(start=start_date, freq='H', periods=len(temp_data))
        temp_data.index = dates
        # temp_data = temp_data.apply(pd.to_numeric, errors='coerce')
        temp_df = pd.DataFrame({col_name: temp_data.resample(resample_period).mean().max()})
        outdf = pd.concat([temp_df, outdf], axis=1, sort=False)
    outdf.insert(0, "Index", "")
    outdf["Index"] = data.columns
    return outdf
