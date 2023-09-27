from typing import Iterable, List, Union, Any
from rdflib import  Literal, Variable, URIRef, BNode, Graph
from rdflib.namespace import NamespaceManager

PrettyprintManager = NamespaceManager(Graph())
PrettyprintManager.bind("ex", "http://example.org/testOntology.owl#")

def _pretty(t: Any) -> str:
    """Prints a representation of given input for representation of facts"""
    if isinstance(t, Literal):
        return repr(t)
    elif isinstance(t, Variable):
        return "?%s" % t
    elif isinstance(t, URIRef):
        return PrettyprintManager.normalizeUri(t)
        return "<%s>" % t
    elif isinstance(t, BNode):
        return "_:%s" % t
    else:
        return repr(t)
