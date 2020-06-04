import os, io
from binary_file_search.BinaryFileSearch import BinaryFileSearch


class GeneOntology:
    def __init__(self, reload=False):
        self.obo_path = os.path.join(os.path.dirname(__file__), 'go.obo.converted')
        self._remote_path = 'http://purl.obolibrary.org/obo/go.obo'

        # download ontology if required
        if reload or not os.path.isfile(self.obo_path):
            self.__download_and_convert()

    def search(self, query: str):
        assert query.startswith('GO:')
        query = int(query[3:])

        with BinaryFileSearch(file=self.obo_path, sep="\t", string_mode=False) as bfs:
            return_value = bfs.search(query=query)

        return return_value[0][1]

    def __download_and_convert(self):
        import urllib.request

        target_file = open(self.obo_path, 'w')
        # source_file = open(os.path.join(os.path.dirname(__file__), 'go.obo'), 'rb')
        source_file = urllib.request.urlopen(self._remote_path)

        def get_name(entry: list):
            for line in entry:
                if line.startswith('name: '):
                    return line.rstrip()[6:]
            raise TypeError(F'The go.obo file seems to have a wrong format! broken entry: {entry}')

        def get_go(entry: list):
            assert entry[1].startswith('id: GO:')
            return int(entry[1][7:])

        gos = self.__go_generator(io=source_file)

        # skip first entry
        file_head = next(gos)
        assert not file_head[0].startswith('[Term]'), F'The go.obo file seems to have a wrong format! file_head looks wrong: {file_head}'

        for entry in gos:
            go = get_go(entry)
            name = get_name(entry)
            print(go, name)
            target_file.write(F'{go}\t{name}\n')

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
    go = GeneOntology(reload=False)
    print(go.search('GO:0000001'))
