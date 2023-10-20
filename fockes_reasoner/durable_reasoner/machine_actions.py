from dataclasses import dataclass
from rdflib import Variable
import typing as typ
from collections.abc import Iterable
from . import abc_machine
from .abc_machine import abc_action, Machine, fact, BINDING, TRANSLATEABLE_TYPES, abc_external

class action_assert(abc_action):
    facts: Iterable[fact]
    machine: Machine
    def __init__(self, facts: Iterable[fact], machine: Machine,
                 ) -> None:
        raise Exception()
        self.facts = list(facts)
        self.machine = machine

    def __call__(self, bindings: BINDING) -> None:
        for f in self.facts:
            self.machine.assert_fact(f, bindings)


class action_retract(abc_action):
    facts: Iterable[fact]
    machine: Machine
    def __init__(self, facts: Iterable[fact], machine: Machine,
                 ) -> None:
        self.facts = list(facts)
        self.machine = machine

    def __call__(self, bindings: BINDING) -> None:
        for f in self.facts:
            self.machine.retract_fact(f, bindings)

