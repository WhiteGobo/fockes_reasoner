import abc
import logging
logger = logging.getLogger(__name__)
import uuid
from .durable_reasoner import machine_facts, fact, NoPossibleExternal, _resolve
from .durable_reasoner.machine_facts import external, TRANSLATEABLE_TYPES
import rdflib
from rdflib import IdentifiedNode, Graph, Variable, Literal, URIRef
import typing as typ
from typing import Union, Iterable, Any, Callable, MutableMapping, List, Tuple, Optional, Mapping
from .shared import RIF
from rdflib import RDF
from . import durable_reasoner
from .durable_reasoner import machine
from .durable_reasoner import BINDING, RESOLVABLE
from dataclasses import dataclass

ATOM = typ.Union[TRANSLATEABLE_TYPES, external, Variable]
SLOT = Tuple[ATOM, ATOM]

class NotPossibleAction(SyntaxError):
    """Raise if wanted action is not available for this rif object"""

class RIFSyntaxError(Exception):
    """The given RIF Document has syntaxerrors"""

class _resolvable_gen(abc.ABC):
    """Subclass can be used to retrieve a :term:`translateable object` as
    described in bridge-rdflib. Is equal to a :term:`formula` in :term:`RIF`
    """
    @abc.abstractmethod
    def as_resolvable(self, machine: durable_reasoner.machine) -> RESOLVABLE:
        ...

class _action_gen(abc.ABC):
    @abc.abstractmethod
    def generate_action(self,
                        machine: durable_reasoner.machine,
                        ) -> Callable[..., None]:
        ...

def _generate_object(infograph: Graph, target: IdentifiedNode,
                     type_to_generator: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], Any]]) -> Any:
    target_type = infograph.value(target, RDF.type)
    gen = type_to_generator[target_type]
    return gen(infograph, target)


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
    payload: Optional["rif_group"]
    directives: Iterable["rif_import"]
    def __init__(self, payload: Optional["rif_group"] = None,
                 directives: Iterable["rif_import"] = []) -> None:
        self.payload = payload
        self.directives = list(directives)

    def create_rules(self, machine: durable_reasoner.machine,
                     ) -> None:
        for directive in self.directives:
            directive.apply_to(machine)
        if self.payload is not None:
            self.payload.create_rules(machine)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 extraDocuments: Mapping[str, Graph] = {},
                 **kwargs: Any) -> "rif_document":
        """
        :param extraDocuments: A Manager of all importable documents
        """
        kwargs = {}
        payload_nodes: list[IdentifiedNode] = list(infograph.objects(rootnode, RIF.payload)) #type: ignore[assignment]
        if len(payload_nodes) == 1:
            payload_node = payload_nodes[0]
            payload_type, = infograph.objects(payload_node, RDF.type)
            if payload_type == RIF.Group:
                kwargs["payload"] = rif_group.from_rdf(infograph, payload_node)
            else:
                raise NotImplementedError(payload_type)
            
        elif len(payload_nodes) > 1:
            raise SyntaxError("This doesnt looks like a valid rif document.")

        try:
            directives_node, = infograph.objects(rootnode, RIF.directives)
            directives_lists = rdflib.collection.Collection(infograph, directives_node)
        except ValueError:
            directives_lists = []
        for directive_node in directives_lists:
            tmp_directive = cls._generate_directive(infograph, directive_node, extraDocuments)
            kwargs.setdefault("directives", []).append(tmp_directive)

        return cls(**kwargs)

    @classmethod
    def _generate_directive(cls, infograph: Graph,
                            directive_node: IdentifiedNode,
                            extraDocuments: Mapping[str, Graph],
                            ):
        t = infograph.value(directive_node, RDF.type)
        if t == RIF.Import:
            return rif_import.from_rdf(infograph, directive_node,
                                       extraDocuments)
        else:
            raise NotImplementedError(t)

    def __repr__(self) -> str:
        return "Document %s" % repr(self.payload)


class rif_import:
    extraDocuments: Mapping[str, Graph]
    profile: Optional[URIRef]
    location: URIRef
    def __init__(self, extraDocuments: Mapping[str, Graph],
                 location: Union[IdentifiedNode, Literal],
                 profile: Optional[URIRef] = None):
        self.extraDocuments = extraDocuments
        if isinstance(location, IdentifiedNode):
            self.location = location
        else:
            self.location = URIRef(location)
        if isinstance(profile, IdentifiedNode):
            self.profile = profile
        else:
            self.profile = URIRef(profile)

    def apply_to(self, machine: durable_reasoner.machine,
                 ) -> None:
        infograph = self.extraDocuments[self.location]
        if self.profile is not None:
            machine.import_data(infograph,
                                self.location, self.profile,
                                extraDocuments = self.extraDocuments)
        else:
            machine.import_data(infograph, self.location,
                                extraDocuments = self.extraDocuments)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 extraDocuments: Mapping[str, Graph] = {},
                 **kwargs: Any) -> "rif_group":
        location, = infograph.objects(rootnode, RIF.location)
        profile = infograph.value(rootnode, RIF.profile)
        if profile:
            return cls(extraDocuments, location, profile)
        return cls(extraDocuments, location)


