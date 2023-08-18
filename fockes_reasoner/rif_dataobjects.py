import abc
import logging
logger = logging.getLogger(__name__)
from .durable_reasoner import machine_facts, fact
from .durable_reasoner.machine_facts import external, TRANSLATEABLE_TYPES
import rdflib
from rdflib import IdentifiedNode, Graph, Variable, Literal
import typing as typ
from typing import Union, Iterable, Any, Callable, MutableMapping, List, Tuple, Optional
from .shared import RIF
from rdflib import RDF
from . import durable_reasoner
from .durable_reasoner import machine
from .durable_reasoner import BINDING

ATOM = typ.Union[TRANSLATEABLE_TYPES, external, Variable]
SLOT = Tuple[ATOM, ATOM]

class RIFSyntaxError(Exception):
    """The given RIF Document has syntaxerrors"""

class _action_gen(abc.ABC):
    @abc.abstractmethod
    def generate_action(self,
                        machine: durable_reasoner.machine.durable_machine,
                        ) -> Callable[..., None]:
        ...


def slot2node(infograph: Graph, x: IdentifiedNode) -> ATOM:
    """Transform
    """
    val_info = dict(infograph.predicate_objects(x))
    t = val_info[RDF.type]
    if t == RIF.Var:
        return rdflib.Variable(str(val_info[RIF.varname]))
    elif t == RIF.Const and RIF.constIRI in val_info:
        return rdflib.URIRef(str(val_info[RIF.constIRI]))
    elif t == RIF.Const and RIF.value in val_info:
        val: Literal = val_info[RIF.value]#type: ignore[assignment]
        return val
    elif t == RIF.External:
        return rif_external.from_rdf(infograph, x)
    else:
        raise NotImplementedError(t)

class rif_document:
    payload: "rif_group"
    def __init__(self, payload: "rif_group") -> None:
        self.payload = payload

    def create_rules(self, machine: durable_reasoner.machine.durable_machine) -> None:
        self.payload.create_rules(machine)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: Any) -> "rif_document":
        payload_node: IdentifiedNode
        payload_node, = infograph.objects(rootnode, RIF.payload) #type: ignore[assignment]
        payload_type, = infograph.objects(payload_node, RDF.type)
        if payload_type == RIF.Group:
            payload = rif_group.from_rdf(infograph, payload_node)
        else:
            raise NotImplementedError(payload_type)
        return cls(payload)

    def __repr__(self) -> str:
        return "Document %s" % repr(self.payload)


class rif_group:
    sentences: tuple[Union["rif_forall", "rif_frame", "rif_group"], ...]
    def __init__(self,
                 sentences: Iterable[Union["rif_forall", "rif_frame", "rif_group"]],
                 ) -> None:
        self.sentences = tuple(sentences)

    def create_rules(self, machine: durable_reasoner.machine.durable_machine) -> None:
        for s in self.sentences:
            s.create_rules(machine)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: Any) -> "rif_group":
        sentences_list_node, = infograph.objects(rootnode, RIF.sentences)
        sentences: list[Union[rif_forall, rif_frame, rif_group]] = []
        next_sentence: Union[rif_forall, rif_frame, rif_group]
        sentences_list: Iterable[IdentifiedNode]\
                = rdflib.collection.Collection(infograph, sentences_list_node) #type: ignore[assignment]
        for sentence_node in sentences_list:
            sentence_type = infograph.value(sentence_node, RDF.type)
            if sentence_type == RIF.Forall:
                next_sentence = rif_forall.from_rdf(infograph, sentence_node)
            elif sentence_type == RIF.Frame:
                next_sentence = rif_frame.from_rdf(infograph, sentence_node)
            elif sentence_type == RIF.Group:
                next_sentence = rif_group.from_rdf(infograph, sentence_node)
            elif sentence_type == RIF.Implies:
                next_sentence = rif_implies.from_rdf(infograph, sentence_node)
            else:
                raise NotImplementedError(sentence_type)
            sentences.append(next_sentence)
        return cls(sentences, **kwargs)

    def __repr__(self) -> str:
        return "Group (%s)" % ", ".join(repr(x) for x in self.sentences)


