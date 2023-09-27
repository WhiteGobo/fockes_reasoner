import durable.lang as rls
import durable.engine
import uuid
import abc
import logging
logger = logging.getLogger(__name__)
import traceback
from typing import Union, Mapping, Iterable, Callable, Any, MutableMapping, Optional, Container, Dict, Set, get_args, Tuple, List, Iterator
from collections.abc import Collection
from dataclasses import dataclass
from hashlib import sha1
import itertools as it
import rdflib
from rdflib import URIRef, Variable, Literal, BNode, Graph, IdentifiedNode, XSD
from . import abc_machine
from .abc_machine import TRANSLATEABLE_TYPES, FACTTYPE, BINDING, BINDING_WITH_BLANKS, VARIABLE_LOCATOR, NoPossibleExternal, importProfile, RESOLVABLE, ATOM_ARGS, abc_external, RESOLVER, RuleNotComplete, pattern_generator, VariableNotBoundError, abc_pattern, _resolve, _assignment
from ..class_profileOWLDirect import profileOWLDirect

from .bridge_rdflib import rdflib2string, string2rdflib, term_list

from ..shared import RDF, pred, func, entailment, RIF, OWL
from . import machine_facts
from .machine_facts import frame, member, subclass, atom, fact, external, rdflib2string, _node2string
from . import special_externals
#from .machine_facts import frame, member, subclass, fact

from . import default_externals as def_ext
from .owl_facts import rdfs_subclass

BINDING_DESCRIPTION = Mapping[tuple[bool], Callable]
"""Maps a tuple representing the position of unbound variables to a generator
"""

PATTERNGENERATOR\
        = Callable[[Iterable[RESOLVABLE], Container[Variable]],
                   Iterable[Tuple[Iterable[abc_pattern],
                                  Iterable[Callable[[BINDING], Literal]],
                                  Iterable[Variable]]]]

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

class ReachedStepLimit(Exception):
    ...

class _pattern(abc_pattern):
    pattern: Mapping[str, Union[Variable, str, TRANSLATEABLE_TYPES]]
    factname: str
    def __init__(
            self,
            pattern: Mapping[str, Union[Variable, str, TRANSLATEABLE_TYPES]],
            factname: Optional[str] = None,
            ) -> None:
        self.pattern = pattern
        if factname is None:
            _as_string = repr(sorted(pattern.items()))
            self.factname = "f%s" % sha1(_as_string.encode("utf8")).hexdigest()
        else:
            self.factname = factname

    def __repr__(self) -> str:
        return "f(%s): %s" % (self.factname, self.pattern)

    @classmethod
    def from_fact(cls, factid: str, myfact, name: str) -> "_pattern":
        d = {FACTTYPE: factid, **myfact}
        return cls(d, name)

    def generate_rls(self,
                     bindings: MutableMapping[Variable, VARIABLE_LOCATOR],
                     ) -> rls.value:
        next_constraint: rls.value
        constraint: Union[rls.value, None] = None
        for key, value in self.pattern.items():
            next_constraint = None
            if type(value) == str:
                next_constraint = getattr(rls.m, key) == value
            elif isinstance(value, rdflib.Variable):
                if value in bindings:
                    loc = bindings[value]
                    newpattern = getattr(rls.m, key) == loc(rls.c)
                    #log.append(f"rls.m.{fact_label} == {loc}")
                else:
                    loc = _value_locator(self.factname, key)
                    bindings[value] = loc
                    next_constraint = None
                    #logger.debug("bind: %r-> %r" % (value, loc))
            elif isinstance(value, (URIRef, BNode, Literal)):
                next_constraint = getattr(rls.m, key) == rdflib2string(value)
            elif isinstance(value, external):
                raise NotImplementedError()
                #newnode = value.serialize(c, bindings, external_resolution)
                #next_constraint = getattr(rls.m, key) == newnode
            else:
                raise NotImplementedError(value, type(value))
            if next_constraint is not None:
                if constraint is None:
                    constraint = next_constraint
                else:
                    constraint = constraint & next_constraint
        if constraint is None:
            raise Exception("Cant handle %s" % self.pattern)
        pattern_part = getattr(rls.c, self.factname) << constraint
        return pattern_part


class _context_helper(abc.ABC):
    """helper class to decide how to assert and retract facts"""
    machine: "_base_durable_machine"

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
    def __init__(self, machine: "_base_durable_machine"):
        self.machine = machine

    def assert_fact(self, fact: Mapping[str, str]) -> None:
        rls.assert_fact(self.machine._rulename, fact)

    def get_facts(self, fact_filter: Union[Mapping[str, str], None] = None,
                  ) -> Iterable[Mapping[str, str]]:
        if fact_filter is None:
            return rls.get_facts(self.machine._rulename)#type: ignore[no-any-return]
        else:
            return (f #type: ignore[no-any-return]
                    for f in rls.get_facts(self.machine._rulename)
                    if all(f.get(key) == val for key, val in fact_filter.items()))

    def retract_fact(self, fact: Mapping[str, str]) -> None:
        for f in self.get_facts():
            if all(f.get(x) == y for x,y in fact.items()):
                rls.retract(self.machine._rulename, f)


