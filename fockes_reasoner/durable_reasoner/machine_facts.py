import abc
from .machine import FACTTYPE, MACHINESTATE, RUNNING_STATE, machine
import durable.engine
import durable.lang as rls

import logging
logger = logging.getLogger(__name__)

import rdflib
from rdflib import URIRef, BNode, Literal
import typing as typ
from typing import MutableMapping, Mapping, Union, Callable


class external(abc.ABC):
    """Parentclass for all extension for information representation."""
    @abc.abstractmethod
    @classmethod
    def parse(cls, string: str) -> "external":
        ...

    @abc.abstractmethod
    def serialize(self, c: typ.Union[durable.engine.Closure, str],
                  bindings: BINDING,
                  external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], external],
                  ) -> str:
        ...

TRANSLATEABLE_TYPES = typ.Union[rdflib.Variable,
                                rdflib.URIRef,
                                rdflib.BNode,
                                rdflib.Literal,
                                list["TRANSLATEABLE_TYPES"],
                                external,
                                ]
BINDING = MutableMapping[rdflib.Variable, str]
VARIABLE_LOCATOR = Callable[[typ.Union[durable.engine.Closure, None]], TRANSLATEABLE_TYPES]
CLOSURE_BINDINGS = MutableMapping[rdflib.Variable, VARIABLE_LOCATOR]


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


class fact(abc.ABC):
    @abc.abstractmethod
    def assert_fact(self, c: machine,
               bindings: BINDING = {},
               external_resolution: Mapping[Union[rdflib.URIRef,
                                                  rdflib.BNode], external] = {},
               ) -> None:
        ...

    @abc.abstractmethod
    def generate_pattern(self, bindings: CLOSURE_BINDINGS,
                         factname: str) -> rls.value:
        ...

    @abc.abstractmethod
    def retract_fact(self, c: machine,
                bindings: BINDING = {},
                external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], external] = {},
                ) -> None:
        ...

    @abc.abstractmethod
    def modify_fact(self, c: machine,
               bindings: BINDING = {},
               external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], external] = {},
               ) -> None:
        ...


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

    def assert_fact(self, c: machine,
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

    def generate_pattern(self, bindings: CLOSURE_BINDINGS,
                                  factname: str) -> rls.value:
        """Used to generate a pattern for when_all method of durable"""
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

    def retract_fact(self, c: machine,
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

    def modify_fact(self, c: machine,
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
    MEMBER = "member"
    """facttype :term:`member` are labeled with this."""


class subclass(fact):
    SUBCLASS = "subclass"
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
            return bindings[x]
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
