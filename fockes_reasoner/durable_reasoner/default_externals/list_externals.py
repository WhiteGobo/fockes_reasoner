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

@dataclass
class is_list:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        target = _resolve(self.target, bindings)
        return Literal(isinstance(target, term_list))

@dataclass
class list_contains:
    container: RESOLVABLE
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        container = _resolve(self.container, bindings)
        if not isinstance(container, term_list):
            raise TypeError("Expected a list: %s" % container)
        target = _resolve(self.target, bindings)
        return Literal(target in container)

class make_list:
    items: Iterable[RESOLVABLE]
    def __init__(self, *items: RESOLVABLE) -> None:
        self.items = items

    def __call__(self, bindings: BINDING) -> _term_list:
        items = [_resolve(item, bindings) for item in self.items]
        return _term_list(items)

@dataclass
class count:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        target = _resolve(self.target, bindings)
        return Literal(len(target))

@dataclass
class list_get:
    target: RESOLVABLE
    index: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        index = int(_resolve(self.index, bindings))#type: ignore[arg-type]
        return target[index]

@dataclass
class sublist:
    target: RESOLVABLE
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        left = int(_resolve(self.left, bindings))#type: ignore[arg-type]
        right = int(_resolve(self.right, bindings))#type: ignore[arg-type]
        return target[left: right]

class append:
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


@dataclass
class union:
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

@dataclass
class distinct_values:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        return _term_list(list(set(target)))

@dataclass
class intersect:
    first: RESOLVABLE
    second: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        first = _resolve(self.first, bindings)
        assert isinstance(first, term_list)
        second = _resolve(self.second, bindings)
        assert isinstance(second, term_list)
        return _term_list([x for x in first if x in second])

@dataclass
class list_except:
    target: RESOLVABLE
    switch: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        switch = _resolve(self.switch, bindings)
        assert isinstance(switch, term_list)
        return _term_list([x for x in target if x not in switch])


@dataclass
class concatenate:
    first: RESOLVABLE
    second: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        first = _resolve(self.first, bindings)
        assert isinstance(first, term_list)
        second = _resolve(self.second, bindings)
        assert isinstance(second, term_list)
        return _term_list(list(it.chain(first, second)))

@dataclass
class insert_before:
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

@dataclass
class remove:
    target: RESOLVABLE
    index: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        index = int(_resolve(self.index, bindings))#type: ignore[arg-type]
        newlist = list(target)
        newlist.pop(index)
        return _term_list(newlist)


@dataclass
class reverse_list:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        newlist = list(target)
        newlist.reverse()
        return _term_list(newlist)


@dataclass
class index_of:
    target: RESOLVABLE
    item: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        item = _resolve(self.item, bindings)
        indices = (Literal(i) for i, x in enumerate(target) if x == item)
        return _term_list(list(indices))