class rif_forall:
    formula: Union["rif_implies"]
    pattern: Union[None]
    def __init__(self, formula: Union["rif_implies"],
                 pattern: Union[None] = None) -> None:
        self.formula = formula
        self.pattern = pattern

    def is_implication(self) -> bool:
        """Checks if this is a rule for implication like in RIF-BLD"""
        return False
        self.pattern is None
        isinstance(self.formula, rif_implies)
        isinstance(self.formula.then_, (rif_frame,))
        isinstance(self.formula.if_, (rif_frame,))

    def create_rules(self, machine: durable_reasoner.machine.durable_machine) -> None:
        if self.is_implication():
            raise NotImplementedError()
        elif self.pattern is None and isinstance(self.formula, rif_implies):
            newrule = machine.create_rule_builder()
            conditions = []
            if isinstance(self.formula.if_, rif_and):
                for pat in self.formula.if_.formulas:
                    try:
                        pat.add_pattern(newrule)
                    except Exception:
                        raise
                        conditions.append(pat.generate_condition(machine))
            else:
                self.formula.if_.add_pattern(newrule)
            if len(conditions) == 0:
                action = self.formula.then_.generate_action(machine)
            else:
                raise NotImplementedError()
            newrule.action = action
            logger.info("create rule %r" % newrule)
            newrule.finalize()
            return
        elif self.pattern is not None:
            raise NotImplementedError()
        else:
            raise NotImplementedError()
            self._create_action(machine)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: IdentifiedNode) -> "rif_forall":
        formula_node: IdentifiedNode
        info = dict(infograph.predicate_objects(rootnode))
        try:
            formula_node = info[RIF.formula] #type: ignore[assignment]
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

    def __repr__(self) -> str:
        if self.pattern is None:
            return "Forall ? (%s)" % self.formula
        else:
            return "Forall ? such that %s (%s)" % (self.pattern, self.formula)


class rif_implies:
    if_: Union["rif_frame"]
    then_: Union["rif_do"]
    def __init__(self, if_: Union["rif_frame"], then_: Union["rif_do"]):
        self.if_ = if_
        self.then_ = then_

    def create_rules(self, machine: durable_reasoner.machine.durable_machine) -> None:
        logger.critical("Implications are not yet supported")
        return
        raise NotImplementedError()
        newrule = machine.create_rule_builder()
        self.formula.if_.add_pattern(newrule)
        action = self.formula.then_.generate_action(machine)
        newrule.action = action
        newrule.finalize()

    def generate_action(self,
                        machine: durable_reasoner.machine.durable_machine,
                        ) -> Callable[[BINDING], None]:
        condition = self.if_.generate_condition(machine)
        implicated_action = self.then_.generate_action(machine)
        def act(bindings: BINDING) -> None:
            if condition(bindings):
                implicated_action(bindings)
        return act

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 model = None,
                 ) -> "rif_implies":
        if model is None: #please remove later
            from .class_rdfmodel import rdfmodel
            model = rdfmodel()
        if_node: IdentifiedNode
        then_node: IdentifiedNode
        info = dict(infograph.predicate_objects(rootnode))
        try:
            if_node = info[RIF["if"]] #type: ignore[assignment]
            then_node = info[RIF["then"]] #type: ignore[assignment]
        except KeyError as err:
            raise RIFSyntaxError() from err
        if_ = model.generate_object(infograph, if_node)
        then_ = model.generate_object(infograph, then_node)
        return cls(if_, then_)

    def __repr__(self) -> str:
        return "If %s Then %s" %(self.if_, self.then_)

class rif_and:
    formulas: Iterable[Union["rif_frame"]]
    def __init__(self, formulas: Iterable[Union["rif_frame"]]):
        self.formulas = list(formulas)

    def add_pattern(self, rule: durable_reasoner.machine.durable_rule) -> None:
        for form in self.formulas:
            form.add_pattern(rule)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: IdentifiedNode,
                 model = None,
                 ) -> "rif_do":
        if model is None: #please remove later
            from .class_rdfmodel import rdfmodel
            model = rdfmodel()
        try:
            formula_list_node, = infograph.objects(rootnode, RIF.formulas)
        except ValueError as err:
            raise Exception("Syntaxerror of RIF document") from err
        formula_list: Iterable[IdentifiedNode] = rdflib.collection.Collection(infograph, formula_list_node) #type: ignore[assignment]
        formulas: List[Union[rif_assert]] = []
        for formula_node in formula_list:
            next_formula = model.generate_object(infograph, formula_node)
            #assert isinstance(next_formula, (rif_assert, rif_retract, rif_modify)), "got unexpected rif object. Invalid RIF document?"
            formulas.append(next_formula)
        return cls(formulas)

