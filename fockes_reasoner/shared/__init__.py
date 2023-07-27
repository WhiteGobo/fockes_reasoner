"""Provides multiple shared methods between different parts of this package.
"""
import typing as typ
import rdflib
import pyparsing.results

tmpdata = rdflib.Namespace("http://example.com/temporarydata#")
focke = rdflib.Namespace("http://example.com/internaldata#")
rif2internal = rdflib.Namespace("http://example.com/builtin#")
RIF = rdflib.Namespace("http://www.w3.org/2007/rif#")
from rdflib import XSD
from rdflib import RDF


import pyparsing as pp
bnode = pp.Combine(pp.Suppress("_:") + pp.Regex('[^<>"{}|^`\\\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1A\x1B\x1C\x1D\x1E\x1F\x20]*'))
bnode.set_parse_action(lambda parse_result: rdflib.BNode(*parse_result))

from rdflib.plugins.sparql.parser import iri, RDFLiteral
def _compile_RDFLiteral(parser_result: pyparsing.results.ParseResults,
                        ) -> rdflib.Literal:
    l = parser_result[0]
    kwargs = dict(l)
    v = kwargs.pop("string")
    return rdflib.Literal(v, **kwargs)
myRDFLiteral = RDFLiteral.copy()
myRDFLiteral.add_parse_action(_compile_RDFLiteral)
rdf_identifier = iri | myRDFLiteral | bnode

SUPPORTED_TRANSLATEABLE = typ.Union[rdflib.Literal,
                                    rdflib.Variable,
                                    rdflib.URIRef,
                                    rdflib.BNode,
                                    rdflib.IdentifiedNode
                                    ]

import re
class RifSyntaxError(SyntaxError):
    """Raise if RIF hasnt expected form"""


def rdflib2string(identifier: SUPPORTED_TRANSLATEABLE) -> str:
    """Translates from rdflib to strings.
    Inverse to string2rdflib.
    """
    if isinstance(identifier, rdflib.URIRef):
        return f"<{identifier}>"
    elif isinstance(identifier, rdflib.BNode):
        return f"_:{identifier}"
    elif isinstance(identifier, rdflib.Literal):
        parts = ["'%s'"%identifier.value]
        if identifier.datatype:
            parts.append("^^<%s>" % identifier.datatype)
        try:
            if identifier.language:
                parts.append("@%s" % identifier.language)
        except AttributeError:
            pass
        return "".join(parts)
    else:
        raise NotImplementedError(type(identifier), identifier)

def string2rdflib(string: str) -> SUPPORTED_TRANSLATEABLE:
    """Translates from rdflib to strings. Inverse to rdflib2string
    """
    return rdf_identifier.parse_string(string)[0]# type: ignore[no-any-return]

