from typing import Any
from .durable_reasoner.machine import durableMachine
from .importProfiles import import_profileOWLDirect,\
        import_profileSimpleEntailment,\
        import_profileRDFSEntailment
from rdflib import URIRef, Namespace, IdentifiedNode
RIF_ENTAILMENT = Namespace("http://www.w3.org/ns/entailment/")

class machineWithImport(durableMachine):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        #q = profileSimpleEntailment()
        #self.available_import_profiles[None] = rifImportProfile()
        #self.available_import_profiles[RIF_ENTAILMENT.Simple]\
                #        = profileSimpleEntailment()
        #self.available_import_profiles[RIF_ENTAILMENT.RDF]\
                #        = profileSimpleEntailment()
        #self.available_import_profiles[RIF_ENTAILMENT.RDFS]\
                #        = profileRDFSEntailment()
