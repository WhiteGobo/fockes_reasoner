from typing import Any, Union, Optional, Tuple, List
from dataclasses import dataclass, field
from .bridge_rdflib import term_list, _term_list
from collections.abc import Iterable, Mapping, Callable, Container
from rdflib import Variable, URIRef, Literal, IdentifiedNode
from .abc_machine import abc_external, TRANSLATEABLE_TYPES, RESOLVABLE, BINDING, _resolve, fact, abc_pattern
from .machine_facts import _node2string, external
from . import abc_machine
from .default_externals import literal_equal
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
class _special_external(Mapping):
    op: _id
    asaction: Optional[Tuple[Callable, bool]]\
            = field(default=None)
    asassign: Optional[Callable] = field(default=None)
    aspattern: Optional[Callable] = field(default=None)
    asbinding: Optional[Mapping[tuple[bool], Callable]] = field(default=None)
    asgroundaction: Optional[Any] = field(default=None)

    def __iter__(self):
        for x in ["op", "asassign", "asbinding", "asaction", "asgroundaction",
                  "aspattern"]:
            if getattr(self, x, None) is not None:
                yield x

    def __len__(self) -> int:
        i = 0
        for x in ["op", "asassign", "asbinding", "asaction", "asgroundaction",
                  "aspattern"]:
            if getattr(self, x, None) is not None:
                i += 1
        return i

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError as err:
            raise KeyError(key) from err


@dataclass
class _create_list:
    items: Iterable[RESOLVABLE]
    def __init__(self, *items: Iterable[RESOLVABLE]):
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
class _bind_second:
    left: RESOLVABLE
    right: Variable

    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        bindings[self.right] = left
        return Literal(True)
equality = _special_external(_id("rif equality"),
                             asassign=literal_equal,
                             asbinding={(True, False): _bind_first,
                                        (False, True): _bind_second},
                             )

@dataclass
class _assert_fact_function:
    machine: abc_machine.machine
    facts: Iterable[Union[fact, Callable[[BINDING], fact]]]
    def __init__(self, machine:abc_machine.machine,
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
                                 asaction=(_assert_fact_function, False))

@dataclass
class _retract_object_function:
    machine: abc_machine.machine
    atom: Union[TRANSLATEABLE_TYPES, abc_external, Variable]

    def __call__(self, bindings: BINDING = {}) -> None:
        atom = _node2string(self.atom, self.machine, bindings)
        self.machine.retract_object(atom)
        #fact = {"type": frame.ID, frame.FRAME_OBJ: atom}
        #self.machine.retract_fact(fact, binding)

    def __repr__(self) -> str:
        return "Retract(%s)" % self.atom
retract_object = _special_external(_id("retract_object"),
                                   asaction=(_retract_object_function, False))

class _do_function:
    actions: Iterable[Callable[[BINDING], None]]
    def __init__(self, machine: abc_machine.machine,
                 *actions: Iterable[Callable[[BINDING], None]],
                 ) -> None:
        self.actions = actions

    def __call__(self, bindings: BINDING = {}) -> None:
        for act in self.actions:
            act(bindings)

do = _special_external(_id("do"),
                       asaction=(_do_function, True))

_import_id = _id("import")
def _register_import_as_init_action(machine: abc_machine.machine,
                                    location: str,
                                    profile: Optional[str] = None,
                                    ) -> None:
    if location in machine._imported_locations:
        logger.debug("Already import %s" % location)
        return
    logger.debug("import data %s" % profile)
    args = [location] if profile is None else [location, profile] 
    machine.add_init_action(external(_import_id, args))

@dataclass
class _import_action:
    machine: abc_machine.machine
    location: Literal
    profile: Literal = field(default=None)

    def __call__(self, bindings: BINDING) -> None:
        try:
            usedImportProfile\
                    = self.machine.available_import_profiles[str(self.profile)]
        except KeyError:
            raise Exception("Import rejected because profile is not "
                            "registered", str(self.profile))
        usedImportProfile(self.machine, self.location)
