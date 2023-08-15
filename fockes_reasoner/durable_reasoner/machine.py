import durable.lang as rls
import durable.engine
import uuid
import abc
import logging
import traceback
from typing import Union, Mapping, Iterable, Callable, Any, MutableMapping
from hashlib import sha1
import rdflib
from rdflib import URIRef, Variable, Literal, BNode
from . import abc_machine
from .abc_machine import TRANSLATEABLE_TYPES, FACTTYPE, BINDING, VARIABLE_LOCATOR
from .machine_facts import rdflib2string, string2rdflib

from ..shared import RDF
from . import machine_facts
#from .machine_facts import frame, member, subclass, fact

MACHINESTATE = "machinestate"
RUNNING_STATE = "running"
INIT_STATE = "init"

LIST = "list"
"""All facts that represent :term:`list` are labeled with this."""
LIST_ID = "id"
"""Facts that represent :term:`list` may have a label of which represent them
in RDF.
"""
LIST_MEMBERS = "member"
""":term:`list` enlist all their members under this label."""

class FailedInternalAction(Exception):
    ...

class _context_helper(abc.ABC):
    """helper class to decide how to assert and retract facts"""
    machine: "machine"

    @abc.abstractmethod
    def assert_fact(self, fact: Mapping[str, str]) -> None:
        ...

    @abc.abstractmethod
    def retract_fact(self, fact: Mapping[str, str]) -> None:
        """Retract all facts, that are matching with given fact.
        Eg {1:"a"} matches {1:"a", 2:"b"}
        """
        ...

    @abc.abstractmethod
    def get_facts(self, fact_filter: Union[Mapping[str, str], None] = None,
                  ) -> Iterable[Mapping[str, str]]:
        ...


class _no_closure(_context_helper):
    def __init__(self, machine:"machine"):
        self.machine = machine

    def assert_fact(self, fact: Mapping[str, str]) -> None:
        rls.assert_fact(self.machine._rulename, fact)

    def get_facts(self, fact_filter: Union[Mapping[str, str], None] = None,
                  ) -> Iterable[Mapping[str, str]]:
        if fact_filter is None:
            return rls.get_facts(self.machine._rulename) #type: ignore[no-any-return]
        else:
            return (f #type: ignore[no-any-return]
                    for f in rls.get_facts(self.machine._rulename)
                    if all(f[key] == val for key, val in fact_filter.items()))

    def retract_fact(self, fact: Mapping[str, str]) -> None:
        for f in self.get_facts():
            if all(f.get(x) == y for x,y in fact.items()):
                rls.retract(self.machine._rulename, f)


class _closure_helper(_context_helper):
    previous_context: _context_helper 
    c: durable.engine.Closure
    def __init__(self, machine: "machine", c: durable.engine.Closure):
        self.machine = machine
        self.c = c

    def assert_fact(self, fact: Mapping[str, str]) -> None:
        self.c.assert_fact(fact)

    def get_facts(self, fact_filter: Union[Mapping[str, str], None] = None,
                  ) -> Iterable[Mapping[str, str]]:
        if fact_filter is None:
            return self.c.get_facts() #type: ignore[no-any-return]
        else:
            return (f for f in self.c.get_facts() #type: ignore[no-any-return]
                    if all(f[key] == val for key, val in fact_filter.items()))

    def retract_fact(self, fact: Mapping[str, str]) -> None:
        for f in self.get_facts():
            if all(f.get(x) == y for x,y in fact.items()):
                self.c.retract_fact(f)

    def __enter__(self) -> None:
        self.previous_context = self.machine._current_context
        self.machine._current_context = self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.machine._current_context = self.previous_context


