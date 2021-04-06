import pandas as pd
import re
import typing


def _available_template_types():
    return ["volemarb", "baemarb", "ptemarb"]


def _get_header_template(template_type: str) -> str:
    if template_type == "volemarb":
        # This is determined from CALPUFF Manual
        return """VOLEMARB.DAT    2.1             Comments  times with seconds  time zone  coord info             
1
{file_name}
UTM
{utm_zone}
{projection}   {nima_date}  
{distance_units}  
{time_zone}
{time_start} {time_end}
{number_of_sources}   {number_of_pollutants}
"""
    elif template_type == "baemarb":
        # This is determined from CALPUFF Manual
        return """BAEMARB.DAT    2.1             Comments  times with seconds  time zone  coord info             
1
{file_name}
UTM
{utm_zone}
{projection}   {nima_date}  
{distance_units}  
{time_zone}
{time_start} {time_end}
{number_of_sources}   {number_of_pollutants}
"""
    elif template_type == "ptemarb":
        # This is determined from CALPUFF Manual
        return """PTEMARB.DAT    2.1             Comments  times with seconds  time zone  coord info             
1
{file_name}
UTM
{utm_zone}
{projection}   {nima_date}  
{distance_units}  
{time_zone}
{time_start} {time_end}
{number_of_sources}   {number_of_pollutants}
"""
    elif template_type == "baemarb_source":
        # At the end of the header there needs to be a list of all the sources
        # This is built from the source datasets & number of sources
        return """{source}   '{source_emission_rate}'       0.0        0.0 
"""
    elif template_type == "source":
        # At the end of the header there needs to be a list of all the sources
        # This is built from the source datasets & number of sources
        return """{source}             0
"""
    elif template_type == "pollutant":
        return """'{pollutant}' """
    elif template_type == "pollutant_weight":
        return """{pollutant_weight} """
    else:
        raise ValueError(f"Template type: {template_type} is currently not supported")


def format_scientific(row: pd.Series) -> pd.Series:
    for index, value in enumerate(row[1:]):
        row.iloc[index + 1] = f"{float(value):.6e}"

    return row


def marb_generator(
    df: pd.DataFrame,
    ignore_columns: int,
    number_of_sources: int,
    output_path: str,
    template_type: str,
    pollutants: typing.List[str],
    pollutant_weights: typing.List[str],
    header_data: typing.Dict,
):

    # Remove any ignored columns
    df = df[df.columns[ignore_columns:]]

    # Nth row is determined through number of sources + 1
    nth_row_index = number_of_sources + 1

    source_names = df.iloc[1:nth_row_index, 0]

    source_names = source_names.apply(lambda x: re.sub(" +", " ", x))

    print(f"Source names: {source_names.tolist()}")
    print("10% Complete")

    # Format every nth sources row correctly (scientific notation, 6 decimal places, 'REAL format')
    # For multiple sources, this iterates through each source
    for nth, _ in enumerate(range(number_of_sources), 1):
        df.loc[nth::nth_row_index] = df.loc[nth::nth_row_index].apply(
            format_scientific, axis=1
        )

    print("25% Complete")

    # Format every nth date time row correctly (insert leading zeroes for columns 5 & 9 (3 and 7 after removing first two))
    df.loc[::nth_row_index, 3] = df.loc[::nth_row_index, 3].apply(
        lambda x: "{0:0>4}".format(int(x))
    )
    df.loc[::nth_row_index, 7] = df.loc[::nth_row_index, 7].apply(
        lambda x: "{0:0>4}".format(int(x))
    )

    df = df.fillna("")

    print("50% Complete")

    print(f"File read successfully! Number of rows = {len(df.index)}")

    with open(output_path, "w") as myfile:

        # Insert arguments passed into header_template
        # Argument name must match in template
        header_template = _get_header_template(template_type)

        myfile.write(header_template.format(**header_data))

        header_pollutant_template = _get_header_template("pollutant")

        for pollutant in pollutants:
            myfile.write(header_pollutant_template.format(pollutant=pollutant))

        myfile.write("\n")

        header_pollutant_weight_template = _get_header_template("pollutant_weight")

        for pollutant_weight in pollutant_weights:
            pollutant_weight = f"{float(pollutant_weight):.2f}"
            myfile.write(
                header_pollutant_weight_template.format(
                    pollutant_weight=pollutant_weight
                )
            )

        myfile.write("\n")

        if template_type == "baemarb":
            header_source_template = _get_header_template("baemarb_source")
        else:
            header_source_template = _get_header_template("source")

        for source in source_names:
            header_data["source"] = source
            myfile.write(header_source_template.format(**header_data))

        # Writes entire data frame to string
        dataframe_string = df.to_string(index=False, header=False)

        # Replace multiple spaces with single space
        dataframe_string_single_spaced = re.sub(" +", " ", dataframe_string)

        # Strip leading space
        import textwrap

        dataframe_string_single_spaced = textwrap.dedent(dataframe_string_single_spaced)

        myfile.write(dataframe_string_single_spaced)

    print("100% Complete")


