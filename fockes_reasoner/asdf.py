from typing import Union
import rdflib
from rdflib import RDF, IdentifiedNode
from .shared import RIF
import logging
logger = logging.getLogger(__name__)

from .rif_dataobjects import rif_document
from .durable_reasoner.machine import durable_machine as machine

class simpleLogicMachine:
    document: rif_document
    def __init__(self, document: rif_document):
        self.document = document
        #reset machine
        self.machine = machine()
        self.document.create_rules(self.machine)

    def check(self, rif_facts) -> bool:
        checks = {f: f.check(self.machine) for f in rif_facts}
        logger.debug("Checks: %s" % checks)
        return all(checks.values())

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph) -> "simpleLogicMachine":
        rootdocument_node: IdentifiedNode
        rootdocument_node,\
                = infograph.subjects(RDF.type, #type: ignore[assignment]
                                     RIF.Document)
                                                
        document = rif_document.from_rdf(infograph, rootdocument_node)
        return cls(document)

    def run(self, steps: Union[int, None] = None) -> None:
        if steps is None:
            self.machine.run()
        else:
            self.machine.run(steps)
        myfacts = self.machine.get_facts()
        return myfacts
