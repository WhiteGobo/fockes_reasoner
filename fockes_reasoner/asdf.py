from typing import Union
import rdflib
from rdflib import RDF
from .shared import RIF

from .rif_dataobjects import rif_document
from .durable_reasoner.machine import machine

class simpleLogicMachine:
    document: rif_document
    def __init__(self, document: rif_document):
        self.document = document

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph) -> "simpleLogicMachine":
        rootdocument_node, = infograph.subjects(RDF.type, RIF.Document)
        document = rif_document.from_rdf(infograph, rootdocument_node)
        return cls(document)

    def run(self, steps: Union[int, None] = None):
        mymachine = machine()
        self.document.create_rules(mymachine)
        if steps is None:
            mymachine.run()
        else:
            mymachine.run(steps)
        myfacts = mymachine.get_facts()
        raise Exception(myfacts)

