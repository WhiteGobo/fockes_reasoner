import abc
import logging
logger = logging.getLogger(__name__)
import uuid
from .durable_reasoner import machine_facts, fact, NoPossibleExternal, _resolve, ATOM_ARGS, term_list, machine_list, pattern_generator
from .durable_reasoner.machine_facts import external, TRANSLATEABLE_TYPES
import rdflib
from rdflib import IdentifiedNode, Graph, Variable, Literal, URIRef
import typing as typ
from typing import Union, Iterable, Any, Callable, MutableMapping, List, Tuple, Optional, Mapping
from .shared import RIF, pred, XSD
from rdflib import RDF
from . import durable_reasoner
from .durable_reasoner import machine
from .durable_reasoner import BINDING, RESOLVABLE
from dataclasses import dataclass
from collections.abc import Sequence

ATOM = Union[TRANSLATEABLE_TYPES, Variable, "rif_external", "rif_list"]
SATOM = Union[TRANSLATEABLE_TYPES, external, Variable, "rif_list"]
SLOT = Tuple[ATOM, ATOM]
RIF_ATOM = Union[TRANSLATEABLE_TYPES, "rif_external"]
FORMULA = Union["rif_frame",
                "rif_atom",
                "rif_member",
                "rif_subclass",
                "rif_and",
                "rif_or",
                "rif_ineg",
                "rif_exists"]

class _child_action:
    """Shared parent for all action classes for callables for the machine"""
    parent: Any

class NotPossibleAction(SyntaxError):
    """Raise if wanted action is not available for this rif object"""

class RIFSyntaxError(Exception):
    """The given RIF Document has syntaxerrors"""

class _rule_gen(abc.ABC):
    @abc.abstractmethod
    def create_rules(self, machine: durable_reasoner.machine) -> None:
        ...

class _action_gen(abc.ABC):
    @abc.abstractmethod
    def generate_action(self,
                        machine: durable_reasoner.machine,
                        ) -> Callable[..., None]:
        ...

class _rif_check(pattern_generator, abc.ABC):
    """Class that has everything to do with checking if some type of statement
    holds true or not.
    """
    @abc.abstractmethod
    def check(self,
            machine: durable_reasoner.machine,
            bindings: BINDING = {},
            ) -> bool:
        ...

class rif_fact(_rif_check, _action_gen, _rule_gen):
    @abc.abstractmethod
    def _create_facts(self) -> Iterable[fact]:
        ...

    def check(self,
            machine: durable_reasoner.machine,
            bindings: BINDING = {},
            ) -> bool:
        """Checks if all micro-facts are true for given machine.
        Variables are treated as blanks if not given by bindings,
        so accepts instead of a variable anything.
        """
        for f in self._create_facts():
            if not f.check_for_pattern(machine, bindings):
                return False
        return True

    @dataclass
    class __assert_action(_child_action):
        parent: "rif_fact"
        facts: Iterable[fact]
        machine: durable_reasoner.machine
        def __call__(self, bindings: BINDING) -> None:
            for f in self.facts:
                f.assert_fact(self.machine, bindings)

    def generate_action(self,
                        machine: durable_reasoner.machine,
                        ) -> Callable[..., None]:
        return self.generate_assert_action(machine)

    def generate_assert_action(self,
                               machine: durable_reasoner.machine,
                               ) -> Callable[[machine_facts.BINDING], None]:
        """
        :TODO: Creation of variable is not safe
        """
        return self.__assert_action(self, self._create_facts(), machine)

    def create_rules(self, machine: durable_reasoner.machine) -> None:
        """Is called, when frame is direct sub to a Group"""
        action = self.generate_assert_action(machine)
        machine.add_init_action(action)


class _resolvable_gen(abc.ABC):
    """Subclass can be used to retrieve a :term:`translateable object` as
    described in bridge-rdflib. Is equal to a :term:`formula` in :term:`RIF`
    """
    @abc.abstractmethod
    def as_resolvable(self, machine: durable_reasoner.machine) -> RESOLVABLE:
        ...

    @abc.abstractmethod
    def as_machinefact(self) -> Union[external, TRANSLATEABLE_TYPES]:
        """
        :TODO: This should be as_machineterm
        """
        ...

def _try_as_machinefact(x: Union[TRANSLATEABLE_TYPES, external, Variable, _resolvable_gen],
                        ) -> Union[TRANSLATEABLE_TYPES, external, Variable]:
    if isinstance(x, _resolvable_gen):
        return x.as_machinefact()
    else:
        return x

