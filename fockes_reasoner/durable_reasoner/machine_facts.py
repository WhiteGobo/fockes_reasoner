import abc
#from .machine import FACTTYPE, MACHINESTATE, RUNNING_STATE, machine
from . import abc_machine
from dataclasses import dataclass

import logging
logger = logging.getLogger(__name__)

import rdflib
from rdflib import URIRef, BNode, Literal, Variable
import typing as typ
from typing import MutableMapping, Mapping, Union, Callable, Iterable, Tuple, Optional, overload, cast
from collections.abc import Collection


from .abc_machine import BINDING, BINDING_WITH_BLANKS, CLOSURE_BINDINGS, VARIABLE_LOCATOR, TRANSLATEABLE_TYPES, ATOM_ARGS, abc_external, RESOLVABLE, _resolve

from .bridge_rdflib import *
from .bridge_rdflib import term_list, _term_list
from .abc_machine import fact
from ..shared import _pretty
from .special_externals import create_list

class _NotBoundVar(KeyError):
    ...

class _dict_fact(fact):
    ...


class external(abc_external):
    op: URIRef
    args: Iterable[Union[TRANSLATEABLE_TYPES, "external", Variable]]
    def __init__(self, op: URIRef, args: Iterable[Union[TRANSLATEABLE_TYPES, "external", Variable]]) -> None:
        self.op = op
        self.args = list(args)

    def __repr__(self) -> str:
        return "external %s(%s)" % (self.op,
                                    ", ".join(_pretty(x) for x in self.args))

class executable(external):
    def __init__(self, op: URIRef,
                 args: Iterable[Union[TRANSLATEABLE_TYPES, "external", Variable]],
                 machine: abc_machine.machine,
                 ) -> None:
        super().__init__(op, args)
        self.machine = machine

    def __call__(self, bindings: BINDING) -> None:
        raise NotImplementedError()

class machine_or(external):
    op: URIRef
    args: Iterable[Union[TRANSLATEABLE_TYPES, "external", Variable]]
    def __init__(self, op: URIRef, args: Iterable[Union[TRANSLATEABLE_TYPES, "external", Variable]]) -> None:
        assert op == URIRef("http://www.w3.org/2007/rif#Or")
        self.op = op
        self.args = list(args)


class machine_and(external):
    op: URIRef
    args: Iterable[Union[TRANSLATEABLE_TYPES, "external", Variable]]
    def __init__(self, op: URIRef, args: Iterable[Union[TRANSLATEABLE_TYPES, "external", Variable]]) -> None:
        assert op == URIRef("http://www.w3.org/2007/rif#And")
        self.op = op
        self.args = list(args)


class machine_list(external):
    op = create_list.op
    items: Iterable[Union[TRANSLATEABLE_TYPES, external, Variable]]
    def __init__(self, items: Iterable[Union[TRANSLATEABLE_TYPES, external, Variable]]) -> None:
        self.items = list(items)

    @property
    def args(self) -> Iterable[Union[TRANSLATEABLE_TYPES, external, Variable]]:
        return self.items

    def __repr__(self) -> str:
        return "m[%s]" % ", ".join(str(x) for x in self.items)


