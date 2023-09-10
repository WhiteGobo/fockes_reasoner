import abc
#from .machine import FACTTYPE, MACHINESTATE, RUNNING_STATE, machine
from . import abc_machine
import durable.engine
import durable.lang as rls
from dataclasses import dataclass

import logging
logger = logging.getLogger(__name__)

import rdflib
from rdflib import URIRef, BNode, Literal, Variable
import typing as typ
from typing import MutableMapping, Mapping, Union, Callable, Iterable, Tuple


from .abc_machine import BINDING, CLOSURE_BINDINGS, VARIABLE_LOCATOR, TRANSLATEABLE_TYPES, ATOM_ARGS, abc_external, RESOLVABLE, _resolve

from .bridge_rdflib import *
from .bridge_rdflib import term_list
from .abc_machine import fact

class external(abc_external):
    op: URIRef
    args: Iterable[Union[TRANSLATEABLE_TYPES, "external", Variable]]
    def __init__(self, op: URIRef, args: Iterable[Union[TRANSLATEABLE_TYPES, "external", Variable]]) -> None:
        self.op = op
        self.args = list(args)

    def add_pattern(self, rule: abc_machine.rule) -> None:
        rule.generate_pattern_external(self.op, self.args)

    @dataclass
    class __resolver:
        parent: "external"
        op: URIRef
        args: Iterable[RESOLVABLE]
        machine: abc_machine.machine
        def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
            args = [_resolve(arg, bindings) for arg in self.args]
            return _resolve(self.machine.get_binding_action(self.op, args), bindings)

    def as_resolvable(self, machine: abc_machine.machine) -> RESOLVABLE:
        args = [arg.as_resolvable(machine) if isinstance(arg, external) else arg for arg in self.args]
        return self.__resolver(self, self.op, args, machine)

    def __repr__(self) -> str:
        return "external %s(%s)" % (self.op, ", ".join(str(x) for x in self.args))


class machine_list(term_list):
    items: Iterable[Union[TRANSLATEABLE_TYPES, external, Variable]]
    def __init__(self, items: Iterable[Union[TRANSLATEABLE_TYPES, external, Variable]]) -> None:
        self.items = list(items)

    def __iter__(self) -> Iterator[TRANSLATEABLE_TYPES]:
        q = []
        for x in self.items:
            assert not isinstance(x, (external, Variable))
            q.append(x)
        return iter(q)


class fact_subclass(fact):
    sub_class: typ.Union[TRANSLATEABLE_TYPES, abc_external, Variable, ]
    super_class: typ.Union[TRANSLATEABLE_TYPES, abc_external, Variable]
    ID: str = "subclass"
    SUBCLASS_SUB: str = "sub"
    SUBCLASS_SUPER: str = "super"
    def __init__(self, 
                 sub_class: typ.Union[TRANSLATEABLE_TYPES, abc_external, Variable],
                 super_class: typ.Union[TRANSLATEABLE_TYPES, abc_external, Variable],
                 ) -> None:
        self.sub_class = sub_class
        self.super_class = super_class

    def check_for_pattern(self, c: abc_machine.machine,
                          bindings: BINDING = {},
                          ) -> bool:
        fact = {"type": self.ID}
        for label, x in [
                (self.SUBCLASS_SUB, self.sub_class),
                (self.SUBCLASS_SUPER, self.super_class),
                ]:
            fact[label] = _node2string(x, c, bindings)
        for _ in c.get_facts(fact):
            #triggers, when any corresponding fact is found
            return True
        return False

    def assert_fact(self, c: abc_machine.machine,
               bindings: BINDING = {},
               ) -> None:
        raise NotImplementedError()

    def add_pattern(self, rule: abc_machine.rule) -> None:
        raise NotImplementedError()

    def retract_fact(self, c: abc_machine.machine,
                bindings: BINDING = {},
                ) -> None:
        raise NotImplementedError()

    def modify_fact(self, c: abc_machine.machine,
               bindings: BINDING = {},
               ) -> None:
        raise NotImplementedError()

    @classmethod
    def from_fact(cls, fact: Mapping[str, str]) -> "fact_subclass":
        raise NotImplementedError()

