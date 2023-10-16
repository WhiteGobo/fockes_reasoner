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
import locale

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS
from .. import abc_machine
from ...shared import pred, func
from .shared import is_datatype, invert, assign_rdflib
from .numeric_externals import literal_equal, pred_less_than

_externals: Iterable
_datatypes: Iterable[URIRef] = [
        RDF.PlainLiteral,
        ]

def _register_plainLiteralExternals(machine: abc_machine.extensible_machine) -> None:
    for dt in _datatypes:
        machine.register(dt, asassign=assign_rdflib.gen(dt))
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
    asassign = None
    target: RESOLVABLE
    op: URIRef = pred["is-literal-PlainLiteral"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        if t.datatype is None:
            return Literal(True)
        return Literal(t.datatype == RDF.PlainLiteral)


class is_literal_not_PlainLiteral:
    op: URIRef = pred["is-literal-not-PlainLiteral"]
    asassign = invert.gen(is_literal_PlainLiteral)


@dataclass
class PlainLiteral_from_string_lang:
    asassign = None
    target: RESOLVABLE
    lang: RESOLVABLE
    op: URIRef = func["PlainLiteral-from-string-lang"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        lang = _resolve(self.lang, bindings)
        #return Literal(t, lang=str(lang), datatype=RDF.PlainLiteral)
        return Literal(str(t), lang=str(lang))

@dataclass
class string_from_PlainLiteral:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["string-from-PlainLiteral"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(str(t), datatype=XSD.string)


@dataclass
class lang_from_PlainLiteral:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["lang-from-PlainLiteral"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        if t.language is not None:
            return Literal(str(t.language), datatype=XSD.language)
        else:
            return Literal("", datatype=XSD.string)

@dataclass
class PlainLiteral_compare:
    """Return an -1, 0 or 1 depending on the alphabetical order of the two
    Literals. See :term:`codepoint collation` for more information.
    """
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["PlainLiteral-compare"]
    def __call__(self, bindings: BINDING) -> Literal:
        l = _resolve(self.left, bindings)
        r = _resolve(self.right, bindings)
        assert isinstance(l, Literal)
        assert isinstance(r, Literal)
        return Literal(locale.strcoll(l, r))

@dataclass
class matches_language_range:
    asassign = None
    target: RESOLVABLE
    language_range: RESOLVABLE
    op: URIRef = pred["matches-language-range"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        #lang_range = _resolve(self.language_range, bindings).value
        raise NotImplementedError("No ability to match language spaces to language")

_externals = [
        is_literal_PlainLiteral,
        is_literal_not_PlainLiteral,
        PlainLiteral_from_string_lang,
        string_from_PlainLiteral,
        lang_from_PlainLiteral,
        PlainLiteral_compare,
        matches_language_range,
        ]
