import abc
import typing as typ
from collections.abc import Iterable, Callable, Mapping
import rdflib
import logging
logger = logging.getLogger(__name__)
import durable.lang as rls
import durable.engine
from . import durable_abc as dur_abc
from .durable_abc import TRANSLATEABLE_TYPES
from ..shared import rdflib2string, string2rdflib

class value_locator:
    factname: str
    """Name of the fact, where the variable is defined"""
    in_fact_label: str
    """Position in fact, where the variable is defined"""
    def __init__(self, factname: str, in_fact_label: str):
        self.factname = factname
        self.in_fact_label = in_fact_label

    def __call__(self,
                 c: typ.Union[durable.engine.Closure, rls.closure],
                 ) -> typ.Union[dur_abc.TRANSLATEABLE_TYPES, rls.value]:
        fact = getattr(c, self.factname)
        return getattr(fact, self.in_fact_label)

    def __repr__(self) -> str:
        return f"%s(c.{self.factname}.{self.in_fact_label})"\
                % type(self).__name__

class rule_generator(dur_abc.rule, abc.ABC):
    @abc.abstractmethod
    def generate_rule(self, ruleset: rls.ruleset) -> None:
        ...

class group(dur_abc.group):
    sentences: Iterable[typ.Union[rule_generator, "group"]]
    def generate_rules(self, ruleset: rls.ruleset, **kwargs: typ.Any) -> None:
        logger.debug("kwargs %r" %kwargs)
        for s in self.sentences:
            if isinstance(s, group):
                s.generate_rules(ruleset, **kwargs)
            else:
                logger.debug("generate rules for: %r" % s)
                s.generate_rule(ruleset, **kwargs)
                self._check_for_errors(ruleset)

    def _check_for_errors(self, ruleset: rls.ruleset) -> None:
        pass

class action(rule_generator, dur_abc.action):
    functions: Iterable[dur_abc.contextless_function]
    def generate_rule(self, ruleset: rls.ruleset, **kwargs: typ.Any) -> None:
        for func in self.functions:
            func(ruleset.name, **kwargs)

class forall(rule_generator, dur_abc.rule):
    _closure_bindings: dur_abc.CLOSURE_BINDINGS
    def generate_rule(self, ruleset: rls.ruleset, **kwargs: typ.Any) -> None:
        logger.debug("Using additional resources %r" % (kwargs))
        self._closure_bindings = {}
        patterns: rls.value\
                = [p._generate_durable_pattern(self._closure_bindings, f"f{i}")
                   for i, p in enumerate(self.patterns)]
        assert patterns
        with ruleset:
            @rls.when_all(*patterns)
            def myfunction(c: durable.engine.Closure) -> None:
                bindings: dur_abc.BINDING = self._generate_bindings(c)
                for func in self.functions:
                    func(c, bindings, **kwargs)

    def _generate_bindings(self, c:durable.engine.Closure) -> dur_abc.BINDING:
        return {v: loc(c) for v, loc in self._closure_bindings.items()}

class _mixin_pattern:
    def _add_pattern(self, bindings: dur_abc.CLOSURE_BINDINGS,
                     factname: str, log: list,
                     fact_label: str, value: dur_abc.TRANSLATEABLE_TYPES) -> rls.value:
        if isinstance(value, rdflib.Variable):
            if value in bindings:
                loc = bindings[value]
                log.append(f"rls.m.{fact_label} == {loc}")
                pattern = getattr(rls.m, fact_label) == loc(rls.c)
            else:
                loc = value_locator(factname, fact_label)
                bindings[value] = loc
                logger.debug("bind: %r-> %r" % (value, loc))
        else:
            fact_value: str = rdflib2string(value)
            log.append(f"rls.m.{fact_label} == %r" % fact_value)
            pattern = getattr(rls.m, fact_label) == fact_value
        return pattern

class frame_pattern(dur_abc.frame_pattern):
    def _generate_durable_pattern(self, bindings: dur_abc.CLOSURE_BINDINGS,
                                  factname: str) -> rls.value:
        """Used to generate a pattern for when_all method of durable"""
        log = [f"rls.m.{dur_abc.FACTTYPE} == {self.fact_type}"]
        pattern = (getattr(rls.m, dur_abc.FACTTYPE) == self.fact_type)
        for fact_label, value in [
                (self.label_obj, self.obj),
                (self.label_slotkey, self.slotkey),
                (self.label_slotvalue, self.slotvalue),
                ]:
            if isinstance(value, rdflib.Variable):
                if value in bindings:
                    loc = bindings[value]
                    log.append(f"rls.m.{fact_label} == {loc}")
                    newpattern = getattr(rls.m, fact_label) == loc(rls.c)
                    pattern = pattern & newpattern
                else:
                    loc = value_locator(factname, fact_label)
                    bindings[value] = loc
                    logger.debug("bind: %r-> %r" % (value, loc))
            else:
                fact_value: str = rdflib2string(value)
                log.append(f"rls.m.{fact_label} == %r" % fact_value)
                newpattern = getattr(rls.m, fact_label) == fact_value
                pattern = pattern & newpattern
        logger.debug(f"{factname} << %s" % " & ".join(log))
        return getattr(rls.c, factname) << pattern

class member_pattern(dur_abc.Member_pattern):
    ...

class subclass_pattern(dur_abc.Subclass_pattern):
    ...

class external_pattern(dur_abc.External_pattern):
    ...

class frame_condition(dur_abc.frame_condition):
    ...

class member_condition(dur_abc.member_condition):
    ...

class subclass_condition(dur_abc.subclass_condition):
    ...

class external_condition(dur_abc.external_condition):
    ...

#EXTERNAL_CALL = Callable[[Iterable[TRANSLATEABLE_TYPES]],
EXTERNAL_CALL = Callable[...,
                         typ.Union[None, TRANSLATEABLE_TYPES, bool]]

class execute(dur_abc.execute):
    op: typ.Union[rdflib.URIRef, rdflib.BNode]
    args: tuple[TRANSLATEABLE_TYPES, ...]

    def __call__(self, c: typ.Union[durable.engine.Closure, str],
                 bindings: dur_abc.BINDING = {},
                 external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], EXTERNAL_CALL] = {},
                 ) -> typ.Union[None, TRANSLATEABLE_TYPES, bool]:
        try:
            func = external_resolution[self.op]
        except KeyError as err:
            raise KeyError("Tried to call not provided external function: %r" % self.op) from err
        return func(bindings, self.args)

class assert_frame(dur_abc.assert_frame):
    def __call__(self, c: typ.Union[durable.engine.Closure, str],
                 bindings: dur_abc.BINDING = {}) -> None:
        fact = {"type":self.fact_type}
        for label, x, in [
                (self.label_obj, self.obj),
                (self.label_slotkey, self.slotkey),
                (self.label_slotvalue, self.slotvalue),
                ]:
            if isinstance(x, rdflib.Variable):
                fact[label] = bindings[x]
            else:
                fact[label] = rdflib2string(x)
        if isinstance(c, str):
            rls.assert_fact(c, fact)
        else:
            c.assert_fact(fact)

class assert_member(dur_abc.assert_member):
    ...

class assert_subclass(dur_abc.assert_subclass):
    ...

class assert_external(dur_abc.assert_external):
    ...
