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

def rdflib2string(identifier: TRANSLATEABLE_TYPES) -> str:
    """Translates from rdflib to strings.
    Inverse to string2rdflib.
    """
    if isinstance(identifier, rdflib.URIRef):
        return f"<{identifier}>"
    elif isinstance(identifier, rdflib.BNode):
        return f"_:{identifier}"
    elif isinstance(identifier, rdflib.Literal):
        parts = ["'%s'"%identifier.value]
        if identifier.datatype:
            parts.append("^^<%s>" % identifier.datatype)
        try:
            if identifier.language:
                parts.append("@%s" % identifier.language)
        except AttributeError:
            pass
        return "".join(parts)
    elif type(identifier) == list:
        raise NotImplementedError(type(identifier), identifier)
    else:
        raise NotImplementedError(type(identifier), identifier)


def string2rdflib(string: str) -> TRANSLATEABLE_TYPES:
    """Translates from rdflib to strings. Inverse to rdflib2string
    """
    try:
        return rdf_identifier.parse_string(string)[0]# type: ignore[no-any-return]
    except Exception as err:
        pass
    raise NotImplementedError("Currently no lists and externals are supported"
                              "happend with %r" % string)


from .abc_machine import fact

class frame(fact):
    obj: typ.Union[TRANSLATEABLE_TYPES, external]
    slotkey: typ.Union[TRANSLATEABLE_TYPES, external]
    slotvalue: typ.Union[TRANSLATEABLE_TYPES, external]
    ID = "frame"
    FRAME_OBJ: str = "obj"
    FRAME_SLOTKEY: str = "slotkey"
    FRAME_SLOTVALUE: str = "slotvalue"
    def __init__(self, obj: typ.Union[TRANSLATEABLE_TYPES, external],
                 slotkey: typ.Union[TRANSLATEABLE_TYPES, external],
                 slotvalue: typ.Union[TRANSLATEABLE_TYPES, external],
                 ) -> None:
        self.obj = obj
        self.slotkey = slotkey
        self.slotvalue = slotvalue

    @classmethod
    def from_fact(cls, fact: Mapping[str, str]) -> "frame":
        obj = string2rdflib(fact[cls.FRAME_OBJ])
        slotkey = string2rdflib(fact[cls.FRAME_SLOTKEY])
        slotvalue = string2rdflib(fact[cls.FRAME_SLOTVALUE])
        return cls(obj, slotkey, slotvalue)

    def assert_fact(self, c: abc_machine.machine,
               bindings: BINDING = {},
               external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], external] = {},
               ) -> None:
        fact = {"type": self.ID}
        for label, x, in [
                (self.FRAME_OBJ, self.obj),
                (self.FRAME_SLOTKEY, self.slotkey),
                (self.FRAME_SLOTVALUE, self.slotvalue),
                ]:
            fact[label] = _node2string(x, c, bindings, external_resolution)
        c.assert_fact(fact)


    def add_pattern(self, rule: abc_machine.rule) -> None:
        pattern = {abc_machine.FACTTYPE: self.ID,
                   self.FRAME_OBJ: self.obj,
                   self.FRAME_SLOTKEY: self.slotkey,
                   self.FRAME_SLOTVALUE: self.slotvalue,
                   }
        rule.add_pattern(pattern)

    def generate_pattern(self, bindings: CLOSURE_BINDINGS,
                         factname: Union[str, None] = None) -> rls.value:
        """Used to generate a pattern for when_all method of durable"""
        raise Exception("not used anymore")
        if factname is None:
            factname = "f%s" % uuid.uuid3(uuid.NAMESPACE_X500,
                                          str((self.obj,self.slotkey,
                                               self.slotvalue)))
        from .machine import FACTTYPE, MACHINESTATE, RUNNING_STATE
        log = [f"rls.m.{FACTTYPE} == {self.ID}"]
        pattern = (getattr(rls.m, FACTTYPE) == self.ID)
        for fact_label, value in [
                (self.FRAME_OBJ, self.obj),
                (self.FRAME_SLOTKEY, self.slotkey),
                (self.FRAME_SLOTVALUE, self.slotvalue),
                ]:
            if isinstance(value, rdflib.Variable):
                if value in bindings:
                    loc = bindings[value]
                    log.append(f"rls.m.{fact_label} == {loc}")
                    newpattern = getattr(rls.m, fact_label) == loc(rls.c)
                    pattern = pattern & newpattern
                else:
                    loc = value_locator(factname, fact_label)
                    bindings[value] = loc
                    logger.debug("bind: %r-> %r" % (value, loc))
            else:
                try:
                    fact_value: str = rdflib2string(value)
                except NotImplementedError as err:
                    raise Exception("failed to generate pattern for %r becaus"
                                    "e of value for %s"
                                    % (self, fact_label)) from err
                log.append(f"rls.m.{fact_label} == %r" % fact_value)
                newpattern = getattr(rls.m, fact_label) == fact_value
                pattern = pattern & newpattern
        logger.debug(f"{factname} << %s" % " & ".join(log))
        return getattr(rls.c, factname) << pattern

    @property
    def used_variables(self) -> Iterable[Variable]:
        try:
            return self._used_variables
        except AttributeError:
            pass
        used_variables = []
        for x in (self.obj, self.slotkey, self.slotvalue):
            if isinstance(x, Variable):
                used_variables.append(x)
        self._used_variables = used_variables
        return used_variables

    def check_for_pattern(self, c: abc_machine.machine,
                          bindings: BINDING = {},
                          external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], external] = {},
                          ) -> bool:
        self.assert_fact(c, bindings, external_resolution)
        logger.info(list(c.get_facts()))
        raise NotImplementedError()

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
            fact[label] = _node2string(x, c, bindings, external_resolution)

        c.retract_fact(fact)

    def __repr__(self):
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
            fact[label] = _node2string(x, c, bindings, external_resolution)

        c.retract_fact(fact)
        c.assert_fact(fact)


class member(fact):
    ID = "member"
    """facttype :term:`member` are labeled with this."""


class subclass(fact):
    ID = "subclass"
    """facttype :term:`subclass` are labeled with this."""


class value_locator:
    factname: str
    """Name of the fact, where the variable is defined"""
    in_fact_label: str
    """Position in fact, where the variable is defined"""
    def __init__(self, factname: str, in_fact_label: str):
        self.factname = factname
        self.in_fact_label = in_fact_label

    def __call__(self,
                 c: typ.Union[durable.engine.Closure, rls.closure],
                 ) -> typ.Union[TRANSLATEABLE_TYPES, rls.value]:
        fact = getattr(c, self.factname)
        return getattr(fact, self.in_fact_label)

    def __repr__(self) -> str:
        return f"%s(c.{self.factname}.{self.in_fact_label})"\
                % type(self).__name__


def _node2string(x: TRANSLATEABLE_TYPES,
                 c: typ.Union[durable.engine.Closure, str],
                 bindings: BINDING,
                 external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], external],
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
        newnode = x.serialize(c, bindings, external_resolution)
        return newnode
    else:
        raise NotImplementedError(type(x))
