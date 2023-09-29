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
from ...shared import pred, func
from .shared import is_datatype, invert, assign_rdflib
import locale

VALID_STRING_TYPES = {None, RDF.PlainLiteral, XSD.string}
_externals: Iterable
_datatypes: Iterable[URIRef] = [
        XSD.anyURI,
        ]

def _register_anyURIExternals(machine):
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
class is_literal_anyURI:
    op = pred["is-literal-anyURI"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype == XSD.anyURI)

@dataclass
class is_literal_not_anyURI:
    op = pred["is-literal-not-anyURI"]
    asassign = invert.gen(is_literal_anyURI)

_externals = [
        is_literal_anyURI,
        is_literal_not_anyURI,
        ]
