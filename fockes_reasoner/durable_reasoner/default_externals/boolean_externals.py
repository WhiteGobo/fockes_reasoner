from typing import Callable, Union, TypeVar, Iterable, Container, Tuple
import rdflib
import urllib
import itertools as it
from rdflib import Literal, Variable, XSD, IdentifiedNode, Literal, URIRef, RDF
import logging
logger = logging.getLogger()
from dataclasses import dataclass, field
from ..bridge_rdflib import term_list, _term_list, TRANSLATEABLE_TYPES
import re
from .numeric_externals import pred_less_than, pred_greater_than

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS
from .. import abc_machine
from ...shared import pred, func
from .shared import is_datatype, invert, assign_rdflib
import locale

VALID_STRING_TYPES = {None, RDF.PlainLiteral, XSD.string}
_externals: Iterable
_datatypes: Iterable[URIRef] = [
        XSD.boolean,
        ]

def _register_booleanExternals(machine: abc_machine.extensible_Machine) -> None:
    for dt in _datatypes:
        machine.register(dt, asassign=assign_rdflib.gen(dt))
    for x in _externals:
        as_ = {}
        for t in ["asassign", "aspattern", "asbinding"]:
            if hasattr(x, t):
                foo = getattr(x, t)
                if foo is None:
                    as_[t] = x
                elif isinstance(foo, str):
                    as_[t] = getattr(x, foo)
                else:
                    as_[t] = foo
        machine.register(x.op, **as_)

@dataclass
class is_literal_boolean:
    asassign = None
    target: RESOLVABLE
    op: URIRef = pred["is-literal-boolean"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        return Literal(t.datatype == XSD.boolean)

class is_literal_not_boolean:
    op: URIRef = pred["is-literal-not-boolean"]
    asassign = invert.gen(is_literal_boolean)

@dataclass
class _check_value_equality:
    left: RESOLVABLE
    right: RESOLVABLE
    #def __init__(self, left, right, *args):
    #    if args:
    #        raise TypeError("pred:numeric_equal expects exactly 2 arguments "
    #                        "got %d" % len(args)+2)
    #    self.left = left
    #    self.right = right

    def __call__(self, bindings:BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value == right.value) #type: ignore[union-attr]

class boolean_equal:
    op: URIRef = pred["boolean-equal"]
    asassign = _check_value_equality

class boolean_less_than:
    op: URIRef = pred["boolean-less-than"]
    asassign = pred_less_than

class boolean_greater_than:
    op: URIRef = pred["boolean-greater-than"]
    asassign = pred_greater_than

_externals = [
        is_literal_boolean,
        is_literal_not_boolean,
        boolean_equal,
        boolean_greater_than,
        boolean_less_than,
        ]
