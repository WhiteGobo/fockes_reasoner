import durable.lang as rls
import durable.engine
import json
import uuid
import abc
import logging
logger = logging.getLogger(__name__)
import traceback
from typing import Union, Mapping, Iterable, Callable, Any, MutableMapping, Optional, Container, Dict, Set, get_args, Tuple, List, Iterator, Hashable
from collections.abc import Collection
from dataclasses import dataclass
from hashlib import sha1
import itertools as it
import rdflib
from rdflib import URIRef, Variable, Literal, BNode, Graph, IdentifiedNode, XSD
from . import abc_machine
from .abc_machine import TRANSLATEABLE_TYPES, FACTTYPE, BINDING, BINDING_WITH_BLANKS, VARIABLE_LOCATOR, NoPossibleExternal, IMPORTPROFILE, RESOLVABLE, ATOM_ARGS, abc_external, RESOLVER, RuleNotComplete, pattern_generator, VariableNotBoundError, abc_pattern, _resolve, ASSIGNMENT, StopRunning, EXTERNAL_ARG, ACTIONGENERATOR, ACTION, INDIPENDENTACTIONGENERATOR

from ..importProfiles import import_profileOWLDirect,\
        import_profileSimpleEntailment,\
        import_profileRDFSEntailment

from .bridge_rdflib import rdflib2string, string2rdflib, term_list

from ..shared import RDF, pred, func, entailment, RIF, OWL
from . import machine_facts
from .machine_facts import frame, member, subclass, atom, fact, external, rdflib2string, _node2string
from . import special_externals
#from .machine_facts import frame, member, subclass, fact

from . import default_externals as def_ext
from .owl_facts import rdfs_subclass
from .machine_patterns import _pattern, _value_locator, MACHINESTATE, RUNNING_STATE, INIT_STATE
from .abc_machine import BINDING_DESCRIPTION, PATTERNGENERATOR


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
                    if all(f.get(key) == val
                           for key, val in fact_filter.items()))

    def retract_fact(self, fact: Mapping[str, str]) -> None:
        logger.critical(repr(fact))
        for f in self.get_facts():
            if all(f.get(x) == y for x,y in fact.items()):
                self.c.retract_fact(f)

    def __enter__(self) -> None:
        self.previous_context = self.machine._current_context
        self.machine._current_context = self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.machine._current_context = self.previous_context

def _transform_all_externals_to_calls(args: Iterable[EXTERNAL_ARG],
                                      tmp_machine: "_base_durable_machine",
                                      ) -> Iterable[RESOLVABLE]:
    """This is used for when a fact is expected and when resources are
    expected. This is bad for typechecking reasons.
    """
    useable_args: list[RESOLVABLE] = []
    tmp_assign: RESOLVABLE
    t_arg: TRANSLATEABLE_TYPES
    e_arg: abc_external
    for arg in args:
        if isinstance(arg, abc_external):
            _assign_args = []
            for x in arg.args:
                assert isinstance(x, (IdentifiedNode, Literal, term_list, Variable, abc_external))
                _assign_args.append(x)
            _assignment = tmp_machine._create_assignment_from_external(
                    arg.op, _assign_args)
            useable_args.append(_assignment)
            continue
        elif isinstance(arg, (Variable, Literal, IdentifiedNode)):
            useable_args.append(arg)
            continue
        elif isinstance(arg, fact):
            raise SyntaxError("found fact, where a resource is expected")
            #gen = tmp_machine._fact_generator.gen_for_machine(tmp_machine,arg)
            #useable_args.append(gen)
            #continue
        try:
            t_arg = arg#type: ignore[assignment]
            assert rdflib2string(t_arg)
            useable_args.append(t_arg)
            continue
        except (AssertionError, TypeError):
            pass

        raise NotImplementedError(arg)
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

