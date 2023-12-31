from typing import Callable, Union, TypeVar, Iterable, Container, Tuple
import rdflib
import itertools as it
from rdflib import Literal, Variable, XSD, IdentifiedNode, Literal, URIRef
import logging
logger = logging.getLogger()
from dataclasses import dataclass, field
import math
from ..bridge_rdflib import term_list, _term_list, TRANSLATEABLE_TYPES

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS
from ...shared import pred, func
from .numeric_externals import *
from .numeric_externals import register_numeric_externals
from .list_externals import *
from .list_externals import register_list_externals
from .time_externals import _register_timeExternals
from .plainLiteral_externals import _register_plainLiteralExternals
from .xml_externals import _register_xmlExternals
from .anyURI_externals import _register_anyURIExternals
from .string_externals import _register_stringExternals
from .boolean_externals import _register_booleanExternals
from .action_externals import _register_actionExternals
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

    #@classmethod
    #def pattern_generator(
    #        cls,
    #        args: Iterable[RESOLVABLE],
    #        bound_variables: Container[Variable],
    #        ) -> Tuple[Iterable[abc_pattern],
    #                   Tuple["pred_iri_string"],
    #                   Iterable[Variable]]:
    #    raise NotImplementedError()
        

