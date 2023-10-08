from rdflib import Graph, IdentifiedNode
from rdflib.term import Node, Node
from .durable_reasoner import importProfile, machine, fact, frame, TRANSLATEABLE_TYPES, subclass, member
from rdflib import IdentifiedNode, Literal, URIRef, BNode, RDF, RDFS
from typing import Union, Any, List, Dict, Mapping
from dataclasses import dataclass

def import_profileRDFSEntailment(machine, location):
    helper = profileRDFSEntailment._initImport(machine, location)
    helper({})

def export_profileRDFEntailment(machine):
    data = machine.get_facts()
    for tmp_fact in data:
        if isinstance(tmp_fact, frame):
            axiom = (tmp_fact.obj, tmp_fact.slotkey, tmp_fact.slotvalue)
            if any(not isinstance(x, Node) for x in axiom):
                raise NotImplementedError("lists are not yet supported")
            yield axiom
        elif isinstance(tmp_fact, atom):
            raise NotImplementedError()
        elif isinstance(tmp_fact, subclass):
            raise NotImplementedError()
        elif isinstance(tmp_fact, member):
            raise NotImplementedError()
        else:
            raise Exception(tmp_fact)


class profileRDFSEntailment(importProfile):
    """
    See `https://www.w3.org/TR/2013/REC-rif-rdf-owl-20130205/#RDF_Compatibility`_ for more information.
    """
    @dataclass
    class _initImport:
        machine: machine
        location: Union[str, IdentifiedNode]
        def __call__(self, bindings: Any) -> None:
            mapping: Dict[Node, Union[Node, List[Node]]] = {}
            infograph = Graph()
            for ax in self.machine.load_external_resource(self.location):
                infograph.add(ax)
            mapping.update(self.extract_lists(infograph))#type: ignore[arg-type]
            self.load_types(infograph)
            self.load_subclasses(infograph)
            self.load_subproperties(infograph)
            self.load_axiom_as_frames(infograph, mapping)

        def load_types(self, infograph: Graph) -> None:
            for subj, obj in infograph.subject_objects(RDF.type):
                infograph.remove((subj, RDF.type, obj))
                assert isinstance(subj, (BNode, URIRef, Literal))
                assert isinstance(obj , (BNode, URIRef, Literal))
                f = member(subj, obj)
                self.machine.assert_fact(f, {})

        def load_subclasses(self, infograph: Graph) -> None:
            for subj, obj in infograph.subject_objects(RDFS.subClassOf):
                infograph.remove((subj, RDFS.subClassOf, obj))
                assert isinstance(subj, (BNode, URIRef, Literal))
                assert isinstance(obj , (BNode, URIRef, Literal))
                f = subclass(subj, obj)
                self.machine.assert_fact(f, {})

        def load_subproperties(self, infograph: Graph) -> None:
            for subj, obj in infograph.subject_objects(RDFS.subPropertyOf):
                infograph.remove((subj, RDFS.subPropertyOf, obj))
                #assert isinstance(subj, (BNode, URIRef, Literal))
                #assert isinstance(obj , (BNode, URIRef, Literal))
                #f = frame(subj, RDF.subPropertyOf, obj)
                #f.assert_fact(self.machine)

        def extract_lists(self, infograph: Graph)-> Dict[IdentifiedNode, List[Node]]:
            mylists: Dict[IdentifiedNode, List[Node]] = {RDF.nil: []}
            found: List[IdentifiedNode] = [RDF.nil]
            for obj in found:
                for subj in infograph.subjects(RDF.rest, obj):
                    infograph.remove((subj, RDF.rest, obj))
                    assert isinstance(subj, IdentifiedNode)
                    found.append(subj)
                    item, = infograph.objects(subj, RDF.first)
                    mylists[subj] = [item] + mylists[obj]
                    infograph.remove((subj, RDF.first, item))
            return mylists

        def load_axiom_as_frames(
                self,
                infograph: Graph,
                replacements: Mapping[Node, Union[Node, List[Node]]],
                ) -> None:
            """
            :TODO: lists as replacement are not yet supported.
            """
            for subj, pred, obj in infograph:
                assert isinstance(subj, (BNode, URIRef, Literal))
                assert isinstance(pred, (BNode, URIRef, Literal))
                assert isinstance(obj , (BNode, URIRef, Literal))
                subj_ = replacements.get(subj, subj)
                pred_ = replacements.get(pred, pred)
                obj_ = replacements.get(obj, obj)
                assert isinstance(subj_, (BNode, URIRef, Literal))
                assert isinstance(pred_, (BNode, URIRef, Literal))
                assert isinstance(obj_ , (BNode, URIRef, Literal))
                f = frame(subj_, pred_, obj_)
                self.machine.assert_fact(f, {})


    def create_rules(self, machine: machine, location: str) -> None:
        machine.add_init_action(self._initImport(machine, location))