class _closure_helper(_context_helper):
    previous_context: _context_helper 
    c: durable.engine.Closure
    def __init__(self, machine: "_base_durable_machine",
                 c: durable.engine.Closure) -> None:
        self.machine = machine
        self.c = c

    def assert_fact(self, fact: Mapping[str, str]) -> None:
        try:
            self.c.assert_fact(fact)
        except durable.engine.MessageObservedException:
            pass

    def get_facts(self, fact_filter: Optional[Mapping[str, str]] = None,
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

def _transform_all_externals_to_calls(args: ATOM_ARGS,
                                      tmp_machine: "_base_durable_machine",
                                      ) -> Iterable[RESOLVABLE]:
    useable_args: list[RESOLVABLE] = []
    tmp_assign: RESOLVABLE
    t_arg: TRANSLATEABLE_TYPES
    e_arg: abc_external
    for arg in args:
        if isinstance(arg, abc_external):
            useable_args.append(arg.as_resolvable(tmp_machine))
            continue
        elif isinstance(arg, (Variable, Literal, IdentifiedNode)):
            useable_args.append(arg)
            continue
        try:
            t_arg = arg#type: ignore[assignment]
            assert rdflib2string(t_arg)
            useable_args.append(t_arg)
            continue
        except (AssertionError, TypeError):
            pass

        raise NotImplementedError()
        try:
            e_arg = arg#type: ignore[assignment]
            tmp_assign = tmp_machine._create_assignment_from_external(
                    e_arg.op, e_arg.args)
            useable_args.append(tmp_assign)
            continue
        except AttributeError:
            pass
        raise NotImplementedError(arg, type(arg))
    return useable_args

class _base_durable_machine(abc_machine.machine):
    _ruleset: rls.ruleset
    logger: logging.Logger
    """Logger for specific output, expected from the machine, eg execute:print.
    Also logs internal failures.
    """
    errors: list
    inconsistent_information: bool
    _current_context: _context_helper
    _initialized: bool
    _imported_location: Container[IdentifiedNode]
    available_import_profiles: MutableMapping[Optional[IdentifiedNode],
                                              importProfile]
    _registered_pattern_generator: Dict[IdentifiedNode,
                                        PATTERNGENERATOR]
    _registered_action_generator: Dict[IdentifiedNode,
                                       Callable[..., RESOLVABLE]]
    _registered_assignment_generator: Dict[IdentifiedNode,
                                           Callable[..., _assignment]]
    _registered_binding_generator: Dict[IdentifiedNode, BINDING_DESCRIPTION]

    _imported_locations: Set[Optional[IdentifiedNode]]
    _knownLocations: MutableMapping[IdentifiedNode, rdflib.Graph]

    _registered_facttypes: Mapping[type[fact], str] = {
            frame: frame.ID,
            member: member.ID,
            subclass: subclass.ID,
            atom: atom.ID,
            }
    _fact_generator_from_id: Mapping[str, type[fact]] = {
            frame.ID: frame,
            member.ID: member,
            subclass.ID: subclass,
            atom.ID: atom,
            }

    def __init__(self, loggername: str = __name__) -> None:
        rulesetname = str(uuid.uuid4())
        self.inconsistent_information = False
        self._ruleset = rls.ruleset(rulesetname)
        self.logger = logging.getLogger(loggername)
        self.__set_basic_rules()
        self.errors = []
        self._current_context = _no_closure(self)
        self._initialized = False

        self._registered_pattern_generator = {}
        self._registered_action_generator = {}
        self._registered_assignment_generator = {}
        self._registered_binding_generator = {}

        self._imported_locations = set()
        self.available_import_profiles = {}
        self._knownLocations = {}
        self._steps_left = 1

    def import_data(self,
                    infograph: Graph,
                    location: IdentifiedNode,
                    profile: Union[IdentifiedNode, None] = None,
                    extraDocuments: Mapping[IdentifiedNode, Graph] = {},
                    ) -> None:
        if location in self._imported_locations:
            logger.debug("Already import %s" % location)
            return
        usedImportProfile = self.available_import_profiles[profile]
        logger.debug("import data %s" % profile)
        usedImportProfile.create_rules(self, location)
        self._imported_locations.add(location)
        for key, g in extraDocuments.items():
            if isinstance(key, str):
                self._knownLocations[URIRef(key)] = g
            else:
                self._knownLocations[key] = g

    def load_external_resource(self, location: Union[str, IdentifiedNode],
                               ) -> rdflib.Graph:
        if isinstance(location, str):
            return self._knownLocations[URIRef(location)]
        else:
            return self._knownLocations[location]

    def get_replacement_node(self,
                             op: IdentifiedNode,
                             args: Iterable[RESOLVABLE],
                             ) -> TRANSLATEABLE_TYPES:
        raise NoPossibleExternal()

    def get_binding_action(self,
                           op: IdentifiedNode,
                           args: Iterable[RESOLVABLE],
                           ) -> RESOLVABLE:
        try:
            funcgen = self._registered_assignment_generator[op]
        except KeyError as err:
            raise NoPossibleExternal(op) from err
        return funcgen(*args)

    def check_statement(self,
                        statement: Union[Collection[Union[machine_facts.fact, machine_facts.abc_external]], machine_facts.fact, machine_facts.abc_external],
                        bindings: BINDING_WITH_BLANKS = {},
                        ) -> bool:
        """Checks if given proposition is true.
        If machine is the machine holds incosistent data, everything is true.

        :TODO: currently facts are only simple facts like a frame. But check
            should support complex statement like 'Xor'
        """
        if self.inconsistent_information:
            return True
        if isinstance(statement, (machine_facts.fact, machine_facts.abc_external)):
            statement = [statement]
        for f in statement:
            if isinstance(f, machine_facts.fact):
                d = {FACTTYPE: self._registered_facttypes[type(f)]}
                for key, x in f.items():
                    x_ = _node2string(x, self, bindings)
                    if x_ is not None:
                        d[key] = x_
                try:
                    iter(self.get_facts(d)).__next__()
                except StopIteration:
                    return False
            else:
                raise NotImplementedError(f)
                q = self._create_assignment_from_external(f.op, f.args)
                if not _resolve(q, bindings):
                    return False
        return True

    def assert_fact(self, new_fact: abc_machine.fact, bindings: BINDING,
                    ) -> None:
        d = {FACTTYPE: self._registered_facttypes[type(new_fact)]}
        for key, x in new_fact.items():
            d[key] = _node2string(x, self, bindings)
        self._current_context.assert_fact(d)
    
    def retract_fact(self, fact: Mapping[str, str]) -> None:
        self._current_context.retract_fact(fact)

    def get_facts(self, fact_filter: Optional[Mapping[str, str]] = None,
            ) -> Iterable[abc_machine.fact]:
        for f in self._current_context.get_facts(fact_filter):
            fact_id = f[FACTTYPE]
            yield self._fact_generator_from_id[fact_id].from_fact(f)

    def _make_rule(self, patterns: Iterable[_pattern],
                  action: Callable,
                  error_message: str = "") -> None:
        pats: List[rls.value] = []
        variable_locators: MutableMapping[Variable, VARIABLE_LOCATOR] = {}
        for p in patterns:
            pats.append(p.generate_rls(variable_locators))
        with self._ruleset:
            @rls.when_all(*pats)
            def myfoo(c: durable.engine.Closure) -> None:
                bindings = {}
                try:
                    for var, loc in variable_locators.items():
                        bindings[var] = loc(c)
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
                                     % (action, bindings,
                                        traceback.format_exc()))
                    raise FailedInternalAction(error_message) from err
                self._steps_left = self._steps_left - 1
                if self._steps_left == 0:
                    c.retract_fact({MACHINESTATE: RUNNING_STATE})

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
        if self.inconsistent_information:
            raise Exception("machine has reached a state with inconsistent "
                            "information. No Action is possible anymore.")
        if not self._initialized:
            rls.assert_fact(self._rulename, {MACHINESTATE: INIT_STATE})
            rls.retract_fact(self._rulename, {MACHINESTATE: INIT_STATE})
            self._initialized = True
        if steps is None:
            rls.assert_fact(self._rulename, {MACHINESTATE: RUNNING_STATE})
            rls.retract_fact(self._rulename, {MACHINESTATE: RUNNING_STATE})
        else:
            self._steps_left = steps
            rls.assert_fact(self._rulename, {MACHINESTATE: RUNNING_STATE})
            rls.retract_fact(self._rulename, {MACHINESTATE: RUNNING_STATE})
        if self.errors:
            raise Exception("Rules produced an error.", self.errors)

    @property
    def _rulename(self) -> str:
        return self._ruleset.name #type: ignore[no-any-return]

    def add_init_action(self, action: Callable[[BINDING], None]) -> None:
        q = durable_rule(self)
        def act(bindings: BINDING) -> None:
            logger.debug("execute init: %s" % action)
            action(bindings)
        q.set_action(act, [])
        #q.action = action
        q.finalize()

    def create_rule_builder(self) -> "durable_rule":
        return durable_rule(self)

    def create_implication_builder(self) -> "durable_rule":
        return durable_rule(self)

    def _create_pattern_from_external(
            self,
            op: IdentifiedNode,
            args: ATOM_ARGS,
            bound_variables: Container[Variable],
            ) -> Iterable[Tuple[Iterable[_pattern],
                                Iterable[Callable[[BINDING], Literal]],
                                Iterable[Variable]]]:
        """Try to create a complete pattern for given external statement.
        :raises NoPossibleExternal: If given external is not defined
            or cant be used to directly produce a pattern raise this error.
        """
        try:
            mygen = self._registered_pattern_generator[op]
        except KeyError:
            raise NoPossibleExternal()
        args_ = []
        for a in args:
            assert not isinstance(a, abc_external)
            args_.append(a)
        for tmp_pattern, cond, new_bound_vars in mygen(args_, bound_variables):
            tmp_pattern_: list[_pattern] = []
            for _x in tmp_pattern:
                assert isinstance(_x, _pattern)
                tmp_pattern_.append(_x)
            yield tmp_pattern_, cond, new_bound_vars

    def _create_binding_from_external(
            self,
            op: IdentifiedNode,
            args: ATOM_ARGS,
            bound_variables: Container[Variable] = [],
            ) -> Tuple[Iterable[_pattern],
                       Iterable[Callable[[BINDING], Literal]],
                       Iterable[Variable]]:
        try:
            binding_map = self._registered_binding_generator[op]
        except KeyError as err:
            raise NoPossibleExternal(op) from err
        try:
            funcgen = binding_map[tuple(isinstance(x, Variable)
                                        and x not in bound_variables
                                        for x in args)]
        except KeyError as err:
            raise NoPossibleExternal(op) from err
        args_: Iterable[RESOLVABLE]\
                = _transform_all_externals_to_calls(args, self)
        return [], [funcgen(*args_)], [x for x in args
                                      if (isinstance(x, Variable)
                                          and x not in bound_variables)]

    def _create_assignment_from_external(
            self,
            op: IdentifiedNode,
            args: ATOM_ARGS,
            bound_variables: Container[Variable] = [],
            ) -> _assignment:
        try:
            mygen = self._registered_assignment_generator[op]
        except KeyError as err:
            raise NoPossibleExternal(op) from err
        useable_args = _transform_all_externals_to_calls(args, self)
        try:
            return mygen(*useable_args)
        except Exception as err:
            raise Exception(useable_args) from err

    def register(self, op: rdflib.URIRef,
                 asaction: Optional[Callable] = None,
                 asassign: Optional[Callable] = None,
                 aspattern: Optional[PATTERNGENERATOR] = None,
                 asbinding: Optional[BINDING_DESCRIPTION] = None,
                 ) -> None:
        if asaction is not None:
            self._registered_action_generator[op] = asaction
        if asassign is not None:
            self._registered_assignment_generator[op] = asassign
        if aspattern is not None:
            self._registered_pattern_generator[op] = aspattern
        if asbinding is not None:
            self._registered_binding_generator[op] = asbinding

