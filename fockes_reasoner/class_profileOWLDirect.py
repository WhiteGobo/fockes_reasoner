from rdflib import Graph, URIRef
from . import durable_reasoner
from .durable_reasoner import importProfile, fact, TRANSLATEABLE_TYPES, member
from rdflib import IdentifiedNode, Literal, URIRef, BNode
from typing import Union, Any
from dataclasses import dataclass
from .shared import entailment, OWL, RDF

class profileOWLDirect(importProfile):
    """
    See `https://www.w3.org/TR/2013/REC-rif-rdf-owl-20130205/#RDF_Compatibility`_ for more information.
    """
    ID: URIRef = entailment["OWL-Direct"]
    """IRI to identify if this profile should be used for import"""

    @dataclass
    class _initImport:
        machine: durable_reasoner.machine
        location: Union[str, IdentifiedNode]
        def __call__(self, bindings: Any) -> None:
            infograph = self.machine.load_external_resource(self.location)
            self.load_types(infograph)

        def load_types(self, infograph: Graph) -> None:
            for subj, obj in infograph.subject_objects(RDF.type):
                if obj == OWL.Ontology:
                    continue
                infograph.remove((subj, RDF.type, obj))
                assert isinstance(subj, (BNode, URIRef, Literal))
                assert isinstance(obj , (BNode, URIRef, Literal))
                f = member(subj, obj)
                self.machine.assert_fact(f, {})

    def create_rules(self, machine: durable_reasoner.machine, location: str,
                     ) -> None:
        machine.add_init_action(self._initImport(machine, location))
