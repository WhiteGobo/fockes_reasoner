import abc
import logging
import typing as typ
from typing import MutableMapping, Mapping, Union, Callable, Iterable
import rdflib

FACTTYPE = "type"
"""Labels in where the type of fact is saved"""

TRANSLATEABLE_TYPES = typ.Union[rdflib.Variable,
                                rdflib.URIRef,
                                rdflib.BNode,
                                rdflib.Literal,
                                list["TRANSLATEABLE_TYPES"],
                                "external",
                                ]
BINDING = MutableMapping[rdflib.Variable, str]
#VARIABLE_LOCATOR = Callable[[typ.Union[durable.engine.Closure, None]], TRANSLATEABLE_TYPES]
VARIABLE_LOCATOR = Callable[[typ.Any], TRANSLATEABLE_TYPES]
CLOSURE_BINDINGS = MutableMapping[rdflib.Variable, VARIABLE_LOCATOR]

class external(abc.ABC):
    """Parentclass for all extension for information representation."""
    @classmethod
    @abc.abstractmethod
    def parse(cls, string: str) -> "external":
        ...

    @abc.abstractmethod
    def serialize(self, c: typ.Any,
                  bindings: BINDING,
                  external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], "external"],
                  ) -> str:
        ...

class pattern(abc.ABC):
    #replaces rls.value
    pass

class fact(abc.ABC):
    ID: str

    @abc.abstractmethod
    def assert_fact(self, c: "machine",
               bindings: BINDING = {},
               external_resolution: Mapping[Union[rdflib.URIRef,
                                                  rdflib.BNode], external] = {},
               ) -> None:
        ...

    @abc.abstractmethod
    def generate_pattern(self, bindings: CLOSURE_BINDINGS,
                         factname: str) -> pattern:
        ...

    @abc.abstractmethod
    def retract_fact(self, c: "machine",
                bindings: BINDING = {},
                external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], external] = {},
                ) -> None:
        ...

    @abc.abstractmethod
    def modify_fact(self, c: "machine",
               bindings: BINDING = {},
               external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], external] = {},
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
    def make_rule(self) -> None:
        ...

    @abc.abstractmethod
    def make_start_action(self) -> None:
        ...

    @abc.abstractmethod
    def run(self, steps: Union[int, None] = None) -> None:
        ...

class rule:
    patterns: typ.Any
    action: Callable
    machine: machine
    def __init__(self, machine: machine, patterns = [], action = None):
        self.machine = machine
        self.patterns = list(patterns)
        self.action = action

    @abc.abstractmethod
    def finalize_rule(self) -> None:
        ...

    @abc.abstractmethod
    def add_pattern(self) -> None:
        ...

    @abc.abstractmethod
    def set_action(self) -> None:
        ...
