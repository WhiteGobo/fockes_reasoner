from typing import Union, Iterable, Optional, Iterator
import rdflib
from rdflib import RDF, IdentifiedNode, Graph, URIRef
from .shared import RIF
from collections.abc import Mapping
import logging
logger = logging.getLogger(__name__)

from .rif_dataobjects import rif_document, rif_fact
from .class_machineWithImport import machineWithImport as machine

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

    def __getitem__(self, document: IdentifiedNode) -> Graph:
        try:
            return self.documents[document]
        except KeyError:
            logger.error("tried to retrieve %s. Given documents are %s"
                         % (document, tuple(self.documents.keys())))
            raise

    def __len__(self) -> int:
        return len(self.documents)

    def __iter__(self) -> Iterator[IdentifiedNode]:
        return iter(self.documents)


class simpleLogicMachine:
    document: rif_document
    def __init__(self, document: rif_document):
        self.document = document
        #reset machine
        self.machine = machine()
        self.document.create_rules(self.machine)

    def check(self, rif_facts: Iterable[rif_fact]) -> bool:
        checks = {f: f.check(self.machine) for f in rif_facts}
        logger.debug("Checks: %s" % checks)
        return all(checks.values())

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 extraDocuments: Optional[Mapping[str, rdflib.Graph]] = None,
                 ) -> "simpleLogicMachine":
        extraOptions = {}
        if extraDocuments is not None:
            extraOptions["extraDocuments"] = importManager(extraDocuments)
        rootdocument_node: IdentifiedNode
        rootdocument_node,\
                = infograph.subjects(RDF.type, #type: ignore[assignment]
                                     RIF.Document)
                                                
        document = rif_document.from_rdf(infograph, rootdocument_node, **extraOptions)
        return cls(document)

    def run(self, steps: Union[int, None] = None) -> None:
        if steps is None:
            self.machine.run()
        else:
            self.machine.run(steps)
        myfacts = self.machine.get_facts()
