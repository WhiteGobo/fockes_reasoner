"""This module provides all things to translate rdflib nodes 
to str. Because the logicmachine only uses strings this should give a
unified translator from rdflib nodes to these string and back
"""
import abc
import rdflib
from rdflib import XSD
from typing import Iterable, Union, Iterator, List, Any, TypeAlias
from collections.abc import Sequence
from dataclasses import dataclass
import logging
logger = logging.getLogger(__name__)

import rdflib

TRANSLATEABLE_TYPES: TypeAlias = Union[rdflib.URIRef,
                                       rdflib.BNode,
                                       rdflib.IdentifiedNode,
                                       rdflib.Literal,
                                       "term_list",
                                       ]

class term_list(Sequence):
    @abc.abstractmethod
    def __iter__(self) -> Iterator["TRANSLATEABLE_TYPES"]:
        ...

    def _as_machinestring(self) -> str:
        return "[%s]" % " ".join(rdflib2string(x) for x in self)

    @abc.abstractmethod
    def __len__(self) -> int:
        ...

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, term_list):
            return False
        for x, y in zip(self, other):
            if x != y:
                return False
        return True

    @abc.abstractmethod
    def __getitem__(self, index: Union[int, slice]) -> TRANSLATEABLE_TYPES:
        ...


import pyparsing as pp
bnode = pp.Combine(pp.Suppress("_:") + pp.Regex('[^<>"{}|^`\\\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1A\x1B\x1C\x1D\x1E\x1F\x20]*'))
bnode.set_parse_action(lambda parse_result: rdflib.BNode(*parse_result))

from rdflib.plugins.sparql.parser import iri, RDFLiteral
def _compile_RDFLiteral(parser_result: pp.results.ParseResults,
                        ) -> rdflib.Literal:
    l = parser_result[0]
    v = l["string"]
    kwargs = dict(l)
    v = kwargs.pop("string")
    return rdflib.Literal(v, **kwargs)
myRDFLiteral = RDFLiteral.copy()
myRDFLiteral.add_parse_action(_compile_RDFLiteral)
rdf_identifier = iri | myRDFLiteral | bnode
myparser = pp.Forward()

@dataclass
class _term_list(term_list):
    """Simple implementation for term_list"""
    items: List[TRANSLATEABLE_TYPES]
    def __iter__(self) -> Iterator[TRANSLATEABLE_TYPES]:
        return iter(self.items)

    #@_term_parser.add_parse_action
    @classmethod
    def _from_machinestring(cls, parser_result: pp.results.ParseResults) -> "_term_list":
        return cls(list(parser_result))

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: Union[int, slice]) -> TRANSLATEABLE_TYPES:
        if isinstance(index, slice):
            return _term_list(self.items[index])
        else:
            return self.items[index]


_term_parser = pp.Suppress("[")\
            + pp.ZeroOrMore(myparser)\
            + pp.Suppress("]")
_term_parser.add_parse_action(_term_list._from_machinestring)

myparser <<= pp.MatchFirst((rdf_identifier, _term_parser))

def rdflib2string(identifier: TRANSLATEABLE_TYPES) -> str:
    """Translates from rdflib to strings.
    Inverse to string2rdflib.
    """
    if isinstance(identifier, rdflib.URIRef):
        return f"<{identifier}>"
    elif isinstance(identifier, rdflib.BNode):
        return f"_:{identifier}"
    elif isinstance(identifier, rdflib.Literal):
        if identifier.value is not None:
            parts = ["'%s'" % identifier.value]
        else:
            parts = ["'%s'" % identifier]
        if identifier.datatype is None or identifier.datatype == XSD.string:
            pass
        else:
            parts.append("^^<%s>" % identifier.datatype)
        try:
            if identifier.language:
                parts.append("@%s" % identifier.language)
        except AttributeError:
            pass
        return "".join(parts)
    elif isinstance(identifier, term_list):
        return identifier._as_machinestring()
    else:
        raise TypeError(type(identifier))


def string2rdflib(string: str) -> TRANSLATEABLE_TYPES:
    """Translates from rdflib to strings. Inverse to rdflib2string
    """
    try:
        return myparser.parse_string(string)[0]# type: ignore[no-any-return]
    except pp.exceptions.ParseException as err:
        raise ValueError("Given string is not a valid translation produced"
                         "by rdflib2string", string) from err
