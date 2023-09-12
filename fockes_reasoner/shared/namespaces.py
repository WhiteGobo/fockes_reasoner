from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef

rif2internal = Namespace("http://example.com/builtin#")

class pred(DefinedNamespace):
    _fail = True
    _extras = [
            "iri-string",
            "numeric-greater-than",
            "numeric-greater-than-or-equal",
            "numeric-less-than",
            "numeric-less-than-or-equal",
            "numeric-equal",
            "numeric-not-equal",
            "literal-not-identical",
            "is-literal-hexBinary",
            "is-literal-not-hexBinary",
            "is-literal-base64Binary",
            "is-literal-not-base64Binary",
            "is-literal-double",
            "is-literal-not-double",
            "is-literal-float",
            "is-literal-not-float",
            "is-literal-decimal",
            "is-literal-not-decimal",
            "is-literal-integer",
            "is-literal-not-integer",
            "is-literal-long",
            "is-literal-not-long",
            "is-literal-unsignedLong",
            "is-literal-not-unsignedLong",
            "is-literal-unsignedInt",
            "is-literal-not-unsignedInt",
            "is-literal-unsignedShort",
            "is-literal-not-unsignedShort",
            "is-literal-unsignedByte",
            "is-literal-not-unsignedByte",
            "is-literal-int",
            "is-literal-not-int",
            "is-literal-short",
            "is-literal-not-short",
            "is-literal-byte",
            "is-literal-not-byte",
            "is-literal-nonNegativeInteger",
            "is-literal-not-nonNegativeInteger",
            "is-literal-positiveInteger",
            "is-literal-not-positiveInteger",
            "is-literal-negativeInteger",
            "is-literal-not-negativeInteger",
            "is-literal-nonPositiveInteger",
            "is-literal-not-nonPositiveInteger",
            "XMLLiteral-equal",
            "is-list",
            "list-contains",
            #"",
            #"",
            ]
    _NS = Namespace("http://www.w3.org/2007/rif-builtin-predicate#")

class entailment(DefinedNamespace):
    _extras = [
            "OWL-Direct",
            ]
    _NS = Namespace("http://www.w3.org/ns/entailment/")

class func(DefinedNamespace):
    _fail = True

    sublist: URIRef
    get: URIRef
    append: URIRef
    reverse: URIRef
    union: URIRef
    intersect: URIRef
    _extras = [
            "count",
            "make-list",
            "concatenate",
            "list-contains",
            "insert-before",
            "remove",
            "index-of",
            "except",
            "distinct-values",
            "numeric-subtract",
            "numeric-add",
            "numeric-multiply",
            "numeric-divide",
            "numeric-integer-divide",
            "numeric-mod",
            "numeric-integer-mod",
            ]

    _NS = Namespace("http://www.w3.org/2007/rif-builtin-function#")
