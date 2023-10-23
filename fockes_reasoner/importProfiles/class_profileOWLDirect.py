from rdflib import Graph, URIRef
from rdflib.term import Node
from .. import durable_reasoner
from ..durable_reasoner import fact, TRANSLATEABLE_TYPES, member, rdfs_subclass, frame
from rdflib import IdentifiedNode, Literal, URIRef, BNode
from typing import Union, Any, Dict, List
from dataclasses import dataclass
from ..shared import entailment, OWL, RDF, RDFS
import logging
logger = logging.getLogger(__name__)

def import_profileOWLDirect(machine: durable_reasoner.Machine, location: str,
                            ) -> None:
    helper = profileOWLDirect._initImport(machine, location)
    helper({})


class profileOWLDirect:
    """
    See `https://www.w3.org/TR/2013/REC-rif-rdf-owl-20130205/#RDF_Compatibility`_ for more information.
    """
    ID: URIRef = entailment["OWL-Direct"]
    """IRI to identify if this profile should be used for import"""

    @dataclass
    class _initImport:
        machine: durable_reasoner.Machine
        location: Union[str, IdentifiedNode]
        def __call__(self, bindings: Any) -> None:
            infograph = self.machine.load_external_resource(self.location)
            self.extract_annotations(infograph)
            logger.debug("read owl information without annotations:\n%s"
                         % infograph.serialize())
            #constructs = self.load_constructs(infograph)
            self.load_constructs(infograph)
            mylists = self.extract_lists(infograph)
            self.load_ObjectProperties(infograph)
            self.load_ClassInformation(infograph)
            self.load_types(infograph)
            self.load_subclasses(infograph)
            rest_info = list(infograph)
            if rest_info:
                logger.warning("Didnt convert all information from owl "
                               "ontology:\n%s" % infograph.serialize())
            self.load_frames(infograph)

        def extract_annotations(self, infograph: Graph) -> None:
            ontology_id, = infograph.subjects(RDF.type, OWL.Ontology)
            infograph.remove((ontology_id, RDF.type, OWL.Ontology))
            for annotation_type in [OWL.OntologyProperty]:
                for pred in infograph.subjects(RDF.type, annotation_type):
                    infograph.remove((pred, RDF.type, annotation_type))
                    for subj, obj in infograph.subject_objects(pred):
                        infograph.remove((subj, pred, obj))

        def load_frames(self, infograph: Graph) -> None:
            for subj, pred, obj in infograph:
                #infograph.remove((subj, pred, obj))
                assert isinstance(subj, (IdentifiedNode, Literal))
                assert isinstance(pred, (IdentifiedNode, Literal))
                assert isinstance(obj, (IdentifiedNode, Literal))
                f = frame(subj, pred, obj)
                self.machine.assert_fact(f, {})

        def load_constructs(self, infograph: Graph) -> None:
            for construct, info in infograph.subject_objects(OWL.unionOf):
                infograph.remove((construct, OWL.unionOf, info))

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

        def load_ObjectProperties(self, infograph: Graph) -> None:
            for prop in infograph.subjects(RDF.type, OWL.ObjectProperty):
                infograph.remove((prop, RDF.type, OWL.ObjectProperty))
                assert isinstance(prop, (IdentifiedNode, Literal))
                f = frame(prop, RDF.type, OWL.ObjectProperty)
                self.machine.assert_fact(f, {})
                for pred, info in infograph.predicate_objects(prop):
                    if pred == RDFS.domain:
                        infograph.remove((prop, pred, info))
                    elif pred == RDFS.range:
                        infograph.remove((prop, pred, info))
                    elif pred == RDF.type:
                        infograph.remove((prop, pred, info))
                    else:
                        raise NotImplementedError(pred, info)


        def load_ClassInformation(self, infograph: Graph) -> None:
            for cls in infograph.subjects(RDF.type, OWL.Class):
                infograph.remove((cls, RDF.type, OWL.ObjectProperty))
                for pred, info in infograph.predicate_objects(cls):
                    if pred == RDF.type:
                        infograph.remove((cls, pred, info))
                    elif pred == RDFS.subClassOf:
                        infograph.remove((cls, RDFS.subClassOf, info))
                        assert isinstance(info , (IdentifiedNode, Literal))
                        assert isinstance(cls , (IdentifiedNode, Literal))
                        f = rdfs_subclass(cls, info)
                        self.machine.assert_fact(f, {})
                    else:
                        raise NotImplementedError(pred, info)

        def load_types(self, infograph: Graph) -> None:
            for subj, obj in infograph.subject_objects(RDF.type):
                if obj == OWL.Ontology:
                    continue
                infograph.remove((subj, RDF.type, obj))
                assert isinstance(subj, (BNode, URIRef, Literal))
                assert isinstance(obj , (BNode, URIRef, Literal))
                #f = member(subj, obj)
                f = frame(subj, RDF.type, obj)
                self.machine.assert_fact(f, {})

        def load_subclasses(self, infograph: Graph) -> None:
            for subj, obj in infograph.subject_objects(RDFS.subClassOf):
                infograph.remove((subj, RDFS.subClassOf, obj))
                assert isinstance(subj, (BNode, URIRef, Literal))
                assert isinstance(obj , (BNode, URIRef, Literal))
                f = rdfs_subclass(subj, obj)
                self.machine.assert_fact(f, {})

    def create_rules(self, machine: durable_reasoner.Machine, location: str,
                     ) -> None:
        #machine.add_init_action(self._initImport(machine, location))
        raise Exception()
