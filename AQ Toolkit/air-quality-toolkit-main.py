from src.functions import GUI_Scaffold
import typing
from src.functions.File_Utilties import (
    _export_excel,
    _read_large_dataset,
    _export_csv,
    gooey_tqdm,
    separate_header_data,
    prepend_header_dataframe
)
from src.version_check import check_if_latest
import os


# New actions can be created by:
# 1. adding a new function in a .py file within the functions folder
# 2. adding a new subparser in GUI_Scaffold.py (arguments will be returned under user_inputs below)
# 3. interfacing with the function!

# User inputs calls to create the GUI for user input and returns a NameSpace object, this can be converted to a dictionary using vars() otherwise access attributes just like any class

# Check for latest available version
updates_path = "\\\\AUNTL1FP001\\Groups\\!ENV\\Team_AQ\\Modelling\\+Support_Data\\+Models & Software\\Air Quality Toolkit"

# If updates folder is available check, otherwise must be latest :P
if os.path.isdir(updates_path):
    latest_version = check_if_latest(updates_path)
else:
    latest_version = True

if not latest_version:
    import ctypes  # An included library with Python install.

    ctypes.windll.user32.MessageBoxW(
        0,
        f"Check for New Updates in {updates_path}. Ensure only the latest version is in this folder.",
        "New Update Available",
        1,
    )


