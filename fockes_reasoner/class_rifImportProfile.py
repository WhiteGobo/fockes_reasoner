from collections.abc import Mapping
from typing import Union
from rdflib import Graph, IdentifiedNode, URIRef
from .durable_reasoner import importProfile, machine
from .shared import RIF
from rdflib import RDF
from .rif_dataobjects import rif_document

class rifImportProfile(importProfile):
    """
    """
    def create_rules(self, machine: machine, infograph: Graph,
                     extraDocuments: Mapping[Union[str, IdentifiedNode], Graph] = {}) -> None:
        as_uri = lambda key: key if isinstance(key, IdentifiedNode) else URIRef(key)
        _extraDocs = {as_uri(key): value
                      for key, value in extraDocuments.items()}
        documents = list(infograph.subjects(RDF.type, RIF.Document))
        if len(documents) > 1:
            raise SyntaxError("Expected zero or one rif:Document in to be "
                              "to be imported documents.")
        elif len(documents) == 1:
            root = documents[0]
            assert isinstance(root, IdentifiedNode)
            doc = rif_document.from_rdf(infograph, root, _extraDocs)
            doc.create_rules(machine)
        else:
            raise Exception("Still testing so expecting one document.")
