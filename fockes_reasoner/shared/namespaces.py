from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef

rif2internal = Namespace("http://example.com/builtin#")

class pred(DefinedNamespace):
    _fail = True
    _extras = [
            "numeric-greater-than",
            "numeric-equal",
            #"",
            #"",
            #"",
            #"",
            ]
    _NS = Namespace("http://www.w3.org/2007/rif-builtin-predicate#")

class func(DefinedNamespace):
    _fail = True

    sublist: URIRef
    get: URIRef
    append: URIRef
    _extras = [
            "count",
            "make-list",
            "concatenate",
            "list-contains",
            "insert-before",
            ]

    _NS = Namespace("http://www.w3.org/2007/rif-builtin-function#")
