from typing import Any, Union, Optional, Tuple, List, Dict
from dataclasses import dataclass, field
from .bridge_rdflib import term_list, _term_list
from collections.abc import Iterable, Mapping, Callable, Container, Iterator
from rdflib import Variable, URIRef, Literal, IdentifiedNode
from .abc_machine import abc_external, TRANSLATEABLE_TYPES, RESOLVABLE, BINDING, _resolve, fact, abc_pattern, ASSIGNMENT
from .machine_facts import _node2string, external
from . import abc_machine
from .machine_patterns import _pattern, generate_action_prerequisites, RUNNING_STATE, MACHINESTATE
import logging
logger = logging.getLogger(__name__)
import traceback

_special_externals: List["_special_external"]
    

@dataclass(frozen=True)
class _id:
    """Alternative to uri"""
    name: str = field(hash=True)

@dataclass
class _special_external(Mapping[str, Union[Tuple, Callable, Mapping, Any]]):
    op: _id
    assuperaction: Optional[Callable] = field(default=None)
    asnormalaction: Optional[Callable] = field(default=None)
    asassign: Optional[Callable] = field(default=None)
    aspattern: Optional[Callable] = field(default=None)
    asbinding: Optional[Mapping[tuple[bool, ...], Callable]] = field(default=None)
    asgroundaction: Optional[Any] = field(default=None)

    def __iter__(self) -> Iterator[str]:
        for x in ["op", "asassign", "asbinding", "assuperaction", "asnormalaction", "asgroundaction",
                  "aspattern"]:
            if getattr(self, x, None) is not None:
                yield x

    def __len__(self) -> int:
        i = 0
        for x in ["op", "asassign", "asbinding", "assuperaction", "asnormalaction", "asgroundaction",
                  "aspattern"]:
            if getattr(self, x, None) is not None:
                i += 1
        return i

    def __getitem__(self, key: str) -> Any:
        try:
            return getattr(self, key)
        except AttributeError as err:
            raise KeyError(key) from err


@dataclass
class _create_list:
    items: Iterable[RESOLVABLE]
    def __init__(self, *items: RESOLVABLE) -> None:
        self.items = items

    def __call__(self, bindings: BINDING) -> term_list:
        items = [_resolve(item, bindings) for item in self.items]
        return _term_list(items)
create_list = _special_external(_id("create_list"),
                                asassign=_create_list,
                                )


@dataclass
class _bind_first:
    left: Variable
    right: RESOLVABLE

    def __call__(self, bindings: BINDING) -> Literal:
        right = _resolve(self.right, bindings)
        bindings[self.left] = right
        return Literal(True)