def _generate_object(infograph: Graph, target: IdentifiedNode,
                     type_to_generator: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], Any]]) -> Any:
    target_type = infograph.value(target, RDF.type)
    if not isinstance(target_type, IdentifiedNode):
        raise Exception("Syntaxerror in graph. Missing type for %s" % target)
    gen = type_to_generator[target_type]
    return gen(infograph, target)


def slot2node(infograph: Graph, x: IdentifiedNode) -> ATOM:
    """Transform
    :TODO: Local variables are not correctly transformed but instead
        just Literals are used.
    """
    val_info = dict(infograph.predicate_objects(x))
    t = val_info[RDF.type]
    if t == RIF.Var:
        return rdflib.Variable(str(val_info[RIF.varname]))
    elif t == RIF.Const and RIF.constIRI in val_info:
        return rdflib.URIRef(str(val_info[RIF.constIRI]))
    elif t == RIF.Const and RIF.value in val_info:
        val = val_info[RIF.value]
        assert isinstance(val, Literal)
        #if val.datatype is None and val.language is None:
        #    val = Literal(val, datatype=XSD.string)
        #elif val.datatype is None:
        #    val = Literal(val, datatype=XSD.string, language=val.language)
        return val
    elif t == RIF.Const and RIF.constname in val_info:
        val = val_info[RIF.constname]
        assert isinstance(val, Literal)
        #return local(val, graph.identifier)
        return val
    elif t == RIF.Const:
        raise NotImplementedError(val_info)
    elif t == RIF.External:
        return rif_external.from_rdf(infograph, x)
    elif t == RIF.List:
        return rif_list.from_rdf(infograph, x)
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
                 extraDocuments: Mapping[IdentifiedNode, Graph] = {},
                 **kwargs: Any) -> "rif_document":
        """
        :param extraDocuments: A Manager of all importable documents
        """
        directives_lists: Iterable[IdentifiedNode]
        kwargs = {}
        payload_nodes: list[IdentifiedNode] = list(infograph.objects(rootnode, RIF.payload)) #type: ignore[assignment, arg-type]
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
            typ.cast(Iterable[IdentifiedNode], directives_lists)
        except ValueError:
            directives_lists = []
        for directive_node in directives_lists:
            tmp_directive = cls._generate_directive(infograph, directive_node,
                                                    extraDocuments)
            kwargs.setdefault("directives", []).append(tmp_directive)

        return cls(**kwargs)

    @classmethod
    def _generate_directive(cls, infograph: Graph,
                            directive_node: IdentifiedNode,
                            extraDocuments: Mapping[IdentifiedNode, Graph],
                            ) -> "rif_import":
        t = infograph.value(directive_node, RDF.type)
        if t == RIF.Import:
            return rif_import.from_rdf(infograph, directive_node,
                                       extraDocuments)
        else:
            raise NotImplementedError(t)

    def __repr__(self) -> str:
        return "Document %s" % repr(self.payload)


class rif_import:
    extraDocuments: Mapping[IdentifiedNode, Graph]
    profile: Optional[URIRef]
    location: URIRef
    def __init__(self, extraDocuments: Mapping[IdentifiedNode, Graph],
                 location: Union[URIRef, Literal],
                 profile: Optional[URIRef] = None):
        self.extraDocuments = dict(extraDocuments)
        if isinstance(location, IdentifiedNode):
            self.location = location
        else:
            self.location = URIRef(location)
        if isinstance(profile, IdentifiedNode):
            self.profile = profile
        else:
            self.profile = None

    def apply_to(self, machine: durable_reasoner.machine,
                 ) -> None:
        try:
            infograph = self.extraDocuments[self.location]
        except Exception as err:
            raise Exception(self.extraDocuments) from err
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
                 extraDocuments: Mapping[IdentifiedNode, Graph] = {},
                 **kwargs: Any) -> "rif_import":
        location, = infograph.objects(rootnode, RIF.location)
        assert isinstance(location, Literal)
        loc_as_uri = URIRef(location)
        if loc_as_uri not in extraDocuments:
            raise SyntaxError("Have the directive to import '%s' but it isnt "
                              "in supplied extraDocuments %s"
                              % (loc_as_uri, extraDocuments))
        profile = infograph.value(rootnode, RIF.profile)
        #assert isinstance(location, URIRef), repr(location)
        if profile:
            return cls(extraDocuments, loc_as_uri, URIRef(profile))
        return cls(extraDocuments, loc_as_uri)


