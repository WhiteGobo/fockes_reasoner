from typing import Iterable, Mapping, Any, Callable, MutableMapping
import rdflib
from rdflib import RDF, Graph, URIRef, IdentifiedNode
from .shared import RIF
from .durable_reasoner import fact, frame
from .rif_dataobjects import slot2node, rif_frame, rif_assert, rif_retract, rif_modify, rif_do, rif_and, rif_external

DEFAULT_REGISTER: Mapping[URIRef, Callable[[Graph, IdentifiedNode], Any]]\
        = {RIF.Frame: rif_frame.from_rdf,
           RIF.Assert: rif_assert.from_rdf,
           RIF.Retract: rif_retract.from_rdf,
           RIF.Modify: rif_modify.from_rdf,
           RIF.Var: slot2node,
           RIF.Do: rif_do.from_rdf,
           RIF.And: rif_and.from_rdf,
           RIF.External: rif_external.from_rdf,
           #RIF.constIRI: slot2node,
           RIF.Const: slot2node,
           }

class rdfmodel:
    registered_types: MutableMapping[rdflib.URIRef, Callable[[Graph, IdentifiedNode], Any]]
    def __init__(self, registered_types = DEFAULT_REGISTER) -> None:
        self.registered_types = dict(registered_types)

    def export_graph(self, facts: Iterable[fact]) -> rdflib.Graph:
        raise NotImplementedError()

    def import_graph(self, infograph: rdflib.Graph) -> Iterable[fact]:
        """Import all available objects from given graph

        :TODO: This might be a little problematic. It should be more restrictive. see test_rif_basic
        """
        for typeref, generator in self.registered_types.items():
            for node in infograph.subjects(RDF.type, typeref):
                yield generator(infograph, node)

    def generate_object(self, infograph: Graph, target: IdentifiedNode) -> Any:
        target_type = infograph.value(target, RDF.type)
        return self.registered_types[target_type](infograph, target)
