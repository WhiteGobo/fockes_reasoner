from typing import Union, Optional, Tuple, Callable, List, Set, Hashable, overload, Dict
from collections.abc import Mapping, MutableMapping, Iterable, Container
from rdflib import  Variable, URIRef, BNode, Literal, IdentifiedNode
from hashlib import sha1
import durable.lang as rls
import durable.engine
from . import abc_machine
from .abc_machine import abc_pattern, TRANSLATEABLE_TYPES, VARIABLE_LOCATOR, FACTTYPE, BINDING, abc_external, ATOM_ARGS, NoPossibleExternal, VariableNotBoundError, EXTERNAL_ARG, RESOLVABLE
from .bridge_rdflib import rdflib2string, _term_list
from .machine_facts import frame, member, subclass, atom, fact, external, rdflib2string, _node2string, string2rdflib
import logging
logger = logging.getLogger(__name__)
import traceback

MACHINESTATE = "machinestate"
RUNNING_STATE = "running"
INIT_STATE = "init"

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
    def from_fact(cls, factid: str, myfact: Mapping[str, str |TRANSLATEABLE_TYPES| abc_external| Variable],
                  name: Optional[str] = None,
                  ) -> "_pattern":
        d: Dict[str, Union[Variable, str, TRANSLATEABLE_TYPES]]\
                = {FACTTYPE: factid}
        for key, value in myfact.items():
            assert isinstance(value, (Variable, str, BNode, URIRef, _term_list))
            d[key] = value
        if name is not None:
            return cls(d, name)
        else:
            return cls(d)

    def generate_rls(self,
                     bindings: MutableMapping[Variable, VARIABLE_LOCATOR],
                     ) -> rls.value:
        next_constraint: rls.value
        constraint: Union[rls.value, None] = None
        for key, value in self.pattern.items():
            next_constraint = None
            if type(value) == str:
                next_constraint = getattr(rls.m, key) == value
            elif isinstance(value, Variable):
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


def generate_action_prerequisites(
        machine: abc_machine.Machine,
        p: Iterable[Union[fact, abc_external]],
        ) -> Iterable[Tuple[Iterable[abc_pattern],
                            Iterable[Callable[[BINDING], Literal]],
                            Iterable[Variable]]]:
    #p: List[Union[fact, abc_external]] = list(self.orig_pattern)
    conditions: List[Callable[[BINDING], Literal]]
    patterns: List[abc_pattern]
    bound_variables: Set[Variable]
    try:
        for patterns_, conditions, bound_variables in _generate_action_prerequisites_inner(machine, p, [], [], set()):
            if len(patterns_) == 0 and len(conditions) == 0:
                #create rule as initialisation rule
                patterns = [_pattern({MACHINESTATE: INIT_STATE}), *patterns_]
                #patterns.insert(0, _pattern({MACHINESTATE: INIT_STATE}))
            elif len(patterns_) > 0:
                patterns = [_pattern({MACHINESTATE: RUNNING_STATE}),
                            *patterns_]
                #patterns.insert(0, _pattern({MACHINESTATE: RUNNING_STATE}))
            else:
                #TODO : This rule lacks any trigger. 
                patterns = [_pattern({MACHINESTATE: RUNNING_STATE})]
                #patterns.insert(0, _pattern({MACHINESTATE: RUNNING_STATE}))
            yield patterns, conditions, bound_variables
    except VariableNotBoundError:
        raise

def _generate_action_prerequisites_inner(
        machine: abc_machine.Machine,
        pattern_parts: Iterable[Union[fact, abc_external]],
        patterns: list[abc_pattern],
        conditions: List[Callable[[BINDING], Literal]],
        bound_variables: Set[Variable],
        ) -> Iterable[Tuple[List[abc_pattern],
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
                    in _process_external_as_pattern(machine, q.op, q.args,
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
                next_gen = _generate_action_prerequisites_inner(
                        machine,
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

def _process_external_as_pattern(
        machine: abc_machine.Machine,
        op: Hashable,
        args: Iterable[EXTERNAL_ARG],
        bound_variables: Container[Variable] = {},
        ) -> Iterable[Tuple[Iterable[abc_pattern],
                   Iterable[Callable[[BINDING], Literal]],
                   Iterable[Variable]]]:
    """
    :TODO: resolve this method into surrounding. Seems overkill
    """
    new_bound_vars: Iterable[Variable]
    try:
        for patterns, conditions, new_bound_vars\
                in machine._create_pattern_from_external(
                        op, args, bound_variables):
            yield patterns, conditions, new_bound_vars
        return
    except NoPossibleExternal:
        pass
    try:
        yield machine._create_binding_from_external(op, args,
                                                         bound_variables)
        return
    except NoPossibleExternal:
        pass
    cond = machine._create_assignment_from_external(op, args)
    yield [], [cond], []
