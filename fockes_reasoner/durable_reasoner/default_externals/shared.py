from typing import Callable, Union, TypeVar, Iterable, Container, Tuple
import rdflib
import itertools as it
from rdflib import Literal, Variable, XSD, IdentifiedNode, Literal, URIRef
import logging
logger = logging.getLogger()
from dataclasses import dataclass
import math
from ..bridge_rdflib import term_list, _term_list, TRANSLATEABLE_TYPES

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS, ASSIGNMENTGENERATOR, ASSIGNMENT
from ...shared import pred, func


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
