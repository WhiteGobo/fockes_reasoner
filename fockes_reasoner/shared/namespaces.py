from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef

rif2internal = Namespace("http://example.com/builtin#")

class pred(DefinedNamespace):
    _fail = True
    _extras = [

            "is-literal-boolean",
            "is-literal-not-boolean",
            "boolean-equal",
            "boolean-less-than",
            "boolean-greater-than",
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
            "is-literal-date",
            "is-literal-not-date",
            "is-literal-dateTime",
            "is-literal-not-dateTime",
            "is-literal-dateTimeStamp",
            "is-literal-not-dateTimeStamp",
            "is-literal-time",
            "is-literal-not-time",
            "is-literal-dayTimeDuration",
            "is-literal-not-dayTimeDuration",
            "is-literal-yearMonthDuration",
            "is-literal-not-yearMonthDuration",
            "dateTime-equal",
            "dateTime-less-than",
            "dateTime-greater-than",
            "date-equal",
            "date-less-than",
            "date-greater-than",
            "time-equal",
            "time-less-than",
            "time-greater-than",
            "duration-equal",
            "yearMonthDuration-less-than",
            "yearMonthDuration-greater-than",
            "dayTimeDuration-less-than",
            "dayTimeDuration-greater-than",
            "dateTime-not-equal",
            "dateTime-less-than-or-equal",
            "dateTime-greater-than-or-equal",
            "date-not-equal",
            "date-less-than-or-equal",
            "date-greater-than-or-equal",
            "time-not-equal",
            "time-less-than-or-equal",
            "time-greater-than-or-equal",
            "duration-not-equal",
            "yearMonthDuration-less-than-or-equal",
            "yearMonthDuration-greater-than-or-equal",
            "dayTimeDuration-less-than-or-equal",
            "dayTimeDuration-greater-than-or-equal",
            "is-literal-PlainLiteral",
            "is-literal-not-PlainLiteral",
            "matches-language-range",

            "is-literal-string",
            "is-literal-normalizedString",
            "is-literal-token",
            "is-literal-NMTOKEN",
            "is-literal-language",
            "is-literal-Name",
            "is-literal-NCName",
            "is-literal-not-string",
            "is-literal-not-normalizedString",
            "is-literal-not-token",
            "is-literal-not-NMTOKEN",
            "is-literal-not-language",
            "is-literal-not-Name",
            "is-literal-not-NCName",
            "contains",
            "starts-with",
            "ends-with",
            "matches",
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

            "year-from-dateTime",
            "month-from-dateTime",
            "day-from-dateTime",
            "hours-from-dateTime",
            "minutes-from-dateTime",
            "seconds-from-dateTime",
            "year-from-date",
            "month-from-date",
            "day-from-date",
            "hours-from-time",
            "minutes-from-time",
            "seconds-from-time",
            "timezone-from-dateTime",
            "timezone-from-date",
            "timezone-from-time",
            "years-from-duration",
            "months-from-duration",
            "days-from-duration",
            "hours-from-duration",
            "minutes-from-duration",
            "seconds-from-duration",
            "subtract-dateTimes",
            "subtract-dates",
            "subtract-times",
            "add-yearMonthDurations",
            "subtract-yearMonthDurations",
            "divide-yearMonthDuration",
            "multiply-yearMonthDuration",
            "divide-yearMonthDuration-by-yearMonthDuration",
            "add-dayTimeDurations",
            "subtract-dayTimeDurations",
            "subtract-dayTimeDuration-from-dateTime",
            "subtract-dayTimeDuration-from-date",
            "subtract-dayTimeDuration-from-time",
            "multiply-dayTimeDuration",
            "divide-dayTimeDuration",
            "divide-dayTimeDuration-by-dayTimeDuration",
            "add-yearMonthDuration-to-dateTime",
            "add-yearMonthDuration-to-date",
            "add-dayTimeDuration-to-dateTime",
            "add-dayTimeDuration-to-date",
            "add-dayTimeDuration-to-time",
            "subtract-yearMonthDuration-from-dateTime",
            "subtract-yearMonthDuration-from-date",

            "PlainLiteral-from-string-lang",
            "string-from-PlainLiteral",
            "lang-from-PlainLiteral",
            "PlainLiteral-compare",

            "compare",
            "concat",
            "string-join",
            "substring",
            "string-length",
            "upper-case",
            "lower-case",
            "encode-for-uri",
            "iri-to-uri",
            "escape-html-uri",
            "substring-before",
            "substring-after",
            "replace",
            ]

    _NS = Namespace("http://www.w3.org/2007/rif-builtin-function#")