class frame(fact):
    obj: typ.Union[TRANSLATEABLE_TYPES, external, Variable]
    slotkey: typ.Union[TRANSLATEABLE_TYPES, external, Variable]
    slotvalue: typ.Union[TRANSLATEABLE_TYPES, external, Variable]
    ID: str = "frame"
    FRAME_OBJ: str = "obj"
    FRAME_SLOTKEY: str = "slotkey"
    FRAME_SLOTVALUE: str = "slotvalue"
    _used_variables: Union[list[Variable], None]
    def __init__(self, obj: typ.Union[TRANSLATEABLE_TYPES, external, Variable],
                 slotkey: typ.Union[TRANSLATEABLE_TYPES, external, Variable],
                 slotvalue: typ.Union[TRANSLATEABLE_TYPES, external, Variable],
                 ) -> None:
        self.obj = obj
        self.slotkey = slotkey
        self.slotvalue = slotvalue
        self._used_variables = None

    @classmethod
    def from_fact(cls, fact: Mapping[str, str]) -> "frame":
        obj = string2rdflib(fact[cls.FRAME_OBJ])
        slotkey = string2rdflib(fact[cls.FRAME_SLOTKEY])
        slotvalue = string2rdflib(fact[cls.FRAME_SLOTVALUE])
        return cls(obj, slotkey, slotvalue)

    def assert_fact(self, c: abc_machine.machine,
               bindings: BINDING = {},
               ) -> None:
        fact = {"type": self.ID}
        for label, x, in [
                (self.FRAME_OBJ, self.obj),
                (self.FRAME_SLOTKEY, self.slotkey),
                (self.FRAME_SLOTVALUE, self.slotvalue),
                ]:
            fact[label] = _node2string(x, c, bindings)
        c.assert_fact(fact)

    def add_pattern(self, rule: abc_machine.rule) -> None:
        if isinstance(self.obj, external) or isinstance(self.slotkey, external) or isinstance(self.slotvalue, external):
            raise NotImplementedError()
        pattern: Mapping[str, Union[str, Variable, TRANSLATEABLE_TYPES]]\
                = {abc_machine.FACTTYPE: self.ID,
                   self.FRAME_OBJ: self.obj,
                   self.FRAME_SLOTKEY: self.slotkey,
                   self.FRAME_SLOTVALUE: self.slotvalue,
                   }
        rule.add_pattern(pattern)

    @property
    def used_variables(self) -> Iterable[Variable]:
        if self._used_variables is not None:
            return self._used_variables
        used_variables: list[Variable] = []
        for x in (self.obj, self.slotkey, self.slotvalue):
            if isinstance(x, Variable):
                used_variables.append(x)
        self._used_variables = used_variables
        return used_variables

    def check_for_pattern(self, c: abc_machine.machine,
                          bindings: BINDING = {},
                          ) -> bool:
        fact = {"type": self.ID}
        for label, x, in [
                (self.FRAME_OBJ, self.obj),
                (self.FRAME_SLOTKEY, self.slotkey),
                (self.FRAME_SLOTVALUE, self.slotvalue),
                ]:
            fact[label] = _node2string(x, c, bindings)
        for _ in c.get_facts(fact):
            #triggers, when any corresponding fact is found
            return True
        return False

    def retract_fact(self, c: abc_machine.machine,
                bindings: BINDING = {},
                external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], external] = {},
                ) -> None:
        fact = {"type": self.ID}
        for label, x, in [
                (self.FRAME_OBJ, self.obj),
                (self.FRAME_SLOTKEY, self.slotkey),
                (self.FRAME_SLOTVALUE, self.slotvalue),
                ]:
            fact[label] = _node2string(x, c, bindings)

        c.retract_fact(fact)

    def __repr__(self) -> str:
        return "%s[%s->%s]" % (self.obj, self.slotkey, self.slotvalue)

    def modify_fact(self, c: abc_machine.machine,
               bindings: BINDING = {},
               external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], external] = {},
               ) -> None:
        fact = {"type": self.ID}
        for label, x, in [
                (self.FRAME_OBJ, self.obj),
                (self.FRAME_SLOTKEY, self.slotkey),
                (self.FRAME_SLOTVALUE, self.slotvalue),
                ]:
            fact[label] = _node2string(x, c, bindings)

        c.retract_fact(fact)
        c.assert_fact(fact)


class member(fact):
    ID: str = "member"
    """facttype :term:`member` are labeled with this."""
    def check_for_pattern(self, c: abc_machine.machine,
                          bindings: BINDING = {},
                          ) -> bool:
        raise NotImplementedError()

    def assert_fact(self, c: abc_machine.machine,
               bindings: BINDING = {},
               ) -> None:
        raise NotImplementedError()

    def add_pattern(self, rule: abc_machine.rule) -> None:
        raise NotImplementedError()

    def retract_fact(self, c: abc_machine.machine,
                bindings: BINDING = {},
                ) -> None:
        raise NotImplementedError()

    def modify_fact(self, c: abc_machine.machine,
               bindings: BINDING = {},
               ) -> None:
        raise NotImplementedError()

    @classmethod
    def from_fact(cls, fact: Mapping[str, str]) -> "member":
        raise NotImplementedError()


