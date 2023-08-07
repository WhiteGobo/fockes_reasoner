from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef

pred = Namespace("http://www.w3.org/2007/rif-builtin-predicate#")

class func(DefinedNamespace):
    _fail = True

    sublist: URIRef
    get: URIRef
    append: URIRef
    _extras = [
            "count",
            "make-list",
            ]

    _NS = Namespace("http://www.w3.org/2007/rif-builtin-function#")
