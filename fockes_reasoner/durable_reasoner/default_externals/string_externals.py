from typing import Callable, Union, TypeVar, Iterable, Container, Tuple, Optional
import rdflib
import urllib
import itertools as it
from rdflib import Literal, Variable, XSD, IdentifiedNode, Literal, URIRef, RDF
import logging
logger = logging.getLogger()
from dataclasses import dataclass, field
from ..bridge_rdflib import term_list, _term_list, TRANSLATEABLE_TYPES
import re

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS, NoPossibleExternal
from .. import abc_machine
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

def _register_stringExternals(machine: abc_machine.extensible_Machine) -> None:
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
    asassign = None
    target: RESOLVABLE
    op: URIRef = pred["is-literal-string"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        return Literal(t.datatype in VALID_STRING_TYPES)


@dataclass
class is_literal_normalizedString:
    asassign = None
    target: RESOLVABLE
    _VALID_TYPES = VALID_STRING_TYPES.union([XSD.normalizedString])
    op: URIRef = pred["is-literal-normalizedString"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        if t.datatype not in self._VALID_TYPES:
            return Literal(False)
        elif "\t" in t:
            return Literal(False)
        else:
            return Literal(True)

@dataclass
class is_literal_token:
    asassign = None
    target: RESOLVABLE
    op: URIRef = pred["is-literal-token"]
    _VALID_TYPES = VALID_STRING_TYPES.union([XSD.token])
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)

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
    asassign = None
    target: RESOLVABLE
    op: URIRef = pred["is-literal-NMTOKEN"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        return Literal(t.datatype == XSD.NMTOKEN)

@dataclass
class is_literal_language:
    asassign = None
    target: RESOLVABLE
    op: URIRef = pred["is-literal-language"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        return Literal(t.datatype == XSD.language)

@dataclass
class is_literal_Name:
    asassign = None
    target: RESOLVABLE
    op: URIRef = pred["is-literal-Name"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        return Literal(t.datatype == XSD.Name)

@dataclass
class is_literal_NCName:
    asassign = None
    target: RESOLVABLE
    op: URIRef = pred["is-literal-NCName"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        return Literal(t.datatype == XSD.NCName)

class is_literal_not_string:
    op: URIRef = pred["is-literal-not-string"]
    asassign = invert.gen(is_literal_string)

class is_literal_not_normalizedString:
    op: URIRef = pred["is-literal-not-normalizedString"]
    asassign = invert.gen(is_literal_normalizedString)

class is_literal_not_token:
    op: URIRef = pred["is-literal-not-token"]
    asassign = invert.gen(is_literal_token)

class is_literal_not_NMToken:
    op: URIRef = pred["is-literal-not-NMTOKEN"]
    asassign = invert.gen(is_literal_NMToken)

class is_literal_not_language:
    op: URIRef = pred["is-literal-not-language"]
    asassign = invert.gen(is_literal_language)

class is_literal_not_Name:
    op: URIRef = pred["is-literal-not-Name"]
    asassign = invert.gen(is_literal_Name)

class is_literal_not_NCName:
    op: URIRef = pred["is-literal-not-NCName"]
    asassign = invert.gen(is_literal_NCName)

@dataclass
class compare:
    """Return an -1, 0 or 1 depending on the alphabetical order of the two
    Literals. See :term:`codepoint collation` for more information.
    """
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["compare"]
    def __call__(self, bindings: BINDING) -> Literal:
        l = _resolve(self.left, bindings)
        r = _resolve(self.right, bindings)
        assert isinstance(l, Literal)
        assert isinstance(r, Literal)
        return Literal(locale.strcoll(l, r))

class concat:
    asassign = None
    args: Iterable[RESOLVABLE]
    op: URIRef = func["concat"]
    def __init__(self, *args: RESOLVABLE):
        self.args = list(args)
    def __call__(self, bindings: BINDING) -> Literal:
        args = []
        for x in self.args:
            x_ = _resolve(x, bindings)
            assert isinstance(x_, Literal)
            args.append(x_)
        return Literal("".join(args), datatype=XSD.string)

class string_join:
    """
    :TODO: should work with any number of arguments
    """
    asassign = None
    items: Iterable[RESOLVABLE]
    separator: RESOLVABLE
    op: URIRef = func["string-join"]
    def __init__(self, *args: RESOLVABLE) -> None:
        self.items = tuple(args[:-1])
        self.separator = args[-1]

    def __call__(self, bindings: BINDING) -> Literal:
        items = []
        for x in self.items:
            x_ = _resolve(x, bindings)
            assert isinstance(x_, Literal)
            items.append(x_)
        sep = str(_resolve(self.separator, bindings))
        return Literal(sep.join(items), datatype=XSD.string)

@dataclass
class substring:
    asassign = None
    target: RESOLVABLE
    left: RESOLVABLE
    right: Optional[RESOLVABLE] = field(default=None)
    op: URIRef = func["substring"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        l = _resolve(self.left, bindings)
        assert isinstance(l, Literal)
        if self.right is not None:
            r = _resolve(self.right, bindings)
            assert isinstance(r, Literal)
            substring = t[l.value:r.value]
        else:
            substring = t[l.value:]
        logger.error(substring)
        return Literal(substring, datatype=XSD.string)

@dataclass
class string_length:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["string-length"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(len(t))

@dataclass
class uppercase:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["upper-case"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        return Literal(t.upper(), datatype=XSD.string)

@dataclass
class lowercase:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["lower-case"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        return Literal(t.lower(), datatype=XSD.string)

@dataclass
class encode_for_uri:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["encode-for-uri"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        return Literal(urllib.parse.quote(t), datatype=XSD.string)


@dataclass
class iri_to_uri:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["iri-to-uri"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        components = list(urllib.parse.urlparse(t))
        for i, x in enumerate(components):
            components[i] = urllib.parse.quote(x)
        return Literal(urllib.parse.urlunparse(components),
                       datatype=XSD.string)

@dataclass
class escape_html_uri:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["escape-html-uri"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        #return Literal("javascript:if (navigator.browserLanguage == 'fr') window.open('http://www.example.com/~b%C3%A9b%C3%A9');", datatype=XSD.string)
        raise NotImplementedError()

@dataclass
class substring_before:
    asassign = None
    superstring: RESOLVABLE
    substring: RESOLVABLE
    op: URIRef = func["substring-before"]
    def __call__(self, bindings: BINDING) -> Literal:
        substring = _resolve(self.substring, bindings)
        superstring = _resolve(self.superstring, bindings)
        assert isinstance(substring, Literal)
        assert isinstance(superstring, Literal)
        i = superstring.find(substring)
        return Literal(superstring[:i],
                       datatype=superstring.datatype)

@dataclass
class substring_after:
    asassign = None
    superstring: RESOLVABLE
    substring: RESOLVABLE
    op: URIRef = func["substring-after"]
    def __call__(self, bindings: BINDING) -> Literal:
        substring = _resolve(self.substring, bindings)
        superstring = _resolve(self.superstring, bindings)
        assert isinstance(substring, Literal)
        assert isinstance(superstring, Literal)
        i = superstring.find(substring) + len(substring)
        return Literal(superstring[i:],
                       datatype=superstring.datatype)

@dataclass
class replace:
    asassign = None
    target: RESOLVABLE
    pattern: RESOLVABLE
    replacement: RESOLVABLE
    op: URIRef = func["replace"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        p = _resolve(self.pattern, bindings)
        r = _resolve(self.replacement, bindings)
        #return Literal("[1=ab][2=]cd", datatype=XSD.string)
        raise NotImplementedError()

@dataclass
class contains:
    asassign = None
    superstring: RESOLVABLE
    substring: RESOLVABLE
    op: URIRef = pred["contains"]
    def __call__(self, bindings: BINDING) -> Literal:
        superstring = str(_resolve(self.superstring, bindings))
        substring = str(_resolve(self.substring, bindings))
        assert isinstance(substring, Literal)
        assert isinstance(superstring, Literal)
        return Literal(substring in superstring)


@dataclass
class starts_with:
    asassign = None
    superstring: RESOLVABLE
    substring: RESOLVABLE
    op: URIRef = pred["starts-with"]
    def __call__(self, bindings: BINDING) -> Literal:
        superstring = str(_resolve(self.superstring, bindings))
        substring = str(_resolve(self.substring, bindings))
        assert isinstance(substring, Literal)
        assert isinstance(superstring, Literal)
        return Literal(superstring.startswith(substring))

@dataclass
class ends_with:
    asassign = None
    superstring: RESOLVABLE
    substring: RESOLVABLE
    op: URIRef = pred["ends-with"]
    def __call__(self, bindings: BINDING) -> Literal:
        superstring = str(_resolve(self.superstring, bindings))
        substring = str(_resolve(self.substring, bindings))
        assert isinstance(substring, Literal)
        assert isinstance(superstring, Literal)
        right_pos = superstring.rfind(substring)
        if right_pos == -1:
            return Literal(False)
        else:
            return Literal(len(superstring) == right_pos+len(substring))

@dataclass
class matches:
    asassign = None
    superstring: RESOLVABLE
    substring: RESOLVABLE
    op: URIRef = pred["matches"]
    def __call__(self, bindings: BINDING) -> Literal:
        superstring = str(_resolve(self.superstring, bindings))
        substring = str(_resolve(self.substring, bindings))
        assert isinstance(substring, Literal)
        assert isinstance(superstring, Literal)
        pattern = re.compile(substring)
        return Literal(pattern.match(superstring))

@dataclass
class iri_string:
    """Assigns to given variable the string as iri
    """
    target_var: RESOLVABLE
    source_string: RESOLVABLE
    _is_binding: bool = field(default=False)
    asassign = None
    aspattern = "pattern_generator"
    op: URIRef = pred["iri-string"]

    @classmethod
    def pattern_generator(
            cls,
            machine: abc_machine.Machine,
            args: Iterable[RESOLVABLE],
            bound_variables: Container[Variable],
            ) -> Iterable[Tuple[Iterable[abc_pattern],
                                Tuple["iri_string"],
                                Iterable[Variable]]]:
        target_var, source_string = args
        not_bound_vars = [x for x in args
                          if isinstance(x, Variable)
                          and x not in bound_variables]
        if source_string in not_bound_vars:
            raise NoPossibleExternal()
        if not not_bound_vars:
            condition = cls(target_var, source_string)
            yield tuple(), (condition,), tuple()
        elif isinstance(target_var, Variable)\
                and target_var not in bound_variables:
            condition = cls(target_var, source_string, _is_binding=True)
            yield tuple(), (condition,), [target_var]
        else:
            raise NotImplementedError()


    def __call__(self, bindings: BINDING) -> Literal:
        s = _resolve(self.source_string, bindings)
        if self._is_binding:
            assert isinstance(self.target_var, Variable)
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