class subclass(_dict_fact):
    sub_class: typ.Union[TRANSLATEABLE_TYPES, abc_external, Variable]
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

    def __iter__(self) -> Iterator[str]:
        yield self.SUBCLASS_SUB
        yield self.SUBCLASS_SUPER

    def __len__(self) -> int:
        return 2

    def __getitem__(self, key: str,
                ) -> Union[TRANSLATEABLE_TYPES, abc_external, Variable]:
        if key == self.SUBCLASS_SUB:
            return self.sub_class
        elif key == self.SUBCLASS_SUPER:
            return self.super_class
        else:
            raise KeyError(key)

    @property
    def used_variables(self) -> Iterable[Variable]:
        if isinstance(self.sub_class, Variable):
            yield self.sub_class
        if isinstance(self.super_class, Variable):
            yield self.super_class

    def __repr__(self) -> str:
        return "%s ## %s" % (_pretty(self.sub_class),
                             _pretty(self.super_class))

    def as_dict(self, bindings: Optional[BINDING] = None,
                ) -> Mapping[str, Union[str, Variable, TRANSLATEABLE_TYPES]]:
        if isinstance(self.sub_class, abc_external) or isinstance(self.super_class, abc_external):
            raise NotImplementedError()
        pattern: Mapping[str, Union[str, Variable, TRANSLATEABLE_TYPES]]\
                = {abc_machine.FACTTYPE: self.ID,
                   self.SUBCLASS_SUB: self.sub_class,
                   self.SUBCLASS_SUPER: self.super_class,
                   }
        return pattern

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
        sub_class = string2rdflib(fact[cls.SUBCLASS_SUB])
        super_class = string2rdflib(fact[cls.SUBCLASS_SUPER])
        return cls(sub_class, super_class)

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

    def __iter__(self) -> Iterator[str]:
        yield self.FRAME_OBJ
        yield self.FRAME_SLOTKEY
        yield self.FRAME_SLOTVALUE

    def __len__(self) -> int:
        return 3

    def __getitem__(self, key: str,
                ) -> Union[TRANSLATEABLE_TYPES, abc_external, Variable]:
        if key == self.FRAME_OBJ:
            return self.obj
        elif key == self.FRAME_SLOTKEY:
            return self.slotkey
        elif key == self.FRAME_SLOTVALUE:
            return self.slotvalue
        else:
            raise KeyError(key)

    @classmethod
    def from_fact(cls, fact: Mapping[str, str]) -> "frame":
        obj = string2rdflib(fact[cls.FRAME_OBJ])
        slotkey = string2rdflib(fact[cls.FRAME_SLOTKEY])
        slotvalue = string2rdflib(fact[cls.FRAME_SLOTVALUE])
        return cls(obj, slotkey, slotvalue)

    def as_dict(self, bindings: Optional[BINDING] = None,
                ) -> Mapping[str, Union[str, Variable, TRANSLATEABLE_TYPES]]:
        if isinstance(self.obj, external) or isinstance(self.slotkey, external) or isinstance(self.slotvalue, external):
            raise NotImplementedError()
        pattern: Mapping[str, Union[str, Variable, TRANSLATEABLE_TYPES]]\
                = {abc_machine.FACTTYPE: self.ID,
                   self.FRAME_OBJ: self.obj,
                   self.FRAME_SLOTKEY: self.slotkey,
                   self.FRAME_SLOTVALUE: self.slotvalue,
                   }
        return pattern

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
        return "%s[%s->%s]" % (_pretty(self.obj),
                               _pretty(self.slotkey),
                               _pretty(self.slotvalue))

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
        c.assert_fact(self, bindings)


class member(_dict_fact):
    ID: str = "member"
    """facttype :term:`member` are labeled with this."""
    INSTANCE: str = "instance"
    CLASS: str = "class"
    instance: typ.Union[TRANSLATEABLE_TYPES, external, Variable]
    cls: typ.Union[TRANSLATEABLE_TYPES, external, Variable]
    def __init__(self, instance: Union[TRANSLATEABLE_TYPES, external, Variable], cls: Union[TRANSLATEABLE_TYPES, external, Variable]) -> None:
        self.instance = instance
        self.cls = cls

    def __iter__(self) -> Iterator[str]:
        yield self.INSTANCE
        yield self.CLASS

    def __len__(self) -> int:
        return 2

    def __getitem__(self, key: str,
                ) -> Union[TRANSLATEABLE_TYPES, abc_external, Variable]:
        if key == self.INSTANCE:
            return self.instance
        elif key == self.CLASS:
            return self.cls
        else:
            raise KeyError(key)

    @property
    def used_variables(self) -> Iterable[Variable]:
        if isinstance(self.instance, Variable):
            yield self.instance
        if isinstance(self.cls, Variable):
            yield self.cls

    def __repr__(self) -> str:
        return "%s # %s" % (_pretty(self.instance), _pretty(self.cls))

    def as_dict(self, bindings: Optional[BINDING] = None,
                ) -> Mapping[str, Union[str, Variable, TRANSLATEABLE_TYPES]]:
        if isinstance(self.instance, external) or isinstance(self.cls, external):
            raise NotImplementedError()
        pattern: Mapping[str, Union[str, Variable, TRANSLATEABLE_TYPES]]\
                = {abc_machine.FACTTYPE: self.ID,
                   self.INSTANCE: self.instance,
                   self.CLASS: self.cls,
                   }
        return pattern

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
        instance = string2rdflib(fact[cls.INSTANCE])
        cls_ = string2rdflib(fact[cls.CLASS])
        return cls(instance, cls_)


