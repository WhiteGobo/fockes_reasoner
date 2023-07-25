import durable.lang as rls
import abc
import durable.engine
import rdflib
from collections.abc import Iterable, Mapping
import typing as typ
from .durable_reasoner import durable_abc as dur_abc
from .durable_reasoner import durable_dataobjects as dur_obj
from .durable_reasoner.durable_abc import TRANSLATEABLE_TYPES

class group(dur_obj.group):
    sentences: tuple[typ.Union["rule", "action", "group"], ...]
    def __init__(self,
                 sentences: Iterable[typ.Union["rule", "action", "group"]],
                 ):
        self.sentences = tuple(sentences)

    def generate_rules(self, ruleset: rls.ruleset,
                       external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], typ.Any] = {},
                       **kwargs: typ.Any) -> None:
        super().generate_rules(ruleset,
                               external_resolution=external_resolution,
                               **kwargs)

    def __repr__(self) -> str:
        return "%s(%s)" % (type(self).__name__,
                           ", ".join(repr(x) for x in self.sentences))

class external_function(dur_abc.contextless_function):
    @abc.abstractmethod
    def __call__(self, c: typ.Union[durable.engine.Closure, str],
                 bindings: dur_abc.BINDING = {},
                 external_resolution: typ.Mapping[rdflib.URIRef, typ.Callable]={}) -> None:
        ...


class action(dur_obj.action):
    functions: tuple[dur_abc.contextless_function, ...]

    def __init__(self,
                 functions: Iterable[dur_abc.contextless_function]):
        self.functions = tuple(functions)

    def generate_rule(self, ruleset: rls.ruleset,
                      external_resolution: typ.Mapping[rdflib.URIRef, typ.Callable] = {},
                      **kwargs: typ.Any) -> None:
        super().generate_rule(ruleset, external_resolution=external_resolution)

    def __repr__(self) -> str:
        return f"%s:->{self.functions}" % type(self).__name__

class rule(dur_obj.forall):
    patterns: tuple[dur_abc.pattern, ...]
    functions: tuple[dur_abc.function, ...]

    def __init__(self,
                 patterns: Iterable[dur_abc.pattern],
                 functions: Iterable[dur_abc.function]):
        self.patterns = tuple(patterns)
        self.functions = tuple(functions)

    def generate_rule(self, ruleset: rls.ruleset,
                      external_resolution: typ.Any = None,
                      **kwargs: typ.Any) -> None:
        super().generate_rule(ruleset, external_resolution=external_resolution,
                              **kwargs)

    def __repr__(self) -> str:
        return f"%s:{self.patterns}->{self.functions}" % type(self).__name__

class frame_pattern(dur_obj.frame_pattern):
    def __init__(self, obj: TRANSLATEABLE_TYPES, slotkey: TRANSLATEABLE_TYPES,
                 slotvalue: TRANSLATEABLE_TYPES):
        self.obj = obj
        self.slotkey = slotkey
        self.slotvalue = slotvalue

    def __repr__(self) -> str:
        return f"%s({self.obj}[{self.slotkey}->{self.slotvalue}])"\
                % type(self).__name__

class member_pattern(dur_obj.member_pattern):
    ...

class subclass_pattern(dur_obj.subclass_pattern):
    ...


class external_pattern(dur_obj.external_pattern):
    ...


class frame_condition(dur_obj.frame_condition):
    ...


class member_condition(dur_obj.member_condition):
    ...


class subclass_condition(dur_obj.subclass_condition):
    ...


class external_condition(dur_obj.external_condition):
    ...


class execute(dur_obj.execute):
    def __init__(self, op: typ.Union[rdflib.URIRef, rdflib.BNode],
                 args: Iterable[TRANSLATEABLE_TYPES]):
        self.op = op
        self.args = tuple(args)

    def __repr__(self) -> str:
        return "%s:%r%r" % (type(self).__name__, self.op, self.args)


class assert_frame(dur_obj.assert_frame):
    def __init__(self, obj: TRANSLATEABLE_TYPES, slotkey: TRANSLATEABLE_TYPES,
                 slotvalue: TRANSLATEABLE_TYPES):
        self.obj = obj
        self.slotkey = slotkey
        self.slotvalue = slotvalue

    def __call__(self, c: typ.Union[durable.engine.Closure, str],
                 bindings: dur_abc.BINDING = {},
                 external_resolution: typ.Any = {}) -> None:
        """
        :TODO: Remove this and make a functioning solution with typecontrol
        """
        super().__call__(c, bindings=bindings)

    def __repr__(self) -> str:
        return f"%s({self.obj}[{self.slotkey}->{self.slotvalue}])"\
                % type(self).__name__

class assert_member(dur_obj.assert_member):
    ...

class assert_subclass(dur_obj.assert_subclass):
    ...

class assert_external(dur_obj.assert_external):
    ...
