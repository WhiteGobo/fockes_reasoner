import typing as typ
from typing import Union, Iterator, Iterable, Optional, Mapping
from .abc_machine import fact, BINDING, BINDING_WITH_BLANKS, CLOSURE_BINDINGS, VARIABLE_LOCATOR, TRANSLATEABLE_TYPES, ATOM_ARGS, RESOLVABLE, _resolve, abc_external
from . import abc_machine
from rdflib import Variable
from .bridge_rdflib import string2rdflib, rdflib2string
from ..shared import _pretty


class rdfs_subclass(fact):
    sub_class: Union[TRANSLATEABLE_TYPES, abc_external, Variable]
    super_class: Union[TRANSLATEABLE_TYPES, abc_external, Variable]
    ID: str = "owl_subclass"
    SUBCLASS_SUB: str = "sub"
    SUBCLASS_SUPER: str = "super"
    def __init__(self, 
                 sub_class: Union[TRANSLATEABLE_TYPES, abc_external, Variable],
                 super_class: Union[TRANSLATEABLE_TYPES, abc_external, Variable],
                 ) -> None:
        self.sub_class = sub_class
        self.super_class = super_class

    def __iter__(self) -> Iterator[str]:
        yield self.SUBCLASS_SUB
        yield self.SUBCLASS_SUPER

    def __len__(self) -> int:
        return 2

    def __getitem__(self, key: str,
                ) -> Union[TRANSLATEABLE_TYPES, abc_external, Variable]:
        if key == self.SUBCLASS_SUB:
            return self.sub_class
        elif key == self.SUBCLASS_SUPER:
            return self.super_class
        else:
            raise KeyError(key)

    @property
    def used_variables(self) -> Iterable[Variable]:
        if isinstance(self.sub_class, Variable):
            yield self.sub_class
        if isinstance(self.super_class, Variable):
            yield self.super_class

    def __repr__(self) -> str:
        return "OWL SubClassOf(%s, %s)" % (_pretty(self.sub_class),
                                           _pretty(self.super_class))

    def as_dict(self, bindings: Optional[BINDING] = None,
                ) -> Mapping[str, Union[str, Variable, TRANSLATEABLE_TYPES]]:
        if isinstance(self.sub_class, abc_external) or isinstance(self.super_class, abc_external):
            raise NotImplementedError()
        pattern: Mapping[str, Union[str, Variable, TRANSLATEABLE_TYPES]]\
                = {abc_machine.FACTTYPE: self.ID,
                   self.SUBCLASS_SUB: self.sub_class,
                   self.SUBCLASS_SUPER: self.super_class,
                   }
        return pattern

    def retract_fact(self, c: abc_machine.machine,
                bindings: BINDING = {},
                ) -> None:
        raise NotImplementedError()

    def modify_fact(self, c: abc_machine.machine,
               bindings: BINDING = {},
               ) -> None:
        raise NotImplementedError()

    @classmethod
    def from_fact(cls, fact: Mapping[str, str]) -> "subclass":
        sub_class = string2rdflib(fact[cls.SUBCLASS_SUB])
        super_class = string2rdflib(fact[cls.SUBCLASS_SUPER])
        return cls(sub_class, super_class)
