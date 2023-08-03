import durable.lang as rls
import abc
import durable.engine
import rdflib
import logging
logger = logging.getLogger(__name__)
from collections.abc import Iterable, Mapping
import typing as typ
from typing import Union
from .durable_reasoner import durable_abc as dur_abc
from .durable_reasoner import durable_dataobjects as dur_obj
from .durable_reasoner.durable_abc import TRANSLATEABLE_TYPES
from .shared import focke, RDF, rdflib2string

from rdflib import Variable, URIRef, BNode, Literal
def _transform_complex(
        graph: rdflib.Graph,
        valuenode: typ.Union[URIRef, BNode, Literal],
        ) -> typ.Union[Variable, URIRef, BNode, Literal]:
    if isinstance(valuenode, rdflib.IdentifiedNode):
        if (valuenode, RDF.type, focke.Variable) in graph:
            varname = graph.value(valuenode, focke.variablename)
            return rdflib.Variable(varname)
    return valuenode

class group(dur_obj.group):
    sentences: tuple[typ.Union["rule", "action", "group"], ...]
    def __init__(self,
                 sentences: Iterable[typ.Union["rule", "action", "group"]],
                 ):
        self.sentences = tuple(sentences)

    def generate_rules(self, ruleset: rls.ruleset,
                       external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], typ.Any] = {},
                       **kwargs: typ.Any) -> None:
        """
        :TODO: This inheritance thingy looks like it is not wanted here
        """
        super().generate_rules(ruleset,
                               external_resolution=external_resolution,
                               **kwargs)

    def __repr__(self) -> str:
        return "%s(%s)" % (type(self).__name__,
                           ", ".join(repr(x) for x in self.sentences))

    @classmethod
    def from_rdf(cls, graph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode) -> "group":
        sentences_id = graph.value(subject=rootnode, predicate=focke.sentences)
        sentences_infolist = rdflib.collection.Collection(graph, sentences_id)
        sentences: list[typ.Union["rule", "action", "group"]] = []
        for x in sentences_infolist:
            if (x, RDF.type, focke.forall) in graph:
                sentences.append(rule.from_rdf(graph, x))
            elif (x, RDF.type, focke.action) in graph:
                sentences.append(action.from_rdf(graph, x))
            elif (x, RDF.type, focke.group) in graph:
                sentences.append(group.from_rdf(graph, x))
            else:
                foundtype = list(graph.objects(x, RDF.type))
                raise NotImplementedError(f"couldnt figure out how to load "
                                          "rule {x} with types {foundtype}")
        return cls(sentences)
        

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

    @classmethod
    def from_rdf(cls, graph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode) -> "action":
        functions_id = graph.value(subject=rootnode, predicate=focke.functions)
        functions_infolist = rdflib.collection.Collection(graph, functions_id)
        functions: list[dur_abc.contextless_function] = []
        for x in functions_infolist:
            if (x, RDF.type, focke.assert_frame) in graph:
                functions.append(assert_frame.from_rdf(graph, x))
            else:
                foundtype = list(graph.objects(x, RDF.type))
                raise NotImplementedError(f"couldnt figure out how to load "
                                          "rule {x} with types {foundtype}")
        return cls(functions)

class create_new(dur_abc.function):
    variable: rdflib.Variable
    """Variable that will be bound to a new node"""
    def __init__(self, variable: rdflib.Variable):
        self.variable = variable

    def __call__(self, c: durable.engine.Closure,
                 bindings: dur_abc.BINDING = {},
                 external_resolution: typ.Any = {}) -> None:
        bindings[self.variable] = rdflib2string(rdflib.BNode())

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

    @classmethod
    def from_rdf(cls, graph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode) -> "rule":
        patterns_id = graph.value(subject=rootnode, predicate=focke.patterns)
        patterns_infolist = rdflib.collection.Collection(graph, patterns_id)
        patterns = []
        for x in patterns_infolist:
            if (x, RDF.type, focke.frame_pattern) in graph:
                patterns.append(frame_pattern.from_rdf(graph, x))
            else:
                foundtype = list(graph.objects(x, RDF.type))
                raise NotImplementedError("couldnt figure out how to load "
                                          f"rule {x} with types {foundtype}")
        functions_id = graph.value(subject=rootnode, predicate=focke.functions)
        functions_infolist = rdflib.collection.Collection(graph, functions_id)
        functions = []
        for x in functions_infolist:
            if (x, RDF.type, focke.assert_frame) in graph:
                functions.append(assert_frame.from_rdf(graph, x))
            else:
                foundtype = list(graph.objects(x, RDF.type))
                raise NotImplementedError("couldnt figure out how to load "
                                          f"rule {x} with types {foundtype}")
        return cls(patterns, functions)

class frame_pattern(dur_obj.frame_pattern):
    def __init__(self, obj: TRANSLATEABLE_TYPES, slotkey: TRANSLATEABLE_TYPES,
                 slotvalue: TRANSLATEABLE_TYPES):
        self.obj = obj
        self.slotkey = slotkey
        self.slotvalue = slotvalue

    def __repr__(self) -> str:
        return f"%s({self.obj}[{self.slotkey}->{self.slotvalue}])"\
                % type(self).__name__

    @classmethod
    def from_rdf(cls, graph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode) -> "frame_pattern":
        obj = _transform_complex(graph,\
                graph.value(rootnode, focke.object))
        slotkey = _transform_complex(graph,\
                graph.value(rootnode, focke.slotkey))
        slotvalue = _transform_complex(graph,\
                graph.value(rootnode, focke.slotvalue))
        return cls(obj, slotkey, slotvalue)


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

class external(dur_obj.external):
    def __init__(self, const: typ.Union[rdflib.URIRef, rdflib.BNode],
                 terms: Iterable[Union[TRANSLATEABLE_TYPES, dur_obj.external]]):
        self.const = const
        self.terms = tuple(terms)

    def __repr__(self) -> str:
        return "%s:%r%r" % (type(self).__name__, self.const, self.terms)

class execute(dur_obj.execute):
    def __init__(self, op: typ.Union[rdflib.URIRef, rdflib.BNode],
                 args: Iterable[Union[TRANSLATEABLE_TYPES, dur_obj.external]]):
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


    @classmethod
    def from_rdf(cls, graph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode) -> "assert_frame":

        obj = _transform_complex(graph,\
                graph.value(rootnode, focke.object))
        slotkey = _transform_complex(graph,\
                graph.value(rootnode, focke.slotkey))
        slotvalue = _transform_complex(graph,\
                graph.value(rootnode, focke.slotvalue))
        return cls(obj, slotkey, slotvalue)


class assert_member(dur_obj.assert_member):
    ...

class assert_subclass(dur_obj.assert_subclass):
    ...

class assert_external(dur_obj.assert_external):
    ...
