from rdflib import Graph
from .durable_reasoner import importProfile, machine, fact, frame, TRANSLATEABLE_TYPES, subclass, member
from rdflib import IdentifiedNode, Literal, URIRef, BNode, RDF, RDFS
from typing import Union, Any
from dataclasses import dataclass


class profileRDFSEntailment(importProfile):
    """
    See `https://www.w3.org/TR/2013/REC-rif-rdf-owl-20130205/#RDF_Compatibility`_ for more information.
    """
    @dataclass
    class _initImport:
        machine: machine
        location: Union[str, IdentifiedNode]
        def __call__(self, bindings: Any) -> None:
            infograph = Graph()
            for ax in self.machine.load_external_resource(self.location):
                infograph.add(ax)
            mylists = self.extract_lists(infograph)
            self.load_types(infograph)
            self.load_subclasses(infograph)
            self.load_subproperties(infograph)
            self.load_axiom_as_frames(infograph, mylists)

        def load_types(self, infograph):
            for subj, obj in infograph.subject_objects(RDF.type):
                infograph.remove((subj, RDF.type, obj))
                assert isinstance(subj, (BNode, URIRef, Literal))
                assert isinstance(obj , (BNode, URIRef, Literal))
                f = member(subj, obj)
                f.assert_fact(self.machine)

        def load_subclasses(infograph):
            for subj, obj in infograph.subject_objects(RDFS.subClassOf):
                infograph.remove((subj, RDFS.subClassOf, obj))
                assert isinstance(subj, (BNode, URIRef, Literal))
                assert isinstance(obj , (BNode, URIRef, Literal))
                f = subclass(subj, obj)
                f.assert_fact(self.machine)

        def load_subproperties(infograph):
            for subj, obj in infograph.subject_objects(RDFS.subPropertyOf):
                infograph.remove((subj, RDFS.subPropertyOf, obj))
                #assert isinstance(subj, (BNode, URIRef, Literal))
                #assert isinstance(obj , (BNode, URIRef, Literal))
                #f = frame(subj, RDF.subPropertyOf, obj)
                #f.assert_fact(self.machine)

        def extract_lists(self, infograph):
            mylists = {RDF.nil: []}
            found = [RDF.nil]
            for obj in found:
                for subj in infograph.subjects(RDF.rest, obj):
                    infograph.remove((subj, RDF.rest, obj))
                    found.append(subj)
                    item, = infograph.objects(obj, RDF.first)
                    mylists[subj] = [item] + mylists[obj]
            return mylists

        def load_axiom_as_frames(self, infograph, replacements):
            for subj, pred, obj in infograph:
                assert isinstance(subj, (BNode, URIRef, Literal))
                assert isinstance(pred, (BNode, URIRef, Literal))
                assert isinstance(obj , (BNode, URIRef, Literal))
                subj = replacements.get(subj, subj)
                pred = replacements.get(pred, pred)
                obj = replacements.get(obj, obj)
                f = frame(subj, pred, obj)
                f.assert_fact(self.machine)


    def create_rules(self, machine: machine, location: str) -> None:
        machine.add_init_action(self._initImport(machine, location))