class machine(abc_machine.machine):
    _ruleset: rls.ruleset
    logger: logging.Logger
    errors: list
    _current_context: _context_helper
    _initialized: bool

    def __init__(self, loggername: str = __name__) -> None:
        rulesetname = str(uuid.uuid4())
        self._ruleset = rls.ruleset(rulesetname)
        self.logger = logging.getLogger(loggername)
        self.__set_basic_rules()
        self.errors = []
        self._current_context = _no_closure(self)
        self._initialized = False

    def check_statement(self, statement: machine_facts.fact) -> bool:
        """Checks if given proposition is true.
        :TODO: currently facts are only simple facts like a frame. But check
            should support complex statement like 'Xor'
        """
        raise NotImplementedError()

    def assert_fact(self, fact: Mapping[str, str]) -> None:
        self._current_context.assert_fact(fact)
    
    def retract_fact(self, fact: Mapping[str, str]) -> None:
        self._current_context.retract_fact(fact)

    def get_facts(self) -> Iterable[abc_machine.fact]:
        from .machine_facts import frame, member, subclass, fact
        q: Mapping[str, type[fact]] = {frame.ID: frame,
                                       member.ID: member,
                                       subclass.ID: subclass}
        for f in self._current_context.get_facts():
            fact_id = f[FACTTYPE]
            yield q[fact_id].from_fact(f)

    def make_rule(self, patterns: Iterable[rls.value],
                  action: Callable,
                  variable_locator: VARIABLE_LOCATOR,
                  error_message: str = "") -> None:
        with self._ruleset:
            @rls.when_all(*patterns)
            def myfoo(c: durable.engine.Closure) -> None:
                bindings = {}
                try:
                    for var, loc in variable_locator.items():
                        bindings[var] = string2rdflib(loc(c))
                except Exception as err:
                    self.logger.info("failed loading bindings: %s"
                                     % traceback.format_exc())
                    raise FailedInternalAction(error_message) from err
                try:
                    with _closure_helper(self, c):
                        action(bindings)
                except FailedInternalAction:
                    raise
                except Exception as err:
                    self.logger.info("Failed at action %r with bindings %s. "
                                     "Produced traceback:\n%s"
                                     % (action, bindings,  traceback.format_exc()))
                    raise FailedInternalAction(error_message) from err

    def make_start_action(self, actions: Iterable[Callable]) -> None:
        raise Exception()
        with self._ruleset:
            @rls.when_all(getattr(rls.m, MACHINESTATE) == INIT_STATE)
            def init_function(c: durable.engine.Closure) -> None:
                with _closure_helper(self, c):
                    for act in actions:
                        #act()
                        pass

    def __set_basic_rules(self) -> None:
        with self._ruleset:
            @rls.when_all(rls.pri(-3), +rls.s.exception)
            def second(c: durable.engine.Closure) -> None:
                self.logger.critical(c.s.exception)
                self.errors.append(str(c.s.exception))
                c.s.exception = None
                try:
                    c.retract_state({MACHINESTATE: RUNNING_STATE})
                except Exception:
                    pass

            @rls.when_all(+getattr(rls.m, FACTTYPE))
            def accept_all_frametypes(c: durable.engine.Closure) -> None:
                pass

            @rls.when_all(+rls.m.machinestate)
            def accept_every_machinestate(c: durable.engine.Closure) -> None:
                pass

    def run(self, steps: Union[int, None] = None) -> None:
        if not self._initialized:
            rls.assert_fact(self._rulename, {MACHINESTATE: INIT_STATE})
            rls.retract_fact(self._rulename, {MACHINESTATE: INIT_STATE})
            self._initialized = True
        if steps is None:
            rls.assert_fact(self._rulename, {MACHINESTATE: RUNNING_STATE})
            rls.retract_fact(self._rulename, {MACHINESTATE: RUNNING_STATE})
        else:
            raise NotImplementedError()
            for t in steps:
                rls.post(self._rulename, {MACHINESTATE: RUNNING_STATE})
        if self.errors:
            raise Exception("Rules produced an error.", self.errors)

    @property
    def _rulename(self) -> str:
        return self._ruleset.name #type: ignore[no-any-return]


class RDFmachine(machine):
    """Implements translation of as in RDF specified syntax for the machine
    """
    def __init__(self, loggername: str = __name__) -> None:
        super().__init__(loggername)
        self.__transform_list_rules()

    def __transform_list_rules(self) -> None:
        from .machine_facts import rdflib2string, frame
        LIST_ID = "id"
        LIST = "list"
        LIST_MEMBERS = "member"
        FRAME_OBJ = frame.FRAME_OBJ
        FRAME_SLOTVALUE = frame.FRAME_SLOTVALUE
        FRAME_SLOTKEY = frame.FRAME_SLOTKEY

        NIL = rdflib2string(RDF.nil)
        REST = rdflib2string(RDF.rest)
        FIRST = rdflib2string(RDF.first)
        with self._ruleset:
            @rls.when_all(
                    rls.pri(-2),
                    rls.c.base << (getattr(rls.m, FRAME_SLOTVALUE) == NIL)
                    & (getattr(rls.m, FACTTYPE) == frame.ID)
                    & (getattr(rls.m, FRAME_SLOTKEY) == REST),
                    rls.c.lastelem << (getattr(rls.m, FRAME_OBJ)
                                       == getattr(rls.c.base, FRAME_OBJ))
                    & (getattr(rls.m, FRAME_SLOTKEY) == FIRST)
                    )
            def start_list(c: durable.engine.Closure) -> None:
                l = c.lastelem[FRAME_OBJ]
                elem = c.lastelem[FRAME_SLOTVALUE]
                self.logger.debug("found list %s" % l)
                c.assert_fact({FACTTYPE: LIST,
                               LIST_ID: l,
                               LIST_MEMBERS: [elem]})
                c.retract_fact(c.base)
                c.retract_fact(c.lastelem)

            @rls.when_all(
                    rls.pri(-2),
                    rls.c.list << (getattr(rls.m, FACTTYPE) == LIST),
                    rls.c.base << (getattr(rls.m, FRAME_SLOTKEY) == REST)
                    #& (getattr(rls.m, FRAME_SLOTVALUE)
                    #                == getattr(rls.c.list, LIST_ID))
                    & (getattr(rls.m, FACTTYPE) == frame.ID),
                    rls.c.element <<(getattr(rls.m, FRAME_OBJ)
                                    == getattr(rls.c.base, FRAME_OBJ))
                    & (getattr(rls.m, FRAME_SLOTKEY) == FIRST)
                    & (getattr(rls.m, FACTTYPE) == frame.ID),
                    )
            def combine_list(c: durable.engine.Closure) -> None:
                """
                :TODO: remove workaround c.base.slotval != c.list.id
                """
                if c.base[FRAME_SLOTVALUE] != c.list[LIST_ID]:
                    return
                newid = c.base[FRAME_OBJ]
                elem = c.element[FRAME_SLOTVALUE]
                self.logger.debug(f"combining list with {elem}\n{newid}\n{c.list[LIST_ID]}")
                c.retract_fact(c.list)
                c.retract_fact(c.base)
                c.retract_fact(c.element)
                c.assert_fact({FACTTYPE: LIST,
                               LIST_ID: newid,
                               LIST_MEMBERS: list(c.list[LIST_MEMBERS]) + [elem]})

            @rls.when_all(
                    rls.pri(-1),
                    getattr(rls.m, FRAME_SLOTKEY) == REST,
                    rls.c.machinestate << (getattr(rls.m, MACHINESTATE) == RUNNING_STATE),
                    )
            def is_list_combined(c: durable.engine.Closure) -> None:
                c.retract_fact(c.machinestate)
                raise Exception("Couldnt transform all lists")

