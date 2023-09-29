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
from ...shared import pred, func
from .shared import is_datatype, invert, assign_rdflib

_externals: Iterable

def _register_actionExternals(machine):
    for x in _externals:
        as_ = {}
        for t in ["asassign", "aspattern", "asbinding", "asaction"]:
            if hasattr(x, t):
                foo = getattr(x, t)
                if foo is not None:
                    as_[t] = foo
                else:
                    as_[t] = x
        machine.register(x.op, **as_)

class builtin_print:
    op = URIRef("http://www.w3.org/2007/rif-builtin-action#print")
    args: Iterable[RESOLVABLE]
    ascondition = None
    def __init_(self, *args: Iterable[RESOLVABLE]):
        self.args = list(args)

    def __call__(self, bindings: BINDING) -> Literal:
        q = []
        for arg in self.args:
            q.append(str(_resolve(arg, bindings)))
        print(" ".join(q))

_externals = [
        builtin_print,
        ]
