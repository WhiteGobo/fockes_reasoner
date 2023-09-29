from dataclasses import dataclass
from collections.abc import Iterable
from . import abc_machine
from .abc_machine import abc_action, machine, fact, BINDING

class action_assert(abc_action):
    facts: Iterable[fact]
    machine: machine
    def __init__(self, facts: Iterable[fact], machine: abc_machine.machine,
                 ) -> None:
        self.facts = list(facts)
        self.machine = machine

    def __call__(self, bindings: BINDING) -> None:
        for f in self.facts:
            self.machine.assert_fact(f, bindings)


class action_retract(abc_action):
    facts: Iterable[fact]
    machine: machine
    def __init__(self, facts: Iterable[fact], machine: abc_machine.machine,
                 ) -> None:
        self.facts = list(facts)
        self.machine = machine

    def __call__(self, bindings: BINDING) -> None:
        for f in self.facts:
            self.machine.retract_fact(f, bindings)
