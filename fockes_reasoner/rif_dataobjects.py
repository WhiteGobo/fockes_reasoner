import abc
from .durable_reasoner import machine_facts
import rdflib
import typing as typ
from typing import Union, Iterable, Any, Callable
from .shared import RIF
from rdflib import RDF
from . import durable_reasoner
from .durable_reasoner import machine

class RIFSyntaxError(Exception):
    """The given RIF Document has syntaxerrors"""

class _action_gen(abc.ABC):
    @abc.abstractmethod
    def generate_action(self,
                        machine: durable_reasoner.machine.machine,
                        ) -> Callable[None, None]:
        ...

class rif_document:
    payload: "rif_group"
    def __init__(self, payload: "rif_group") -> None:
        self.payload = payload

    def create_rules(self, machine: durable_reasoner.machine.machine) -> None:
        self.payload.create_rules(machine)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: Any) -> "rif_group":
        payload_node, = infograph.objects(rootnode, RIF.payload)
        payload_type, = infograph.objects(payload_node, RDF.type)
        if payload_type == RIF.Group:
            payload = rif_group.from_rdf(infograph, payload_node)
        else:
            raise NotImplementedError(payload_type)
        return cls(payload)

    def __repr__(self):
        return "Document %s" % repr(self.payload)


class rif_group:
    sentences: tuple[Union["rif_forall"]]
    def __init__(self, sentences: Iterable[Union["rif_forall"]]):
        self.sentences = tuple(sentences)

    def create_rules(self, machine: durable_reasoner.machine.machine) -> None:
        for s in self.sentences:
            s.create_rules(machine)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: Any) -> "rif_group":
        sentences_list_node, = infograph.objects(rootnode, RIF.sentences)
        sentences: list[Union[rif_forall, rif_frame]] = []
        sentences_list = rdflib.collection.Collection(infograph,
                                                      sentences_list_node)
        for sentence_node in sentences_list:
            sentence_type = infograph.value(sentence_node, RDF.type)
            if sentence_type == RIF.Forall:
                next_sentence = rif_forall.from_rdf(infograph, sentence_node)
            elif sentence_type == RIF.Frame:
                next_sentence = rif_frame.from_rdf(infograph, sentence_node)
            elif sentence_type == RIF.Group:
                next_sentence = rif_group.from_rdf(infograph, sentence_node)
            else:
                raise NotImplementedError(sentence_type)
            sentences.append(next_sentence)
        return cls(sentences, **kwargs)

    def __repr__(self):
        return "Group (%s)" % ", ".join(repr(x) for x in self.sentences)


class rif_forall:
    formula: Union["rif_implies"]
    pattern: Union[None]
    def __init__(self, formula, pattern: Union[None] = None):
        self.formula = formula
        self.pattern = pattern

    def is_implication(self):
        """Checks if this is a rule for implication like in RIF-BLD"""
        return False
        self.pattern is None
        isinstance(self.formula, rif_implies)
        isinstance(self.formula.then_, (rif_frame,))
        isinstance(self.formula.if_, (rif_frame,))

    def create_rules(self, machine: durable_reasoner.machine.machine) -> None:
        if self.is_implication():
            raise NotImplementedError()
        elif self.pattern is None and isinstance(self.formula, rif_implies):
            newrule = durable_reasoner.machine.durable_rule(machine)
            patterns = self.formula.if_.add_pattern(newrule)
            actions = self.formula.then_.generate_action(machine)
            machine.make_rule(patterns, actions)
            return
        elif self.pattern is not None:
            raise NotImplementedError()
        else:
            raise NotImplementedError()
            self._create_action(machine)

    def _create_action(self,
                       machine: durable_reasoner.machine.machine,
                       ) -> None:
        if isinstance(self.formula, rif_forall):
            raise NotImplementedError()
        else:
            action = self.formula.generate_action(machine)
        action({rdflib.Variable("X"): rdflib.Literal(3)})
        if self.pattern is not None:
            raise Exception()
            q = self.pattern.generate_pattern(machine)
        else:
            raise NotImplementedError()
            q = None
        machine.make_rule(patterns, actions)
        raise Exception()

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode) -> "rif_forall":
        info = dict(infograph.predicate_objects(rootnode))
        try:
            formula_node = info[RIF.formula]
        except KeyError as err:
            raise RIFSyntaxError() from err
        formula_type = infograph.value(formula_node, RDF.type)
        if formula_type == RIF.Implies:
            formula = rif_implies.from_rdf(infograph, formula_node)
        else:
            raise NotImplementedError(formula_type)
        pattern_node = info.get(RIF.pattern)
        if pattern_node is None:
            return cls(formula)
        else:
            raise NotImplementedError()

    def __repr__(self):
        if pattern is None:
            return "Forall ? (%s)" % self.formula
        else:
            return "Forall ? such that %s (%s)" % (self.pattern, self.formula)