class durable_action(abc_machine.action):
    action: Callable
    """action that is executed in initstate (machinestate==init)"""
    machine: machine
    """Rulemachine for this action"""
    finalized: bool
    """Shows if action is already implemented in machine"""
    def __init__(self, machine: machine, action: Union[None, Callable] = None,
                 finalize: bool = False):
        self.machine = machine
        self.action = action
        self.finalized = False
        if finalize:
            self.finalize()

    def finalize(self):
        if self.finalized:
            raise Exception()
        if self.action is None:
            raise Exception()
        self.finalized = True
        patterns = [getattr(rls.m, MACHINESTATE) == INIT_STATE]
        self.machine.make_rule(patterns, self.action, {})

class durable_rule(abc_machine.rule):
    patterns: list[rls.value]
    action: Callable
    bindings: VARIABLE_LOCATOR
    machine: machine
    def __init__(self, machine: machine):
        self.machine = machine
        self.patterns = [getattr(rls.m, MACHINESTATE) == RUNNING_STATE]
        self.action = None
        self.finalized = False
        self.bindings = {}

    def finalize(self) -> None:
        if self.finalized:
            raise Exception()
        if self.action is None:
            raise Exception()
        self.finalized = True
        self.machine.make_rule(self.patterns, self.action, self.bindings)

    def add_pattern(self,
                    pattern: Mapping[str, Union[str, TRANSLATEABLE_TYPES]],
                    factname: Union[str, None] = None,
                    ):
        from .machine_facts import rdflib2string
        pattern = dict(pattern)
        if factname is None:
            _as_string = repr(sorted(pattern.items()))
            factname = "f%s" % sha1(_as_string.encode("utf8")).hexdigest()
        #         c: typ.Union[durable.engine.Closure, str],
        #         bindings: BINDING,
        #         external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], external],
        next_constraint: rls.value
        constraint: Union[rls.value, None] = None
        for key, value in pattern.items():
            next_constraint = None
            if type(value) == str:
                next_constraint = getattr(rls.m, key) == value
            elif isinstance(value, rdflib.Variable):
                if value in self.bindings:
                    loc = self.bindings[value]
                    newpattern = getattr(rls.m, key) == loc(rls.c)
                    #log.append(f"rls.m.{fact_label} == {loc}")
                else:
                    loc = _value_locator(factname, key)
                    self.bindings[value] = loc
                    next_constraint = None
                    #logger.debug("bind: %r-> %r" % (value, loc))
            elif isinstance(value, (URIRef, BNode, Literal)):
                next_constraint = getattr(rls.m, key) == rdflib2string(value)
            elif isinstance(value, external):
                newnode = value.serialize(c, bindings, external_resolution)
                next_constraint = getattr(rls.m, key) == newnode
            else:
                raise NotImplementedError(value, type(value))
            if next_constraint is not None:
                if constraint is None:
                    constraint = next_constraint
                else:
                    constraint = constraint & next_constraint
        if constraint is None:
            raise Exception("Cant handle %s" % pattern)
        self.patterns.append(getattr(rls.c, factname) << constraint)

class _value_locator:
    factname: str
    """Name of the fact, where the variable is defined"""
    in_fact_label: str
    """Position in fact, where the variable is defined"""
    def __init__(self, factname: str, in_fact_label: str):
        self.factname = factname
        self.in_fact_label = in_fact_label

    def __call__(self,
                 c: Union[durable.engine.Closure, rls.closure],
                 ) -> Union[TRANSLATEABLE_TYPES, rls.value]:
        fact = getattr(c, self.factname)
        return getattr(fact, self.in_fact_label)

    def __repr__(self) -> str:
        return f"%s(c.{self.factname}.{self.in_fact_label})"\
                % type(self).__name__