@dataclass
class _literal_equal:
    left: RESOLVABLE
    right: RESOLVABLE

    def __call__(self, bindings:BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        logger.critical((left, right))
        return Literal(left == right)
@dataclass
class _bind_second:
    left: RESOLVABLE
    right: Variable

    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        bindings[self.right] = left
        return Literal(True)
equality = _special_external(_id("rif equality"),
                             asassign=_literal_equal,
                             asbinding={(True, False): _bind_first,
                                        (False, True): _bind_second},
                             )

#@dataclass
#class _modify_fact_function:

@dataclass
class _assert_fact_function:
    machine: abc_machine.Machine
    facts: Iterable[Union[fact, Callable[[BINDING], fact]]]
    def __init__(self, machine:abc_machine.Machine,
                 *facts: Union[fact, Callable[[BINDING], fact]],
                 ) -> None:
        self.machine = machine
        self.facts = facts

    def __call__(self, bindings: BINDING) -> None:
        for f in self.facts:
            if isinstance(f, fact):
                self.machine.assert_fact(f, bindings)
            else:
                f_ = f(bindings)
                self.machine.assert_fact(f_, bindings)
assert_fact = _special_external(_id("assert_fact"),
                                 assuperaction=_assert_fact_function)

@dataclass
class _retract_fact_function:
    machine: abc_machine.Machine
    facts: Iterable[Union[fact, Callable[[BINDING], fact]]]
    def __init__(self, machine:abc_machine.Machine,
                 *facts: Union[fact, Callable[[BINDING], fact]],
                 ) -> None:
        self.machine = machine
        self.facts = facts

    def __call__(self, bindings: BINDING) -> None:
        for f in self.facts:
            if isinstance(f, fact):
                self.machine.retract_fact(f, bindings)
            else:
                f_ = f(bindings)
                self.machine.retract_fact(f_, bindings)
retract_fact = _special_external(_id("retract_fact"),
                                 assuperaction=_retract_fact_function)

@dataclass
class _retract_object_function:
    machine: abc_machine.Machine
    atom: Union[TRANSLATEABLE_TYPES, abc_external, Variable]

    def __call__(self, bindings: BINDING = {}) -> None:
        atom = _node2string(self.atom, self.machine, bindings)
        self.machine.retract_object(atom)
        #fact = {"type": frame.ID, frame.FRAME_OBJ: atom}
        #self.machine.retract_fact(fact, binding)

    def __repr__(self) -> str:
        return "Retract(%s)" % self.atom
retract_object = _special_external(_id("retract_object"),
                                   asnormalaction=_retract_object_function)

class _do_function:
    actions: Iterable[Callable[[BINDING], None]]
    def __init__(self, machine: abc_machine.Machine,
                 *actions: Callable[[BINDING], None],
                 ) -> None:
        self.actions = actions

    def __call__(self, bindings: BINDING = {}) -> None:
        for act in self.actions:
            act(bindings)

do = _special_external(_id("do"),
                       assuperaction=_do_function)

_import_id = _id("import")
def _register_import_as_init_action(machine: abc_machine.Machine,
                                    location: str,
                                    profile: Optional[str] = None,
                                    ) -> None:
    if location in machine._imported_locations:
        logger.debug("Already import %s" % location)
        return
    machine._imported_locations.append(location)
    logger.debug("import data %s" % profile)
    args = [Literal(location)] if profile is None else [Literal(location),
                                                        Literal(profile)] 
    machine.add_init_action(external(_import_id, args))

@dataclass
class _import_action:
    machine: abc_machine.Machine
    location: Literal
    profile: Optional[Literal] = field(default=None)

    def __call__(self, bindings: BINDING) -> None:
        try:
            usedImportProfile\
                    = self.machine.available_import_profiles[str(self.profile)]
        except KeyError:
            raise Exception("Import rejected because profile is not "
                            "registered", str(self.profile))
        usedImportProfile(self.machine, self.location)
import_data = _special_external(_import_id,
                                asnormalaction=_import_action,
                                asgroundaction=_register_import_as_init_action,
                                )


@dataclass
class _StopRunning_action:
    machine: abc_machine.Machine
    conditions: Iterable[Callable[[BINDING], Literal]]
    stopmessage: str
    def __call__(self, bindings: BINDING) -> None:
        """
        :TODO: remove type:ignore
        """
        try:
            for cond in self.conditions:
                if not cond(bindings):
                    return
            logger.critical("Stopping ...")
            self.machine._current_context.retract_fact( #type: ignore[attr-defined]
                    {MACHINESTATE: RUNNING_STATE})
            raise abc_machine.StopRunning(self.stopmessage)
        except Exception:
            logger.critical(traceback.format_exc())
            raise

def _register_stop_condition(machine: abc_machine.extensible_Machine,
                             *required_facts: fact,
                             ) -> None:

    for patterns, conditions, bound_variables\
            in generate_action_prerequisites(machine, required_facts):
        logger.critical(patterns)
        #if len(patterns) == 1:#always contains machinestate: running
        #    raise NotImplementedError("Doesnt produce any patterns but "
        #                              "currently i need some.")
        msg = "stop conditions reached: %s"
        machine._make_rule(patterns,
                           [_StopRunning_action(machine, conditions, msg)],
                           priority=3)

stop_condition = _special_external(_id("stop_condition"),
                                   asgroundaction=_register_stop_condition
                                   )


def _pattern_generator_and(
        machine: abc_machine.Machine,
        args: Iterable[Union[fact, abc_external]],
        bound_variables: Iterable[Variable],
        ) -> Iterable[Tuple[Iterable[abc_pattern],
                            Iterable[Callable[[BINDING], Literal]],
                            Iterable[Variable]]]:
    patterns: List[abc_pattern]
    conditions: List[Callable[[BINDING], Literal]]
    patterns, conditions = [], []
    bound_vars = set(bound_variables)
    for formula in args:
        if isinstance(formula, fact):
            id_ = machine._registered_facttypes[type(formula)]
            asdict: Dict[str, str] = {}
            for key, val in formula.items():
                if isinstance(val, str):
                    asdict[key] = val
                else:
                    raise NotImplementedError()
            patterns.append(_pattern.from_fact(id_, asdict))
            bound_vars.update(formula.used_variables)
        elif isinstance(formula, abc_external):
            raise NotImplementedError("externals not yet supported", formula)
        else:
            raise TypeError("only supports fact and abc_external", formula)
    yield patterns, conditions, bound_vars

#class _and_assignment:
#    args: Iterable[Union[fact, abc_external]]
#    def __init__(self, *args: Union[fact, abc_external]) -> None:
#        self.args = args
#    def __call__(self, bindings: BINDING) -> Literal:
#        args = (_resolve(x, bindings) for x in self.args)
#        return Literal(all(args))
condition_and = _special_external(_id("rif_and"),
                                  aspattern=_pattern_generator_and,
                                  #asassign=_and_assignment,
                                  )

def _pattern_generator_or(
        machine: abc_machine.Machine,
        args: Iterable[Union[fact, abc_external]],
        bound_variables: Container[Variable],
        ) -> Iterable[Tuple[Iterable[abc_pattern],
                            Iterable[ASSIGNMENT],
                            Iterable[Variable]]]:
    #patterns, conditions, bound_variables = [], [], set()
    for formula in args:
        #for patterns, conditions, bound_variables in generate_action_prerequisites(machine, [args]):
        q = machine.create_internal_and_python_conditions(formula,
                                                          bound_variables)
        for patterns, conditions, new_bound_variables in q:
            yield patterns, conditions, new_bound_variables

#class _or_assignment:
#    args: Iterable
#    def __init__(self, *args):
#        self.args = args
#    def __call__(self, bindings: BINDING) -> Literal:
#        args = (_resolve(x, bindings) for x in self.args)
#        return Literal(any(args))
condition_or = _special_external(_id("rif_or"),
                                 aspattern=_pattern_generator_or,
                                 #asassign=_or_assignment,
                                 )

_special_externals = [
        equality,
        create_list,
        retract_object,
        do,
        assert_fact,
        retract_fact,
        import_data,
        stop_condition,
        condition_and,
        condition_or,
        ]
