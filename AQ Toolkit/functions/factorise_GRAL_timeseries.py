import pandas as pd
import numpy as np


def import_data(config_files, path_name, header_rows, keep_cols):
    # This imports all the data into a dictionary up front
    files = list(config_files[path_name])
    first_df = pd.read_csv(files[0], delimiter=r"\t", header=None, skiprows=header_rows - 1,
                               engine="python", encoding="utf_16", usecols=keep_cols)
    data_dict = {}
    for file in files[1:]:
        df = pd.read_csv(file, delimiter=r"\t", header=None, skiprows=header_rows,
                               engine="python", encoding="utf_16", usecols=keep_cols)

        data_dict[file] = df
    return first_df, data_dict


def diurnal_factoriser(df, factors, file, cols_header):
    # source_group = file.split("\\")[-1].split("_")[-2]
    cols = list(factors.columns)
    cols = [x.lower() if x == 'Hour' else x for x in cols]
    factors.columns = cols

    data = df.copy()
    data.reset_index(inplace=True, drop=True)

    try:
        factors_dict = dict(zip(factors['hour'], factors[file]))
    except:
        print(f"\n********** ERROR ********** The file {file} does not have a corresponding column in the diurnal factor CSV\n")
        raise ValueError

    calc_df = cols_header.iloc[:,-1:].copy()
    calc_df.columns = ['hour']
    calc_df['hour'] = calc_df['hour'].str.replace(":00", "").astype(int)
    calc_df['factor'] = calc_df['hour'].map(factors_dict)
    calc_df.reset_index(inplace=True, drop=True)
    calc_df = pd.concat([calc_df, data], axis=1, ignore_index=True)

    def factorize_row(row):
        factor_value = float(row.iloc[1])
        new_row = []
        # factorize values - ignoring the first two values (hour and factor)
        for value in row[2:]:
            value = value * factor_value
            new_row.append(value)
        return pd.Series(new_row)

    factored_df = calc_df.apply(factorize_row, axis=1)
    factored_df.columns = range(2,factored_df.shape[1] + 2)
    print(f"Applied diurnal factors to {file}")

    return factored_df


def check_paths(config_files, path_col_header):
    files = list(config_files[path_col_header])
    incorrect_paths = []
    import os
    for file in files:
        if os.path.isfile(file) is False:
            incorrect_paths.append(file)
    return incorrect_paths


def factorise_gral_timeseries(
        config_df,
        output_file,
        cols_to_skip,
        GRAL_header_rows,
        num_receptors,
        diurnal_factors
):
    # This function factorises source group timeseries from GRAL by diurnal factors and pollutant specific factors
    # Factors and files are input via config files - read in within the "main" function then passed to this function
    # output is saved directly to csv from within this function

    #first check all paths are correct
    path_name = "Path"
    bad_paths = check_paths(config_df, path_name)
    if len(bad_paths) > 0:
        print(f"********** ERROR ********** The following path/s are invalid or unavailable:\n\n{bad_paths}\n")
        raise ValueError
    else:
        print("All paths in config file checked and valid\n")

    # Read in first dataframe from config file - only keep cols for receptors - redundant cols for other source groups (all zeros) dropped
    keep_cols_data = range(0, cols_to_skip + num_receptors)
    keep_cols_header = range(0, cols_to_skip + num_receptors - 1)

    # Import data
    first_df, data_dict = import_data(config_df, path_name, GRAL_header_rows, keep_cols_data)
    date_time_head = first_df[:1]
    first_df = first_df[1:]

    # Read in the header
    header_df = pd.read_csv(config_df[path_name][0], delimiter=r"\t", header=None, nrows=GRAL_header_rows-1,
                           engine="python", encoding="utf_16", usecols=keep_cols_header)

    # Add a blank column to the front of the header - this will ensure it has the same number of cols as the data
    new_col_nas = [np.nan] * header_df.shape[0]
    new_col_df = pd.DataFrame(new_col_nas)
    header_df = pd.concat([new_col_df, header_df], axis=1)
    header_df.columns = np.arange(0, header_df.shape[1])
    header_df = pd.concat([header_df, date_time_head])

    from src.functions.File_Utilties import split_df

    # Get a list of all columns with scales to factor out
    pollutant_factor_cols = config_df.columns
    pollutant_factor_cols = [x for x in pollutant_factor_cols if 'path' not in x.lower()]
    pollutant_factor_cols = [x for x in pollutant_factor_cols if 'columns to exclude' not in x.lower()]

    for pollutant in pollutant_factor_cols:
        print(f"\nProcessing {pollutant}\n")
        cols_header_df, total_conc_df = split_df(first_df, cols_to_skip)
        cols_header_df.reset_index(inplace=True, drop=True)

        # If hour of day factors are provided, factor the first timeseries by hour of day factors
        if diurnal_factors.shape[0] != 0:
            total_conc_df = diurnal_factoriser(total_conc_df, diurnal_factors, config_df[path_name][0], cols_header_df)

        # Multiply first df by scale factor
        total_conc_df = total_conc_df * config_df[pollutant][0]

        def output_intermediate_file(int_df, source_grp, poll, cols_head, header):
            # This function outputs the intermediate timeseries files
            intermediate_file = source_grp + "_" + poll + ".csv"
            # put df back together and export
            out_int_df = pd.concat([cols_head, int_df], axis=1)

            new_index = np.arange(GRAL_header_rows - 1, out_int_df.shape[0] + GRAL_header_rows - 1)
            out_int_df.index = new_index
            out_int_df = pd.concat([header, out_int_df], ignore_index=True)
            out_int_df.to_csv(intermediate_file, header=False, index=False)
            sg_name = source_grp.split("\\")[-1]
            print(f"Saved factored {poll} timeseries for {sg_name} to {intermediate_file}")

        # Output the first factored timeseries as an intermediate file
        source_group_name = config_df[path_name][0].replace("ReceptorTimeSeries_", "").replace("_NOx.txt", "")
        output_intermediate_file(total_conc_df, source_group_name, pollutant, cols_header_df, header_df)

        # cycle through remaining files and add to total_df
        for i, (file, data) in enumerate(data_dict.items()):

            next_df = data
            next_cols_df, next_conc_df = split_df(next_df, cols_to_skip)
            next_cols_df.reset_index(inplace=True, drop=True)

            # If hour of day factors are provided, factor the next timeseries by hour of day factors
            if diurnal_factors.shape[0] != 0:
                next_conc_df = diurnal_factoriser(next_conc_df, diurnal_factors, config_df[path_name][i+1], cols_header_df)

            # mulitply data by matching scale factor in the config file and add to total
            next_conc_df = next_conc_df * config_df[pollutant][i+1]
            total_conc_df = total_conc_df + next_conc_df

            # Output the next factored timeseries as an intermediate file
            source_group_name = config_df[path_name][i].replace("ReceptorTimeSeries_", "").replace("_NOx.txt", "")
            output_intermediate_file(next_conc_df, source_group_name, pollutant, cols_header_df, header_df)

        # put df back together and export
        output_df = pd.concat([cols_header_df, total_conc_df], axis=1)
        new_index = np.arange(GRAL_header_rows-1,output_df.shape[0] + GRAL_header_rows - 1)
        output_df.index = new_index

        output_df = pd.concat([header_df, output_df], ignore_index=True)

        output_file_csv = output_file.replace(".xlsx", "_" + pollutant + ".csv")
        output_df.to_csv(output_file_csv, header=False, index=False)
        print(f"\nSummed all source groups for {pollutant} and saved to {output_file_csv}\n")
