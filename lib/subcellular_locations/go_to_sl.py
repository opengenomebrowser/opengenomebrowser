import os
import logging
from urllib import request

UNIPROTKB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uniprotkb_sl2go')


class LocationTerm:
    def __init__(self, line: str):
        line = line.removeprefix('UniProtKB-SubCell:')
        self.description = line[8:-13]

        assert line.startswith('SL-'), f'line does not start with SL-: {line=}'
        assert line[-13:-7] == ' ; GO:', f'line does not end with a GO-term: {line=}'

        self.go_id = line[-7:]
        self.sl_id = line[3:7]
        assert self.sl_id.isdigit() and self.go_id.isdigit(), f'failed to extract sl or go from {line=}'

    def __repr__(self) -> str:
        return f'{self.sl}/{self.go}'

    @property
    def go(self) -> str:
        return f'GO:{self.go_id}'

    @property
    def sl(self) -> str:
        return f'SL-{self.sl_id}'


def generate_location_terms(uniprotkb_sl2go: str) -> [LocationTerm]:
    uniprotkb_sl2go = uniprotkb_sl2go.strip().split('\n')
    return [LocationTerm(line) for line in uniprotkb_sl2go if not line.startswith('!')]


def update_uniprotkb_sl2go() -> None:
    with request.urlopen('http://current.geneontology.org/ontology/external2go/uniprotkb_sl2go') as handle:
        uniprotkb_sl2go = handle.read().decode('utf-8')
    try:
        generate_location_terms(uniprotkb_sl2go)
    except Exception as e:
        logging.warning(f'Failed to convert uniprotkb_sl2go to location tags! Did not overwrite local copy. Error: {str(e)}')
        return

    with open('lib/subcellular_locations/uniprotkb_sl2go', 'w') as f:
        f.write(uniprotkb_sl2go)

    print('Successfully updated uniprotkb_sl2go. Restart OpenGenomeBrowser apply the update.')


def get_locusterms() -> [LocationTerm]:
    """
    Parses the file uniprotkb_sl2go into a list of LocationTerm-objects.

    Example: [SL-0476/GO:0031672, SL-0002/GO:0020022, ...]

    :param sl_prefix: what comes before the SL index number (default: 'SL-')
    :param go_prefix: what comes before the GO term number (default: 'GO:')
    :returns: dictionary that maps SL indexes to GO terms
    """
    with open(UNIPROTKB_FILE) as f:
        uniprotkb_sl2go = f.read().strip().split('\n')
    return [LocationTerm(line) for line in uniprotkb_sl2go if not line.startswith('!')]