def volemarb_generator(
    df: pd.DataFrame,
    ignore_columns: int,
    number_of_sources: int,
    output_path: str,
    template_type: str,
    pollutants: typing.List[str],
    pollutant_weights: typing.List[str],
    header_data: typing.Dict,
):

    # Remove any ignored columns
    df = df[df.columns[ignore_columns:]]

    # Nth row is determined through number of sources + 1
    nth_row_index = number_of_sources + 1

    source_names = df.iloc[1:nth_row_index, 0]

    source_names = source_names.apply(lambda x: re.sub(" +", " ", x))

    print(f"Source names: {source_names.tolist()}")
    print("10% Complete")

    # Format every nth sources row correctly (scientific notation, 6 decimal places, 'REAL format')
    # For multiple sources, this iterates through each source
    for nth, _ in enumerate(range(number_of_sources), 1):
        df.loc[nth::nth_row_index] = df.loc[nth::nth_row_index].apply(
            format_scientific, axis=1
        )

    print("25% Complete")

    # Format every nth date time row correctly (insert leading zeroes for columns 5 & 9 (3 and 7 after removing first two))
    df.loc[::nth_row_index, 3] = df.loc[::nth_row_index, 3].apply(
        lambda x: "{0:0>4}".format(int(x))
    )
    df.loc[::nth_row_index, 7] = df.loc[::nth_row_index, 7].apply(
        lambda x: "{0:0>4}".format(int(x))
    )

    df = df.fillna("")

    print("50% Complete")

    print(f"File read successfully! Number of rows = {len(df.index)}")

    with open(output_path, "w") as myfile:

        # Insert arguments passed into header_template
        # Argument name must match in template
        header_template = _get_header_template(template_type)

        myfile.write(header_template.format(**header_data))

        header_pollutant_template = _get_header_template("pollutant")

        for pollutant in pollutants:
            myfile.write(header_pollutant_template.format(pollutant=pollutant))

        myfile.write("\n")

        header_pollutant_weight_template = _get_header_template("pollutant_weight")

        for pollutant_weight in pollutant_weights:
            pollutant_weight = f"{float(pollutant_weight):.2f}"
            myfile.write(
                header_pollutant_weight_template.format(
                    pollutant_weight=pollutant_weight
                )
            )

        myfile.write("\n")

        header_source_template = _get_header_template("source")

        for source in source_names:
            myfile.write(header_source_template.format(source=source))

        if template_type == "ptemarb":
            myfile.write("""[INSERT BUILDING DATA HERE FROM BPIP OR OTHERWISE] """)

        # Writes entire data frame to string
        dataframe_string = df.to_string(index=False, header=False)

        # Replace multiple spaces with single space
        dataframe_string_single_spaced = re.sub(" +", " ", dataframe_string)

        # Strip leading space
        import textwrap

        dataframe_string_single_spaced = textwrap.dedent(dataframe_string_single_spaced)

        myfile.write(dataframe_string_single_spaced)

    print("100% Complete")