class subclass(fact):
    ID: str = "subclass"
    """facttype :term:`subclass` are labeled with this."""
    def check_for_pattern(self, c: abc_machine.machine,
                          bindings: BINDING = {},
                          ) -> bool:
        raise NotImplementedError()

    def assert_fact(self, c: abc_machine.machine,
               bindings: BINDING = {},
               ) -> None:
        raise NotImplementedError()

    def add_pattern(self, rule: abc_machine.rule) -> None:
        raise NotImplementedError()

    def retract_fact(self, c: abc_machine.machine,
                bindings: BINDING = {},
                ) -> None:
        raise NotImplementedError()

    def modify_fact(self, c: abc_machine.machine,
               bindings: BINDING = {},
               ) -> None:
        raise NotImplementedError()

    @classmethod
    def from_fact(cls, fact: Mapping[str, str]) -> "subclass":
        raise NotImplementedError()

class atom(fact):
    ID: str = "atom"
    op: typ.Union[TRANSLATEABLE_TYPES, external, Variable]
    args: Iterable[RESOLVABLE]
    """facttype :term:`atom` are labeled with this."""
    ATOM_OP = "op"
    ATOM_ARGS = "args%d"
    def __init__(self, op: typ.Union[TRANSLATEABLE_TYPES, external, Variable],
                 args: Iterable[RESOLVABLE],
                 ) -> None:
        self.op = op
        self.args = tuple(args)

    def check_for_pattern(self, c: abc_machine.machine,
                          bindings: BINDING = {},
                          ) -> bool:
        fact = {"type": self.ID}
        fact[self.ATOM_OP] = _node2string(self.op, c, bindings)
        for i, x in enumerate(self.args):
            label = self.ATOM_ARGS % i
            #fact[label] = _node2string(x, c, bindings)
            fact[label] = rdflib2string(_resolve(x, bindings))
        for _ in c.get_facts(fact):
            #triggers, when any corresponding fact is found
            return True
        return False

    def assert_fact(self, c: abc_machine.machine,
               bindings: BINDING = {},
               ) -> None:
        fact = {"type": self.ID}
        fact[self.ATOM_OP] = _node2string(self.op, c, bindings)
        for i, x in enumerate(self.args):
            label = self.ATOM_ARGS % i
            fact[label] = rdflib2string(_resolve(x, bindings))
        c.assert_fact(fact)

    def add_pattern(self, rule: abc_machine.rule) -> None:
        raise NotImplementedError()

    def retract_fact(self, c: abc_machine.machine,
                bindings: BINDING = {},
                ) -> None:
        raise NotImplementedError()

    def modify_fact(self, c: abc_machine.machine,
               bindings: BINDING = {},
               ) -> None:
        raise NotImplementedError()

    @classmethod
    def from_fact(cls, fact: Mapping[str, str]) -> "atom":
        op = string2rdflib(fact[cls.ATOM_OP])
        args = []
        for i in range(len(fact)):
            try:
                arg = string2rdflib(fact[cls.ATOM_ARGS % i])
            except KeyError:
                break
            args.append(arg)
        return cls(op, args)

    def __repr__(self) -> str:
        return "%s%s" % (self.op, self.args)

def _node2string(x: Union[TRANSLATEABLE_TYPES, Variable, str, abc_external],
                 machine: abc_machine.machine,
                 bindings: BINDING,
                 ) -> str:
    if isinstance(x, rdflib.Variable):
        try:
            return rdflib2string(bindings[x])
        except KeyError as err:
            raise Exception("Tried to get not yet bind variable '%s' from %s"
                            % (x, bindings)) from err
    elif isinstance(x, (URIRef, BNode, Literal)):
        return rdflib2string(x)
    elif isinstance(x, external):
        newnode = _resolve(x.as_resolvable(machine), bindings)
        return rdflib2string(newnode)
    elif isinstance(x, str):
        raise NotImplementedError()
    else:
        raise NotImplementedError(type(x))

class retract_object_function:
    machine: abc_machine.machine
    atom: typ.Union[TRANSLATEABLE_TYPES, external, Variable]
    def __init__(self, machine: abc_machine.machine, atom: typ.Union[TRANSLATEABLE_TYPES, external, Variable]):
        self.atom = atom
        self.machine = machine

    def __call__(self, bindings: BINDING = {}) -> None:
        atom = _node2string(self.atom, self.machine, bindings)
        fact = {"type": frame.ID, frame.FRAME_OBJ: atom}
        self.machine.retract_fact(fact)

    def __repr__(self) -> str:
        return "Retract(%s)" % self.atom