class rif_group(_rule_gen):
    sentences: tuple[Union["rif_forall", "rif_frame", "rif_group", "rif_implies"], ...]
    _sentence_generators: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], Any]]
    def __init__(self,
                 sentences: Iterable[Union["rif_forall", "rif_frame", "rif_group", "rif_implies"]],
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
        sentences: list[Union[rif_forall, rif_frame, rif_group, rif_implies]] = []
        next_sentence: Union[rif_forall, rif_frame, rif_group, rif_implies]
        sentences_list: Iterable[IdentifiedNode]\
                = rdflib.collection.Collection(infograph, sentences_list_node) #type: ignore[assignment]
        for sentence_node in sentences_list:
            sentence_type = infograph.value(sentence_node, RDF.type)
            gen = cls._sentence_generators[sentence_type]
            next_sentence =  gen(infograph, sentence_node)
            sentences.append(next_sentence)
        return cls(sentences, **kwargs)

    def __repr__(self) -> str:
        return "Group (%s)" % ", ".join(repr(x) for x in self.sentences)


class rif_forall(_rule_gen):
    formula: Union["rif_implies"]
    pattern: Union[None]
    def __init__(self, formula: Union["rif_implies"],
                 pattern: Union[None] = None) -> None:
        self.formula = formula
        self.pattern = pattern

    def _create_generell_rule_without_pattern(
            self,
            machine: durable_reasoner.machine,
            ) -> None:
        newrule = machine.create_rule_builder()
        conditions: list[Callable[[BINDING], Union[Literal, bool]]] = []
        if isinstance(self.formula.if_, rif_and):
            for pat in self.formula.if_.formulas:
                try:
                    newrule.orig_pattern.append(pat)
                except Exception:
                    raise
                    conditions.append(pat.generate_condition(machine))
        else:
            newrule.orig_pattern.append(self.formula.if_)
        if len(conditions) == 0:
            action = self.formula.then_.generate_action(machine)
        else:
            raise NotImplementedError()
        newrule.set_action(action, [])
        logger.info("create rule %r" % newrule)
        newrule.finalize()

    def _create_implication(self, machine: durable_reasoner.machine) -> None:
        newrule = machine.create_rule_builder()
        conditions: list[Callable[[BINDING], Union[Literal, bool]]] = []
        if isinstance(self.formula.if_, rif_and):
            for pat in self.formula.if_.formulas:
                try:
                    newrule.orig_pattern.append(pat)
                except Exception:
                    raise
                    conditions.append(pat.generate_condition(machine))
        else:
            newrule.orig_pattern.append(self.formula.if_)
        if isinstance(self.formula.then_, rif_do):
            raise NotImplementedError()
        if len(conditions) == 0:
            implicated_fact = self.formula.then_
            action = implicated_fact.generate_assert_action(machine)
        else:
            raise NotImplementedError()
        newrule.set_action(action, [])
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


class rif_implies(_rule_gen):
    if_: Union["rif_frame"]
    then_: Union["rif_do"]
    #is set at end of file
    _if_generators: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], Any]]
    _then_generators: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], Any]]
    def __init__(self, if_: Union["rif_frame"], then_: Union["rif_do"]):
        self.if_ = if_
        self.then_ = then_

    @dataclass
    class conditional(_child_action):
        parent: "rif_implies"
        conditions: list[Callable]
        action: Callable
        machine: durable_reasoner.machine
        def __call__(self, bindings: BINDING) -> None:
            for c in self.conditions:
                if not c(bindings):
                    self.machine.logger.debug("stopped %s because %s" % (self, c))
                    return
            self.action(bindings)

        def __repr__(self) -> str:
            return f"condition {self.parent}"


    def create_rules(self, machine: durable_reasoner.machine) -> None:
        """Create this as a rule for an expertsystem.

        """
        newrule = machine.create_implication_builder()
        conditions: list[Callable[[BINDING], Union[Literal, bool]]] = []
        if isinstance(self.if_, rif_and):
            for pat in self.if_.formulas:
                try:
                    newrule.orig_pattern.append(pat)
                    logger.debug("added pat %s" % pat)
                except NotPossibleAction:
                    tmp_cond = pat.generate_condition(machine)
                    conditions.append(tmp_cond)
                    logger.debug("added with %s cond %s" % (pat, tmp_cond))
        else:
            newrule.orig_pattern.append(self.if_)
        if isinstance(self.then_, rif_do):
            action = self.then_.generate_action(machine)
        else:
            action = self.then_.generate_assert_action(machine)
        if len(conditions) == 0:
            newrule.set_action(action, [])
        else:
            act = self.conditional(self, conditions, action, machine)
            newrule.set_action(act)
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
                 ) -> "rif_implies":
        if_node: IdentifiedNode
        then_node: IdentifiedNode
        info = dict(infograph.predicate_objects(rootnode))
        try:
            if_node = info[RIF["if"]] #type: ignore[assignment]
            then_node = info[RIF["then"]] #type: ignore[assignment]
        except KeyError as err:
            raise RIFSyntaxError() from err
        if_ = _generate_object(infograph, if_node, cls._if_generators)
        then_ = _generate_object(infograph, then_node, cls._then_generators)
        return cls(if_, then_)


    def __repr__(self) -> str:
        return "If %s Then %s" %(self.if_, self.then_)