class _base_durable_machine(abc_machine.extensible_Machine):
    _ruleset: rls.ruleset
    logger: logging.Logger
    """Logger for specific output, expected from the machine, eg execute:print.
    Also logs internal failures.
    """
    errors: list
    inconsistent_information: bool
    _current_context: _context_helper
    _initialized: bool
    available_import_profiles: MutableMapping[Optional[str],
                                              IMPORTPROFILE]
    _registered_pattern_generator: Dict[Hashable,
                                        PATTERNGENERATOR]
    _registered_superaction_generator:\
            Dict[Hashable, ACTIONGENERATOR[Union[ACTION, fact], None]]
    _registered_normalaction_generator:\
            Dict[Hashable, ACTIONGENERATOR[RESOLVABLE, None]]
    _registered_assignment_generator:\
            Dict[Hashable, INDIPENDENTACTIONGENERATOR[RESOLVABLE, Literal]]
    _registered_binding_generator: Dict[Hashable, BINDING_DESCRIPTION]
    _registered_groundaction_generator: Dict[Hashable, Any]

    _imported_locations: List[str]
    _knownLocations: MutableMapping[str, Callable[[], rdflib.Graph]]

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
        self._registered_superaction_generator = {}
        self._registered_normalaction_generator = {}
        self._registered_assignment_generator = {}
        self._registered_binding_generator = {}
        self._registered_groundaction_generator = {}

        self._imported_locations = []
        self.available_import_profiles = {}
        self._knownLocations = {}
        self._steps_left = -1

    @dataclass
    class _fact_generator:
        """Generator of translateable facts from facts with externals
        :TODO: replace type[fact] with callable
        """
        fact_generator: type[fact] #theroeticly callable[[res, ...], fact]
        original_fact: fact
        args: Iterable[RESOLVABLE]

        def __call__(self, bindings: BINDING) -> fact:
            args_ = [_resolve(x, bindings) for x in self.args]
            return self.fact_generator.from_flat_translateables(*args_)

        @classmethod
        def gen_for_machine(cls, machine: "_base_durable_machine",
                            original_fact: fact,
                            )-> "_base_durable_machine._fact_generator":
            gen = machine._fact_generator_from_id[original_fact.ID]
            args: List[RESOLVABLE] = []
            for arg_name, x in original_fact.items():
                if isinstance(x, abc_external):
                    args.append(machine._create_assignment_from_external(
                                    x.op, x.args))
                else:#isinstance(x, (TRANSLATEABLE_TYPES, Variable))
                    args.append(x)
            return cls(gen, original_fact, args)


    def apply(self, ext_order: abc_external) -> None:
        registering_action\
                = self._registered_groundaction_generator[ext_order.op]
        registering_action(self, *ext_order.args)

    def register_information(self,
                             location: Union[str, Literal],
                             graph_getter: Callable[[], rdflib.Graph],
                             ) -> None:
        self._knownLocations[str(location)] = graph_getter

    def load_external_resource(self, location: Union[str, Literal],
                               ) -> rdflib.Graph:
        return self._knownLocations[str(location)]()

    def get_replacement_node(self,
                             op: Hashable,
                             args: Iterable[RESOLVABLE],
                             ) -> TRANSLATEABLE_TYPES:
        raise NoPossibleExternal()

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
                _args = []
                for xx in f.args:
                    assert isinstance(xx, (Literal, IdentifiedNode, Variable,
                                           abc_external, term_list))
                    _args.append(xx)
                q = self._create_assignment_from_external(f.op, _args)
                assert isinstance(q, (Literal, IdentifiedNode, term_list))
                if not _resolve(q, bindings):
                    return False
        return True

    def assert_fact(self, new_fact: abc_machine.fact, bindings: BINDING,
                    ) -> None:
        d = {FACTTYPE: self._registered_facttypes[type(new_fact)]}
        for key, x in new_fact.items():
            d[key] = _node2string(x, self, bindings)
        self._current_context.assert_fact(d)
    
    def retract_object(self, obj: str) -> None:
        """
        :TODO: rework this
        """
        d = {FACTTYPE: self._registered_facttypes[frame],
             frame.FRAME_OBJ: obj}
        self._current_context.retract_fact(d)

    def retract_fact(self, old_fact: abc_machine.fact, bindings: BINDING,
                     ) -> None:
        d = {FACTTYPE: self._registered_facttypes[type(old_fact)]}
        for key, x in old_fact.items():
            d[key] = _node2string(x, self, bindings)
        self._current_context.retract_fact(d)
        #for f in self.get_facts(d):
        #    self._current_context.retract_fact(f)

    def get_facts(self, fact_filter: Optional[Mapping[str, str]] = None,
            ) -> Iterable[abc_machine.fact]:
        for f in self._current_context.get_facts(fact_filter):
            fact_id = f[FACTTYPE]
            yield self._fact_generator_from_id[fact_id].from_fact(f)

    def _make_rule(self, patterns: Iterable[abc_pattern],
                   actions: Iterable[Union[Callable, fact]],
                   *,
                   error_message: str = "",
                   priority: int = 5) -> None:
        assert 0 < priority < 10, "expect priorities within 1-9"
        assert all(type(f) in self._registered_facttypes
                   for f in actions
                   if isinstance(f, fact))
        pats: List[rls.value] = [rls.pri(priority)]
        variable_locators: MutableMapping[Variable, VARIABLE_LOCATOR] = {}
        for p in patterns:
            assert isinstance(p, _pattern)
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
                with _closure_helper(self, c):
                    for act in actions:
                        if isinstance(act, fact):
                            try:
                                self.assert_fact(act, bindings)
                            except durable.engine.MessageObservedException:
                                pass
                        else:
                            try:
                                act(bindings)
                            except StopRunning:
                                logger.critical("qwer")
                                self._current_context.retract_fact({MACHINESTATE: RUNNING_STATE})
                            except FailedInternalAction:
                                raise
                            except Exception as err:
                                self.logger.info("Failed at action %r with "
                                                 "bindings %s. Produced "
                                                 "traceback:\n%s"
                                                 % (act, bindings,
                                                    traceback.format_exc()))
                                raise FailedInternalAction(error_message)\
                                        from err
                self._steps_left = self._steps_left - 1
                if self._steps_left == 0:
                    logger.debug("Stopping... maximal steplimit")
                    c.retract_fact({MACHINESTATE: RUNNING_STATE})

    def __set_basic_rules(self) -> None:
        with self._ruleset:
            @rls.when_all(rls.pri(1), +rls.s.exception)
            def second(c: durable.engine.Closure) -> None:
                self.logger.critical(c.s.exception.replace("\\n", "\n"))
                self.errors.append(str(c.s.exception))
                c.s.exception = None
                c.retract_fact({MACHINESTATE: RUNNING_STATE})

            @rls.when_all(rls.pri(2),+getattr(rls.m, FACTTYPE))
            def accept_all_frametypes(c: durable.engine.Closure) -> None:
                pass

            @rls.when_all(rls.pri(2),+rls.m.machinestate)
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

    def add_init_action(self, action: abc_external) -> None:
        q = durable_rule(self)
        #def act(bindings: BINDING) -> None:
        #    logger.debug("execute init: %s" % action)
        #    action(bindings)
        #q.set_action(act, [])
        q.set_action(action, [])
        q.finalize()

    def create_rule_builder(self) -> "durable_rule":
        return durable_rule(self)

    def create_implication_builder(self) -> "durable_rule":
        return durable_rule(self)

    def _create_executable_from_external(
            self,
            op: Hashable,
            args: ATOM_ARGS,
            ) -> Iterable[Tuple[Iterable[_pattern],
                                Iterable[Callable[[BINDING], Literal]],
                                Iterable[Variable]]]:
        raise NotImplementedError()

    def _create_pattern_from_external(
            self,
            op: Hashable,
            args: Iterable[EXTERNAL_ARG],
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
        for tmp_pattern, cond, new_bound_vars in mygen(self, args, bound_variables):
            tmp_pattern_: list[_pattern] = []
            for _x in tmp_pattern:
                assert isinstance(_x, _pattern)
                tmp_pattern_.append(_x)
            yield tmp_pattern_, cond, new_bound_vars

    def _create_binding_from_external(
            self,
            op: Hashable,
            args: Iterable[EXTERNAL_ARG],
            bound_variables: Container[Variable] = [],
            ) -> Tuple[Iterable[_pattern],
                       Iterable[Callable[[BINDING], Literal]],
                       Iterable[Variable]]:
        try:
            binding_map = self._registered_binding_generator[op]
        except KeyError as err:
            raise NoPossibleExternal(op) from err
        try:
            _bound_var_positions = tuple(isinstance(x, Variable)
                                         and x not in bound_variables
                                         for x in args)
            funcgen = binding_map[_bound_var_positions]
        except KeyError as err:
            raise NoPossibleExternal(op) from err
        args_: Iterable[RESOLVABLE]\
                = _transform_all_externals_to_calls(args, self)
        return [], [funcgen(*args_)], [x for x in args
                                      if (isinstance(x, Variable)
                                          and x not in bound_variables)]

    def _create_action_from_external(
            self,
            op: Hashable,
            args: Iterable[EXTERNAL_ARG],
            ) -> Callable[[BINDING], None]:
        mygen: ACTIONGENERATOR[Union[ACTION, fact], None]\
                | ACTIONGENERATOR[Union[RESOLVABLE], None]
        try:
            mygen = self._registered_superaction_generator[op]
        except KeyError as err:
            pass
        else:
            acts: list[Union[fact, Callable[[BINDING], None]]] = []
            for x in args:
                if isinstance(x, abc_external):
                    acts.append(self._create_action_from_external(x.op, x.args))
                elif isinstance(x, fact):
                    acts.append(x)
                else:
                    raise Exception(x, op, args)
            return mygen(self, *acts)
        try:
            mygen = self._registered_normalaction_generator[op]
        except KeyError as err:
            raise NoPossibleExternal(op) from err
        useable_args = _transform_all_externals_to_calls(args, self)
        return mygen(self, *useable_args)

    def _create_assignment_from_external(
            self,
            op: Hashable,
            args: Iterable[EXTERNAL_ARG],
            ) -> ASSIGNMENT:
        try:
            mygen = self._registered_assignment_generator[op]
        except KeyError as err:
            raise NoPossibleExternal(op) from err
        useable_args = _transform_all_externals_to_calls(args, self)
        try:
            return mygen(*useable_args)
        except Exception as err:
            raise Exception(useable_args) from err

    def register(self, op: rdflib.URIRef | Hashable,
                 assuperaction: Optional[ACTIONGENERATOR[Union[ACTION, fact], None]] = None,
                 asnormalaction: Optional[ACTIONGENERATOR[RESOLVABLE, None]] = None,
                 asassign: Optional[INDIPENDENTACTIONGENERATOR[RESOLVABLE, Literal]] = None,
                 aspattern: Optional[PATTERNGENERATOR] = None,
                 asbinding: Optional[BINDING_DESCRIPTION] = None,
                 asgroundaction: Optional[Any] = None,
                 ) -> None:
        if assuperaction is not None:
            self._registered_superaction_generator[op] = assuperaction
        if asnormalaction is not None:
            self._registered_normalaction_generator[op] = asnormalaction
        if asassign is not None:
            self._registered_assignment_generator[op] = asassign
        if aspattern is not None:
            self._registered_pattern_generator[op] = aspattern
        if asbinding is not None:
            self._registered_binding_generator[op] = asbinding
        if asgroundaction is not None:
            self._registered_groundaction_generator[op] = asgroundaction

class OWLmachine(_base_durable_machine):
    """Implements owl functionality"""
    _registered_facttypes: Mapping[type[fact], str]\
            = {**_base_durable_machine._registered_facttypes,
               **{rdfs_subclass: rdfs_subclass.ID}}
    _fact_generator_from_id: Mapping[str, type[fact]]\
            = {**_base_durable_machine._fact_generator_from_id,
               **{rdfs_subclass.ID: rdfs_subclass}}

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
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
        self._make_rule([desc_subclass, desc_objMember], [newObjMember], priority=3)

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
                        [evaluate_inconsistency], priority=3)


