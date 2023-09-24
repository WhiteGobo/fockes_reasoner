from typing import Callable, Union, TypeVar, Iterable, Container, Tuple
import rdflib
import itertools as it
from rdflib import Literal, Variable, XSD, IdentifiedNode, Literal, URIRef, RDF
import logging
logger = logging.getLogger()
from dataclasses import dataclass
import math
from decimal import Decimal
from ..bridge_rdflib import term_list, _term_list, TRANSLATEABLE_TYPES
import datetime
import isodate

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS, _assignment
from ...shared import pred, func
from .shared import is_datatype, invert, assign_rdflib
from .numeric_externals import literal_equal, pred_less_than, ascondition_pred_greater_than

_externals: Iterable
_datatypes: Iterable[URIRef] = [
        RDF.PlainLiteral,
        ]

def _register_plainLiteralExternals(machine):
    for x in _externals:
        as_ = {}
        for t in ["asassign", "aspattern", "asbinding"]:
            if hasattr(x, t):
                foo = getattr(x, t)
                if foo is not None:
                    as_[t] = foo
                else:
                    as_[t] = x
        machine.register(x.op, **as_)

@dataclass
class is_literal_PlainLiteral:
    op = pred["is-literal-PlainLiteral"]
    asassign = is_datatype

@dataclass
class is_literal_not_PlainLiteral:
    op = pred["is-literal-not-PlainLiteral"]
    asassign = invert.gen(is_literal_PlainLiteral)


@dataclass
class PlainLiteral_from_string_lang:
    op = func["PlainLiteral-from-string-lang"]

@dataclass
class string_from_PlainLiteral:
    op = func["string-from-PlainLiteral"]

@dataclass
class lang_from_PlainLiteral:
    op = func["lang-from-PlainLiteral"]

@dataclass
class PlainLiteral_compare:
    op = func["PlainLiteral-compare"]

@dataclass
class matches_language_range:
    op = pred["matches-language-range"]

_externals = [
        is_literal_PlainLiteral,
        is_literal_not_PlainLiteral,
        PlainLiteral_from_string_lang,
        string_from_PlainLiteral,
        lang_from_PlainLiteral,
        PlainLiteral_compare,
        matches_language_range,
        ]
