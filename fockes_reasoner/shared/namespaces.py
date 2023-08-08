from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef

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
            ]

    _NS = Namespace("http://www.w3.org/2007/rif-builtin-function#")
