from typing import Callable, Union, TypeVar, Iterable, Container, Tuple
import rdflib
import urllib
import itertools as it
from rdflib import Literal, Variable, XSD, IdentifiedNode, Literal, URIRef, RDF
import logging
logger = logging.getLogger()
from dataclasses import dataclass, field
from ..bridge_rdflib import term_list, _term_list, TRANSLATEABLE_TYPES
import re

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS
from ...shared import pred, func
from .shared import is_datatype, invert, assign_rdflib
import locale

VALID_STRING_TYPES = {None, RDF.PlainLiteral, XSD.string}
_externals: Iterable
_datatypes: Iterable[URIRef] = [
        XSD.string,
        XSD.normalizedString,
        XSD.token,
        XSD.language,
        XSD.Name,
        XSD.NCName,
        XSD.NMTOKEN,
        ]

def _register_stringExternals(machine):
    for dt in _datatypes:
        machine.register(dt, asassign=assign_rdflib.gen(dt))
    for x in _externals:
        as_ = {}
        for t in ["asassign", "aspattern", "asbinding"]:
            if hasattr(x, t):
                foo = getattr(x, t)
                if foo is None:
                    as_[t] = x
                elif isinstance(foo, str):
                    as_[t] = getattr(x, foo)
                else:
                    as_[t] = foo
        machine.register(x.op, **as_)

@dataclass
class is_literal_string:
    op = pred["is-literal-string"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype in VALID_STRING_TYPES)


@dataclass
class is_literal_normalizedString:
    op = pred["is-literal-normalizedString"]
    asassign = None
    target: RESOLVABLE
    _VALID_TYPES = VALID_STRING_TYPES.union([XSD.normalizedString])
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype not in self._VALID_TYPES:
            return Literal(False)
        elif "\t" in t:
            return Literal(False)
        else:
            return Literal(True)

@dataclass
class is_literal_token:
    op = pred["is-literal-token"]
    asassign = None
    target: RESOLVABLE
    _VALID_TYPES = VALID_STRING_TYPES.union([XSD.token])
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)

        if t.datatype not in self._VALID_TYPES:
            return Literal(False)
        elif any(x in t for x in ("\t", "  ", "\n", "\r")):
            return Literal(False)
        elif t[0]==" " or t[-1] == " ":
            return Literal(False)
        else:
            return Literal(True)

@dataclass
class is_literal_NMToken:
    op = pred["is-literal-NMTOKEN"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype == XSD.NMTOKEN)

@dataclass
class is_literal_language:
    op = pred["is-literal-language"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype == XSD.language)

@dataclass
class is_literal_Name:
    op = pred["is-literal-Name"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype == XSD.Name)

@dataclass
class is_literal_NCName:
    op = pred["is-literal-NCName"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype == XSD.NCName)

@dataclass
class is_literal_not_string:
    op = pred["is-literal-not-string"]
    asassign = invert.gen(is_literal_string)

@dataclass
class is_literal_not_normalizedString:
    op = pred["is-literal-not-normalizedString"]
    asassign = invert.gen(is_literal_normalizedString)

@dataclass
class is_literal_not_token:
    op = pred["is-literal-not-token"]
    asassign = invert.gen(is_literal_token)

@dataclass
class is_literal_not_NMToken:
    op = pred["is-literal-not-NMTOKEN"]
    asassign = invert.gen(is_literal_NMToken)

@dataclass
class is_literal_not_language:
    op = pred["is-literal-not-language"]
    asassign = invert.gen(is_literal_language)

@dataclass
class is_literal_not_Name:
    op = pred["is-literal-not-Name"]
    asassign = invert.gen(is_literal_Name)

@dataclass
class is_literal_not_NCName:
    op = pred["is-literal-not-NCName"]
    asassign = invert.gen(is_literal_NCName)

