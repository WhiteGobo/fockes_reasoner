import rdflib
from typing import Iterable



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
