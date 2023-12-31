from typing import Union, Iterable, Optional, Iterator, Any, Mapping
import rdflib
from rdflib import RDF, IdentifiedNode, Graph, URIRef
from .shared import RIF
from collections.abc import Mapping
import logging
logger = logging.getLogger(__name__)
from .abc_logicMachine import PRD_logicMachine, SyntaxReject, AlgorithmRejection, ImportReject, StuckWithIncosistentInformation

from .rif_dataobjects import rif_document, rif_fact
#from .class_machineWithImport import machineWithImport
from .durable_reasoner import VariableNotBoundError, external, fact
from .durable_reasoner import special_externals, Machine
from .durable_reasoner.machine import durableMachine

from .importProfiles import export_profileRDFEntailment

class importManager(Mapping[IdentifiedNode, Graph]):
    documents: Mapping[IdentifiedNode, Graph]
    def __init__(self,
                 documents: Mapping[Union[str, IdentifiedNode], rdflib.Graph],
                 ) -> None:
        self.documents = {}
        for location, infograph in documents.items():
            if isinstance(location, IdentifiedNode):
                self.documents[location] = infograph
            else:
                self.documents[URIRef(location)] = infograph

    def __repr__(self) -> str:
        return "importManager[%s]" % ", ".join(iter(self.documents))

    def __getitem__(self, document: Union[IdentifiedNode, str]) -> Graph:
        try:
            if isinstance(document, IdentifiedNode):
                return self.documents[document]
            else:
                return self.documents[URIRef(document)]
        except KeyError:
            logger.error("tried to retrieve %s. Given documents are %s"
                         % (document, tuple(self.documents.keys())))
            raise

    def __len__(self) -> int:
        return len(self.documents)

    def __iter__(self) -> Iterator[IdentifiedNode]:
        return iter(self.documents)


class simpleLogicMachine(PRD_logicMachine):
    document: rif_document
    machine: Machine
    def __init__(self, document: rif_document,
                 extraDocuments: Optional[Mapping[str, rdflib.Graph]] = None,
                 machine: Optional[Machine] = None,
                 ) -> None:
        """
        :param machine: Use this to not use autogenerated internal logicmachine
            Use this if you want to :term:`register` own actions.
        """
        self.document = document
        #reset machine
        if machine is None:
            self.machine = durableMachine()
        else:
            self.machine = machine
        if extraDocuments is not None:
            for loc_id, information_graph in extraDocuments.items():
                q = list(information_graph)
                def get_graph() -> rdflib.Graph:
                    g = rdflib.Graph()
                    for x in q: 
                        g.add(x)
                    return g
                self.machine.register_information(loc_id, get_graph)
        try:
            self.document.create_rules(self.machine)
        except VariableNotBoundError as err:
            raise SyntaxReject() from err

    def add_stop_condition(self, rif_facts: Iterable[fact]) -> None:
        ext = external(special_externals.stop_condition.op, rif_facts)
        self.machine.apply(ext)

    def export_rdflib(self) -> Graph:
        return export_profileRDFEntailment(self.machine)

    def check(self, rif_facts: Iterable[rif_fact]) -> bool:
        checks = {f: f.check(self.machine) for f in rif_facts}
        logger.debug("Checks: %s" % checks)
        return all(checks.values())

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 extraDocuments: Optional[Mapping[str, rdflib.Graph]] = None,
                 **kwargs: Any,
                 ) -> "simpleLogicMachine":
        """
        :param kwargs: Is directed to __init__. See __init__ for valid
            arguments
        """
        extraOptions = {}
        if extraDocuments is not None:
            extraOptions["extraDocuments"] = importManager(extraDocuments)
        rootdocument_node: IdentifiedNode
        rootdocument_node,\
                = infograph.subjects(RDF.type, #type: ignore[assignment]
                                     RIF.Document)
                                                
        document = rif_document.from_rdf(infograph, rootdocument_node, **extraOptions)
        return cls(document, extraDocuments, **kwargs)

    def run(self, steps: Union[int, None] = None) -> None:
        try:
            if steps is None:
                self.machine.run()
            else:
                self.machine.run(steps)
        except Exception as err:
            if self.machine.inconsistent_information:
                raise StuckWithIncosistentInformation() from err
            else:
                raise
        myfacts = self.machine.get_facts()