class atom(fact):
    ID: str = "atom"
    op: typ.Union[TRANSLATEABLE_TYPES, external, Variable]
    args: Sequence[Union[TRANSLATEABLE_TYPES, external, Variable]]
    """facttype :term:`atom` are labeled with this."""
    ATOM_OP = "op"
    ATOM_ARGS = "args%d"
    def __init__(self, op: typ.Union[TRANSLATEABLE_TYPES, external, Variable],
                 args: Iterable[Union[TRANSLATEABLE_TYPES, external, Variable]],
                 ) -> None:
        self.op = op
        self.args = tuple(args)

    def __iter__(self) -> Iterator[str]:
        yield self.ATOM_OP
        for i in range(len(self.args)):
            yield self.ATOM_ARGS % i

    def __len__(self) -> int:
        return 1 + len(self.args)

    def __getitem__(self, key: str,
                ) -> Union[TRANSLATEABLE_TYPES, abc_external, Variable]:
        if key == self.ATOM_OP:
            return self.op
        elif key[:4] == "args":
            try:
                i = int(key[4:])
            except ValueError as err:
                raise KeyError(key) from err
            return self.args[i]
        else:
            raise KeyError(key)

    @property
    def used_variables(self) -> Iterable[Variable]:
        for x in (self.op, *self.args):
            if isinstance(x, Variable):
                yield x

    def as_dict(self, bindings: Optional[BINDING] = None,
                ) -> Mapping[str, Union[str, Variable, TRANSLATEABLE_TYPES]]:
        if isinstance(self.op, external):
            raise NotImplementedError()
        pattern: MutableMapping[str,
                                Union[str, Variable, TRANSLATEABLE_TYPES]]\
                = {abc_machine.FACTTYPE: self.ID,
                   self.ATOM_OP: self.op,
                   }
        for i, arg in enumerate(self.args):
            if isinstance(arg, external):
                raise NotImplementedError()
            pattern[self.ATOM_ARGS % i] = arg
        return pattern

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

@overload
def _node2string(x: Union[TRANSLATEABLE_TYPES, Variable, str, abc_external],
                 machine: abc_machine.machine,
                 bindings: BINDING,
                 ) -> str:
    ...

@overload
def _node2string(x: Union[TRANSLATEABLE_TYPES, Variable, str, abc_external],
                 machine: abc_machine.machine,
                 bindings: BINDING_WITH_BLANKS,
                 ) -> Optional[str]:
    ...

def _node2string(x: Union[TRANSLATEABLE_TYPES, Variable, str, abc_external],
                 machine: abc_machine.machine,
                 bindings: Union[BINDING_WITH_BLANKS, BINDING],
                 ) -> Optional[str]:
    if isinstance(x, rdflib.Variable):
        try:
            q = bindings[x]
        except KeyError as err:
            raise _NotBoundVar("Tried to get not yet bind variable '%s' "
                               "from %s" % (x, bindings)) from err
        if q is None:
            return None
        else:
            return rdflib2string(q)
    elif isinstance(x, (URIRef, BNode, Literal)):
        return rdflib2string(x)
    elif isinstance(x, external):
        assert None not in bindings.values()
        #cast(BINDING, bindings)
        res = machine._create_assignment_from_external(x.op, x.args)
        newnode = _resolve(res, bindings)
        return rdflib2string(newnode)
    elif isinstance(x, str):
        return x
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