class OWLmachine(_base_durable_machine):
    """Implements owl functionality"""
    _registered_facttypes: Mapping[type[fact], str]\
            = {**_base_durable_machine._registered_facttypes,
               **{rdfs_subclass: rdfs_subclass.ID}}
    _fact_generator_from_id: Mapping[str, type[fact]]\
            = {**_base_durable_machine._fact_generator_from_id,
               **{rdfs_subclass.ID: rdfs_subclass}}

    def __init__(self, loggername: str = __name__) -> None:
        super().__init__(loggername)
        self.__inconsistency_rules()
        self.__rdfs_subclass_rule()

    def __rdfs_subclass_rule(self) -> None:
        sub_type = Variable("sub")
        super_type = Variable("super")
        inst = Variable("inst")
        desc_subclass = _pattern.from_fact(
                self._registered_facttypes[rdfs_subclass],
                rdfs_subclass(sub_type, super_type),
                "DescriptionSubclass")
        desc_objMember = _pattern.from_fact(
                self._registered_facttypes[frame],
                frame(inst, RDF.type, sub_type),
                "ObjMember")
        newObjMember = frame(inst, RDF.type, super_type)
        def assert_membership(bindings: BINDING) -> None:
            try:
                self.assert_fact(newObjMember, bindings)
            except durable.engine.MessageObservedException:
                pass
        self._make_rule([desc_subclass, desc_objMember], assert_membership)

    def __inconsistency_rules(self) -> None:
        x = Variable("x")
        described_property = Variable("descprop")
        value = Variable("value")
        desc_findObjectProperty = _pattern.from_fact(
                self._registered_facttypes[frame],
                frame(described_property, RDF.type, OWL.ObjectProperty),
                "findObjectProperty")
        desc_valueToProperty = _pattern({
            FACTTYPE: frame.ID,
            frame.FRAME_OBJ: x,
            frame.FRAME_SLOTKEY: described_property,
            frame.FRAME_SLOTVALUE: value,
            }, "FindValueToProperty")
        def evaluate_inconsistency(bindings: BINDING) -> None:
            if isinstance(bindings[value], Literal):
                self.inconsistent_information = True
                err_message = "found inconsistency. owl.objectProperty %s "\
                        "is pointed to a literal value %r"\
                        % (bindings[described_property], bindings[value])
                logger.error(err_message)
                raise FailedInternalAction(err_message)
        self._make_rule([desc_findObjectProperty, desc_valueToProperty],
                        evaluate_inconsistency)

