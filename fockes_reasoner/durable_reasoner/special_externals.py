from typing import Any, Union, Optional
from dataclasses import dataclass, field
from collections.abc import Iterable, Mapping, Callable
from rdflib import Variable, URIRef, Literal
from .abc_machine import abc_external, TRANSLATEABLE_TYPES, RESOLVABLE, BINDING, _resolve
from . import abc_machine
from .default_externals import literal_equal

@dataclass(frozen=True)
class _id:
    """Alternative to uri"""
    name: str = field(hash=True)

@dataclass
class _special_external(Mapping):
    op: _id
    asassign: Optional[Callable] = field(default=None)
    aspattern: Optional[Callable] = field(default=None)
    asbinding: Optional[Mapping[tuple[bool], Callable]] = field(default=None)

    def __iter__(self):
        for x in ["op", "asassign", "asbinding"]:
            if getattr(self, x, None) is not None:
                yield x

    def __len__(self) -> int:
        i = 0
        for x in ["op", "asassign", "asbinding"]:
            if getattr(self, x, None) is not None:
                i += 1
        return i

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError as err:
            raise KeyError(key) from err

@dataclass
class bind_first:
    left: Variable
    right: RESOLVABLE

    def __call__(self, bindings:BINDING) -> Literal:
        right = _resolve(self.right, bindings)
        bindings[self.left] = right
        return Literal(True)
equality = _special_external(_id("rif equality"),
                             asassign=literal_equal,
                             asbinding={(True, False): bind_first},
                             )
