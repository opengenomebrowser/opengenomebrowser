from django.db import models
from website.models.GenomeContent import GenomeContent
from website.models.Annotation import Annotation
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from Bio.SeqUtils import GC
from OpenGenomeBrowser import settings


class Gene(models.Model):
    """
    Represents a gene. Belongs to a Genome.

    Sequences aren't stored in the database and need to be retrieved from the gbk-file.
    """
    genomecontent = models.ForeignKey(GenomeContent, on_delete=models.CASCADE)

    identifier = models.CharField(max_length=50, primary_key=True)

    annotations = models.ManyToManyField(Annotation)

    def __repr__(self):
        return self.identifier

    def __str__(self):
        return self.identifier

    def natural_key(self):
        return self.identifier

    @property
    def html(self):
        tsi = self.genomecontent.genome.taxscientificname
        return F'<div class="gene ogb-tag" data-species="{tsi}" data-toggle="tooltip">{self.identifier}</div>'

    def gc_content(self) -> float:
        return GC(self.nucleotide_sequence())

    def fasta_nucleotide(self) -> str:
        return F'>{self.identifier}\n{self.nucleotide_sequence()}'

    def nucleotide_sequence(self) -> str:
        self.__load_gbk_seqrecord()
        return str(self._gbk_record.seq).upper()

    def fasta_protein(self):
        sequence = self.protein_sequence()
        if sequence is None:
            raise KeyError(F'The gene {self.identifier} is not protein-coding.')
        return F'>{self.identifier}\n{self.protein_sequence()}'

    def protein_sequence(self):
        self.__load_gbk_seqrecord()
        if 'translation' in self._all_qualifiers:
            return self._all_qualifiers['translation'][0].upper()
        else:
            return None

    def get_gbk_qualifiers(self):
        self.__load_gbk_seqrecord()
        if 'translation' in self._all_qualifiers:
            qualifiers = self._all_qualifiers.copy()
            qualifiers.pop('translation')
            return qualifiers
        return self._all_qualifiers

    def get_gbk_seqrecord(self):
        self.__load_gbk_seqrecord()
        return self._gbk_record

    def __load_gbk_seqrecord(self):
        # ensure it's only loaded once
        if not hasattr(self, '_gbk_record'):
            self._gbk_record = self.__get_gbk_seqrecord(self.genomecontent.genome.cds_gbk(relative=False), self.identifier)
            all_qualifiers = dict()
            for f in self._gbk_record.features:
                all_qualifiers.update(f.qualifiers)
            self._all_qualifiers = all_qualifiers

    @staticmethod
    def __get_gbk_seqrecord(file: str, identifier: str) -> SeqRecord:
        gb_records = SeqIO.parse(file, "genbank")
        for scf in gb_records:
            for feature in scf.features:
                locus_tag = feature.qualifiers.get('locus_tag', [0])[0]  # returns [0] so it can be unpacked
                if locus_tag == identifier:
                    seqrecord = feature.extract(scf)
                    seqrecord.scf_id = scf.id
                    return seqrecord
        raise KeyError(F'Could not find locus_tag {identifier} in {file}')

    @staticmethod
    def __get_seq_from_fasta(file: str, identifier: str) -> str:
        # this would be faster, but fasta-ids have stupid preambles that may cause problems
        faa_records = SeqIO.parse(file, "fasta")
        for seq in faa_records:
            if seq.id.endswith(identifier):
                return str(seq.seq)
        raise KeyError(F'Could not find locus_tag {identifier} in {file}')
