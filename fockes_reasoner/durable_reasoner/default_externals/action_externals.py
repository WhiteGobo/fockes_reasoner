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
from .. import abc_machine
import datetime
import isodate
import locale

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS
from .. import abc_machine
from ...shared import pred, func
from .shared import is_datatype, invert, assign_rdflib

_externals: Iterable

def _register_actionExternals(machine: abc_machine.extensible_Machine) -> None:
    for x in _externals:
        as_ = {}
        for t in ["asassign", "aspattern", "asbinding"]:
            if hasattr(x, t):
                foo = getattr(x, t)
                if foo is not None:
                    as_[t] = foo
                else:
                    as_[t] = x
        try:
            act, expects_actions = x.asaction
            if act is None:
                as_["asaction"] = x, expects_actions
            else:
                as_["asaction"] = act, expects_actions
        except AttributeError:
            pass
        machine.register(x.op, **as_)

class builtin_print:
    machine: abc_machine.Machine
    args: Iterable[RESOLVABLE]
    op: URIRef = URIRef("http://www.w3.org/2007/rif-builtin-action#print")
    asaction = (None, False)
    def __init__(self, machine: abc_machine.Machine,
                 *args: RESOLVABLE):
        self.machine = machine
        self.args = list(args)

    def __call__(self, bindings: BINDING) -> None:
        q = []
        for arg in self.args:
            q.append(str(_resolve(arg, bindings)))
        print(" ".join(q))
        #self.machine.logger.info(" ".join(q))

_externals = [
        builtin_print,
        ]
