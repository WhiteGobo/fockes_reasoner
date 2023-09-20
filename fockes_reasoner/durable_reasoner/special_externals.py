from typing import Any, Union
from dataclasses import dataclass
from collections.abc import Iterable
from rdflib import Variable, URIRef
from .abc_machine import abc_external, TRANSLATEABLE_TYPES, RESOLVABLE, BINDING, _resolve
from . import abc_machine

class equality(abc_external):
    op: Any = object()
    args: Iterable[Union[TRANSLATEABLE_TYPES, "external", Variable]]
    def __init__(left: Union[TRANSLATEABLE_TYPES, "external", Variable],
                 right: Union[TRANSLATEABLE_TYPES, "external", Variable],
                 )-> None:
        self.args = [left, right]

    @dataclass
    class __resolver:
        parent: "external"
        op: Any
        args: Iterable[RESOLVABLE]
        machine: abc_machine.machine
        def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
            args = [_resolve(arg, bindings) for arg in self.args]
            return _resolve(self.machine.get_binding_action(self.op, args), bindings)

    def as_resolvable(self, machine: abc_machine.machine) -> RESOLVABLE:
        args = [arg.as_resolvable(machine) if isinstance(arg, external) else arg for arg in self.args]
        return self.__resolver(self, self.op, args, machine)