class rif_exists(_rif_check):
    formula: rif_fact
    _formula_generators: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], rif_fact]]
    def __init__(self, formula: rif_fact):
        self.formula = formula

    def __repr__(self) -> str:
        return "exists(%s)" % self.formula

    def _add_pattern(self, rule: durable_reasoner.rule) -> None:
        raise NotImplementedError()

    def check(self,
            machine: durable_reasoner.machine,
            bindings: BINDING = {},
            ) -> bool:
        return self.formula.check(machine, bindings)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: IdentifiedNode,
                 ) -> "rif_exists":
        vars_node, = infograph.objects(rootnode, RIF.vars)
        var_list = rdflib.collection.Collection(infograph, vars_node)
        formula_node, = infograph.objects(rootnode, RIF.formula)
        assert isinstance(formula_node, IdentifiedNode)
        formula = _generate_object(infograph, formula_node,
                                   cls._formula_generators)
        return cls(formula)

class rif_and(_rif_check):
    formulas: Iterable[_rif_check]
    _formulas_generators: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], _rif_check]]
    def __init__(self, formulas: Iterable[_rif_check]):
        self.formulas = list(formulas)

    def check(self,
            machine: durable_reasoner.machine,
            bindings: BINDING = {},
            ) -> bool:
        return all(f.check(machine, bindings) for f in self.formulas)

    def _add_pattern(self, rule: durable_reasoner.rule) -> None:
        for form in self.formulas:
            rule.orig_pattern.append(form)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: IdentifiedNode,
                 ) -> "rif_and":
        from .class_rdfmodel import rdfmodel
        model = rdfmodel()
        try:
            formula_list_node, = infograph.objects(rootnode, RIF.formulas)
        except ValueError as err:
            raise Exception("Syntaxerror of RIF document") from err
        formula_list: Iterable[IdentifiedNode] = rdflib.collection.Collection(infograph, formula_list_node) #type: ignore[assignment]
        formulas: list[Union["rif_frame"]] = []
        for formula_node in formula_list:
            next_formula = _generate_object(infograph, formula_node, cls._formulas_generators)
            formulas.append(next_formula)
        return cls(formulas)

class rif_do(_action_gen):
    target: List[Union["rif_assert", "rif_retract", "rif_modify"]]
    def __init__(self, actions: Iterable[Union["rif_assert", "rif_retract", "rif_modify"]]):
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
                 ) -> "rif_do":
        from .class_rdfmodel import rdfmodel
        model = rdfmodel()
        try:
            target_list_node, = infograph.objects(rootnode, RIF.actions)
        except ValueError as err:
            raise Exception("Syntaxerror of RIF document") from err
        target_list: Iterable[IdentifiedNode] = rdflib.collection.Collection(infograph, target_list_node) #type: ignore[assignment]
        actions: List[Union[rif_assert, "rif_retract", "rif_modify"]] = []
        for target_node in target_list:
            next_target = model.generate_object(infograph, target_node)
            assert isinstance(next_target, (rif_assert, rif_retract, rif_modify)), "got unexpected rif object. Invalid RIF document?"
            actions.append(next_target)
        return cls(actions)

    def __repr__(self) -> str:
        return "Do( %s )" % ", ".join(repr(x) for x in self.actions)

