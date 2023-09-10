from typing import Any
from .durable_reasoner.machine import durable_machine as machine
from .durable_reasoner.abc_machine import importProfile
from .class_profileSimpleEntailment import profileSimpleEntailment
from .class_rifImportProfile import rifImportProfile
from rdflib import URIRef, Namespace, IdentifiedNode
RIF_ENTAILMENT = Namespace("http://www.w3.org/ns/entailment/")

class machineWithImport(machine):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        q = profileSimpleEntailment()
        self.available_import_profiles[None] = rifImportProfile()
        self.available_import_profiles[RIF_ENTAILMENT.Simple]\
                = profileSimpleEntailment()