class RDFSmachine(_base_durable_machine):
    """Implements translation of as in RDF specified syntax for the machine
    """
    def __init__(self, loggername: str = __name__) -> None:
        super().__init__(loggername)
        self.__subclass_rule()

    def __subclass_rule(self) -> None:
        sub_type = Variable("sub")
        super_type = Variable("super")
        inst = Variable("inst")
        desc_subclass = _pattern({
            FACTTYPE: subclass.ID,
            subclass.SUBCLASS_SUB: sub_type,
            subclass.SUBCLASS_SUPER: super_type,
            }, "DescriptionSubclass")
        desc_objMember = _pattern({
            FACTTYPE: member.ID,
            member.INSTANCE: inst,
            member.CLASS: sub_type,
            }, "ObjMember")
        newObjMember = member(inst, super_type)
        def assert_membership(bindings: BINDING) -> None:
            try:
                self.assert_fact(newObjMember, bindings)
            except durable.engine.MessageObservedException:
                pass
        self._make_rule([desc_subclass, desc_objMember], assert_membership)


class durable_rule(abc_machine.implication, abc_machine.rule):
    patterns: list[rls.value]
    bindings: MutableMapping[Variable, VARIABLE_LOCATOR]
    machine: _base_durable_machine
    conditions: list[Callable[[BINDING], Literal]]
    action: Optional[Callable[[BINDING], None]] = None
    needed_variables: Iterable[Variable]
    finalized: bool = False
    _orig_pattern: list[Any]
    __tmp_pattern_organizer: "_pattern_organizer"
    def __init__(self, machine: _base_durable_machine):
        self.machine = machine
        self.patterns = [getattr(rls.m, MACHINESTATE) == RUNNING_STATE]
        #self.action = None
        self.conditions = []
        #self.finalized = False
        self.bindings = {}

        self._orig_pattern = []

    @dataclass
    class _pattern_organizer(abc_machine.pattern_organizer):
        _parent: "durable_rule"
        def __getitem__(self, index): #type: ignore[no-untyped-def]
            return self._parent._orig_pattern[index]

        def __setitem__(self, index, item): #type: ignore[no-untyped-def]
            if self._parent.finalized:
                raise SyntaxError("Cant change pattern after finalizing.")
            raise NotImplementedError()
            self._parent._orig_pattern.__setitem__(index, item)

        def __delitem__(self, index: Union[int, slice]) -> None:
            self._parent._orig_pattern.__delitem__(index)

        def __len__(self) -> int:
            return len(self._parent._orig_pattern)

        def insert(self, index, item): #type: ignore[no-untyped-def]
            if self._parent.finalized:
                raise SyntaxError("Cant change pattern after finalizing.")
            assert isinstance(item, (fact, abc_external))
            logger.debug((item, index))
            self._parent._orig_pattern.insert(index, item)

        def __bool__(self) -> bool:
            return bool(self._parent._orig_pattern)

        def append(self, item: Union[fact, abc_external, "pattern_generator"],
                   ) -> None:
            if isinstance(item, pattern_generator):
                item._add_pattern(self._parent)
            elif isinstance(item, (abc_external, fact)):
                self.insert(len(self), item)
            else:
                raise NotImplementedError(item, type(item))

    @property
    def orig_pattern(self) -> _pattern_organizer:
        try:
            return self.__tmp_pattern_organizer
        except AttributeError:
            self.__tmp_pattern_organizer = self._pattern_organizer(self)
            return self.__tmp_pattern_organizer

    def generate_node_external(self, op: IdentifiedNode, args: ATOM_ARGS,
            ) -> Union[str, rdflib.BNode, rdflib.URIRef, rdflib.Literal]:
        raise NotImplementedError()

    @dataclass
    class _conditional_action:
        action: Callable[[BINDING], None]
        logger: logging.Logger
        conditions: Iterable[Callable[[BINDING], Literal]]
        def __call__(self, bindings: BINDING) -> None:
            self.logger.debug("execute %s" % self)
            for cond in self.conditions:
                try:
                    if not cond(bindings):
                        self.logger.debug("Stopped rule because %s"
                                                  % cond)
                        return
                except Exception as err:
                    self.logger.info("Failed at condition %r with "
                                "bindings %s.\n Produced traceback:\n%s"
                                 % (cond, bindings,
                                    traceback.format_exc()))
                    raise FailedInternalAction() from err
            if self.action is None:
                raise RuleNotComplete("action is missing")
            try:
                self.action(bindings)
            except Exception as err:
                self.logger.info("Failed at action %r with bindings %s.\n"
                                 "Produced traceback:\n%s"
                                 % (self.action, bindings,
                                    traceback.format_exc()))
                raise FailedInternalAction() from err

    @dataclass
    class _simple_action:
        action: Callable[[BINDING], None]
        logger: logging.Logger
        def __call__(self, bindings: BINDING) -> None:
            self.logger.debug("execute %s" % self)
            self.action(bindings)

    def _generate_action_prerequisites(
            self,
            ) -> Iterable[Tuple[Iterable[_pattern],
                                Iterable[Callable[[BINDING], Literal]],
                                Iterable[Variable]]]:
        p: List[Union[fact, abc_external]] = list(self.orig_pattern)
        conditions: List[Callable[[BINDING], Literal]]
        patterns: List[_pattern]
        bound_variables: Set[Variable]
        for patterns, conditions, bound_variables in self._generate_action_prerequisites_inner(p, [], [], set()):
            if len(patterns) == 0 and len(conditions) == 0:
                #create rule as initialisation rule
                patterns.insert(0, _pattern({MACHINESTATE: INIT_STATE}))
            elif len(patterns) > 0:
                patterns.insert(0, _pattern({MACHINESTATE: RUNNING_STATE}))
            else:
                #TODO : This rule lacks any trigger. 
                patterns.insert(0, _pattern({MACHINESTATE: RUNNING_STATE}))
            yield patterns, conditions, bound_variables

    def _generate_action_prerequisites_inner(
            self,
            pattern_parts: List[Union[fact, abc_external]],
            patterns: list[_pattern],
            conditions: List[Callable[[BINDING], Literal]],
            bound_variables: Set[Variable],
            ) -> Iterable[Tuple[List[_pattern],
                                List[Callable[[BINDING], Literal]],
                                Set[Variable]]]:
        """
        :TODO: The rules are not garantueed to be in the same sequence as
            binding the variables would be required. For this case
        """
        #sorting cause patterns always bind succesfully -> more Success chance
        pattern_parts = sorted(pattern_parts,
                               key=lambda x: 0 if isinstance(x, fact) else 1)
        for i, q in enumerate(pattern_parts):
            if isinstance(q, fact):
                logger.debug("appends %s as pattern." % q)
                patterns.append(_pattern(q.as_dict()))
                bound_variables.update(q.used_variables)
            elif isinstance(q, abc_external):
                for tmp_p, tmp_c, tmp_v\
                        in self._process_external_as_pattern(q.op, q.args,
                                                             bound_variables):
                    logger.debug("uses %s to append:\npattern: %s\ncondition: %s"
                                 %(q, tmp_p, tmp_c))
                    new_bound_variables = bound_variables.union(tmp_v)
                    if any(x not in new_bound_variables for x in q.args
                           if isinstance(x, Variable)):
                        raise VariableNotBoundError(
                                "Condition (%s) uses unbound variables %s "
                                "but doesnt bind it."
                                % (q.op, [x for x in q.args
                                          if isinstance(x, Variable)
                                          and x not in new_bound_variables]))
                    next_gen = self._generate_action_prerequisites_inner(
                            pattern_parts[i+1:],
                            [*patterns, *tmp_p],
                            [*conditions, *tmp_c],
                            new_bound_variables,
                            )
                    for x in next_gen:
                        yield x
                return
            else:
                raise Exception(type(q))
        yield patterns, conditions, bound_variables

    def _generate_action(
            self,
            conditions: Iterable[Callable[[BINDING], Literal]],
            action: Callable[[BINDING], None],
            ) -> Callable[[BINDING], None]:
        if conditions:
            return self._conditional_action(action, self.machine.logger,
                                            conditions)
        else:
            return self._simple_action(action, self.machine.logger)

    def finalize(self) -> None:
        if self.finalized:
            raise Exception()
        if self.action is None:
            raise Exception()
        self.finalized = True
        logger.debug("Create rule %s" % self)
        for patterns, conditions, bound_variables\
                in self._generate_action_prerequisites():
            if not all(x in bound_variables for x in self.needed_variables):
                notbound = [x for x in self.needed_variables
                            if x not in bound_variables]
                raise VariableNotBoundError(notbound)
            action = self._generate_action(conditions, self.action)
            self.machine._make_rule(patterns, action)

    def set_action(self, action: Callable[[BINDING], None],
                   needed_variables: Iterable[Variable]) -> None:
        self.action = action
        self.needed_variables = list(needed_variables)

    def _process_external_as_pattern(
            self,
            op: IdentifiedNode,
            args: ATOM_ARGS,
            bound_variables: Container[Variable] = {},
            ) -> Iterable[Tuple[Iterable[_pattern],
                       Iterable[Callable[[BINDING], Literal]],
                       Iterable[Variable]]]:
        """
        :TODO: resolve this method into surrounding. Seems overkill
        """
        new_bound_vars: Iterable[Variable]
        try:
            for patterns, conditions, new_bound_vars\
                    in self.machine._create_pattern_from_external(
                            op, args, bound_variables):
                yield patterns, conditions, new_bound_vars
            return
        except NoPossibleExternal:
            pass
        try:
            yield self.machine._create_binding_from_external(op, args,
                                                             bound_variables)
            return
        except NoPossibleExternal:
            pass
        cond = self.machine._create_assignment_from_external(op, args, bound_variables)
        yield [], [cond], []

    @property
    def logger(self) -> logging.Logger:
        return self.machine.logger

    def _generate_pattern(
            self,
            pattern: Mapping[str, Union[Variable, str, TRANSLATEABLE_TYPES]],
            bindings: MutableMapping[Variable, VARIABLE_LOCATOR],
            factname: Optional[str] = None,
            ) -> rls.value:
        if factname is None:
            _as_string = repr(sorted(pattern.items()))
            factname = "f%s" % sha1(_as_string.encode("utf8")).hexdigest()
        next_constraint: rls.value
        constraint: Union[rls.value, None] = None
        for key, value in pattern.items():
            next_constraint = None
            if type(value) == str:
                next_constraint = getattr(rls.m, key) == value
            elif isinstance(value, rdflib.Variable):
                if value in bindings:
                    loc = bindings[value]
                    newpattern = getattr(rls.m, key) == loc(rls.c)
                    #log.append(f"rls.m.{fact_label} == {loc}")
                else:
                    loc = _value_locator(factname, key)
                    bindings[value] = loc
                    next_constraint = None
                    #logger.debug("bind: %r-> %r" % (value, loc))
            elif isinstance(value, (URIRef, BNode, Literal)):
                next_constraint = getattr(rls.m, key) == rdflib2string(value)
            elif isinstance(value, external):
                raise NotImplementedError()
                #newnode = value.serialize(c, bindings, external_resolution)
                #next_constraint = getattr(rls.m, key) == newnode
            else:
                raise NotImplementedError(value, type(value))
            if next_constraint is not None:
                if constraint is None:
                    constraint = next_constraint
                else:
                    constraint = constraint & next_constraint
        if constraint is None:
            raise Exception("Cant handle %s" % pattern)
        pattern_part = getattr(rls.c, factname) << constraint
        return pattern_part

    def __repr__(self) -> str:
        return f"rule: {self._orig_pattern}-> {self.action}"


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
        try:
            val = getattr(fact, self.in_fact_label)
        except Exception:
            logger.critical("In facts(%s) value locator failed: %s" % (c._m, self))
            raise
        if isinstance(val, str):
            return string2rdflib(val)
        else:
            return val

    def __repr__(self) -> str:
        return f"%s(c.{self.factname}.{self.in_fact_label})"\
                % type(self).__name__