class rif_atom(rif_fact):
    op: IdentifiedNode
    args: Iterable[RIF_ATOM]
    _atom_op_generator: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], ATOM]]
    _atom_args_generator: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], ATOM]]
    def __init__(self, op: IdentifiedNode, args: Iterable[RIF_ATOM]):
        self.op = op
        self.args = list(args)

    def _add_pattern(self, rule: durable_reasoner.rule) -> None:
        args = [_try_as_machinefact(arg) for arg in self.args]
        f = machine_facts.atom(self.op, args)
        rule.orig_pattern.append(f)

    def _create_facts(self) -> Iterable[fact]:
        raise NotImplementedError()

    def check(self,
            machine: durable_reasoner.machine,
            bindings: BINDING = {},
            ) -> bool:
        args_ = [_try_as_machinefact(arg) for arg in self.args]
        #args: list[RESOLVABLE] = [_get_resolveable(x, machine) for x in args_]
        f = machine_facts.atom(self.op, args_)
        return f.check_for_pattern(machine, bindings)

    @dataclass
    class assert_action(_child_action):
        parent: "rif_atom"
        fact: machine_facts.atom
        binding_actions: Iterable[Callable[[BINDING], None]]
        machine: durable_reasoner.machine
        def __call__(self, bindings: BINDING) -> None:
            for act in self.binding_actions:
                act(bindings)
            self.fact.assert_fact(self.machine, bindings)

    def generate_assert_action(self,
                               machine: durable_reasoner.machine,
                               ) -> Callable[[machine_facts.BINDING], None]:
        """
        :TODO: Creation of variable is not safe
        """
        logger.info("op: %s\nargs: %s" % (self.op, self.args))
        binding_actions: list[Callable[[BINDING], None]] = []
        args = [_try_as_machinefact(arg) for arg in self.args]
        fact = machine_facts.atom(self.op, args)
        return self.assert_action(self, fact, binding_actions, machine)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_atom":
        op_node = infograph.value(rootnode, RIF.op)
        assert isinstance(op_node, IdentifiedNode)
        op = _generate_object(infograph, op_node, cls._atom_op_generator)
        args = []
        arg_list_node = infograph.value(rootnode, RIF.args)
        if arg_list_node is not None:
            arg_list = rdflib.collection.Collection(infograph, arg_list_node)
            for x in arg_list:
                assert isinstance(x, IdentifiedNode)
                args.append(_generate_object(infograph, x,
                                             cls._atom_args_generator))
        return cls(op, args)

    def __repr__(self) -> str:
        return "%s (%s)" % (self.op, ", ".join(str(x) for x in self.args))

class rif_external(_resolvable_gen, _rif_check):
    op: URIRef
    args: Sequence[ATOM]
    _atom_args_generator: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], ATOM]]
    def __init__(self, op: URIRef, args: Iterable[ATOM]):
        self.op = op
        self.args = list(args)

    def check(self,
            machine: durable_reasoner.machine,
            bindings: BINDING = {},
            ) -> bool:
        raise NotImplementedError()

    def as_machinefact(self) -> external:
        args = [x.as_machinefact() if isinstance(x, _resolvable_gen) else x for x in self.args]
        return external(self.op, args)

    def as_resolvable(self, machine: durable_reasoner.machine) -> RESOLVABLE:
        args = [_get_resolveable(x, machine) for x in self.args]
        return machine.get_binding_action(self.op, args)

    def get_replacement_node(self,
                      machine: durable_reasoner.machine,
            ) -> TRANSLATEABLE_TYPES:
        args = [_get_resolveable(x, machine) for x in self.args]
        return machine.get_replacement_node(self.op, args)

    def get_binding_action(self,
                      machine: durable_reasoner.machine,
            ) -> RESOLVABLE:
        return self.as_resolvable(machine)
        #return machine.get_binding_action(self.op, self.args)

    def generate_condition(self,
                           machine: durable_reasoner.machine,
                           ) -> Callable[[BINDING], bool]:
        raise NotImplementedError()

    def _add_pattern(self, rule: durable_reasoner.rule) -> None:
        m = self.as_machinefact()
        rule.orig_pattern.append(m)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_external":
        content_node: rdflib.IdentifiedNode = infograph.value(rootnode, RIF.content) #type: ignore[assignment]
        op_node, = infograph.objects(content_node, RIF.op)
        assert isinstance(op_node, IdentifiedNode)
        op = slot2node(infograph, op_node)
        assert isinstance(op, URIRef), "rif_external expects an uri as op"
        arg_list_node, = infograph.objects(content_node, RIF.args)
        assert isinstance(arg_list_node, IdentifiedNode)
        arg_list = rdflib.collection.Collection(infograph, arg_list_node)
        args = []
        for x in arg_list:
            assert isinstance(x, IdentifiedNode)
            x_type = infograph.value(x, RDF.type)
            args.append(cls._atom_args_generator[x_type](infograph, x))
        return cls(op, args)

    def __repr__(self) -> str:
        return "external %s (%s)" % (self.op, ", ".join(str(x) for x in self.args))


