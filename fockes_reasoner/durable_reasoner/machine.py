import durable.lang as rls
import durable.engine
import uuid
import abc
import logging
from typing import Union, Mapping, Iterable, Callable, Any
from . import abc_machine

from ..shared import RDF
from . import machine_facts
#from .machine_facts import frame, member, subclass, fact

FACTTYPE = "type"
"""Labels in where the type of fact is saved"""
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
    def get_facts(self) -> Iterable[Mapping[str, str]]:
        ...


class _no_closure(_context_helper):
    def __init__(self, machine:"machine"):
        self.machine = machine

    def assert_fact(self, fact: Mapping[str, str]) -> None:
        rls.assert_fact(self.machine._rulename, fact)

    def get_facts(self) -> Iterable[Mapping[str, str]]:
        return rls.get_facts(self.machine._rulename) #type: ignore[no-any-return]

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

    def get_facts(self) -> Iterable[Mapping[str, str]]:
        return self.c.get_facts() #type: ignore[no-any-return]

    def retract_fact(self, fact: Mapping[str, str]) -> None:
        for f in self.get_facts():
            if all(f.get(x) == y for x,y in fact.items()):
                self.c.retract_fact(f)

    def __enter__(self) -> None:
        self.previous_context = machine._current_context
        machine._current_context = self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        machine._current_context = self.previous_context


class machine(abc_machine.machine):
    _ruleset: rls.ruleset
    logger: logging.Logger
    errors: list
    _current_context: _context_helper

    def __init__(self, loggername: str = __name__) -> None:
        rulesetname = str(uuid.uuid4())
        self._ruleset = rls.ruleset(rulesetname)
        self.logger = logging.getLogger(loggername)
        self.__set_basic_rules()
        self.errors = []
        self._current_context = _no_closure(self)

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

    def make_rule(self) -> None:
        patterns: Iterable[rls.value] = []
        actions: Iterable[Callable] = []
        with self._ruleset:
            @rls.when_all(patterns)
            def myfoo(c: durable.engine.Closure) -> None:
                with _closure_helper(self, c):
                    for act in actions:
                        #act()
                        pass

    def make_start_action(self) -> None:
        actions: Iterable[Callable] = []
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
