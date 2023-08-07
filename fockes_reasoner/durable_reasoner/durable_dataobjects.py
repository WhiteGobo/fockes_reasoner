import abc
import typing as typ
from collections.abc import Iterable, Callable, Mapping
import rdflib
from rdflib import URIRef, BNode, Literal, Variable
import logging
logger = logging.getLogger(__name__)
import durable.lang as rls
import durable.engine
from . import durable_abc as dur_abc
from .durable_abc import TRANSLATEABLE_TYPES
from ..shared import rdflib2string, string2rdflib
import traceback

#EXTERNAL_CALL = Callable[[Iterable[TRANSLATEABLE_TYPES]],
EXTERNAL = Callable[[dur_abc.BINDING, Iterable[TRANSLATEABLE_TYPES]], TRANSLATEABLE_TYPES]
EXTERNAL_CALL = Callable[[dur_abc.BINDING, Iterable[TRANSLATEABLE_TYPES]], None]

class FailedAction(Exception):
    """Exception thrown within the machine, when an action fails."""
    def __init__(self, func, *args):
        super().__init__("Failed at action. See logging for more "
                         "details. Function: %r" % func, *args)

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
    """is equal to focke:group
    """
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

class implies(dur_abc.implies):
    condition: dur_abc.external
    functions: tuple[dur_abc.function, ...]

    def __init__(self,
                 condition: dur_abc.external,
                 functions: Iterable[dur_abc.function]):
        self.condition = condition
        self.functions = tuple(functions)

    def __call__(self, c: typ.Union[durable.engine.Closure, str],
                 bindings: dur_abc.BINDING = {},
                 external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], EXTERNAL] = {},
                 ) -> None:
        if self.condition(c, bindings, external_resolution):
            for act in self.functions:
                act(c, bindings, external_resolution)

    def __repr__(self) -> str:
        return f"%s:{self.condition}->{self.functions}" % type(self).__name__


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
            @rls.when_all(rls.m.machinestate == "running",
                          *patterns)
            def myfunction(c: durable.engine.Closure) -> None:
                bindings: dur_abc.BINDING = self._generate_bindings(c)
                logger.critical("starting function for %r" % self)
                for func in self.functions:
                    try:
                        logger.critical("act %r" % func)
                        func(c, bindings, **kwargs)
                    except FailedAction:
                        raise
                    except Exception as err:
                        logger.critical(f"Failure in rule {self}\nFailed at "
                                        "func %r with message:\n%s"
                                        % (func, traceback.format_exc()))
                        raise FailedAction(func) from err

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

class external(dur_abc.external):
    const: typ.Union[rdflib.URIRef, rdflib.BNode]
    terms: tuple[typ.Union[TRANSLATEABLE_TYPES, "external"], ...]

    def __call__(self, c: typ.Union[durable.engine.Closure, str],
                 bindings: dur_abc.BINDING = {},
                 external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], EXTERNAL] = {},
                 ) -> TRANSLATEABLE_TYPES:
        try:
            func = external_resolution[self.const]
        except KeyError as err:
            raise KeyError("Tried to call not provided external function: %r" % self.const, external_resolution.keys()) from err
        args: list[TRANSLATEABLE_TYPES] = []
        for x in self.terms:
            if isinstance(x, (URIRef, BNode, Literal, Variable)):
                args.append(x)
            else:
                args.append(x(c, bindings, external_resolution))
        return func(bindings, args)


class execute(dur_abc.execute):
    op: typ.Union[rdflib.URIRef, rdflib.BNode]
    args: tuple[typ.Union[TRANSLATEABLE_TYPES, external], ...]

    def __call__(self, c: typ.Union[durable.engine.Closure, str],
                 bindings: dur_abc.BINDING = {},
                 external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], EXTERNAL] = {},
                 ) -> None:
        try:
            func = external_resolution[self.op]
        except KeyError as err:
            raise KeyError("Tried to call not provided external function: %r" % self.op) from err
        args: list[TRANSLATEABLE_TYPES] = []
        for x in self.args:
            if isinstance(x, (URIRef, BNode, Literal, Variable)):
                args.append(x)
            else:
                args.append(x(c, bindings, external_resolution))
        func(bindings, args)


class bind(dur_abc.bind):
    var: rdflib.Variable
    target: typ.Union[TRANSLATEABLE_TYPES, external]

    def __call__(self, c: typ.Union[durable.engine.Closure, str],
                 bindings: dur_abc.BINDING = {},
                 external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], EXTERNAL] = {},
                 ) -> None:
        if isinstance(self.target, Variable):
            bindings[self.var] = bindings[self.target]
        elif isinstance(self.target, (URIRef, BNode, Literal)):
            bindings[self.var] = rdflib2string(self.target)
        else:
            bindings[self.var] = rdflib2string(self.target(c, bindings, external_resolution))

class modify_frame(dur_abc.modify_frame):
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
            elif isinstance(x, (URIRef, BNode, Literal)):
                fact[label] = rdflib2string(x)
            else:
                newnode = x(c, bindings, external_resolution)
                fact[label] = rdflib2string(newnode)
        def retract_first_frame(facts):
            """Get first frame with given obj and slotkey"""
            for f in facts:
                try:
                    if f[self.label_obj] == self.obj\
                            and f[self.label_slotkey] == self.slotkey:
                        return f
                except KeyError:
                    pass
            return None
        if isinstance(c, str):
            f = retract_first_frame(rls.get_facts(c))
            if f is not None:
                rls.retract_fact(c, f)
            rls.assert_fact(c, fact)
        else:
            f = retract_first_frame(c.get_facts())
            if f is not None:
                c.retract_fact(f)
            c.assert_fact(fact)

class assert_frame(dur_abc.assert_frame):
    def __call__(self, c: typ.Union[durable.engine.Closure, str],
                 bindings: dur_abc.BINDING = {},
                 external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], EXTERNAL] = {},
                 ) -> None:
        fact = {"type":self.fact_type}
        for label, x, in [
                (self.label_obj, self.obj),
                (self.label_slotkey, self.slotkey),
                (self.label_slotvalue, self.slotvalue),
                ]:
            if isinstance(x, rdflib.Variable):
                fact[label] = bindings[x]
            elif isinstance(x, (URIRef, BNode, Literal)):
                fact[label] = rdflib2string(x)
            else:
                newnode = x(c, bindings, external_resolution)
                fact[label] = rdflib2string(newnode)
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
