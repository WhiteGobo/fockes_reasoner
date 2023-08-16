from typing import Iterable, Mapping, Any, Callable, MutableMapping
import rdflib
from rdflib import RDF, Graph, URIRef, IdentifiedNode
from .shared import RIF
from .durable_reasoner import fact, frame
from .rif_dataobjects import slot2node, rif_frame

DEFAULT_REGISTER: Mapping[rdflib.URIRef, Callable[[Graph, IdentifiedNode], Any]]\
        = {RIF.Frame: rif_frame.from_rdf,
            RIF.Var: slot2node,
            #RIF.constIRI: slot2node,
            #RIF.RIF.Const: slot2node,
            }

class rdfmodel:
    registered_types: MutableMapping[rdflib.URIRef, Callable[[Graph, IdentifiedNode], Any]]
    def __init__(self, registered_types = DEFAULT_REGISTER) -> None:
        self.registered_types = dict(registered_types)

    def export_graph(self, facts: Iterable[fact]) -> rdflib.Graph:
        raise NotImplementedError()

    def import_graph(self, infograph: rdflib.Graph) -> Iterable[fact]:
        for typeref, generator in self.registered_types.items():
            for node in infograph.subjects(RDF.type, typeref):
                yield generator(infograph, node)

    def generate_object(self, infograph: Graph, target: IdentifiedNode) -> Any:
        target_type = infograph.value(target, RDF.type)
        return self.registered_types[target_type](infograph, target)
