import abc
#from .machine import FACTTYPE, MACHINESTATE, RUNNING_STATE, machine
from . import abc_machine
import durable.engine
import durable.lang as rls

import logging
logger = logging.getLogger(__name__)

import rdflib
from rdflib import URIRef, BNode, Literal, Variable
import typing as typ
from typing import MutableMapping, Mapping, Union, Callable


from .abc_machine import external

from .abc_machine import BINDING, CLOSURE_BINDINGS, VARIABLE_LOCATOR, TRANSLATEABLE_TYPES

from .bridge_rdflib import *
from .abc_machine import fact

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
        for x in c.get_facts(fact):
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


class subclass(fact):
    ID: str = "subclass"
    """facttype :term:`subclass` are labeled with this."""


def _node2string(x: Union[TRANSLATEABLE_TYPES, Variable, str, external],
                 c: typ.Union[durable.engine.Closure, str],
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
        raise NotImplementedError()
        newnode = x.serialize(c, bindings)
        return newnode
    elif isinstance(x, str):
        raise NotImplementedError()
    else:
        raise NotImplementedError(type(x))
