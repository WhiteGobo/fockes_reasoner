from rdflib import Graph
from .durable_reasoner import importProfile, machine, fact, frame

class profileSimpleEntailment(importProfile):
    """
    See `https://www.w3.org/TR/2013/REC-rif-rdf-owl-20130205/#RDF_Compatibility`_ for more information.
    """
    def create_rules(self, machine: machine, infograph: Graph) -> None:
        for subj, pred, obj in infograph:
            f = frame(subj, pred, obj)
            f.assert_fact(machine)
