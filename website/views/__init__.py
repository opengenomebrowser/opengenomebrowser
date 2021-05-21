from .Home import home_view
from .OrganismDetailView import OrganismDetailView
from .GenomeTable import genome_list_view
from .GenomeDetailView import GenomeDetailView
from .GenomeTableAjax import GenomeTableAjax
from .LoadTableScript import render_script
from .PathwayView import pathway_view
from .TaxIDDetailView import TaxIDDetailView
from .GeneDetailView import GeneDetailView
from .AnnotationSearch import annotation_view
from .AnnotationDetailView import AnnotationDetailView
from .Trees import trees
from .Dotplot import dotplot_view, get_dotplot, get_dotplot_annotations
from .Blast import blast_view
from .Api import Api
from .Files import files_html, files_json
from .ClickMenu import click_view
from .CompareGenes import CompareGenes
from .GeneTraitMatching import gtm_view
from .Downloader import downloader_view

from .helpers.magic_string import MagicQueryManager
