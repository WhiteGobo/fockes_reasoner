import abc
import logging
import typing as typ
from typing import MutableMapping, Mapping, Union, Callable, Iterable, Optional, overload
from collections.abc import Collection
import rdflib
from rdflib import IdentifiedNode, Graph, Literal, Variable
from collections.abc import MutableSequence

FACTTYPE = "type"
"""Labels in where the type of fact is saved"""

from .bridge_rdflib import TRANSLATEABLE_TYPES, term_list

BINDABLE_TYPES = Union[TRANSLATEABLE_TYPES]
BINDING = MutableMapping[rdflib.Variable, TRANSLATEABLE_TYPES]
BINDING_WITH_BLANKS = MutableMapping[rdflib.Variable,
                                     Union[TRANSLATEABLE_TYPES, None]]
RESOLVER = Callable[[BINDING], TRANSLATEABLE_TYPES]
RESOLVABLE = Union[Variable, TRANSLATEABLE_TYPES, RESOLVER]
#VARIABLE_LOCATOR = Callable[[typ.Union[durable.engine.Closure, None]], TRANSLATEABLE_TYPES]
VARIABLE_LOCATOR = Callable[[typ.Any], TRANSLATEABLE_TYPES]
CLOSURE_BINDINGS = MutableMapping[rdflib.Variable, VARIABLE_LOCATOR]
ATOM_ARGS = Iterable[Union[TRANSLATEABLE_TYPES, Variable, "abc_external"]]

class RuleNotComplete(Exception):
    """Rules are objects, that are worked on. So if you finalize a rule
    There may not be all needed information. Raise this error in that case
    """

class VariableNotBoundError(Exception):
    """If a rules doesnt bound Variables as expected by the action."""

class abc_external(abc.ABC):
    op: IdentifiedNode
    args: ATOM_ARGS

    @abc.abstractmethod
    def as_resolvable(self, machine: "machine") -> RESOLVABLE:
        ...

def _resolve(x: RESOLVABLE, bindings: BINDING,
             ) -> TRANSLATEABLE_TYPES:
    """Resolve variables and externals
    """
    if isinstance(x, (IdentifiedNode, Literal, list, tuple, term_list)):
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

class fact(Mapping[str, Union[TRANSLATEABLE_TYPES, abc_external, Variable]],
           abc.ABC):
    ID: str

    @abc.abstractmethod
    def check_for_pattern(self, c: "machine",
                          bindings: BINDING = {},
                          ) -> bool:
        """Checks if all fact is true for given machine.
        Variables are treated as blanks if not given by bindings,
        so accepts anything instead of a variable.
        """
        ...

    @property
    @abc.abstractmethod
    def used_variables(self) -> Iterable[Variable]:
        ...

    @abc.abstractmethod
    def assert_fact(self, c: "machine",
               bindings: BINDING = {},
               ) -> None:
        ...

    @abc.abstractmethod
    def as_dict(self, bindings: Optional[BINDING] = None,
                ) -> Mapping[str, Union[str, Variable, TRANSLATEABLE_TYPES]]:
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
    def load_external_resource(self, location: Union[str, IdentifiedNode],
                               ) -> rdflib.Graph:
        ...

    @abc.abstractmethod
    def check_statement(self, statement: Collection[fact],
                        bindings: BINDING_WITH_BLANKS = {},
                        ) -> bool:
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
    def get_facts(self, fact_filter: Optional[Mapping[str, str]]) -> Iterable[fact]:
        ...

    @abc.abstractmethod
    def run(self, steps: Union[int, None] = None) -> None:
        ...

    @abc.abstractmethod
    def import_data(self,
                    infograph: Graph,
                    location: IdentifiedNode,
                    profile: Optional[IdentifiedNode] = None,
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

    @abc.abstractmethod
    def add_init_action(self, action: Callable[[BINDING], None]) -> None:
        ...

    @abc.abstractmethod
    def get_binding_action(self, op: IdentifiedNode, args: Iterable[RESOLVABLE]) -> RESOLVABLE:
        """Resolve external atoms"""

    @abc.abstractmethod
    def get_replacement_node(self, op: IdentifiedNode, args: Iterable[RESOLVABLE]) -> TRANSLATEABLE_TYPES:
        """
        :TODO: Seems indifferent to get_binding_action but doesnt work if used as replacement. Have to rework the resolution of externals
        """

class action:
    action: Optional[Callable]
    machine: machine

    @abc.abstractmethod
    def finalize(self) -> None:
        ...


class pattern_organizer(MutableSequence[Union[fact, abc_external]]):
    @abc.abstractmethod
    def append(self, item: Union[fact, abc_external, "pattern_generator"],
               ) -> None:
        ...

class rule(abc.ABC):
    patterns: typ.Any
    action: Optional[Callable]
    machine: machine

    @abc.abstractmethod
    def set_action(self, action: Callable[[BINDING], None],
                   needed_variables: Iterable[Variable]) -> None:
        ...

    @property
    @abc.abstractmethod
    def orig_pattern(self) -> pattern_organizer:
        ...

    @abc.abstractmethod
    def finalize(self) -> None:
        """
        :raises: RuleNotComplete
        :raises: VariableNotBoundError
        """
        ...

    @abc.abstractmethod
    def generate_node_external(self, op: IdentifiedNode, args: ATOM_ARGS,
                               ) -> Union[str, IdentifiedNode, Literal]:
        """
        :raises NoPossibleExternal:
        """
        ...


class pattern_generator(abc.ABC):
    @abc.abstractmethod
    def _add_pattern(self, rule: rule) -> None:
        ...

class abc_pattern(abc.ABC):
    """shared implementation of patterns used within machine."""

class implication(rule, abc.ABC):
    patterns: typ.Any
    action: Optional[Callable]
    machine: machine

    @abc.abstractmethod
    def finalize(self) -> None:
        ...

    @abc.abstractmethod
    def generate_node_external(self, op: IdentifiedNode, args: ATOM_ARGS,
                               ) -> Union[str, IdentifiedNode, Literal]:
        """
        :raises NoPossibleExternal:
        """
        ...


class importProfile(abc.ABC):
    @abc.abstractmethod
    def create_rules(self, machine: machine, location: str) -> None:
        ...