class _machine_default_externals(_base_durable_machine):
    """Implements all default externals
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__register_externals()
        self.__register_importProfiles()

    def __register_importProfiles(self) -> None:
        self.available_import_profiles[entailment["OWL-Direct"]] = profileOWLDirect()

    def __register_externals(self) -> None:
        from .default_externals import invert
        def_ext._register_timeExternals(self)
        def_ext._register_plainLiteralExternals(self)
        def_ext._register_stringExternals(self)
        def_ext._register_xmlExternals(self)
        def_ext._register_anyURIExternals(self)
        def_ext._register_booleanExternals(self)
        self.register(**special_externals.equality)
        self.register(RIF.Or, asassign=def_ext.rif_or)
        self.register(pred["numeric-equal"],
                      asassign=def_ext.numeric_equal)
        self.register(pred["numeric-not-equal"],
                      asassign=invert.gen(def_ext.numeric_equal))
        self.register(pred["numeric-greater-than"],
                      asassign=def_ext.pred_greater_than)
        self.register(pred["numeric-less-than-or-equal"],
                      asassign=invert.gen(
                          def_ext.pred_greater_than))
        self.register(pred["numeric-less-than"],
                      asassign=def_ext.pred_less_than)
        self.register(pred["numeric-greater-than-or-equal"],
                      asassign=invert.gen(def_ext.pred_less_than))
        self.register(pred["XMLLiteral-equal"],
                      asassign=def_ext.literal_equal)
        self.register(func["numeric-add"],
                      asassign=def_ext.numeric_add)
        self.register(func["numeric-subtract"],
                      asassign=def_ext.func_numeric_subtract)
        self.register(func["numeric-multiply"],
                      asassign=def_ext.numeric_multiply)
        self.register(func["numeric-divide"],
                      asassign=def_ext.numeric_divide)
        self.register(func["numeric-integer-divide"],
                      asassign=def_ext.numeric_integer_divide)
        self.register(func["numeric-mod"],
                      asassign=def_ext.numeric_mod)
        self.register(func["numeric-integer-mod"],
                      asassign=def_ext.numeric_integer_mod)
        self.register(pred["is-list"],
                      asassign=def_ext.is_list)
        self.register(pred["list-contains"],
                      asassign=def_ext.list_contains)
        self.register(pred["literal-not-identical"],
                      asassign=def_ext.ascondition_pred_literal_not_identical)
        self.register(func["make-list"],
                      asassign=def_ext.make_list)
        self.register(func["count"],
                      asassign=def_ext.count)
        self.register(func["get"],
                      asassign=def_ext.list_get)
        self.register(func["sublist"],
                      asassign=def_ext.sublist)
        self.register(func["append"],
                      asassign=def_ext.append)
        self.register(func["concatenate"],
                      asassign=def_ext.concatenate)
        self.register(func["insert-before"],
                      asassign=def_ext.insert_before)
        self.register(func["remove"],
                      asassign=def_ext.remove)
        self.register(func["reverse"],
                      asassign=def_ext.reverse_list)
        self.register(func["index-of"],
                      asassign=def_ext.index_of)
        self.register(func["union"],
                      asassign=def_ext.union)
        self.register(func["distinct-values"],
                      asassign=def_ext.distinct_values)
        self.register(func["intersect"],
                      asassign=def_ext.intersect)
        self.register(func["except"],
                      asassign=def_ext.list_except)
        self.register(pred["is-literal-hexBinary"],
                      asassign=def_ext.is_literal_hexBinary)
        self.register(pred["is-literal-not-hexBinary"],
                      asassign=invert.gen(def_ext.is_literal_hexBinary))
        self.register(pred["is-literal-base64Binary"],
                      asassign=def_ext.condition_pred_is_literal_base64Binary)
        self.register(pred["is-literal-double"],
                      asassign=def_ext.condition_pred_is_literal_double)
        self.register(pred["is-literal-not-double"],
                      asassign=def_ext.condition_pred_is_literal_not_double)
        self.register(pred["is-literal-float"],
                      asassign=def_ext.condition_pred_is_literal_float)
        self.register(pred["is-literal-not-float"],
                      asassign=def_ext.condition_pred_is_literal_not_float)
        self.register(pred["is-literal-decimal"],
                      asassign=def_ext.condition_pred_is_literal_decimal)
        self.register(pred["is-literal-not-decimal"],
                      asassign=invert.gen(
                          def_ext.condition_pred_is_literal_decimal))
        self.register(pred["is-literal-integer"],
                      asassign=def_ext.condition_pred_is_literal_integer)
        self.register(pred["is-literal-not-integer"],
                      asassign=invert.gen(def_ext.condition_pred_is_literal_integer))
        self.register(pred["is-literal-int"],
                      asassign=def_ext.condition_pred_is_literal_int)
        self.register(pred["is-literal-not-int"],
                      asassign=invert.gen(def_ext.condition_pred_is_literal_int))
        self.register(pred["is-literal-long"],
                      asassign=def_ext.condition_pred_is_literal_long)
        self.register(pred["is-literal-not-long"],
                      asassign=invert.gen(def_ext.condition_pred_is_literal_long))
        self.register(pred["is-literal-short"],
                      asassign=def_ext.condition_pred_is_literal_short)
        self.register(pred["is-literal-not-short"],
                      asassign=invert.gen(
                          def_ext.condition_pred_is_literal_short))
        self.register(pred["is-literal-byte"],
                      asassign=def_ext.condition_pred_is_literal_byte)
        self.register(pred["is-literal-not-byte"],
                      asassign=invert.gen(def_ext.condition_pred_is_literal_byte))
        self.register(pred["is-literal-nonNegativeInteger"],
                      asassign=def_ext.condition_pred_is_literal_positiveInteger)
        self.register(pred["is-literal-not-nonNegativeInteger"],
                      asassign=invert.gen(
                          def_ext.condition_pred_is_literal_positiveInteger))
        self.register(pred["is-literal-positiveInteger"],
                      asassign=def_ext.condition_pred_is_literal_positiveInteger)
        self.register(pred["is-literal-not-positiveInteger"],
                      asassign=invert.gen(
                          def_ext.condition_pred_is_literal_positiveInteger))
        self.register(pred["is-literal-nonPositiveInteger"],
                      asassign=def_ext.condition_pred_is_literal_negativeInteger)
        self.register(pred["is-literal-not-nonPositiveInteger"],
                      asassign=invert.gen(
                          def_ext.condition_pred_is_literal_negativeInteger))
        self.register(pred["is-literal-negativeInteger"],
                      asassign=def_ext.condition_pred_is_literal_negativeInteger)
        self.register(pred["is-literal-not-negativeInteger"],
                      asassign=invert.gen(
                          def_ext.condition_pred_is_literal_negativeInteger))
        self.register(pred["is-literal-unsignedLong"],
                      asassign=def_ext.condition_pred_is_literal_unsignedLong)
        self.register(pred["is-literal-not-unsignedLong"],
                      asassign=invert.gen(
                          def_ext.condition_pred_is_literal_unsignedLong))
        self.register(pred["is-literal-unsignedInt"],
                      asassign=def_ext.condition_pred_is_literal_unsignedInt)
        self.register(pred["is-literal-not-unsignedInt"],
                      asassign=def_ext.invert.gen(
                          def_ext.condition_pred_is_literal_unsignedInt))
        self.register(pred["is-literal-unsignedShort"],
                      asassign=def_ext.condition_pred_is_literal_unsignedShort)
        self.register(pred["is-literal-not-unsignedShort"],
                      asassign=invert.gen(
                          def_ext.condition_pred_is_literal_unsignedShort))
        self.register(pred["is-literal-unsignedByte"],
                      asassign=def_ext.condition_pred_is_literal_unsignedByte)
        self.register(pred["is-literal-not-unsignedByte"],
                      asassign=invert.gen(
                          def_ext.condition_pred_is_literal_unsignedByte))
        self.register(pred["is-literal-not-base64Binary"],
                      asassign=def_ext.ascondition_is_literal_not_base64Binary)
        self.register(XSD["base64Binary"],
                      asassign=def_ext.asassign_xs_base64Binary)
        self.register(XSD["double"],
                      asassign=def_ext.assign_rdflib.gen(XSD["double"]))
        self.register(XSD["float"],
                      asassign=def_ext.assign_rdflib.gen(XSD["float"]))
        self.register(XSD["hexBinary"],
                      asassign=def_ext.assign_rdflib.gen(XSD["hexBinary"]))
        self.register(XSD["decimal"],
                      asassign=def_ext.assign_rdflib.gen(XSD["decimal"]))
        self.register(XSD["integer"],
                      asassign=def_ext.assign_rdflib.gen(XSD["integer"]))
        self.register(XSD["positiveInteger"],
                      asassign=def_ext.assign_rdflib.gen(XSD["positiveInteger"]))
        self.register(XSD["nonPositiveInteger"],
                      asassign=def_ext.assign_rdflib.gen(XSD["nonPositiveInteger"]))
        self.register(XSD["negativeInteger"],
                      asassign=def_ext.assign_rdflib.gen(XSD["negativeInteger"]))
        self.register(XSD["nonNegativeInteger"],
                      asassign=def_ext.assign_rdflib.gen(XSD["nonNegativeInteger"]))
        self.register(XSD["unsignedLong"],
                      asassign=def_ext.assign_rdflib.gen(XSD["unsignedLong"]))
        self.register(XSD["long"],
                      asassign=def_ext.assign_rdflib.gen(XSD["long"]))
        self.register(XSD["int"],
                      asassign=def_ext.assign_rdflib.gen(XSD["int"]))
        self.register(XSD["unsignedInt"],
                      asassign=def_ext.assign_rdflib.gen(XSD["unsignedInt"]))
        self.register(XSD["short"],
                      asassign=def_ext.assign_rdflib.gen(XSD["short"]))
        self.register(XSD["unsignedShort"],
                      asassign=def_ext.assign_rdflib.gen(XSD["unsignedShort"]))
        self.register(XSD["byte"],
                      asassign=def_ext.assign_rdflib.gen(XSD["byte"]))
        self.register(XSD["unsignedByte"],
                      asassign=def_ext.assign_rdflib.gen(XSD["unsignedByte"]))


class durable_machine(_machine_default_externals, RDFSmachine, OWLmachine):
    pass
