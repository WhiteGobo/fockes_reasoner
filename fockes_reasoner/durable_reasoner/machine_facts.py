import abc
from .machine import FACTTYPE, MACHINESTATE, RUNNING_STATE

import rdflib
import typing as typ
from typing import MutableMapping, Mapping, Union

BINDING = MutableMapping[rdflib.Variable, str]
from bridge_rdflib import rdflib2string, string2rdflib, TRANSLATEABLE_TYPES

class external:
    """Parentclass for all extension for information representation."""
    @classmethod
    def parse(cls, string: str) -> "external":
        ...

    @classmethod
    def serialize(self) -> str:
        ...

TRANSLATEABLE_TYPES = typ.Union[rdflib.Variable,
                                rdflib.URIRef,
                                rdflib.BNode,
                                rdflib.Literal,
                                list["TRANSLATEABLE_TYPES"],
                                external,
                                ]

from bridge_rdflib import *

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
    elif type(identifier, list):
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
                              "happend with %r" % string) from err


class fact(abc.ABC):
    @abc.abstractmethod
    def assert(self, c: typ.Union[durable.engine.Closure, str],
               bindings: dur_abc.BINDING = {},
               external_resolution: Mapping[Union[rdflib.URIRef,
                                                  rdflib.BNode], EXTERNAL] = {},
               ) -> None:
        ...

    @abc.abstractmethod
    def generate_durable_pattern(self, bindings: dur_abc.CLOSURE_BINDINGS,
                                  factname: str) -> rls.value:
        ...

    @abc.abstractmethod
    def retract(self, c: typ.Union[durable.engine.Closure, str],
                bindings: dur_abc.BINDING = {},
                external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], EXTERNAL] = {},
                ) -> None:
        ...

    @abc.abstractmethod
    def modify(self, c: typ.Union[durable.engine.Closure, str],
               bindings: dur_abc.BINDING = {},
               external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], EXTERNAL] = {},
               ) -> None:
        ...


class frame(fact):
    obj: typ.Union[TRANSLATEABLE_TYPES, external]
    slotkey: typ.Union[TRANSLATEABLE_TYPES, external]
    slotvalue: typ.Union[TRANSLATEABLE_TYPES, external]
    FRAME_OBJ: str = "obj"
    FRAME_SLOTKEY: str = "slotkey"
    FRAME_SLOTVALUE: str = "slotvalue"

    def assert(self, c: typ.Union[durable.engine.Closure, str],
               bindings: dur_abc.BINDING = {},
               external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], EXTERNAL] = {},
               ) -> None:
        fact = {"type":self.fact_type}
        for label, x, in [
                (self.label_obj, self.obj),
                (self.label_slotkey, self.slotkey),
                (self.label_slotvalue, self.slotvalue),
                ]:
            fact[label] = _node2string(x, c, bindings, external_resolution)
        if isinstance(c, str):
            rls.assert_fact(c, fact)
        else:
            c.assert_fact(fact)

    def generate_durable_pattern(self, bindings: dur_abc.CLOSURE_BINDINGS,
                                  factname: str) -> rls.value:
        """Used to generate a pattern for when_all method of durable"""
        log = [f"rls.m.{dur_abc.FACTTYPE} == {self.fact_type}"]
        pattern = (getattr(rls.m, dur_abc.FACTTYPE) == self.fact_type)
        for fact_label, value in [
                (self.label_obj, self.obj),
                (self.label_slotkey, self.slotkey),
                (self.label_slotvalue, self.slotvalue),
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

    def retract(self, c: typ.Union[durable.engine.Closure, str],
                bindings: dur_abc.BINDING = {},
                external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], EXTERNAL] = {},
                ) -> None:
        fact = {"type":self.fact_type}
        for label, x, in [
                (self.label_obj, self.obj),
                (self.label_slotkey, self.slotkey),
                (self.label_slotvalue, self.slotvalue),
                ]:
            if isinstance(x, rdflib.Variable):
                fact[label] = bindings[x]
            elif isinstance(x, (URIRef, BNode, Literal)):
                fact[label] = rdflib2string(x)
            else:
                newnode = x(c, bindings, external_resolution)
                fact[label] = rdflib2string(newnode)

        if isinstance(c, str):
            facts = rls.get_facts(c)
        else:
            facts =c.get_facts()

        match = None
        _slots = (self.label_obj, self.label_slotkey, self.label_slotvalue)
        for f in facts:
            #if f["type"] != self.fact_type:
            #    continue
            if all(f.get(x, None) == fact[x] for x in _slots):
                match = f
                break

        if match is not None:
            if isinstance(c, str):
                rls.retract_fact(c, f)
            else:
                c.retract_fact(f)

    def modify(self, c: typ.Union[durable.engine.Closure, str],
               bindings: dur_abc.BINDING = {},
               external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], EXTERNAL] = {},
               ) -> None:
        fact = {"type":self.fact_type}
        for label, x, in [
                (self.label_obj, self.obj),
                (self.label_slotkey, self.slotkey),
                (self.label_slotvalue, self.slotvalue),
                ]:
            if isinstance(x, rdflib.Variable):
                fact[label] = bindings[x]
            elif isinstance(x, (URIRef, BNode, Literal)):
                fact[label] = rdflib2string(x)
            else:
                newnode = x(c, bindings, external_resolution)
                fact[label] = rdflib2string(newnode)
        _obj = bindings[self.obj] if isinstance(self.obj, rdflib.Variable)\
                else rdflib2string(self.obj)
        _slotkey = bindings[self.slotkey]\
                if isinstance(self.slotkey, rdflib.Variable)\
                else rdflib2string(self.slotkey)

        def retract_first_frame(facts): #type: ignore[no-untyped-def]
            """Get first frame with given obj and slotkey"""
            for f in facts:
                try:
                    if f[self.label_obj] == _obj\
                            and f[self.label_slotkey] == _slotkey:
                        return f
                except KeyError:
                    pass
            return None
        if isinstance(c, str):
            f = retract_first_frame(rls.get_facts(c))
            if f is not None:
                rls.retract_fact(c, f)
            rls.assert_fact(c, fact)
        else:
            f = retract_first_frame(c.get_facts())
            if f is not None:
                c.retract_fact(f)
            c.assert_fact(fact)


class member(fact):
    MEMBER: ATOMLABEL = "member"
    """facttype :term:`member` are labeled with this."""


class subclass(fact):
    SUBCLASS: ATOMLABEL = "subclass"
    """facttype :term:`subclass` are labeled with this."""