class rif_do(_action_gen):
    target: List[Union["rif_assert", "rif_retract"]]
    def __init__(self, actions: Iterable[Union["rif_assert", "rif_retract"]]):
        self.actions = list(actions)

    def generate_action(self,
                        machine: durable_reasoner.machine.durable_machine,
                        ) -> Callable[[BINDING], None]:
        self._all_actions = [act.generate_action(machine) for act in self.actions]
        return self._act

    def _act(self, bindings: BINDING) -> None:
        for act in self._all_actions:
            try:
                act(bindings)
            except Exception:
                logger.info("Failed at: %s" % act)
                raise

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: IdentifiedNode,
                 model = None,
                 ) -> "rif_do":
        if model is None: #please remove later
            from .class_rdfmodel import rdfmodel
            model = rdfmodel()
        try:
            target_list_node, = infograph.objects(rootnode, RIF.actions)
        except ValueError as err:
            raise Exception("Syntaxerror of RIF document") from err
        target_list: Iterable[IdentifiedNode] = rdflib.collection.Collection(infograph, target_list_node) #type: ignore[assignment]
        actions: List[Union[rif_assert]] = []
        for target_node in target_list:
            next_target = model.generate_object(infograph, target_node)
            assert isinstance(next_target, (rif_assert, rif_retract, rif_modify)), "got unexpected rif object. Invalid RIF document?"
            actions.append(next_target)
        return cls(actions)

    def __repr__(self) -> str:
        return "Do( %s )" % ", ".join(repr(x) for x in self.actions)

class rif_external:
    op: ATOM
    args: Iterable[ATOM]
    def __init__(self, op: ATOM, args: Iterable[ATOM]):
        self.op = op
        self.args = list(args)

    def generate_condition(self,
                           machine: durable_reasoner.machine.durable_machine,
                           ) -> Callable[[BINDING], bool]:
        raise NotImplementedError()

    def add_pattern(self, rule: durable_reasoner.machine.durable_rule) -> None:
        if not isinstance(self.op, rdflib.term.Node) and all(isinstance(x, rdflib.term.Node) for x in self.args):
            raise NotImplementedError("Currently only basic atoms are supported", self.op)
        m = external(self.op, self.args)
        m.add_pattern(rule)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 model = None,
                 **kwargs: typ.Any) -> "rif_retract":
        if model is None: #please remove later
            from .class_rdfmodel import rdfmodel
            model = rdfmodel()
        content_node: rdflib.IdentifiedNode = infograph.value(rootnode, RIF.content) #type: ignore[assignment]
        op_node: rdflib.IdentifiedNode = infograph.value(content_node, RIF.op)
        op = model.generate_object(infograph, op_node)
        arg_list_node = infograph.value(content_node, RIF.args)
        arg_list = rdflib.collection.Collection(infograph, arg_list_node)
        args = []
        for x in arg_list:
            args.append(model.generate_object(infograph, x))
        return cls(op, args)

class rif_frame:
    facts: Tuple[machine_facts.frame, ...]
    def __init__(self, obj: ATOM,
                 slots: Iterable[SLOT],
                 ) -> None:
        facts = []
        for slotkey, slotvalue in slots:
            facts.append(machine_facts.frame(obj, slotkey, slotvalue))
        self.facts = tuple(facts)

    def check(self,
            machine: durable_reasoner.machine.durable_machine,
            bindings: BINDING = {},
            ) -> bool:
        for f in self.facts:
            if not f.check_for_pattern(machine, bindings):
                return False
        return True

    def add_pattern(self, rule: durable_reasoner.machine.durable_rule) -> None:
        for f in self.facts:
            f.add_pattern(rule)

    def generate_condition(self,
                           machine: durable_reasoner.machine.durable_machine,
                           ) -> Callable[[BINDING], bool]:
        raise NotImplementedError()
        def condition(bindings: BINDING) -> bool:
            for f in self.facts:
                if not f.check_for_pattern(machine, bindings):
                    return False
            return True
        return condition

    def generate_retract_action(self,
                      machine: durable_reasoner.machine.durable_machine,
                      ) -> Callable[[machine_facts.BINDING], None]:
        def _assert(bindings: BINDING) -> None:
            for f in self.facts:
                f.retract_fact(machine, bindings)
        return _assert

    def generate_assert_action(self,
                      machine: durable_reasoner.machine.durable_machine,
                      ) -> Callable[[machine_facts.BINDING], None]:
        def _assert(bindings: BINDING) -> None:
            for f in self.facts:
                f.assert_fact(machine, bindings)
        return _assert

    def create_rules(self, machine: durable_reasoner.machine.durable_machine) -> None:
        """Is called, when frame is direct sub to a Group"""
        action = self.generate_assert_action(machine)
        machine.add_init_action(action)

    @property
    def obj(self) -> ATOM:
        return self.facts[0].obj

    def __repr__(self) -> str:
        name = type(self).__name__
        def conv(x: ATOM) -> str:
            if isinstance(x, rdflib.URIRef):
                return "<%s>" % x
            elif isinstance(x, rdflib.Variable):
                return "?%s" % x
            elif isinstance(x, Literal):
                if x.datatype:
                    return "'%s'^^%s" % (x, x.datatype)
                else:
                    return "'%s'" % x
            else:
                return str(x)
        slots = ", ".join("%s->%s"%(conv(f.slotkey), conv(f.slotvalue))
                          for f in self.facts)
        return "%s[%s]" % (conv(self.obj), slots)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_frame":
        info = dict(infograph.predicate_objects(rootnode))
        q = rdflib.collection.Collection(infograph, info[RIF.slots])
        slotinfo = [(slot2node(infograph, d[RIF.slotkey]), slot2node(infograph, d[RIF.slotvalue]))
                    for d in (dict(infograph.predicate_objects(x)) for x in q)]
        obj = slot2node(infograph, info[RIF.object])
        return cls(obj, slotinfo, **kwargs)