class rif_implies:
    if_: Union["rif_frame"]
    then_: Union["rif_do"]
    def __init__(self, if_: Union["rif_frame"], then_: Union["rif_do"]):
        self.if_ = if_
        self.then_ = then_

    def generate_action(self,
                        machine: durable_reasoner.machine.machine,
                        ) -> Callable[(machine_facts.BINDING,), None]:
        condition = self.if_.generate_condition(machine)
        implicated_action = self.then_.generate_action(machine)
        def act(bindings) -> None:
            if condition(bindings):
                implicated_action(bindings)
        return act

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode) -> "rif_implies":
        info = dict(infograph.predicate_objects(rootnode))
        try:
            if_node = info[RIF["if"]]
            then_node = info[RIF["then"]]
        except KeyError as err:
            raise RIFSyntaxError() from err
        if_type = infograph.value(if_node, RDF.type)
        if if_type == RIF.Frame:
            if_ = rif_frame.from_rdf(infograph, if_node)
        else:
            raise NotImplementedError(if_type)
        then_type = infograph.value(then_node, RDF.type)
        if then_type == RIF.Do:
            then_ = rif_do.from_rdf(infograph, then_node)
        else:
            raise NotImplementedError(then_type)
        return cls(if_, then_)

    def __repr__(self):
        return "If %s Then %s" %(self.if_, self.then_)

class rif_do(_action_gen):
    target: Iterable[Union["rif_assert"]]
    def __init__(self, actions: Iterable[Union["rif_assert"]]):
        self.actions = actions

    def generate_action(self,
                        machine: durable_reasoner.machine.machine,
                        ) -> Callable[None, None]:
        actions = [act.generate_action(machine) for act in self.actions]
        return lambda : [act() for act in actions]

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: "rdflib.term.node",
                 ) -> "rif_do":
        try:
            target_list_node, = infograph.objects(rootnode, RIF.actions)
        except ValueError as err:
            raise Exception("Syntaxerror of RIF document", info) from err
        target_list = rdflib.collection.Collection(infograph, target_list_node)
        actions: Iterable[Union[rif_assert]] = []
        for target_node in target_list:
            target_type = infograph.value(target_node, RDF.type)
            if target_type == RIF.Assert:
                next_target = rif_assert.from_rdf(infograph, target_node)
            else:
                raise NotImplementedError()
            actions.append(next_target)
        return cls(actions)

    def __repr__(self):
        return "Do( %s )" % ", ".join(repr(x) for x in self.actions)

class rif_frame:
    facts: tuple[machine_facts.frame]
    def __init__(self, obj, slots):
        facts = []
        for slotkey, slotvalue in slots:
            facts.append(machine_facts.frame(obj, slotkey, slotvalue))
        self.facts = tuple(facts)

    def add_pattern(self, rule: durable_reasoner.machine.durable_rule) -> None:
        for f in self.facts:
            f.add_pattern(rule)

    def generate_condition(self,
                           machine: durable_reasoner.machine.machine,
                           ) -> Callable[(machine_facts.BINDING,), bool]:
        external_resolution = {}
        def condition(bindings: machine_facts.BINDING) -> bool:
            for f in self.facts:
                if not f.check_for_pattern(machine, bindings,
                                           external_resolution):
                    return False
            return True
        return condition

    def generate_assert_action(self,
                      machine: durable_reasoner.machine.machine,
                      ) -> Callable[(machine_facts.BINDING,), bool]:
        external_resolution = {}
        return lambda bindings: [f.assert_fact(machine, bindings,
                                               external_resolution)
                                 for f in self.facts]

    def create_rules(self, machine: durable_reasoner.machine.machine) -> None:
        raise Exception()

    @property
    def obj(self):
        return self.facts[0].obj

    def __repr__(self) -> str:
        name = type(self).__name__
        def conv(x) -> str:
            if isinstance(x, rdflib.URIRef):
                return "<%s>" % x
            elif isinstance(x, rdflib.Variable):
                return "?%s" % x
            else:
                if x.datatype:
                    return "'%s'^^%s" % (x, x.datatype)
                else:
                    return "'%s'" % x
        slots = ", ".join("%s->%s"%(conv(f.slotkey), conv(f.slotvalue))
                          for f in self.facts)
        return "%s[%s]" % (conv(self.obj), slots)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_frame":
        info = dict(infograph.predicate_objects(rootnode))
        def slot2node(x: "rdflib.term.Node") -> "rdflib.term.Node":
            val_info = dict(infograph.predicate_objects(x, RDF.type))
            t = val_info[RDF.type]
            if t == RIF.Var:
                return rdflib.Variable(val_info[RIF.varname])
            elif t == RIF.Const and RIF.constIRI in val_info:
                return rdflib.URIRef(val_info[RIF.constIRI])
            elif t == RIF.Const and RIF.value in val_info:
                return val_info[RIF.value]
        q = rdflib.collection.Collection(infograph, info[RIF.slots])
        slotinfo = [(slot2node(d[RIF.slotkey]), slot2node(d[RIF.slotvalue]))
                    for d in (dict(infograph.predicate_objects(x)) for x in q)]
        obj = slot2node(info[RIF.object])
        return cls(obj, slotinfo, **kwargs)

class rif_assert:
    fact: Union[rif_frame]
    def __init__(self, fact: Union[rif_frame]):
        self.fact = fact

    def generate_action(self,
                        machine: durable_reasoner.machine.machine,
                        ) -> Callable[None, None]:
        return self.fact.generate_assert_action(machine)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_assert":
        target = infograph.value(rootnode, RIF.target)
        target_type = infograph.value(target, RDF.type)
        if target_type == RIF.Frame:
            fact = rif_frame.from_rdf(infograph, target)
        elif target_type == RIF.Member:
            raise NotImplementedError()
        elif target_type == RIF.Subclass:
            raise NotImplementedError()
        else:
            raise NotImplementedError(target_type)
        return cls(fact, **kwargs)

    def __repr__(self):
        return "Assert( %s )" % self.fact
