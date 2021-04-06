from gooey import Gooey, GooeyParser
from src.functions.__version__ import version
from src.functions.volemarb_generator import _available_template_types

# Handy information on grouping arguments https://github.com/chriskiehl/Gooey/issues/288


def _config_type_choices():
    return ["stitcher", "factorizer", "csv_formatter", "extract_column_names"]


def _add_input_output_arguments(
    parser_or_group,
    input_help: str,
    input_metavar: str = "Source File",
    input_widget="FileChooser",
    output_file_type: str = ".xlsx",
):
    parser_or_group.add_argument(
        "path", help=input_help, metavar=input_metavar, type=str, widget=input_widget,
    )

    parser_or_group.add_argument(
        "output_path",
        help=f"Location to save output file ({output_file_type})",
        metavar="Output File",
        type=str,
        widget="FileSaver",
        gooey_options={
            "message": "Pick Output Location",
            "wildcard": f"{output_file_type} (*{output_file_type})|*{output_file_type}|"
            "All files (*.*)|*.*",
        },
    )


@Gooey(
    program_name="Air Quality Toolkit",
    menu=[
        {
            "name": "About",
            "items": [
                {
                    "type": "AboutDialog",
                    "menuTitle": "About",
                    "name": "Air Quality Toolkit",
                    "description": "Miscellaneous Tools useful for air quality modelling",
                    "version": version,
                    "developer": "Jack McKew - AECOM 2020",
                },
            ],
        }
    ],
    hide_progress_msg=False,
    progress_regex=r"(\d+)%",
)
def gui_inputs():
    program_description = "Miscellaneous Tools for Air Quality Modelling"
    parser = GooeyParser(description=program_description)

    subs = parser.add_subparsers(help="commands", dest="command")

    #########################################################

    config_gen_parser = subs.add_parser("config_gen")

    config_gen = config_gen_parser.add_argument_group(
        "Configuration Generator",
        "Generate configuration file for use in other actions",
    )

    _add_input_output_arguments(
        config_gen,
        input_help="Select folder to collect all file types for",
        input_metavar="Source Folder",
        input_widget="DirChooser",
    )

    config_gen.add_argument(
        "--recursive",
        help="If ticked, config generator will search all subfolders as well",
        metavar="Recursive Search",
        action="store_true",
    )

    config_gen.add_argument(
        "--file_types",
        help="Select file types to include separated by a comma (eg '.csv, .xlsx'), if empty all files will be selected",
        metavar="File Types",
        type=str,
    )

    config_gen.add_argument(
        "--config_type",
        help="Select template for configuration file for use with other actions, if None will only output list of files",
        metavar="Configuration Types",
        choices=_config_type_choices(),
    )

    #########################################################

    batch_sum_parser = subs.add_parser("batch_sum")

    batch_sum = batch_sum_parser.add_argument_group(
        "Batch Sum",
        "Batch Sum (aka 'Stitcher') combines data tables by summing them element-wise, Note that all tables must be the same dimensions",
    )

    _add_input_output_arguments(
        batch_sum,
        input_help="Provide a list of files to stitch with their file path (columns required are Path, Scale, Columns to Exclude), Path should be the file path to the file to sum, Scale should be how much you want to multiply by (defaults to 1), Columns to Exclude should be how many columns till the data starts (defaults to 3 for year, month, day timeseries)",
        input_metavar="Configuration File",
    )

    batch_sum.add_argument(
        "--columns_to_exclude_col_name",
        help="Columns to exclude should be how many columns till the data starts (defaults to 3 for year, month, day timeseries)",
        metavar="Columns to Exclude Column Name",
        type=str,
        default="Columns to Exclude",
    )

    batch_sum.add_argument(
        "--path_col_name",
        help="Name of column containing source dataset paths in config file",
        metavar="Path Column Name",
        type=str,
        default="Path",
    )




    batch_sum.add_argument(
        "--scale_col_name",
        help="Name of column containing scales to multiply datasets by",
        metavar="Scale Column Name",
        type=str,
        default="Scale",
    )

    #########################################################

    statistic_parser = subs.add_parser("statistics")

    statistics = statistic_parser.add_argument_group(
        "Statistics Analyser", "Compute statistics for timeseries data",
    )

    _add_input_output_arguments(
        statistics, input_help="Data set to compute statistics upon"
    )

    statistics.add_argument(
        "header_length",
        help="Columns to exclude should be how many columns till the data starts (defaults to 3 for year, month, day timeseries)",
        metavar="Columns to Exclude",
        type=int,
        default=3,
    )

    statistics.add_argument(
        "top_header_length",
        help="Rows to exclude should be how many rows till the data starts",
        metavar="Header Rows to Exclude",
        type=int,
        default=1,
    )

    statistics.add_argument(
        "start_hour",
        help="Hour of the first row in the input data",
        metavar="Start Hour of Data",
        type=int,
        default=0,
    )

    statistics.add_argument(
        "--fill_invalid_value",
        help="Value to fill invalid data points with",
        metavar="Fill Invalid Value",
        default="0",
    )

    mean_options = statistics.add_argument_group(
        "Mean Options",
        "Customise the averaging options",
        gooey_options={"show_border": True},
    )

    mean_options.add_argument(
        "--enable_sensor_mean",
        help="If ticked, output will contain averages for all input data series",
        metavar="Average of Sensor",
        action="store_true",
        default=True,
    )

    mean_options.add_argument(
        "--rolling_mean_window",
        help="Provide a window to compute rolling mean (eg, 8), leave blank to disable",
        metavar="Rolling Mean Window",
    )

    mean_options.add_argument(
        "--custom_hrs_mean",
        help="Provide a non-rolling time period for averaging (eg, 24 for 24-hour averaging), leave blank to disable",
        metavar="Custom Hrs to Average",
    )

    max_options = statistics.add_argument_group(
        "Max Options",
        "Customise the Maximum options",
        gooey_options={"show_border": True},
    )

    max_options.add_argument(
        "--enable_sensor_max",
        help="If ticked, output will contain maxes for all input data series",
        metavar="Max of Sensor",
        action="store_true",
        default=True,
    )

    percentile_options = statistics.add_argument_group(
        "Percentile Options",
        "Customise the Percentile options",
        gooey_options={"show_border": True},
    )

    percentile_options.add_argument(
        "--percentiles",
        help="Input percentiles to compute separated by commas (eg, 0.25, 0.5, 0.75 will compute 25th, 50th and 75th percentiles), leave blank to disable",
        metavar="Percentiles to Compute",
    )

    #########################################################

    contemporaneous_parser = subs.add_parser("contemporaneous",)

    contemporaneous = contemporaneous_parser.add_argument_group(
        "Contemporaneous Processor",
        """Contemporaneous functionality for calculating contemporaneous values with background pollutant
        This function computes the sorted values along with background data
        """,
    )

    _add_input_output_arguments(
        contemporaneous,
        "Provide the source data to calculate contemporaneous values upon",
        output_file_type=".csv",
    )

    contemporaneous.add_argument(
        "background_path",
        help="Provide the data for the background pollutant levels",
        metavar="Background Data",
        type=str,
        widget="FileChooser",
    )

    contemporaneous.add_argument(
        "--background_col_name",
        help="Name of column containing background pollutant data",
        metavar="Background Pollutant Name",
        type=str,
        default="Background NO2",
    )

    contemporaneous.add_argument(
        "--header_length",
        help="Columns to exclude should be how many columns till the data starts (defaults to 3 for year, month, day timeseries)",
        metavar="Columns to Exclude",
        type=int,
        default=3,
    )

    contemporaneous.add_argument(
        "--number_of_rows",
        help="Number of rows to compute",
        metavar="Number of Rows",
        type=int,
        default=5,
    )

    contemporaneous.add_argument(
        "--ascending",
        help="Sort values by ascending (tick if you want to find minimums)",
        metavar="Ascending",
        action="store_true",
    )

    #########################################################

    factorizer_parser = subs.add_parser(
        "factorizer",
        help="Factorizer is a tool to batch multiply time series by factors",
    )

    factorizer = factorizer_parser.add_argument_group(
        "Factorizer",
        """Factorizer is a tool to batch multiply time series by factors
        An example use is if you want to only get hours from 9-5, this tool can 0 out all the other hours if provided a vector data set""",
    )

    factorizer.add_argument(
        "path",
        help="Provide a list of files to factorize with their file path, the path to another dataset containing the factors and the output file name. Note that factors will be taken from the last column in the factor dataset",
        metavar="Configuration File",
        type=str,
        widget="FileChooser",
    )

    factorizer.add_argument(
        "--header_length",
        help="Columns to exclude should be how many columns till the data starts (defaults to 3 for year, month, day timeseries)",
        metavar="Columns to Exclude",
        type=int,
        default=3,
    )

    factorizer.add_argument(
        "--path_col_name",
        help="Name of column containing source dataset paths in config file",
        metavar="Path Column Name",
        type=str,
        default="Path",
    )

    factorizer.add_argument(
        "--factor_col_name",
        help="Name of column containing factor dataset paths in config file",
        metavar="Factor Column Name",
        type=str,
        default="Factor",
    )

    factorizer.add_argument(
        "--output_col_name",
        help="Name of column containing output paths in config file",
        metavar="Output Column Name",
        type=str,
        default="Output",
    )

    #########################################################

    dat_to_csv_parser = subs.add_parser("dat_to_csv", help="Dat to CSV converter",)

    dat_to_csv = dat_to_csv_parser.add_argument_group(
        "Dat to CSV Converter",
        """Dat to CSV Converter with specifics for formatting CALPUFF output format
        If CALPUFF format is ticked a file under the same name with a suffix of _Locations will be output with the x y coordinates in the dat file""",
    )
    dat_to_csv.add_argument(
        "path",
        help="Provide a dat file to be converted to csv, a CSV file of the same name will be in the same location",
        metavar="Source Dat File",
        type=str,
        widget="FileChooser",
    )

    dat_to_csv.add_argument(
        "--calpuff_format",
        help="Tick if dat file is in CALPUFF format",
        metavar="CALPUFF Format",
        action="store_true",
    )

    #########################################################

    batch_dat_to_csv_parser = subs.add_parser(
        "batch_dat_to_csv", help="Dat to CSV converter",
    )

    batch_dat_to_csv = batch_dat_to_csv_parser.add_argument_group(
        "Batch Dat to CSV Converter",
        """Dat to CSV Converter with specifics for formatting CALPUFF output format
        If CALPUFF format is specified, a file under the same name with a suffix of _Locations will be output with the x y coordinates in the dat file""",
    )

    batch_dat_to_csv.add_argument(
        "path",
        help="Provide a list of files to factorize with their file path, the path to another dataset containing the factors and the output file name. Note that factors will be taken from the last column in the factor dataset",
        metavar="Configuration File",
        type=str,
        widget="FileChooser",
    )

    batch_dat_to_csv.add_argument(
        "--path_col_name",
        help="Name of column containing source dataset paths in config file",
        metavar="Path Column Name",
        type=str,
        default="Path",
    )

    batch_dat_to_csv.add_argument(
        "--calpuff_col_name",
        help="Name of column containing CALPUFF State of dataset paths in config file (0 for False, 1 for True)",
        metavar="CALPUFF Column Name",
        type=str,
        default="CALPUFF",
    )

    batch_dat_to_csv.add_argument(
        "--output_col_name",
        help="Name of column containing output paths in config file",
        metavar="Output Column Name",
        type=str,
        default="Output",
    )

    #########################################################

    no2_processor_parser = subs.add_parser("no2_processor", help="NO2 Processor",)

    no2_processor = no2_processor_parser.add_argument_group(
        "NO2 Processor",
        """Apply air quality modelling functions and generate statistics from output
            1. Calculate via the formula (initial * sensor value) + minimum(((1 - initial) * sensor value) or 46/48 * ozone value) + background_no2
            2. Optional to output without the background no2 summed
            3. Count the number of exceedances over a certain limit
            4. Export other statistics (eg 99.9th quantile, 8 hour maximum, etc""",
    )

    _add_input_output_arguments(
        no2_processor,
        input_help="Source data for timeseries to calculate NO2",
        input_metavar="Source Data",
    )

    no2_processor.add_argument(
        "background_path",
        help="Background pollutant timeseries data",
        metavar="Background Pollutant File",
        type=str,
        widget="FileChooser",
    )

    no2_processor.add_argument(
        "--bg_col_name",
        help="Name of column containing background pollutant data",
        metavar="Background NO2 Column Name",
        type=str,
        default="Background NO2",
    )

    no2_processor.add_argument(
        "--ozone_col_name",
        help="Name of column containing ozone data",
        metavar="Ozone Column Name",
        type=str,
        default="Ozone",
    )

    no2_processor.add_argument(
        "--calc_without_background",
        help="If ticked, calculate statistics for data without background summed as well",
        metavar="Calculate Statistics Without Background",
        action="store_true",
        default=False,
    )

    no2_processor.add_argument(
        "--export_data",
        help="Export data following the calculation (initial * sensor value) + minimum(((1 - initial) * sensor value) or 46/48 * ozone value) + background_no2",
        metavar="Export Data",
        widget="FileSaver",
    )

    no2_processor.add_argument(
        "--export_data_without",
        help="Export data without the background NO2 summed (initial * sensor value) + minimum(((1 - initial) * sensor value) or 46/48 * ozone value)",
        metavar="Export Data Without Background",
        widget="FileSaver",
    )

    no2_processor.add_argument(
        "--initial", help="Initial % to process", metavar="Initial", default=0.1,
    )

    no2_processor.add_argument(
        "--exceedance",
        help="This should be an integer declaring how many exceedances eg compare if any are greater than 246",
        metavar="Exceedances",
        default=246,
    )

    no2_processor.add_argument(
        "--fill_invalid_value",
        help="Value to fill invalid data points with",
        metavar="Fill Invalid Value",
        default="0",
    )

    no2_processor.add_argument(
        "--header_length",
        help="Columns to exclude should be how many columns till the data starts (defaults to 3 for year, month, day timeseries)",
        metavar="Columns to Exclude",
        type=int,
        default=3,
    )

    no2_processor.add_argument(
        "--top_header_length",
        help="Rows to exclude should be how many rows till the data starts",
        metavar="Header Rows to Exclude",
        type=int,
        default=1,
    )

    no2_processor.add_argument(
        "--ozone_scale",
        help="Value to scale ozone data by (defaults to 46/48 or 0.9583333)",
        metavar="Ozone Scale",
        type=float,
        default=0.9583333,
    )

    no2_processor.add_argument(
        "--percentile",
        help="Percentile to Compute (eg, 99.9th percentile is 0.999",
        metavar="Percentile",
        type=float,
        default=0.999,
    )

    no2_processor.add_argument(
        "--rolling_window",
        help="Rolling window to compute (eg, 8 for 8 hour windows",
        metavar="Rolling Window",
        type=float,
        default=8,
    )

    #########################################################

    overlap_parser = subs.add_parser("overlap")

    overlap = overlap_parser.add_argument_group(
        "Overlap Sum Tool",
        "This function sums overlapping datasets (receptor IDs spread across dat/csv files)",
    )

    _add_input_output_arguments(
        overlap,
        input_help="Select a configuration file containing the list of files to be processed under the column Path, remaining data in row should be column names for dataset",
        input_metavar="Configuration File",
        output_file_type=".csv",
    )

    # overlap.add_argument(
    #     "input_id_file",
    #     metavar="Input ID File",
    #     help="Select file containing file name matched with receptor ids in each row (first column must be path to file)",
    #     type=str,
    #     widget="FileChooser",
    # )

    overlap.add_argument(
        "--header_length",
        help="Columns to exclude should be how many columns till the data starts (defaults to 3 for year, month, day timeseries)",
        metavar="Columns to Exclude",
        type=int,
        default=3,
    )

    overlap.add_argument(
        "--fill_invalid_value",
        help="Value to fill invalid data points with",
        metavar="Fill Invalid Value",
        default="0",
    )

    #########################################################

    volemarb_parser = subs.add_parser("marb_generator")

    volemarb = volemarb_parser.add_argument_group(
        "Marb Generator (volemarb, baemarb & ptemarb)",
        """Generate a volemarb file from a source data file (xlsx or csv) for use in modelling software. The marb will be generated by:
            1. Selecting the marb type in 'template_type'
            2. Inserting a header template into the file as specified by the standard. Names for sources are determined from rows in the first column equal to number of sources specified.
            3. Formats all the data rows to be scientific notation, 6 decimal places aka 'REAL' format
            4. Formats all the date rows to be correct format (eg, leading zeros for seconds)
            5. Writes to file""",
    )

    _add_input_output_arguments(
        volemarb,
        input_help="Select the source data file",
        input_metavar="Source Data File",
        output_file_type=".dat",
    )

    volemarb.add_argument(
        "number_of_sources",
        metavar="Number of Sources",
        help="Select number of sources provided in dataset",
        type=int,
        default=1,
    )

    volemarb.add_argument(
        "--ignore_columns",
        metavar="Number of columns to ignore",
        help="Number of columns to ignore, eg, ignore A & B column = 2",
        type=int,
        default=0,
    )

    volemarb.add_argument(
        "--file_name",
        metavar="File name in header",
        help="Must be in all caps, do not include extension",
        type=str,
        default="DEFAULT_NAME",
    )

    volemarb.add_argument(
        "--projection", metavar="Projection that data is in", type=str, default="WGS-84"
    )

    volemarb.add_argument(
        "--utm_zone",
        metavar="UTM zone followed by Hemisphere (N or S) that data is in",
        type=str,
        default="55S",
    )

    volemarb.add_argument(
        "--nima_date",
        metavar="NIMA date (MM-DD-YYYY) for datum definitions",
        type=str,
        default="02-21-2003",
    )

    volemarb.add_argument(
        "--distance_units",
        metavar="Units provided for distances (km or deg)",
        type=str,
        default="KM",
    )

    volemarb.add_argument(
        "--time_zone",
        metavar="Timezone that data is in (in UTC format)",
        type=str,
        default="UTC+1000",
    )

    volemarb.add_argument(
        "--time_start",
        metavar="Starting date for time series data (In format YYYY DD HH SSSS)",
        type=str,
        default="2018 1 10 0",
    )

    volemarb.add_argument(
        "--time_end",
        metavar="Ending date for time series data (In format YYYY DD HH SSSS)",
        type=str,
        default="2018 1 10 3600",
    )

    volemarb.add_argument(
        "--pollutants",
        metavar="Pollutant name in data separated by a comma if multiple",
        type=str,
        default="PM2.5",
    )

    volemarb.add_argument(
        "--pollutant_weights",
        metavar="Pollutant weight in data separated by a comma if multiple (order and length must match pollutant names)",
        type=str,
        default="150",
    )

    volemarb.add_argument(
        "--number_of_pollutants",
        metavar="Number of Pollutants in data (if using more than one, ensure pollutant names are formatting correctly",
        type=int,
        default=1,
    )

    volemarb.add_argument(
        "--source_emission_rate",
        metavar="Source emission rate for use in BAEMARB format",
        choices=["g/s", "g/m2/s"],
        default="g/s",
    )

    volemarb.add_argument(
        "--template_type",
        metavar="Template Type",
        default="volemarb",
        choices=_available_template_types(),
    )

    #########################################################

    gral_timeseries = subs.add_parser("GRAL_timeseries_factorizer")

    gral_options = gral_timeseries.add_argument_group("GRAL Timeseries Factorizer",
                                                             "- Batch factors and then sums a set of GRAL timeseries\n"
                                                             "- Outputs a processed timeseries for each pollutant separately\n"
                                                             "- This function reads GRAL timeseries .txt files directly - conversion to csv not required"
                                                             "- Includes optional source-group-specific hour-of-day factoring",
                                                       gooey_options={"show_border": True, "columns": 2})

    _add_input_output_arguments(
        gral_options,
        input_help="- Provide an Excel or CSV file containing with a column containing input file paths under the header 'Path'\n"
                   "- Factors should be in a separate column with the pollutant name as the column header -e.g. 'PM10'\n"
                   "- Mulitple pollutants can be run at the same time - add factors to a new column for each pollutant",
        input_metavar="Pollutant Configuration File",
    )



    gral_options.add_argument(
        "--GRAL_timeseries_header_rows",
        metavar="GRAL timeseries header rows",
        help="Number of header rows in GRAL timeseries files - these will be skipped for calculations",
        type=int,
        default=7
    )
    gral_options.add_argument(
        "--GRAL_timeseries_header_cols",
        metavar="GRAL timeseries header columns",
        help="Number of header columns in GRAL timeseries files - these will be skipped for calculations",
        type=int,
        default=2
    )

    gral_options.add_argument(
        "num_receptors",
        metavar="Number of receptors in GRAL timeseries",
        help="This controls how many columns of data to read in from the raw timeseries for each source group and allows\n"
             "redundant columns full of zeros to be ignored",
        type=int
    )

    gral_timeseries_options = gral_timeseries.add_argument_group('Options')

    gral_timeseries_options.add_argument('--diurnal_factors',
                              metavar='Optional Source-Group-Specific Diurnal Factors File',
                              help="- This function will factor each raw timeseries by specific hour-of-day factors PRIOR to the pollutant scale factoring"
                              "- Provide an Excel or CSV file containing with a column called 'Hour' containing a rows for reach hour 0-23\n"
                              "- Diurnal factors should be in separate columns - one for each source group\n"
                              "- The source group column headers must contain the full path for each source group timeseries file'\n"
                              "- All source groups must be in the file - HoD factors all set to 1 for groups that do not require factoring\n"
                              "- Note that the Pollutant Configuration File must still be included.",
                              widget='FileChooser')

    #########################################################

    timeseries_diff = subs.add_parser("timeseries_difference")

    csv_file_type = ".csv"

    diff_options = timeseries_diff.add_argument_group("Timeseries Difference",
                                                      "- Calculates the difference between two timeseries files and exports a result timeseries\n"
                                                      "- Currently only works for GRAL format timeseries",
                                                       gooey_options={"show_border": True, "columns": 3})

    diff_options.add_argument("input_timeseries", metavar="Input Timeseries", widget="FileChooser")
    diff_options.add_argument("diff_timeseries", metavar="Timeseries to subtract", widget="FileChooser")
    diff_options.add_argument("output_timeseries", metavar="Output Timeseries", widget="FileSaver",
                                 gooey_options={
                                            "message": "Pick Output Location",
                                            "wildcard": f"{csv_file_type} (*{csv_file_type})|*{csv_file_type}|"
                                            "All files (*.*)|*.*"})
    diff_options.add_argument(
        "--GRAL_timeseries_header_rows",
        metavar="GRAL timeseries header rows",
        help="Number of header rows in GRAL timeseries files - these will be skipped for calculations",
        type=int,
        default=7
    )
    diff_options.add_argument(
        "--GRAL_timeseries_header_cols",
        metavar="GRAL timeseries header columns",
        help="Number of header columns in GRAL timeseries files - these will be skipped for calculations",
        type=int,
        default=2
    )

    diff_options.add_argument(
        "num_receptors",
        metavar="Number of receptors in GRAL timeseries",
        help="This controls how many columns of data to read in from the raw timeseries for each source group and allows\n"
             "redundant columns full of zeros to be ignored",
        type=int
    )

    #########################################################

    args = parser.parse_args()
    return args