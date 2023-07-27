from . import model_abc
from collections.abc import Iterator, Container, Mapping, Iterable
import rdflib
from ..durable_reasoner import durable_abc as dur_abc
from ..shared import focke, string2rdflib, rdflib2string

class filtered_rdf_export(model_abc.export_model):
    def export(self, factiterator: Iterable[Mapping[str, str]],
               objects_for_export: Container[str] = [],
               predicates_for_export: Iterable[str] = []) -> Iterator[tuple]:
        predicates_for_export = set().union(predicates_for_export)
        #factiterator = rls.get_facts(self.rulename)
        for fact in factiterator:
            if fact[dur_abc.FACTTYPE] == dur_abc.FRAME:
                if fact[dur_abc.FRAME_SLOTKEY] in predicates_for_export:
                    #Here the model should translate the frame to a rdf axiom
                    s = string2rdflib(fact[dur_abc.FRAME_OBJ])
                    p = string2rdflib(fact[dur_abc.FRAME_SLOTKEY])
                    o = string2rdflib(fact[dur_abc.FRAME_SLOTVALUE])
                    yield (s, p, o)
            elif fact[dur_abc.FACTTYPE] == dur_abc.LIST:
                if fact[dur_abc.LIST_ID] in objects_for_export:
                    g = rdflib.Graph()
                    b = string2rdflib(fact[dur_abc.LIST_ID])
                    q = [string2rdflib(x) for x in fact[dur_abc.LIST_MEMBERS]]
                    rdflib.collection.Collection(g, b, q)
                    for ax in g:
                        yield ax