class rif_retract:
    #fact: Optional[Union[rif_frame]]
    #atom: Optional[Union[IdentifiedNode]]
    def __init__(self, fact_or_atom: Union[rif_frame, IdentifiedNode]):
        if isinstance(fact_or_atom, (rif_frame,)):
            self.fact = fact_or_atom
        elif isinstance(fact_or_atom, IdentifiedNode):
            self.atom = fact_or_atom
        else:
            raise TypeError(fact_or_atom, type(fact_or_atom))

    @property
    def fact_or_atom(self):
        try:
            return self.fact
        except KeyError:
            return self.atom

    def generate_action(self,
                        machine: durable_reasoner.machine.durable_machine,
                        ) -> Callable[[BINDING], None]:
        if getattr(self, "fact", None) is not None:
            return self.fact.generate_retract_action(machine)
        else:
            return machine_facts.retract_object_function(machine, self.atom)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 model = None,
                 **kwargs: typ.Any) -> "rif_retract":
        if model is None: #please remove later
            from .class_rdfmodel import rdfmodel
            model = rdfmodel()
        target_node: rdflib.IdentifiedNode = infograph.value(rootnode, RIF.target) #type: ignore[assignment]
        target = model.generate_object(infograph, target_node)
        return cls(target)


class rif_ineg:
    formula: Union[rif_frame]
    def __init__(self, formula: Union[rif_frame]):
        self.formula = formula

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 model = None,
                 **kwargs: typ.Any) -> "rif_assert":
        if model is None: #please remove later
            from .class_rdfmodel import rdfmodel
            model = rdfmodel()
        target_node: rdflib.IdentifiedNode = infograph.value(rootnode, RIF.formula) #type: ignore[assignment]
        target = model.generate_object(infograph, target_node)
        return cls(target)

    def __repr__(self) -> str:
        return "INeg( %s )" % self.fact

class rif_modify:
    fact: Union[rif_frame]
    def __init__(self, fact: Union[rif_frame]):
        self.fact = fact

    def generate_action(self,
                        machine: durable_reasoner.machine.durable_machine,
                        ) -> Callable[[BINDING], None]:
        return self.fact.generate_assert_action(machine)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 model = None,
                 **kwargs: typ.Any) -> "rif_assert":
        if model is None: #please remove later
            from .class_rdfmodel import rdfmodel
            model = rdfmodel()
        target: rdflib.IdentifiedNode = infograph.value(rootnode, RIF.target) #type: ignore[assignment]
        target_type = infograph.value(target, RDF.type)
        fact = model.generate_object(infograph, target)
        assert isinstance(fact, rif_frame)
        return cls(fact, **kwargs)

    def __repr__(self) -> str:
        return "Modify(%s)" % self.fact


class rif_assert:
    fact: Union[rif_frame]
    def __init__(self, fact: Union[rif_frame]):
        self.fact = fact

    def generate_action(self,
                        machine: durable_reasoner.machine.durable_machine,
                        ) -> Callable[[BINDING], None]:
        return self.fact.generate_assert_action(machine)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_assert":
        target: rdflib.IdentifiedNode = infograph.value(rootnode, RIF.target) #type: ignore[assignment]
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

    def __repr__(self) -> str:
        return "Assert( %s )" % self.fact