class rif_group:
    sentences: tuple[Union["rif_forall", "rif_frame", "rif_group"], ...]
    def __init__(self,
                 sentences: Iterable[Union["rif_forall", "rif_frame", "rif_group"]],
                 ) -> None:
        self.sentences = tuple(sentences)

    def create_rules(self, machine: durable_reasoner.machine) -> None:
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

    def _create_generell_rule_without_pattern(self, machine: durable_reasoner.machine) -> None:
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

    def _create_implication(self, machine: durable_reasoner.machine) -> None:
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
            implicated_fact = self.formula.then_
            action = implicated_fact.generate_assert_action(machine)
        else:
            raise NotImplementedError()
        newrule.action = action
        logger.info("create rule %r" % newrule)
        newrule.finalize()

    def create_rules(self, machine: durable_reasoner.machine) -> None:
        if self.pattern is None and isinstance(self.formula, rif_implies)\
                and isinstance(self.formula.then_, (rif_frame,)):
            return self._create_implication(machine)
        elif self.pattern is None and isinstance(self.formula, rif_implies):
            return self._create_generell_rule_without_pattern(machine)
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
    #is set at end of file
    _then_generators: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], Any]]
    def __init__(self, if_: Union["rif_frame"], then_: Union["rif_do"]):
        self.if_ = if_
        self.then_ = then_

    @dataclass
    class conditional:
        parent: "rif_implies"
        conditions: list[Callable]
        action: Callable
        def __call__(self, bindings: BINDING):
            if all(c(bindings) for c in self.conditions):
                self.action(bindings)

        def __repr__(self):
            return f"condition {self.parent}"


    def create_rules(self, machine: durable_reasoner.machine) -> None:
        """Create this as a rule for an expertsystem.

        """
        newrule = machine.create_implication_builder()
        conditions = []
        if isinstance(self.if_, rif_and):
            for pat in self.if_.formulas:
                try:
                    pat.add_pattern(newrule)
                    logger.debug("added pat %s" % pat)
                except NotPossibleAction:
                    tmp_cond = pat.generate_condition(machine)
                    conditions.append(tmp_cond)
                    logger.debug("added with %s cond %s" % (pat, tmp_cond))
        else:
            self.if_.add_pattern(newrule)
        if len(conditions) == 0:
            newrule.action = self.then_.generate_assert_action(machine)
        else:
            action = self.then_.generate_assert_action(machine)
            newrule.action = self.conditional(self, conditions, action)
        logger.info("create implication %r" % newrule)
        newrule.finalize()

    def generate_action(self,
                        machine: durable_reasoner.machine,
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
        #then_ = model.generate_object(infograph, then_node)
        then_ = _generate_object(infograph, then_node, cls._then_generators)
        return cls(if_, then_)


    def __repr__(self) -> str:
        return "If %s Then %s" %(self.if_, self.then_)

class rif_and:
    formulas: Iterable[Union["rif_frame"]]
    _formulas_generators: Mapping
    def __init__(self, formulas: Iterable[Union["rif_frame"]]):
        self.formulas = list(formulas)

    def add_pattern(self, rule: durable_reasoner.rule) -> None:
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
            next_formula = _generate_object(infograph, formula_node, cls._formulas_generators)
            formulas.append(next_formula)
        return cls(formulas)

class rif_do(_action_gen):
    target: List[Union["rif_assert", "rif_retract"]]
    def __init__(self, actions: Iterable[Union["rif_assert", "rif_retract"]]):
        self.actions = list(actions)

    def generate_action(self,
                        machine: durable_reasoner.machine,
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

class rif_atom:
    op: ATOM
    args: Iterable[ATOM]
    def __init__(self, op: ATOM, args: Iterable[ATOM]):
        self.op = op
        self.args = list(args)

    def check(self,
            machine: durable_reasoner.machine,
            bindings: BINDING = {},
            ) -> bool:

        f = machine_facts.atom(self.op, self.args)
        return f.check_for_pattern(machine, bindings)

    def generate_assert_action(self,
                               machine: durable_reasoner.machine,
                               ) -> Callable[[machine_facts.BINDING], None]:
        """
        :TODO: Creation of variable is not safe
        """
        logger.info("op: %s\nargs: %s" %(self.op,self.args))
        binding_actions = []
        args = [self.op, *self.args]
        for i, arg in enumerate(args):
            if isinstance(arg, rdflib.term.Node):
                pass
            elif isinstance(arg, rif_external):
                try:
                    args[i] = arg.get_replacement_node(machine)
                    continue
                except NoPossibleExternal:
                    pass
                try:
                    bindact = arg.get_binding_action(machine)
                    var = Variable("tmp%s" % uuid.uuid4().hex)
                    binding_actions.append(lambda bindings: bindings.__setitem__(var, bindact(bindings)))
                    args[i] = var
                    continue
                except NoPossibleExternal:
                    raise
                    pass
                raise ValueError("Cant figure out how use '%s' as atom in %s" %(arg, self))
            else:
                raise NotImplementedError(x, type(x))
        fact = machine_facts.atom(args[0], args[1:])
        def _assert(bindings: BINDING) -> None:
            for act in binding_actions:
                act(bindings)
            fact.assert_fact(machine, bindings)
        return _assert

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_retract":
        from .class_rdfmodel import rdfmodel
        model = rdfmodel()
        op_node: rdflib.IdentifiedNode = infograph.value(rootnode, RIF.op)
        op = model.generate_object(infograph, op_node)
        arg_list_node = infograph.value(rootnode, RIF.args)
        arg_list = rdflib.collection.Collection(infograph, arg_list_node)
        args = []
        for x in arg_list:
            args.append(model.generate_object(infograph, x))
        return cls(op, args)

    def __repr__(self) -> str:
        return "%s (%s)" % (self.op, ", ".join(self.args))

class rif_external(_resolvable_gen):
    op: URIRef
    args: Iterable[ATOM]
    def __init__(self, op: ATOM, args: Iterable[ATOM]):
        self.op = op
        self.args = list(args)

    def as_resolvable(self, machine: durable_reasoner.machine) -> RESOLVABLE:
        args = [_get_resolveable(x, machine) for x in self.args]
        return machine.get_binding_action(self.op, args)

    def get_replacement_node(self,
                      machine: durable_reasoner.machine,
            ):
        return machine.get_replacement_node(self.op, self.args)

    def get_binding_action(self,
                      machine: durable_reasoner.machine,
            ):
        return machine.get_binding_action(self.op, self.args)

    def generate_condition(self,
                           machine: durable_reasoner.machine,
                           ) -> Callable[[BINDING], bool]:
        raise NotImplementedError()

    def add_pattern(self, rule: durable_reasoner.rule) -> None:
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

    def __repr__(self) -> str:
        return "external %s (%s)" % (self.op, ", ".join(str(x) for x in self.args))


class rif_member:
    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_member":
        raise NotImplementedError()

class rif_subclass:
    sub_class: ATOM
    super_class: ATOM
    def __init__(self, sub_class: ATOM, super_class: ATOM) -> None:
        self.sub_class = sub_class
        self.super_class = super_class

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_subclass":
        info = dict(infograph.predicate_objects(rootnode))
        sub_node = info[RIF["sub"]]
        super_node = info[RIF["super"]]
        sub_obj = slot2node(infograph, sub_node)
        super_obj = slot2node(infograph, super_node)
        return cls(sub_obj, super_obj)

    def check(self,
            machine: durable_reasoner.machine,
            bindings: BINDING = {},
            ) -> bool:

        f = machine_facts.fact_subclass(self.sub_class, self.super_class)
        return f.check_for_pattern(machine, bindings)

    def __repr__(self) -> str:
        return "%s # %s" % (self.sub_class, self.super_class)


class rif_frame:
    facts: Tuple[machine_facts.frame, ...]
    obj: ATOM
    slots: Iterable[Tuple[ATOM, ATOM]]
    def __init__(self, obj: ATOM,
                 slots: Iterable[SLOT],
                 ) -> None:
        self.obj = obj
        self.slots = [tuple((x,y)) for x,y in slots]

    @property
    def facts(self) -> Iterable[machine_facts.frame]:
        for slotkey, slotvalue in self.slots:
            if any(isinstance(x, rif_external) for x in (self.obj, slotkey, slotvalue)):
                raise Exception(self.obj, slotkey, slotvalue)
            yield machine_facts.frame(self.obj, slotkey, slotvalue)
        

    def check(self,
            machine: durable_reasoner.machine,
            bindings: BINDING = {},
            ) -> bool:
        for f in self.facts:
            if not f.check_for_pattern(machine, bindings):
                return False
        return True

    def add_pattern(self, rule: durable_reasoner.rule) -> None:
        for slotkey, slotvalue in self.slots:
            args = [self.obj, slotkey, slotvalue]
            for i, arg in enumerate(args):
                if isinstance(arg, rdflib.term.Node):
                    pass
                elif isinstance(arg, rif_external):
                    raise NotImplementedError()
                else:
                    raise NotImplementedError(x, type(x))
            f = machine_facts.frame(self.obj, slotkey, slotvalue)
            f.add_pattern(rule)

    def generate_condition(self,
                           machine: durable_reasoner.machine,
                           ) -> Callable[[BINDING], bool]:
        raise NotImplementedError()
        def condition(bindings: BINDING) -> bool:
            for f in self.facts:
                if not f.check_for_pattern(machine, bindings):
                    return False
            return True
        return condition

    def generate_retract_action(self,
                      machine: durable_reasoner.machine,
                      ) -> Callable[[machine_facts.BINDING], None]:
        def _assert(bindings: BINDING) -> None:
            for f in self.facts:
                f.retract_fact(machine, bindings)
        return _assert

    def generate_assert_action(self,
                               machine: durable_reasoner.machine,
                               ) -> Callable[[machine_facts.BINDING], None]:
        """
        :TODO: Creation of variable is not safe
        """
        facts = []
        binding_actions = []
        for slotkey, slotvalue in self.slots:
            args = [self.obj, slotkey, slotvalue]
            for i, arg in enumerate(args):
                if isinstance(arg, rdflib.term.Node):
                    pass
                elif isinstance(arg, rif_external):
                    try:
                        args[i] = arg.get_replacement_node(machine)
                        continue
                    except NoPossibleExternal:
                        pass
                    try:
                        bindact = arg.get_binding_action(machine)
                        var = Variable("tmp%s" % uuid.uuid4().hex)
                        binding_actions.append(lambda bindings: bindings.__setitem__(var, bindact(bindings)))
                        args[i] = var
                        continue
                    except NoPossibleExternal:
                        raise
                        pass
                    raise ValueError("Cant figure out how use '%s' as atom in %s" %(arg, self))
                else:
                    raise NotImplementedError(x, type(x))
            facts.append(machine_facts.frame(*args))
        def _assert(bindings: BINDING) -> None:
            for act in binding_actions:
                act(bindings)
            for f in facts:
                f.assert_fact(machine, bindings)
        return _assert

    def create_rules(self, machine: durable_reasoner.machine) -> None:
        """Is called, when frame is direct sub to a Group"""
        action = self.generate_assert_action(machine)
        machine.add_init_action(action)

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
        slots = ", ".join("%s->%s"%(conv(slotkey), conv(slotvalue))
                          for slotkey, slotvalue in self.slots)
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
        elif isinstance(fact_or_atom, (IdentifiedNode, Variable)):
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
                        machine: durable_reasoner.machine,
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
                        machine: durable_reasoner.machine,
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
                        machine: durable_reasoner.machine,
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

class rif_equal:
    #_side_generators: Mapping
    def __init__(self, left, right):
        self.left = left
        self.right = right

    @dataclass
    class _condition:
        parent: "rif_equal"
        left: Callable[[BINDING], Literal]
        right: Callable[[BINDING], Literal]
        def __call__(self, bindings: BINDING) -> bool:
            left = _resolve(self.parent.left, bindings)
            right = _resolve(self.parent.right, bindings)
            return Literal(left == right)

    def __repr__(self):
        return "(%s = %s)" % (self.left, self.right)

    def add_pattern(self, rule: durable_reasoner.rule) -> None:
        raise NotPossibleAction("generate pattern currently not implemented for rif_equal")

    def generate_condition(self,
                           machine: durable_reasoner.machine,
                           ) -> Callable[[BINDING], bool]:
        left_assign = _get_resolveable(self.left, machine)
        right_assign = _get_resolveable(self.right, machine)
        return self._condition(self, left_assign, right_assign)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_equal":
        leftnode = infograph.value(rootnode, RIF.left)
        rightnode = infograph.value(rootnode, RIF.right)
        left = slot2node(infograph, leftnode)
        right = slot2node(infograph, rightnode)
        #left = _generate_object(infograph, leftnode, cls._side_generators)
        #right = _generate_object(infograph, rightnode, cls._side_generators)
        return cls(left, right)


rif_implies._then_generators = {
        RIF.Frame: rif_frame.from_rdf,
        RIF.Do: rif_do.from_rdf,
        RIF.Atom: rif_atom.from_rdf,
        }

_formulas = {RIF.External: rif_external.from_rdf,
             RIF.Frame: rif_frame.from_rdf,
             RIF.Equal: rif_equal.from_rdf,
             }
rif_and._formulas_generators = dict(_formulas)
#rif_equal._side_generators = {}

def _get_resolveable(x: Union[IdentifiedNode, Literal, Variable, _resolvable_gen], machine: durable_reasoner.machine) -> RESOLVABLE:
    if isinstance(x, (IdentifiedNode, Literal, Variable)):
        return x
    return x.as_resolvable(machine)