import_data = _special_external(_import_id,
                                asaction=(_import_action, False),
                                asgroundaction=_register_import_as_init_action,
                                )


@dataclass
class _StopRunning_action:
    machine: abc_machine.machine
    conditions: Iterable[Callable[[BINDING], Literal]]
    stopmessage: str
    def __call__(self, bindings: BINDING) -> None:
        try:
            for cond in self.conditions:
                if not cond(bindings):
                    return
            logger.critical("Stopping ...")
            self.machine._current_context.retract_fact(
                    {MACHINESTATE: RUNNING_STATE})
            raise abc_machine.StopRunning(self.stopmessage)
        except Exception:
            logger.critical(traceback.format_exc())
            raise

def _register_stop_condition(machine: abc_machine.machine,
                             *required_facts: Iterable[fact],
                             ) -> None:

    myfacts = []
    patterns = []
    for patterns, conditions, bound_variables\
            in generate_action_prerequisites(machine, list(required_facts)):
        logger.critical(patterns)
        #if len(patterns) == 1:#always contains machinestate: running
        #    raise NotImplementedError("Doesnt produce any patterns but "
        #                              "currently i need some.")
        msg = "stop conditions reached: %s" % (str(myfacts))
        machine._make_rule(patterns,
                           [_StopRunning_action(machine, conditions, msg)],
                           priority=3)

stop_condition = _special_external(_id("stop_condition"),
                                   asgroundaction=_register_stop_condition
                                   )


def _pattern_generator_and(
        machine,
        args: Iterable[Union[fact, abc_external]],
        bound_variables: Container[Variable],
        ) -> Iterable[Tuple[Iterable[abc_pattern],
                            Tuple["pred_iri_string"],
                            Iterable[Variable]]]:
    patterns, conditions, bound_variables = [], [], set()
    for formula in args:
        if isinstance(formula, fact):
            id_ = machine._registered_facttypes[type(formula)]
            patterns.append(_pattern.from_fact(id_, formula))
            bound_variables.update(formula.used_variables)
        elif isinstance(formula, abc_external):
            raise NotImplementedError("externals not yet supported", formula)
        else:
            raise TypeError("only supports fact and abc_external", formula)
    yield patterns, conditions, bound_variables

class _and_assignment:
    args: Iterable
    def __init__(self, *args):
        self.args = args
    def __call__(self, bindings: BINDING) -> Literal:
        args = (_resolve(x, bindings) for x in self.args)
        return Literal(all(args))
condition_and = _special_external(_id("rif_and"),
                                  aspattern=_pattern_generator_and,
                                  asassign=_and_assignment,
                                  )

def _pattern_generator_or(
        machine,
        args: Iterable[Union[fact, abc_external]],
        bound_variables: Container[Variable],
        ) -> Iterable[Tuple[Iterable[abc_pattern],
                            Tuple["pred_iri_string"],
                            Iterable[Variable]]]:
    #patterns, conditions, bound_variables = [], [], set()
    for formula in args:
        if isinstance(formula, fact):
            id_ = machine._registered_facttypes[type(formula)]
            patterns = [_pattern.from_fact(id_, formula)]
            bound_variables = formula.used_variables
            conditions = []
        elif isinstance(formula, abc_external):
            raise NotImplementedError("externals not yet supported", formula)
        else:
            raise TypeError("only supports fact and abc_external", formula)
        yield patterns, conditions, bound_variables

class _or_assignment:
    args: Iterable
    def __init__(self, *args):
        self.args = args
    def __call__(self, bindings: BINDING) -> Literal:
        args = (_resolve(x, bindings) for x in self.args)
        return Literal(any(args))
condition_or = _special_external(_id("rif_or"),
                                 aspattern=_pattern_generator_or,
                                 asassign=_and_assignment,
                                 )

_special_externals = [
        equality,
        create_list,
        retract_object,
        do,
        assert_fact,
        import_data,
        stop_condition,
        condition_and,
        condition_or,
        ]
