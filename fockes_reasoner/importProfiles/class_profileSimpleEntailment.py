from rdflib import Graph
from ..durable_reasoner import Machine, fact, frame, TRANSLATEABLE_TYPES
from rdflib import IdentifiedNode, Literal, URIRef, BNode
from typing import Union, Any
from dataclasses import dataclass

def import_profileSimpleEntailment(machine: Machine,
                                   location: Union[str, IdentifiedNode],
                                   ) -> None:
    infograph = machine.load_external_resource(location)
    for subj, pred, obj in infograph:
        assert isinstance(subj, (BNode, URIRef, Literal))
        assert isinstance(pred, (BNode, URIRef, Literal))
        assert isinstance(obj , (BNode, URIRef, Literal))
        f = frame(subj, pred, obj)
        machine.assert_fact(f, {})

class profileSimpleEntailment:
    """
    See `https://www.w3.org/TR/2013/REC-rif-rdf-owl-20130205/#RDF_Compatibility`_ for more information.
    """
    @dataclass
    class _initImport:
        machine: Machine
        location: Union[str, IdentifiedNode]
        def __call__(self, bindings: Any) -> None:
            infograph = self.machine.load_external_resource(self.location)
            for subj, pred, obj in infograph:
                assert isinstance(subj, (BNode, URIRef, Literal))
                assert isinstance(pred, (BNode, URIRef, Literal))
                assert isinstance(obj , (BNode, URIRef, Literal))
                f = frame(subj, pred, obj)
                self.machine.assert_fact(f, {})

    def create_rules(self, machine: Machine, location: str) -> None:
        raise Exception()
        #machine.add_init_action(self._initImport(machine, location))
