from typing import Callable, Union, TypeVar, Iterable, Container, Tuple, Hashable, Optional, Any, Mapping
import rdflib
from rdflib import URIRef
import itertools as it
from rdflib import Literal, Variable, XSD, IdentifiedNode, Literal, URIRef
import logging
logger = logging.getLogger()
from dataclasses import dataclass, field
import math
from ..bridge_rdflib import term_list, _term_list, TRANSLATEABLE_TYPES

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS, ASSIGNMENTGENERATOR, ASSIGNMENT, ACTIONGENERATOR, ACTION, INDIPENDENTACTIONGENERATOR, PATTERNGENERATOR, BINDING_DESCRIPTION, fact, Machine
from ...shared import pred, func

@dataclass
class RegisterInformation(Mapping):
    op: URIRef | Hashable
    assuperaction: Optional[ACTIONGENERATOR[Union[ACTION, fact], None]] = field(default=None)
    asnormalaction: Optional[ACTIONGENERATOR[RESOLVABLE, None]] = field(default=None)
    asassign: Optional[INDIPENDENTACTIONGENERATOR[RESOLVABLE, Literal]] = field(default=None)
    aspattern: Optional[PATTERNGENERATOR] = field(default=None)
    asbinding: Optional[BINDING_DESCRIPTION] = field(default=None)
    asgroundaction: Optional[Any] = field(default=None)

    def set_assuperaction(
            self,
            action_gen: ACTIONGENERATOR[Union[ACTION, fact], None],
            ) -> None:
        self.assuperaction = action_gen

    def set_asnormalaction(
            self,
            action_gen: ACTIONGENERATOR[RESOLVABLE, None],
            ) -> None:
        self.assuperaction = action_gen

    def set_asassign(
            self,
            action_gen: INDIPENDENTACTIONGENERATOR[RESOLVABLE, Literal],
            ) -> None:
        self.asassign = action_gen

    def set_aspattern(
            self,
            action_gen: PATTERNGENERATOR,
            ) -> None:
        self.aspattern = action_gen

    def set_asbinding(
            self,
            action_gen: BINDING_DESCRIPTION,
            ) -> None:
        self.asbinding = action_gen

    def set_asgroundaction(
            self,
            action_gen: Any,
            ) -> None:
        self.asgroundaction = action_gen

    def __iter__(self):
        for key, value in self.__dict__.items():
            if value is not None:
                yield key

    def __getitem__(self, key):
        return getattr(self, key)

    def __len__(self) -> int:
        return len([x for x in self.__dict__.values() if x is not None])

    def register_at(self, machine: Machine):
        machine.register(self.id,
                         self.assuperaction,
                         self.asnormalaction,
                         self.asassign,
                         self.aspattern,
                         self.asbinding,
                         self.asgroundaction,
                         )

@dataclass
class invert:
    to_invert: RESOLVER
    def __call__(self, bindings: BINDING) -> Literal:
        b = self.to_invert(bindings)
        return Literal(not b)

    @classmethod
    def gen(cls, to_invert: Callable[..., RESOLVER]) -> Callable[..., "invert"]:
        return lambda *args: cls(to_invert(*args))


@dataclass
class is_datatype:
    datatype: URIRef
    target: RESOLVER
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype == self.datatype)#type: ignore[union-attr]


@dataclass
class assign_rdflib:
    """
    :TODO: repack this class and make generator of assign_rdflib the outer
        class and assign_rdflib the inner
    """
    target: RESOLVABLE
    type_uri: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        type_uri = _resolve(self.type_uri, bindings)
        assert isinstance(type_uri, URIRef)
        return Literal(t, datatype=type_uri)

    def __repr__(self) -> str:
        return "%s: %s" % (self.type_uri, self.target)

    @dataclass
    class _gen_cont:
        cls: type["assign_rdflib"]
        type_uri: URIRef
        def __call__(self, *args: RESOLVABLE) -> "assign_rdflib":
            assert len(args) == 1
            return self.cls(args[0], self.type_uri)

    @classmethod
    def gen(cls, type_uri: URIRef) -> _gen_cont:
        #ignoring, that there may be more inputargs as expected. Getting more
        #args whithin the generation is expected and will throw a TypeError.
        return cls._gen_cont(cls, type_uri)
        #return lambda target: cls(target, type_uri) #type: ignore[return-value]
