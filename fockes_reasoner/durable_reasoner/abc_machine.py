import abc
import logging
import typing as typ
from typing import MutableMapping, Mapping, Union, Callable, Iterable, Optional
import rdflib
from rdflib import IdentifiedNode, Graph, Literal, Variable

FACTTYPE = "type"
"""Labels in where the type of fact is saved"""

from .bridge_rdflib import TRANSLATEABLE_TYPES

BINDABLE_TYPES = Union[TRANSLATEABLE_TYPES]
BINDING = MutableMapping[rdflib.Variable, TRANSLATEABLE_TYPES]
_RESOLVABLE_SIMPLE = Union[Variable, TRANSLATEABLE_TYPES]
RESOLVABLE = Union[_RESOLVABLE_SIMPLE, Callable[[BINDING], _RESOLVABLE_SIMPLE]]
#VARIABLE_LOCATOR = Callable[[typ.Union[durable.engine.Closure, None]], TRANSLATEABLE_TYPES]
VARIABLE_LOCATOR = Callable[[typ.Any], TRANSLATEABLE_TYPES]
CLOSURE_BINDINGS = MutableMapping[rdflib.Variable, VARIABLE_LOCATOR]

def _resolve(x: RESOLVABLE, bindings: BINDING) -> TRANSLATEABLE_TYPES:
    """Resolve variables and externals
    """
    if isinstance(x, (IdentifiedNode, Literal, list, tuple)):
        return x
    elif isinstance(x, Variable):
        return bindings[x]
    return x(bindings)


class NoPossibleExternal(ValueError):
    """Raise this, if wanted functionality is not implemented for this external
    """
    ...

#class external(abc.ABC):
#    """Parentclass for all extension for information representation."""
#    @classmethod
#    @abc.abstractmethod
#    def parse(cls, string: str) -> "external":
#        ...
#
#    @abc.abstractmethod
#    def serialize(self, c: typ.Any,
#                  bindings: BINDING,
#                  external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], "external"],
#                  ) -> str:
#        ...

class pattern(abc.ABC):
    #replaces rls.value
    pass

class fact(abc.ABC):
    ID: str

    @abc.abstractmethod
    def check_for_pattern(self, c: "machine",
                          bindings: BINDING = {},
                          ) -> bool:
        ...

    @abc.abstractmethod
    def assert_fact(self, c: "machine",
               bindings: BINDING = {},
               ) -> None:
        ...

    @abc.abstractmethod
    def add_pattern(self, rule: "rule") -> None:
        ...

    @abc.abstractmethod
    def retract_fact(self, c: "machine",
                bindings: BINDING = {},
                ) -> None:
        ...

    @abc.abstractmethod
    def modify_fact(self, c: "machine",
               bindings: BINDING = {},
               ) -> None:
        ...

    @classmethod
    @abc.abstractmethod
    def from_fact(cls, fact: Mapping[str, str]) -> "fact":
        ...

class machine(abc.ABC):
    logger: logging.Logger
    errors: list

    @abc.abstractmethod
    def check_statement(self, statement: fact) -> bool:
        """Checks if given proposition is true.
        :TODO: currently facts are only simple facts like a frame. But check
            should support complex statement like 'Xor'
        """

    @abc.abstractmethod
    def assert_fact(self, fact: Mapping[str, str]) -> None:
        ...

    @abc.abstractmethod
    def retract_fact(self, fact: Mapping[str, str]) -> None:
        """Retract all facts, that are matching with given fact.
        Eg {1:"a"} matches {1:"a", 2:"b"}
        """

    @abc.abstractmethod
    def get_facts(self) -> Iterable[fact]:
        ...

    @abc.abstractmethod
    def run(self, steps: Union[int, None] = None) -> None:
        ...

    @abc.abstractmethod
    def import_data(self,
                    infograph: Graph,
                    location: IdentifiedNode = None,
                    profile: IdentifiedNode = None,
                    extraDocuments: Mapping[IdentifiedNode, Graph] = {},
                    ) -> None:
        """
        :param profile: Defines the the model, entailment and satisfiability
            of given graph.
            `https://www.w3.org/TR/2013/REC-rif-rdf-owl-20130205/#Profiles_of_Imports`_
        """
        ...

    @abc.abstractmethod
    def create_rule_builder(self) -> "rule":
        ...

    @abc.abstractmethod
    def create_implication_builder(self) -> "implication":
        ...

class action:
    action: Optional[Callable]
    machine: machine

    @abc.abstractmethod
    def finalize(self) -> None:
        ...

class rule(abc.ABC):
    patterns: typ.Any
    action: Optional[Callable]
    machine: machine

    @abc.abstractmethod
    def finalize(self) -> None:
        ...

    @abc.abstractmethod
    def add_pattern(self,
                    pattern: Mapping[str, Union[str, TRANSLATEABLE_TYPES]],
                    factname: Optional[str] = None,
                    ) -> None:
        ...

    @abc.abstractmethod
    def generate_pattern_external(self, op, args) -> None:
        ...

    @abc.abstractmethod
    def generate_node_external(self, op, args,
                               ) -> Union[str, IdentifiedNode, Literal]:
        """
        :raises NoPossibleExternal:
        """
        ...

class implication(abc.ABC):
    patterns: typ.Any
    action: Optional[Callable]
    machine: machine

    @abc.abstractmethod
    def finalize(self) -> None:
        ...

    @abc.abstractmethod
    def add_pattern(self,
                    pattern: Mapping[str, Union[str, TRANSLATEABLE_TYPES]],
                    factname: Optional[str] = None,
                    ) -> None:
        ...

    @abc.abstractmethod
    def generate_pattern_external(self, op, args) -> None:
        ...

    @abc.abstractmethod
    def generate_node_external(self, op, args,
                               ) -> Union[str, IdentifiedNode, Literal]:
        """
        :raises NoPossibleExternal:
        """
        ...


class importProfile(abc.ABC):
    @abc.abstractmethod
    def create_rules(self, machine: machine, infograph: Graph) -> None:
        ...
