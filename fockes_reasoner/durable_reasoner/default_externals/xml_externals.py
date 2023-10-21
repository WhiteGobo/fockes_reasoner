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

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS
from .. import abc_machine
from ...shared import pred, func
from .shared import is_datatype, invert, assign_rdflib, RegisterInformation
import locale

VALID_STRING_TYPES = {None, RDF.PlainLiteral, XSD.string}
_externals: Iterable
_externals_new: Iterable[RegisterInformation]
_datatypes: Iterable[URIRef] = [
        RDF.XMLLiteral
        ]

def _register_xmlExternals(machine: abc_machine.extensible_Machine) -> None:
    for dt in _datatypes:
        machine.register(dt, asassign=assign_rdflib.gen(dt))
    for y in _externals_new:
        y.register_at(machine)
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

xmlliteral_equal = RegisterInformation(pred["XMLLiteral-equal"])
@xmlliteral_equal.set_asassign
class literal_equal:
    left: RESOLVABLE
    right: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.left, self.right = args

    def __call__(self, bindings:BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        logger.critical((left, right))
        return Literal(left == right)

@dataclass
class is_literal_xmlliteral:
    target: RESOLVABLE
    asassign: None = None
    op: URIRef = pred["is-literal-XMLLiteral"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        return Literal(t.datatype == RDF.XMLLiteral)

class is_literal_not_xmlliteral:
    op: URIRef = pred["is-literal-not-XMLLiteral"]
    asassign = invert.gen(is_literal_xmlliteral)

_externals = [
        is_literal_xmlliteral,
        is_literal_not_xmlliteral,
        ]
_externals_new = [
        xmlliteral_equal,
        ]
