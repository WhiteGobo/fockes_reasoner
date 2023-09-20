from rdflib import Graph
from . import durable_reasoner
from .durable_reasoner import importProfile, fact, frame, TRANSLATEABLE_TYPES
from rdflib import IdentifiedNode, Literal, URIRef, BNode
from typing import Union, Any
from dataclasses import dataclass
from .shared import entailment

class profileOWLDirect(importProfile):
    """
    See `https://www.w3.org/TR/2013/REC-rif-rdf-owl-20130205/#RDF_Compatibility`_ for more information.
    """
    ID = entailment["OWL-Direct"]
    """IRI to identify if this profile should be used for import"""

    @dataclass
    class _initImport:
        machine: durable_reasoner.machine
        location: Union[str, IdentifiedNode]
        def __call__(self, bindings: Any) -> None:
            infograph = self.machine.load_external_resource(self.location)
            raise NotImplementedError()
            for subj, pred, obj in infograph:
                assert isinstance(subj, (BNode, URIRef, Literal))
                assert isinstance(pred, (BNode, URIRef, Literal))
                assert isinstance(obj , (BNode, URIRef, Literal))
                f = frame(subj, pred, obj)
                self.machine.assert_fact(f, {})

    def create_rules(self, machine: durable_reasoner.machine, location: str,
                     ) -> None:
        machine.add_init_action(self._initImport(machine, location))