class rif_member(rif_fact):
    cls: ATOM
    instance: ATOM
    _instance_generators: Mapping[IdentifiedNode,
                                  Callable[[Graph, IdentifiedNode], ATOM]]
    _class_generators: Mapping[IdentifiedNode,
                               Callable[[Graph, IdentifiedNode], ATOM]]

    def __repr__(self) -> str:
        return "rif(%s # %s)" % (self.instance, self.cls)

    def __init__(self, instance: ATOM, cls: ATOM) -> None:
        self.instance = instance
        self.cls = cls

    def _add_pattern(self, rule: durable_reasoner.rule) -> None:
        instance = _try_as_machinefact(self.instance)
        cls = _try_as_machinefact(self.cls)
        f = machine_facts.member(instance, cls)
        rule.orig_pattern.append(f)

    def _create_facts(self) -> Iterable[machine_facts.member]:
        cls = _try_as_machinefact(self.cls)
        instance = _try_as_machinefact(self.instance)
        yield machine_facts.member(instance, cls)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_member":
        q = dict(infograph.predicate_objects(rootnode))
        instance_node, = infograph.objects(rootnode, RIF.instance)
        class_node, = infograph.objects(rootnode, RIF["class"])
        assert isinstance(instance_node, IdentifiedNode)
        assert isinstance(class_node, IdentifiedNode)
        instance = _generate_object(infograph, instance_node,
                                    cls._instance_generators)
        class_ = _generate_object(infograph, class_node,
                                  cls._class_generators)
        return cls(instance, class_)

class rif_subclass(rif_fact):
    sub_class: ATOM
    super_class: ATOM
    def __init__(self, sub_class: ATOM, super_class: ATOM) -> None:
        self.sub_class = sub_class
        self.super_class = super_class

    def _add_pattern(self, rule: durable_reasoner.rule) -> None:
        raise NotImplementedError()

    def _create_facts(self) -> Iterable[fact]:
        raise NotImplementedError()

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_subclass":
        #info = dict(infograph.predicate_objects(rootnode))
        #sub_node = info[RIF["sub"]]
        #super_node = info[RIF["super"]]
        sub_node, = infograph.objects(rootnode, RIF["sub"])
        super_node, = infograph.objects(rootnode, RIF["super"])
        assert isinstance(sub_node, IdentifiedNode)
        assert isinstance(super_node, IdentifiedNode)
        sub_obj = slot2node(infograph, sub_node)
        super_obj = slot2node(infograph, super_node)
        return cls(sub_obj, super_obj)

    def check(self,
            machine: durable_reasoner.machine,
            bindings: BINDING = {},
            ) -> bool:
        sub_class = self.sub_class.as_machinefact() if isinstance(self.sub_class, _resolvable_gen) else self.sub_class
        super_class = self.super_class.as_machinefact() if isinstance(self.super_class, _resolvable_gen) else self.super_class
        f = machine_facts.subclass(sub_class, super_class)
        return f.check_for_pattern(machine, bindings)

    def __repr__(self) -> str:
        return "%s # %s" % (self.sub_class, self.super_class)