class RDFSmachine(_base_durable_machine):
    """Implements translation of as in RDF specified syntax for the machine
    """
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
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
        self._make_rule([desc_subclass, desc_objMember], [newObjMember], priority=3)


class durable_rule(abc_machine.implication, abc_machine.rule):
    patterns: list[rls.value]
    bindings: MutableMapping[Variable, VARIABLE_LOCATOR]
    machine: _base_durable_machine
    conditions: list[Callable[[BINDING], Literal]]
    actions: List[abc_external | fact]
    needed_variables: Iterable[Variable]
    finalized: bool = False
    _orig_pattern: list[Any]
    __tmp_pattern_organizer: "_pattern_organizer"
    def __init__(self, machine: _base_durable_machine):
        self.machine = machine
        self.patterns = [getattr(rls.m, MACHINESTATE) == RUNNING_STATE]
        self.actions = []
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
        actions: Iterable[ACTION[None] | fact]
        logger: logging.Logger
        conditions: Iterable[Callable[[BINDING], Literal]]
        def __call__(self, bindings: BINDING) -> None:
            self.logger.debug("execute %s" % self)
            for cond in self.conditions:
                try:
                    if not cond(bindings):
                        self.logger.debug("Stopped rule because:\n%s"
                                                  % cond)
                        return
                except Exception as err:
                    self.logger.info("Failed with bindings %s at condition:\n"
                                     "%s\nProduced traceback:\n%s"
                                     % (bindings, cond,
                                        traceback.format_exc()))
                    raise FailedInternalAction() from err
            #if self.actions is None:
            #    raise RuleNotComplete("action is missing")
            for act in self.actions:
                if isinstance(act, fact):
                    raise NotImplementedError()
                else:
                    try:
                        act(bindings)
                    except Exception as err:
                        self.logger.info("Failed at action %r with bindings %s.\n"
                                         "Produced traceback:\n%s"
                                         % (act, bindings,
                                            traceback.format_exc()))
                        raise FailedInternalAction() from err

    def _generate_action(
            self,
            conditions: Iterable[Callable[[BINDING], Literal]],
            actions: Iterable[abc_external | fact],
            ) -> Iterable[Union[Callable[[BINDING], None], fact]]:
        actions_: List[ACTION[None] | fact] = []
        for act in actions:
            if isinstance(act, abc_external):
                actions_.append(self.machine._create_action_from_external(act.op, act.args))
            elif isinstance(act, fact):
                actions_.append(act)
            else:
                #act.__call__
                raise Exception(act)
                #actions_.append(act)
        if conditions:
            return [self._conditional_action(actions_, self.machine.logger,
                                             conditions)]
        else:
            return actions_

    def finalize(self) -> None:
        actions: Iterable[Union[Callable[[BINDING], None], fact]]
        if self.finalized:
            raise Exception()
        if not self.actions:
            raise Exception()
        self.finalized = True
        logger.debug("Create rule %s" % self)
        #for patterns, conditions, bound_variables\
        #        in self._generate_action_prerequisites():
        from .machine_patterns import generate_action_prerequisites
        q = generate_action_prerequisites(self.machine,
                                          list(self.orig_pattern))
        for patterns, conditions, bound_variables in q:
            if not all(x in bound_variables for x in self.needed_variables):
                notbound = [x for x in self.needed_variables
                            if x not in bound_variables]
                raise VariableNotBoundError(notbound)
            actions = self._generate_action(conditions, self.actions)
            self.machine._make_rule(patterns, actions)

    def set_action(self, action: abc_external | fact,
                   needed_variables: Iterable[Variable]) -> None:
        self.actions.append(action)
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
        #if all(x in bound_variables for x in args if isinstance(x, Variable)):
        cond = self.machine._create_assignment_from_external(op, args)
        yield [], [cond], []
        #    return
        #else:
        #    raise Exception()

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
        return f"rule: {self._orig_pattern}-> {self.actions}"



class _machine_default_externals(_base_durable_machine):
    """Implements all default externals
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__register_externals()
        self.__register_importProfiles()

    def __register_importProfiles(self) -> None:
        self.available_import_profiles[str(entailment["OWL-Direct"])]\
                = import_profileOWLDirect
        self.available_import_profiles[str(entailment["RDF"])]\
                = import_profileRDFSEntailment
        self.available_import_profiles[str(entailment["RDFS"])]\
                = import_profileRDFSEntailment
        self.available_import_profiles[str(entailment["Simple"])]\
                = import_profileSimpleEntailment

    def __register_externals(self) -> None:
        from .default_externals import invert
        def_ext._register_timeExternals(self)
        def_ext._register_plainLiteralExternals(self)
        def_ext._register_stringExternals(self)
        def_ext._register_xmlExternals(self)
        def_ext._register_anyURIExternals(self)
        def_ext._register_booleanExternals(self)
        def_ext._register_actionExternals(self)
        for ext in special_externals._special_externals:
            self.register(**ext)
        def_ext.register_numeric_externals(self)
        def_ext.register_list_externals(self)


class durableMachine(_machine_default_externals, RDFSmachine, OWLmachine):
    pass