if __name__ == "__main__":
    # Load GUI
    user_inputs = GUI_Scaffold.gui_inputs()

    if user_inputs.command == "batch_sum":
        from src.functions.Stitcher import stitcher

        # Read configuration
        config_df = _read_large_dataset(user_inputs.path)

        # Read first data set
        output_df = _read_large_dataset(config_df.loc[0, user_inputs.path_col_name])

        # Separate header data out and scale first data set

        first_columns_to_exclude = config_df.loc[
            0, user_inputs.columns_to_exclude_col_name
        ]
        output_df_header, output_df = separate_header_data(
            output_df, first_columns_to_exclude
        )
        output_df = output_df.multiply(config_df.loc[0, user_inputs.scale_col_name])

        # Loop over remaining datasets adding as you go
        for index, row in gooey_tqdm(
                config_df.iloc[1:].iterrows(), total=config_df.shape[0] - 1
        ):
            data_df = _read_large_dataset(row[user_inputs.path_col_name])

            data_df = data_df.multiply(row[user_inputs.scale_col_name])

            output_df = stitcher(
                output_df, data_df, 0, row[user_inputs.columns_to_exclude_col_name]
            )

        # Recombine the header data
        output_df = prepend_header_dataframe(output_df, output_df_header)

        _export_excel(output_df, user_inputs.output_path)

    elif user_inputs.command == "config_gen":
        from src.functions.File_Utilties import generate_config

        print(f"Searching in {user_inputs.path}...")

        if user_inputs.file_types:
            file_extensions = [x.strip() for x in user_inputs.file_types.split(",")]
        else:
            file_extensions = None
        # Build DataFrame of files
        df = generate_config(
            user_inputs.path,
            config_type=user_inputs.config_type,
            file_extensions=file_extensions,
            recursive=user_inputs.recursive,
        )

        print(f"Found {len(df.index)} files")

        # Export DataFrame to spreadsheet
        _export_excel(df, user_inputs.output_path)

    elif user_inputs.command == "statistics":
        from src.functions.Statistics import statstics_generator

        print(f"Computing statistics for {user_inputs.path}")
        statistics_settings: typing.Dict = vars(user_inputs)

        df = statstics_generator(statistics_settings)

        print(f"Statistics calculated!")

        _export_excel(df, user_inputs.output_path)

    elif user_inputs.command == "contemporaneous":
        from src.functions.Contemporaneous import contemporaneous

        print(f"Computing contemporaneous values for {user_inputs.path}")

        contemporaneous(
            user_inputs.header_length,
            user_inputs.path,
            user_inputs.background_path,
            user_inputs.background_col_name,
            user_inputs.number_of_rows,
            user_inputs.output_path,
            user_inputs.ascending,
        )

        print(f"Comtemporaneous calculated!")

    elif user_inputs.command == "factorizer":
        from src.functions.Factorizer import factorizer

        # from functions.File_Utilties import _read_large_dataset

        config_df = _read_large_dataset(user_inputs.path, 2000)

        for index, row in gooey_tqdm(config_df.iterrows(), total=config_df.shape[0]):

            # Read datasets
            data_df = _read_large_dataset(row[user_inputs.path_col_name])

            factor_df = _read_large_dataset(row[user_inputs.factor_col_name])

            factorised_df = factorizer(user_inputs.header_length, data_df, factor_df,)

            _export_csv(factorised_df, row[user_inputs.output_col_name])

    elif user_inputs.command == "batch_dat_to_csv":
        from src.functions.dat_to_csv_formatter import csvformatter

        config_df = _read_large_dataset(user_inputs.path)

        for index, row in gooey_tqdm(config_df.iterrows(), total=config_df.shape[0]):
            csvformatter(
                row[user_inputs.path_col_name],
                row[user_inputs.calpuff_col_name],
                row[user_inputs.output_col_name],
            )

    elif user_inputs.command == "dat_to_csv":
        from src.functions.dat_to_csv_formatter import csvformatter
        from src.functions.File_Utilties import _convert_path

        output_file_path = _convert_path(user_inputs.path)

        output_file_path = output_file_path.with_suffix(".csv")

        csvformatter(
            user_inputs.path, user_inputs.calpuff_format, output_file_path,
        )

    elif user_inputs.command == "no2_processor":
        from src.functions.no2_processor import process

        (
            olm_data_with_background,
            olm_data_without_background,
            outdf,
            no_bg_outdf,
        ) = process(
            int(user_inputs.header_length),
            float(user_inputs.initial),
            float(user_inputs.exceedance),
            user_inputs.background_path,
            user_inputs.path,
            user_inputs.ozone_col_name,
            float(user_inputs.fill_invalid_value),
            user_inputs.calc_without_background,
            user_inputs.bg_col_name,
            float(user_inputs.ozone_scale),
            float(user_inputs.percentile),
            int(user_inputs.rolling_window),
            user_inputs.top_header_length
        )

        if user_inputs.export_data:
            _export_excel(olm_data_with_background, user_inputs.export_data)

        if user_inputs.export_data_without:
            _export_excel(olm_data_without_background, user_inputs.export_data_without)

        if user_inputs.calc_without_background:
            from src.functions.File_Utilties import append_to_file_path

            _export_excel(
                no_bg_outdf,
                append_to_file_path(
                    user_inputs.output_path, "_Without_Background_Stats"
                ),
            )

        _export_excel(outdf, user_inputs.output_path)

    elif user_inputs.command == "overlap":
        from src.functions.Overlap_Sum import overlap_sum

        print(
            f"Running Overlap tool, run list {user_inputs.path}, output {user_inputs.output_path}"
        )

        config_df = _read_large_dataset(user_inputs.path)

        from pathlib import Path

        config_df["Path"] = config_df["Path"].apply(Path)

        id_df = config_df.copy()

        id_df.index = id_df["Path"].apply(lambda x: x.stem)

        # id_df = _read_large_dataset(user_inputs.input_id_file)

        # id_df.index = id_df.iloc[:, 0].apply(Path).apply(lambda x: x.stem)

        id_df = id_df.drop(["Path"], axis=1)

        output_df = overlap_sum(
            config_df["Path"].to_list(),
            id_df,
            user_inputs.header_length,
            float(user_inputs.fill_invalid_value),
        )

        _export_csv(output_df, user_inputs.output_path)

    elif user_inputs.command == "marb_generator":

        from src.functions.volemarb_generator import marb_generator

        print(f"Generating {user_inputs.template_type} from {user_inputs.path}...")

        volemarb_data = _read_large_dataset(user_inputs.path, header=None, dtype=str)

        pollutants = [x.strip() for x in user_inputs.pollutants.split(",")]
        pollutant_weights = [
            x.strip() for x in user_inputs.pollutant_weights.split(",")
        ]

        marb_generator(
            volemarb_data,
            user_inputs.ignore_columns,
            user_inputs.number_of_sources,
            user_inputs.output_path,
            user_inputs.template_type,
            pollutants,
            pollutant_weights,
            vars(user_inputs),
        )

        if user_inputs.template_type == "ptemarb":
            import ctypes  # An included library with Python install.

            ctypes.windll.user32.MessageBoxW(
                0,
                f"Ensure to enter building information data from BPIP into the header manually!",
                "Ptemarb Building Data",
                1,
            )

    elif user_inputs.command == "GRAL_timeseries_factorizer":
        import pandas as pd

        print("\n\n********** Running GRAL Timeseries Factorizer ********** \n")

        try:
            config_df = pd.read_excel(user_inputs.path, engine='openpyxl')
        except ValueError:
            config_df = pd.read_csv(user_inputs.path)

        if user_inputs.diurnal_factors is None:
            diurnal_df = pd.DataFrame(None)
        else:
            try:
                diurnal_df = pd.read_excel(user_inputs.diurnal_factors, engine='openpyxl')
            except ValueError:
                diurnal_df = pd.read_csv(user_inputs.diurnal_factors)

        from src.functions.factorise_GRAL_timeseries import factorise_gral_timeseries

        factorise_gral_timeseries(config_df,
                                  output_file=user_inputs.output_path,
                                  cols_to_skip=user_inputs.GRAL_timeseries_header_cols,
                                  GRAL_header_rows=user_inputs.GRAL_timeseries_header_rows,
                                  num_receptors=user_inputs.num_receptors,
                                  diurnal_factors=diurnal_df)

    elif user_inputs.command == "timeseries_difference":
        from src.functions.timeseries_difference import  timeseries_difference
        timeseries_difference(input_ts=user_inputs.input_timeseries,
                              subtract_ts=user_inputs.diff_timeseries,
                              output_file=user_inputs.output_timeseries,
                              cols_to_skip=user_inputs.GRAL_timeseries_header_cols,
                              GRAL_header_rows=user_inputs.GRAL_timeseries_header_rows,
                              num_receptors=user_inputs.num_receptors)