class rif_frame(rif_fact):
    #facts: Iterable[machine_facts.frame]
    obj: SATOM
    slots: Iterable[SLOT]
    def __init__(self, obj: SATOM,
                 slots: Iterable[SLOT],
                 ) -> None:
        self.obj = obj
        self.slots = [(x,y) for x,y in slots]

    @property
    def facts(self) -> Iterable[machine_facts.frame]:
        obj = _try_as_machinefact(self.obj)
        for slotkey, slotvalue in self._machinefact_slots:
            sk = _try_as_machinefact(slotkey)
            sv = _try_as_machinefact(slotvalue)
            yield machine_facts.frame(obj, sk, sv)

    def _create_facts(self) -> Iterable[fact]:
        return self.facts

    @property
    def _machinefact_slots(self) -> Iterable[Tuple[Union[TRANSLATEABLE_TYPES, external, Variable], Union[TRANSLATEABLE_TYPES, external, Variable]]]:
        for slot in self.slots:
            slotkey, slotvalue = (x.as_machinefact() if isinstance(x, _resolvable_gen) else x for x in slot)
            yield slotkey, slotvalue

    def _add_pattern(self, rule: durable_reasoner.rule) -> None:
        obj = _try_as_machinefact(self.obj)
        for slotkey, slotvalue in self._machinefact_slots:
            sk = _try_as_machinefact(slotkey)
            sv = _try_as_machinefact(slotvalue)
            f = machine_facts.frame(obj, sk, sv)
            rule.orig_pattern.append(f)

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

    @dataclass
    class __assert_action(_child_action):
        parent: "rif_frame"
        facts: Iterable[machine_facts.frame]
        machine: durable_reasoner.machine
        def __call__(self, bindings: BINDING) -> None:
            for f in self.facts:
                f.assert_fact(self.machine, bindings)

    def generate_assert_action(self,
                               machine: durable_reasoner.machine,
                               ) -> Callable[[machine_facts.BINDING], None]:
        """
        :TODO: Creation of variable is not safe
        """
        facts = []
        obj = _try_as_machinefact(self.obj)
        for slotkey, slotvalue in self._machinefact_slots:
            facts.append(machine_facts.frame(obj, slotkey, slotvalue))
        return self.__assert_action(self, facts, machine)

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
        return "%s[%s]" % (conv(self.obj), slots) #type: ignore[arg-type]

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_frame":
        info = dict(infograph.predicate_objects(rootnode))
        slotinfo = []
        #q = rdflib.collection.Collection(infograph, info[RIF.slots])
        q_root, = infograph.objects(rootnode, RIF.slots)
        q = rdflib.collection.Collection(infograph, q_root)
        for x in q:
            _slotkey, = infograph.objects(x, RIF.slotkey)
            _slotvalue, = infograph.objects(x, RIF.slotvalue)
            assert isinstance(_slotkey, IdentifiedNode)
            assert isinstance(_slotvalue, IdentifiedNode)
            slotinfo.append((slot2node(infograph, _slotkey), slot2node(infograph, _slotvalue)))
        _obj, = infograph.objects(rootnode, RIF.object)
        assert isinstance(_obj, IdentifiedNode)
        obj = slot2node(infograph, _obj)
        assert not isinstance(obj, rif_external),\
                "rif_external not valid as input for frame.obj"
        return cls(obj, slotinfo, **kwargs)

class rif_retract(_action_gen):
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
    def fact_or_atom(self) -> Union["rif_frame", IdentifiedNode]:
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
                 **kwargs: typ.Any) -> "rif_retract":
        from .class_rdfmodel import rdfmodel
        model = rdfmodel()
        target_node: rdflib.IdentifiedNode = infograph.value(rootnode, RIF.target) #type: ignore[assignment]
        target = model.generate_object(infograph, target_node)
        return cls(target)


class rif_ineg(_rif_check):
    formula: FORMULA
    _formula_generator: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], FORMULA]]
    def __init__(self, formula: FORMULA):
        self.formula = formula

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_ineg":
        target_node = infograph.value(rootnode, RIF.formula)
        assert isinstance(target_node, IdentifiedNode)
        target = _generate_object(infograph, target_node,
                                  cls._formula_generator)
        return cls(target)

    def _add_pattern(self, rule: durable_reasoner.rule) -> None:
        raise NotImplementedError()

    def check(self,
            machine: durable_reasoner.machine,
            bindings: BINDING = {},
            ) -> bool:
        raise NotImplementedError()

    def __repr__(self) -> str:
        return "INeg(%s)" % self.formula

class rif_modify(_action_gen):
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
                 **kwargs: typ.Any) -> "rif_modify":
        from .class_rdfmodel import rdfmodel
        model = rdfmodel()
        target: rdflib.IdentifiedNode = infograph.value(rootnode, RIF.target) #type: ignore[assignment]
        target_type = infograph.value(target, RDF.type)
        fact = model.generate_object(infograph, target)
        assert isinstance(fact, rif_frame)
        return cls(fact, **kwargs)

    def __repr__(self) -> str:
        return "Modify(%s)" % self.fact


class rif_assert(_action_gen):
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

