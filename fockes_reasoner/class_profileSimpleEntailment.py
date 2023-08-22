from rdflib import Graph
from .durable_machine import importProfile, machine

class profileSimpleEntailment(importProfile):
    def create_rules(self, machine: machine, infograph: Graph) -> None:
        raise NotImplementedError()
