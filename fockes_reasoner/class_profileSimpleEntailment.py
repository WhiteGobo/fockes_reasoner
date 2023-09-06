from rdflib import Graph
from .durable_reasoner import importProfile, machine, fact, frame, TRANSLATEABLE_TYPES
from rdflib import IdentifiedNode, Literal, URIRef, BNode

class profileSimpleEntailment(importProfile):
    """
    See `https://www.w3.org/TR/2013/REC-rif-rdf-owl-20130205/#RDF_Compatibility`_ for more information.
    """
    def create_rules(self, machine: machine, infograph: Graph) -> None:
        for subj, pred, obj in infograph:
            assert isinstance(subj, (BNode, URIRef, Literal))
            assert isinstance(pred, (BNode, URIRef, Literal))
            assert isinstance(obj , (BNode, URIRef, Literal))
            f = frame(subj, pred, obj)
            f.assert_fact(machine)