class rif_equal(rif_external):
    op: URIRef = pred["XMLLiteral-equal"]
    def __init__(self, left: ATOM, right: ATOM):
        self.args = (left, right)

    @property
    def left(self) -> ATOM:
        return self.args[0]

    @property
    def right(self) -> ATOM:
        return self.args[1]

    @dataclass
    class _condition(_child_action):
        parent: "rif_equal"
        left: Callable[[BINDING], Literal]
        right: Callable[[BINDING], Literal]
        def __call__(self, bindings: BINDING) -> bool:
            left = _resolve(self.left, bindings)
            right = _resolve(self.right, bindings)
            return Literal(left == right)#type: ignore[return-value]

    def __repr__(self) -> str:
        return "(%s = %s)" % (self.left, self.right)

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


class rif_list(_resolvable_gen):
    items: Iterable[Union[TRANSLATEABLE_TYPES, "rif_list"]]
    _item_generator: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], ATOM]]
    def __init__(self,
                 items: Iterable[Union[TRANSLATEABLE_TYPES, "rif_list"]],
                 ) -> None:
        self.items = list(items)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 extraDocuments: Mapping[IdentifiedNode, Graph] = {},
                 ) -> "rif_list":
        info = dict(infograph.predicate_objects(rootnode))
        item_list_node, = infograph.objects(rootnode, RIF.items)
        item_list = rdflib.collection.Collection(infograph, item_list_node)
        items = []
        for item in item_list:
            item_type = infograph.value(item, RDF.type)
            q = cls._item_generator[item_type](infograph, item)
            assert not isinstance(q, (Variable, rif_external))
            items.append(q)
        return cls(items)

    def as_resolvable(self, machine: durable_reasoner.machine) -> RESOLVABLE:
        raise NotImplementedError()

    def as_machinefact(self) -> machine_list:
        items = [_try_as_machinefact(x) for x in self.items]
        return machine_list(items)


rif_implies._if_generators = {
        RIF.And: rif_and.from_rdf,
        RIF.Frame: rif_frame.from_rdf,
        RIF.Atom: rif_atom.from_rdf,
        RIF.Subclass: rif_subclass.from_rdf,
        RIF.External: rif_external.from_rdf,
        RIF.INeg: rif_ineg.from_rdf,
        }
rif_implies._then_generators = {
        RIF.Frame: rif_frame.from_rdf,
        RIF.Do: rif_do.from_rdf,
        RIF.Atom: rif_atom.from_rdf,
        }

_formulas: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode],
                                            _rif_check]]\
        = {RIF.External: rif_external.from_rdf,
           RIF.Frame: rif_frame.from_rdf,
           RIF.Equal: rif_equal.from_rdf,
           RIF.Atom: rif_atom.from_rdf,
           RIF.Member: rif_member.from_rdf,
           }
rif_and._formulas_generators = dict(_formulas)
rif_exists._formula_generators = {#RIF.External: rif_external.from_rdf,
                                  RIF.Frame: rif_frame.from_rdf,
                                  #RIF.Equal: rif_equal.from_rdf,
                                  RIF.Atom: rif_atom.from_rdf,
                                  }
rif_ineg._formula_generator = {RIF.Frame: rif_frame.from_rdf,
                               RIF.Atom: rif_atom.from_rdf,
                               }
#rif_equal._side_generators = {}
rif_group._sentence_generators = {
        RIF.Forall: rif_forall.from_rdf,
        RIF.Group: rif_group.from_rdf,
        RIF.Implies: rif_implies.from_rdf,
        RIF.Frame: rif_frame.from_rdf,
        RIF.Atom: rif_atom.from_rdf,
        RIF.Member: rif_member.from_rdf,
        }

_term_generators: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], ATOM]] = {
        RIF.Const: slot2node,
        RIF.Var: slot2node,
        RIF.List: slot2node,
        RIF.External: rif_external.from_rdf,
        }
rif_external._atom_args_generator = _term_generators
rif_atom._atom_op_generator = _term_generators
rif_atom._atom_args_generator = _term_generators
rif_list._item_generator = _term_generators

rif_member._instance_generators = _term_generators
rif_member._class_generators = _term_generators



def _get_resolveable(x: Union[TRANSLATEABLE_TYPES, _resolvable_gen, Variable], machine: durable_reasoner.machine) -> RESOLVABLE:
    if isinstance(x, (IdentifiedNode, Literal, Variable, term_list)):
        return x
    elif isinstance(x, Variable):
        raise NotImplementedError()
    return x.as_resolvable(machine)
