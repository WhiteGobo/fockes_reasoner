import abc
import logging
import typing as typ
from typing import MutableMapping, Mapping, Union, Iterable, Optional, overload, Any, Tuple
from collections.abc import MutableSequence, Callable, Collection, Container
import rdflib
from rdflib import IdentifiedNode, Graph, Literal, Variable

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

class StopRunning(Exception):
    ...

class abc_external(abc.ABC):
    op: Any
    args: ATOM_ARGS

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
    """InternalError.
    Raise this, if wanted functionality is not implemented for this external
    """
    ...

ASSIGNMENT = Callable[[BINDING], Literal]


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

    @property
    @abc.abstractmethod
    def used_variables(self) -> Iterable[Variable]:
        ...

    @abc.abstractmethod
    def as_dict(self, bindings: Optional[BINDING] = None,
                ) -> Mapping[str, Union[str, Variable, TRANSLATEABLE_TYPES]]:
        ...


    @classmethod
    @abc.abstractmethod
    def from_fact(cls, fact: Mapping[str, str]) -> "fact":
        ...

    @abc.abstractmethod
    def create_fact_generator(self, machine: "machine",
                              ) -> Callable[[BINDING], "fact"]:
        ...

    #@property
    #def has_variable_attributes(self) -> bool:
    #    return True


class abc_action(abc.ABC):
    machine: "machine"

class machine(abc.ABC):
    logger: logging.Logger
    errors: list

    @abc.abstractmethod
    def load_external_resource(self, location: Union[str, IdentifiedNode],
                               ) -> rdflib.Graph:
        ...

    @abc.abstractmethod
    def check_statement(self, statement: Union[Collection[Union[fact, abc_external]], fact, abc_external],
                        bindings: BINDING_WITH_BLANKS = {},
                        ) -> bool:
        """Checks if given proposition is true.
        :TODO: currently facts are only simple facts like a frame. But check
            should support complex statement like 'Xor'
        """

    @abc.abstractmethod
    def _create_pattern_from_external(
            self,
            op: IdentifiedNode,
            args: ATOM_ARGS,
            bound_variables: Container[Variable],
            ) -> Iterable[Tuple[Iterable[fact],
                                Iterable[Callable[[BINDING], Literal]],
                                Iterable[Variable]]]:
        ...

    @abc.abstractmethod
    def _create_binding_from_external(
            self,
            op: IdentifiedNode,
            args: ATOM_ARGS,
            bound_variables: Container[Variable] = [],
            ) -> Tuple[Iterable[fact],
                       Iterable[Callable[[BINDING], Literal]],
                       Iterable[Variable]]:
        ...

    @abc.abstractmethod
    def _create_assignment_from_external(
            self,
            op: IdentifiedNode,
            args: ATOM_ARGS,
            ) -> ASSIGNMENT:
        ...

    def create_internal_and_python_conditions(
            self,
            info: Union[fact, abc_external],
            bound_variables: Container[Variable] = [],
            ) -> Iterable[Union[Iterable[fact],
                                Iterable[Callable[[BINDING], Literal]],
                                Container[Variable]]]:
        _was_found = False
        if isinstance(info, fact):
            assert all(not isinstance(x, abc_external) for x in info.values())
            yield (info, [], info.used_variables)
            return
        try:
            info.op, info.args
            assert isinstance(info, abc_external)
        except AttributeError:
            raise TypeError("Can only translate registered facts and"
                            " externals", info)
        try:
            q = self._create_pattern_from_external(info.op, info.args,
                                                   bound_variables)
            for x in q:
                yield x
            return
        except NoPossibleExternal as err:
            #_was_found = err.was_implemented
            pass
        try:
            yield self._create_binding_from_external(info.op, info.args,
                                                     bound_variables)
            return
        except NoPossibleExternal:
            #_was_found = err.was_implemented
            pass
        not_bound_vars = [x for x in info.args
                          if isinstance(x, Variable)
                          and x not in bound_variables]
        if not_bound_vars:
            if not _was_found:
                try:
                    self._create_assignment_from_external(info.op, info.args)
                except NoPossibleExternal as err:
                    raise NoPossibleExternal("The external '%s' isnt "
                                             "implemented." % info.op) from err
            raise VariableNotBoundError("The following external cant be used"
                                        "here", info)
        cond = self._create_assignment_from_external(info.op, info.args)
        yield [], [cond], []


    @abc.abstractmethod
    def assert_fact(self, new_fact: fact, bindings: BINDING,
                    ) -> None:
        ...

    @abc.abstractmethod
    def retract_fact(self, new_fact: fact, bindings: BINDING,
                     ) -> None:
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
    def _create_assignment_from_external(
            self,
            op: IdentifiedNode,
            args: ATOM_ARGS,
            ) -> ASSIGNMENT:
        ...

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
