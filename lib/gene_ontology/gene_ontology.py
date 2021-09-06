import os
import urllib.request
from OpenGenomeBrowser import settings


class GeneOntology:
    def __init__(self, reload=False):
        self.out_path = f'{settings.ANNOTATION_DESCRIPTIONS}/GO.tsv'
        self._remote_path = 'http://purl.obolibrary.org/obo/go.obo'

        # download ontology if required
        if not os.path.isfile(self.out_path) or reload:
            self.__download_and_convert()

    def __download_and_convert(self):
        target_file = open(self.out_path, 'w')
        # source_file = open(os.path.join(os.path.dirname(__file__), 'go.obo'), 'rb')
        source_file = urllib.request.urlopen(self._remote_path)

        def get_name(entry: list):
            for line in entry:
                if line.startswith('name: '):
                    return line.rstrip()[6:]
            raise TypeError(f'The go.obo file seems to have a wrong format! broken entry: {entry}')

        def get_go(entry: list):
            entry = entry[1]
            assert entry.startswith('id: GO:') and len(entry) == 15, f'Bad entry in go.obo: {entry}, len={len(entry)}'
            assert entry[7:14].isnumeric()
            return entry[4:14]

        gos = self.__go_generator(io=source_file)

        # skip first entry
        file_head = next(gos)
        assert not file_head[0].startswith('[Term]'), f'The go.obo file seems to have a wrong format! file_head looks wrong: {file_head}'

        for entry in gos:
            go = get_go(entry)
            name = get_name(entry)
            print(go, name)
            target_file.write(f'{go}\t{name}\n')

        source_file.close()
        target_file.close()

    def __go_generator(self, io) -> [str]:
        go_entry = []

        line = io.readline()
        while line:
            if line == b'[Term]\n':
                yield go_entry
                go_entry.clear()

            go_entry.append(line.decode('utf-8'))
            line = io.readline()

        yield go_entry


if __name__ == '__main__':
    go = GeneOntology(reload=True)
