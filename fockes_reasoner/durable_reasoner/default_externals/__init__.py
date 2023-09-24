from typing import Callable, Union, TypeVar, Iterable, Container, Tuple
import rdflib
import itertools as it
from rdflib import Literal, Variable, XSD, IdentifiedNode, Literal, URIRef
import logging
logger = logging.getLogger()
from dataclasses import dataclass
import math
from ..bridge_rdflib import term_list, _term_list, TRANSLATEABLE_TYPES

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS, _assignment
from ...shared import pred, func
from .numeric_externals import *
from .list_externals import *
from .time_externals import _register_timeExternals
from .shared import invert, assign_rdflib

@dataclass
class rif_or:
    args: Iterable[RESOLVABLE]
    def __call__(self, bindings: BINDING) -> Union[IdentifiedNode, Literal, term_list]:
        for x in self.args:
            y = _resolve(x, bindings)
            if y:
                return y
        return Literal(False)

    @classmethod
    def pattern_generator(
            cls,
            args: Iterable[RESOLVABLE],
            bound_variables: Container[Variable],
            ) -> Tuple[Iterable[abc_pattern],
                       Tuple["pred_iri_string"],
                       Iterable[Variable]]:
        raise NotImplementedError()
        


@dataclass
class set_var:
    left: Variable
    right: RESOLVABLE

    def __call__(self, bindings:BINDING) -> Literal:
        right = _resolve(self.right, bindings)
        bindings[left] = right
        return Literal(True)

@dataclass
class pred_iri_string:
    """Assigns to given variable the string as iri
    """
    target_var: Variable
    source_string: RESOLVABLE

    @classmethod
    def pattern_generator(
            cls,
            args: Iterable[RESOLVABLE],
            bound_variables: Container[Variable],
            ) -> Iterable[Tuple[Iterable[abc_pattern],
                                Tuple["pred_iri_string"],
                                Iterable[Variable]]]:
        target_var, source_string = args
        assert isinstance(target_var, Variable)
        assert target_var not in bound_variables
        yield tuple(), (cls(target_var, source_string),), [target_var]

    def __call__(self, bindings: BINDING) -> Literal:
        assert self.target_var not in bindings
        s = _resolve(self.source_string, bindings)
        bindings[self.target_var] = URIRef(str(s))
        return Literal(True)