@dataclass
class compare:
    """Return an -1, 0 or 1 depending on the alphabetical order of the two
    Literals. See :term:`codepoint collation` for more information.
    """
    op = func["compare"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        l = _resolve(self.left, bindings)
        r = _resolve(self.right, bindings)
        return Literal(locale.strcoll(l, r))

@dataclass
class concat:
    """
    :TODO: should work with any number of arguments
    """
    op = func["concat"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        l = _resolve(self.left, bindings)
        r = _resolve(self.right, bindings)
        return Literal("".join((l, r)), datatype=XSD.string)

@dataclass
class string_join:
    """
    :TODO: should work with any number of arguments
    """
    op = func["string-join"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    separator: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        l = _resolve(self.left, bindings)
        r = _resolve(self.right, bindings)
        sep = str(_resolve(self.separator, bindings))
        return Literal(sep.join((l, r)), datatype=XSD.string)

@dataclass
class substring:
    op = func["substring"]
    asassign = None
    target: RESOLVABLE
    left: RESOLVABLE
    right: RESOLVABLE = field(default=None)
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        l = _resolve(self.left, bindings)
        if self.right is not None:
            r = _resolve(self.right, bindings)
            substring = t[l.value:r.value]
        else:
            substring = t[l.value:]
        logger.error(substring)
        return Literal(substring, datatype=XSD.string)

@dataclass
class string_length:
    op = func["string-length"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(len(t))
        raise NotImplementedError()

@dataclass
class uppercase:
    op = func["upper-case"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.upper(), datatype=XSD.string)

@dataclass
class lowercase:
    op = func["lower-case"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.lower(), datatype=XSD.string)

@dataclass
class encode_for_uri:
    op = func["encode-for-uri"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(urllib.parse.quote(t), datatype=XSD.string)


@dataclass
class iri_to_uri:
    op = func["iri-to-uri"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        components = list(urllib.parse.urlparse(t))
        for i, x in enumerate(components):
            components[i] = urllib.parse.quote(x)
        return Literal(urllib.parse.urlunparse(components),
                       datatype=XSD.string)

@dataclass
class escape_html_uri:
    op = func["escape-html-uri"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        #return Literal("javascript:if (navigator.browserLanguage == 'fr') window.open('http://www.example.com/~b%C3%A9b%C3%A9');", datatype=XSD.string)
        raise NotImplementedError()

@dataclass
class substring_before:
    op = func["substring-before"]
    asassign = None
    superstring: RESOLVABLE
    substring: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        substring = _resolve(self.substring, bindings)
        superstring = _resolve(self.superstring, bindings)
        i = superstring.find(substring)
        return Literal(superstring[:i],
                       datatype=superstring.datatype)

@dataclass
class substring_after:
    op = func["substring-after"]
    asassign = None
    superstring: RESOLVABLE
    substring: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        substring = _resolve(self.substring, bindings)
        superstring = _resolve(self.superstring, bindings)
        i = superstring.find(substring) + len(substring)
        return Literal(superstring[i:],
                       datatype=superstring.datatype)

@dataclass
class replace:
    op = func["replace"]
    asassign = None
    target: RESOLVABLE
    pattern: RESOLVABLE
    replacement: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        p = _resolve(self.pattern, bindings)
        r = _resolve(self.replacement, bindings)
        #return Literal("[1=ab][2=]cd", datatype=XSD.string)
        raise NotImplementedError()

@dataclass
class contains:
    op = pred["contains"]
    asassign = None
    superstring: RESOLVABLE
    substring: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        superstring = str(_resolve(self.superstring, bindings))
        substring = str(_resolve(self.substring, bindings))
        return Literal(substring in superstring)


@dataclass
class starts_with:
    op = pred["starts-with"]
    asassign = None
    superstring: RESOLVABLE
    substring: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        superstring = str(_resolve(self.superstring, bindings))
        substring = str(_resolve(self.substring, bindings))
        return Literal(superstring.startswith(substring))

@dataclass
class ends_with:
    op = pred["ends-with"]
    asassign = None
    superstring: RESOLVABLE
    substring: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        superstring = str(_resolve(self.superstring, bindings))
        substring = str(_resolve(self.substring, bindings))
        right_pos = superstring.rfind(substring)
        if right_pos == -1:
            return Literal(False)
        else:
            return Literal(len(superstring) == right_pos+len(substring))

@dataclass
class matches:
    op = pred["matches"]
    asassign = None
    superstring: RESOLVABLE
    substring: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        superstring = str(_resolve(self.superstring, bindings))
        substring = str(_resolve(self.substring, bindings))
        pattern = re.compile(substring)
        return Literal(pattern.match(superstring))

@dataclass
class iri_string:
    """Assigns to given variable the string as iri
    """
    op = pred["iri-string"]
    target_var: RESOLVABLE
    source_string: RESOLVABLE
    _is_binding: bool = field(default=False)
    asassign = None
    aspattern = "pattern_generator"

    @classmethod
    def pattern_generator(
            cls,
            machine,
            args: Iterable[RESOLVABLE],
            bound_variables: Container[Variable],
            ) -> Iterable[Tuple[Iterable[abc_pattern],
                                Tuple["pred_iri_string"],
                                Iterable[Variable]]]:
        target_var, source_string = args
        if all(x in bound_variables for x in (target_var, source_string)
               if isinstance(x, Variable)):
            condition = cls(target_var, source_string)
            yield tuple(), (condition,), tuple()
        elif isinstance(target_var, Variable) and target_var not in bound_variables:
            condition = cls(target_var, source_string, _is_binding=True)
            yield tuple(), (condition,), [target_var]
        else:
            raise NotImplementedError()


    def __call__(self, bindings: BINDING) -> Literal:
        s = _resolve(self.source_string, bindings)
        if self._is_binding:
            assert self.target_var not in bindings
            bindings[self.target_var] = URIRef(str(s))
            return Literal(True)
        else:
            t = _resolve(self.target_var, bindings)
            return Literal(t == URIRef(str(s)))


_externals = [
        is_literal_string,
        is_literal_normalizedString,
        is_literal_token,
        is_literal_NMToken,
        is_literal_language,
        is_literal_Name,
        is_literal_NCName,
        is_literal_not_string,
        is_literal_not_normalizedString,
        is_literal_not_token,
        is_literal_not_NMToken,
        is_literal_not_language,
        is_literal_not_Name,
        is_literal_not_NCName,
        compare,
        concat,
        string_join,
        substring,
        string_length,
        uppercase,
        lowercase,
        encode_for_uri,
        iri_to_uri,
        escape_html_uri,
        substring_before,
        substring_after,
        replace,
        contains,
        starts_with,
        ends_with,
        matches,
        iri_string,
        ]
