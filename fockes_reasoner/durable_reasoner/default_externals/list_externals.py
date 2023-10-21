from typing import Callable, Union, TypeVar, Iterable, Container, Tuple
import rdflib
import itertools as it
from rdflib import Literal, Variable, XSD, IdentifiedNode, Literal, URIRef
import logging
logger = logging.getLogger()
from dataclasses import dataclass
import math
from ..bridge_rdflib import term_list, _term_list, TRANSLATEABLE_TYPES

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS
from ...shared import pred, func
from .shared import RegisterInformation, invert, RegisterHelper

is_list = RegisterInformation(pred["is-list"])
@is_list.set_asassign
@dataclass
class _is_list:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        target = _resolve(self.target, bindings)
        return Literal(isinstance(target, term_list))

list_contains = RegisterInformation(pred["list-contains"])
@list_contains.set_asassign
@dataclass
class _list_contains:
    container: RESOLVABLE
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        container = _resolve(self.container, bindings)
        if not isinstance(container, term_list):
            raise TypeError("Expected a list: %s" % container)
        target = _resolve(self.target, bindings)
        return Literal(target in container)

make_list = RegisterInformation(func["make-list"])
@make_list.set_asassign
class _make_list:
    items: Iterable[RESOLVABLE]
    def __init__(self, *items: RESOLVABLE) -> None:
        self.items = items

    def __call__(self, bindings: BINDING) -> _term_list:
        items = [_resolve(item, bindings) for item in self.items]
        return _term_list(items)

count = RegisterInformation(func["count"])
@count.set_asassign
@dataclass
class _count:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        target = _resolve(self.target, bindings)
        return Literal(len(target))

list_get = RegisterInformation(func["get"])
@list_get.set_asassign
@dataclass
class _list_get:
    target: RESOLVABLE
    index: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        index = int(_resolve(self.index, bindings))#type: ignore[arg-type]
        return target[index]

sublist = RegisterInformation(func["sublist"])
@sublist.set_asassign
@dataclass
class _sublist:
    target: RESOLVABLE
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        left = int(_resolve(self.left, bindings))#type: ignore[arg-type]
        right = int(_resolve(self.right, bindings))#type: ignore[arg-type]
        return target[left: right]

append = RegisterInformation(func["append"])
@append.set_asassign
class _append:
    target: RESOLVABLE
    items: Iterable[RESOLVABLE]
    def __init__(self, target: RESOLVABLE, *items: RESOLVABLE,
                 ) -> None:
        self.target = target
        self.items = items

    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        items = (_resolve(item, bindings) for item in self.items)
        return _term_list(list(it.chain(target, items)))


union = RegisterInformation(func["union"])
@union.set_asassign
@dataclass
class _union:
    """
    :TODO: This is currently the same as concatenate
    """
    first: RESOLVABLE
    second: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        first = _resolve(self.first, bindings)
        assert isinstance(first, term_list)
        second = _resolve(self.second, bindings)
        assert isinstance(second, term_list)
        return _term_list(list(it.chain(first, second)))

distinct_values = RegisterInformation(func["distinct-values"])
@distinct_values.set_asassign
@dataclass
class _distinct_values:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        return _term_list(list(set(target)))

intersect = RegisterInformation(func["intersect"])
@intersect.set_asassign
@dataclass
class _intersect:
    first: RESOLVABLE
    second: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        first = _resolve(self.first, bindings)
        assert isinstance(first, term_list)
        second = _resolve(self.second, bindings)
        assert isinstance(second, term_list)
        return _term_list([x for x in first if x in second])

list_except = RegisterInformation(func["except"])
@list_except.set_asassign
@dataclass
class _list_except:
    target: RESOLVABLE
    switch: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        switch = _resolve(self.switch, bindings)
        assert isinstance(switch, term_list)
        return _term_list([x for x in target if x not in switch])


concatenate = RegisterInformation(func["concatenate"])
@concatenate.set_asassign
@dataclass
class _concatenate:
    first: RESOLVABLE
    second: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        first = _resolve(self.first, bindings)
        assert isinstance(first, term_list)
        second = _resolve(self.second, bindings)
        assert isinstance(second, term_list)
        return _term_list(list(it.chain(first, second)))

insert_before = RegisterInformation(func["insert-before"])
@insert_before.set_asassign
@dataclass
class _insert_before:
    target: RESOLVABLE
    index: RESOLVABLE
    item: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        index = int(_resolve(self.index, bindings))#type: ignore[arg-type]
        item = _resolve(self.item, bindings)
        newlist = list(target)
        newlist.insert(index, item)
        return _term_list(newlist)

remove = RegisterInformation(func["remove"])
@remove.set_asassign
@dataclass
class _remove:
    target: RESOLVABLE
    index: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        index = int(_resolve(self.index, bindings))#type: ignore[arg-type]
        newlist = list(target)
        newlist.pop(index)
        return _term_list(newlist)


reverse_list = RegisterInformation(func["reverse"])
@reverse_list.set_asassign
@dataclass
class _reverse_list:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        newlist = list(target)
        newlist.reverse()
        return _term_list(newlist)


index_of = RegisterInformation(func["index-of"])
@index_of.set_asassign
@dataclass
class _index_of:
    target: RESOLVABLE
    item: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        item = _resolve(self.item, bindings)
        indices = (Literal(i) for i, x in enumerate(target) if x == item)
        return _term_list(list(indices))

register_list_externals = RegisterHelper(
        [],
        [is_list, list_contains, make_list, count, list_get, sublist, append,
         union, distinct_values, intersect, list_except, concatenate,
         insert_before, remove, reverse_list, index_of,
         ],
        )
