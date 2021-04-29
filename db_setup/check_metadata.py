import os
import re

RE_GEOGRAPHICAL_COORDINATES = re.compile(pattern="^([0-9]{1,2})(\.[0-9]{1,4})? (N|S) ([0-9]{1,2})(\.[0-9]{1,4})? (W|E)$")


def is_valid_date(date_string: str) -> bool:
    from datetime import datetime
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        print("Invalid date string:", date_string)
        return False


def is_valid_env(envs) -> bool:
    for env in envs:
        if env[:5] == 'ENVO:' and int(env[5:]) > 0 and len(env) == 13:
            return True
        if env[:7] == 'FOODON:' and int(env[7:]) > 0 and len(env) == 15:
            return True
        print(F"Poorly formatted env: {env}")
        return False
    return True


def is_valid_reference(reference: str) -> bool:
    """ :returns: true if valid PMID, DOI or URL """

    from urllib.parse import urlparse
    isurl = urlparse(reference, scheme='http')
    if all([isurl.scheme, isurl.netloc, isurl.path]):
        return True  # is valid URL

    if re.match("(^[0-9]{8}$)|(^10.[0-9]{4,9}/[-._;()/:A-Za-z0-9]+$)", reference):
        return True  # is valid PMID, DOI
    print("Invalid reference in {}: '{}'. Is neither URL, PMID or DOI!".format(reference))
    return False


def genome_metadata_is_valid(data: dict, path_to_genome: str, raise_exception=False):
    def get_attr(attr):
        if attr in data:
            return data[attr]
        else:
            return None

    try:
        identifier = get_attr('identifier')
        assert identifier is not None, F'metadata contains no identifier'

        # Check if mandatory files exist:
        for file in ['cds_tool_faa_file', 'cds_tool_gbk_file', 'cds_tool_gff_file', 'assembly_fasta_file']:
            file_path = get_attr(file)
            assert file_path is not None, f'{identifier} :: {file} not specified'
            file_path = f'{path_to_genome}/{file_path}'
            assert os.path.isfile(file_path), f'{identifier} :: file {file} does not exist {file_path}'

        # Check if non-mandatory files exist:
        for file in ['cds_tool_sqn_file', 'cds_tool_ffn_file']:
            file_path = get_attr(file)
            if file_path:
                file_path = f'{path_to_genome}/{file_path}'
                assert os.path.isfile(file_path), F"{identifier} :: file {file} does not exist: {file}"

        # check all JSONFields:
        if get_attr('custom_tables'):
            for table_name, table in get_attr('custom_tables').items():
                assert 'rows' in table
                if 'index_col' in table:
                    assert type(table['index_col']) is str, table['index_col']
                if 'columns' in table:
                    assert type(table['columns']) is list, table['columns']

        if get_attr('BUSCO'):
            for char in ['C', 'D', 'F', 'M', 'S', 'T']:
                assert isinstance(get_attr('BUSCO')[char], int), f"{identifier} :: error in BUSCO :: {char}"

        if get_attr('custom_annotations'):
            for tool in get_attr('custom_annotations'):
                assert is_valid_date(tool['date']), f"{identifier} date is invalid: {tool['date']}"
                assert os.path.isfile(F"{path_to_genome}/{tool['file']}"), F"{identifier} :: file does not exist :: {tool['file']}"
                assert isinstance(tool['type'], str), F"{identifier} :: 'type' must be a string :: {tool}"

        for envs in [get_attr('env_broad_scale'), get_attr('env_medium'), get_attr('env_local_scale')]:
            if envs:
                assert is_valid_env(envs), f"{identifier} :: envs are invalid {envs}"

        # test sequencing info
        if get_attr('sequencing_date'):
            for date in get_attr('sequencing_date').split("//"): assert is_valid_date(date)

        # test assembly tool
        if get_attr('assembly_date'):
            for date in get_attr('assembly_date').split("//"): assert is_valid_date(date)

        # Test certain string fields
        if get_attr('literature_references'):
            for reference in get_attr('literature_references'):
                assert is_valid_reference(reference), f"{identifier} :: invalid literature_references :: {reference}"

        if get_attr('geographical_coordinates'):
            assert RE_GEOGRAPHICAL_COORDINATES.match(string=get_attr('geographical_coordinates')) is not None, \
                f'{identifier} :: geographical_coordinates are invalid'

    except Exception as e:
        if raise_exception:
            raise e
        else:
            return False

    return True


if __name__ == "__main__":
    from glacier import glacier
    import json


    def validate(path_to_metadata: str):
        """
        Perform some basic checks on a genome.json

        :param path_to_metadata: Path to a genome.json
        """
        with open(path_to_metadata) as f:
            data = json.load(f)
        path_to_genome = os.path.dirname(path_to_metadata)
        genome_metadata_is_valid(data, path_to_genome, raise_exception=True)


    glacier(validate)
