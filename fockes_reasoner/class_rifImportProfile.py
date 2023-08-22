from collections.abc import Mapping
from rdflib import Graph
from .durable_reasoner import importProfile, machine
from .shared import RIF
from rdflib import RDF
from .rif_dataobjects import rif_document

class rifImportProfile(importProfile):
    """
    """
    def create_rules(self, machine: machine, infograph: Graph,
                     extraDocuments: Mapping[str, Graph] = {}) -> None:
        documents = list(infograph.subjects(RDF.type, RIF.Document))
        if len(documents) > 1:
            raise SyntaxError("Expected zero or one rif:Document in to be "
                              "to be imported documents.")
        elif len(documents) == 1:
            doc = rif_document.from_rdf(infograph, documents[0],
                                        extraDocuments)
            doc.create_rules(machine)
        else:
            raise Exception("Still testing so expecting one document.")
