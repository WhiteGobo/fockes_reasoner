import abc
import logging
logger = logging.getLogger(__name__)
import uuid
import itertools as it
from . import durable_reasoner
from .durable_reasoner import machine_facts, fact, NoPossibleExternal, _resolve, ATOM_ARGS, term_list, pattern_generator, rule
from .durable_reasoner.machine_facts import external, TRANSLATEABLE_TYPES, executable
import rdflib
from rdflib import IdentifiedNode, Graph, Variable, Literal, URIRef, BNode
from rdflib.collection import Collection
import typing as typ
from typing import Union, Iterable, Any, Callable, MutableMapping, List, Tuple, Optional, Mapping, Set, overload, cast, Hashable, TypeVar, Generic, TypeAlias, Protocol
from .shared import RIF, pred, XSD
from rdflib import RDF
from . import durable_reasoner
from .durable_reasoner import machine, action_assert, action_retract
from .durable_reasoner import BINDING, RESOLVABLE, BINDING_WITH_BLANKS
from .durable_reasoner import special_externals 
from dataclasses import dataclass
from collections.abc import Sequence

_R = TypeVar('_R', covariant=True)

RIFGEN: TypeAlias = Callable[[Graph, IdentifiedNode], _R]
#class RIFGEN(Protocol[_R]):
#    def __call__(self,
#                 graph: Graph,
#                 rootnode: IdentifiedNode,
#                 **kwargs: Any,
#                 ) -> _R: ...

ATOM = Union[TRANSLATEABLE_TYPES, Variable, "rif_external", "rif_list"]
SLOT = Tuple[ATOM, ATOM]
RIF_ATOM = Union[TRANSLATEABLE_TYPES, "rif_external", Variable, "rif_list"]
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

class _rif_class(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def from_rdf(cls: type[_R], infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: Any) -> _R: ...


class _rule_gen(_rif_class):
    @abc.abstractmethod
    def create_rules(self, machine: durable_reasoner.Machine) -> None:
        ...

class _action_gen(_rif_class):
    @abc.abstractmethod
    def generate_action(self,
                        machine: durable_reasoner.Machine,
                        ) -> Tuple[external | fact, Iterable[Variable]]:
        ...


class RIF_ACTION(_action_gen):
    """Metaclass for action that are done within a :term:`production rule`."""

class _rif_check(pattern_generator, _rif_class):
    """Class that has everything to do with checking if some type of statement
    holds true or not.
    """
    @abc.abstractmethod
    def check(self,
            machine: durable_reasoner.Machine,
            bindings: BINDING_WITH_BLANKS = {},
            ) -> bool:
        ...


class _resolvable_gen(_rif_class):
    """Subclass can be used to retrieve a :term:`translateable object` as
    described in bridge-rdflib. Is equal to a :term:`formula` in :term:`RIF`
    """
    @abc.abstractmethod
    def as_machineterm(self) -> Union[external, TRANSLATEABLE_TYPES]:
        """
        :TODO: This should be as_machineterm
        """
        ...


class _rif_formula(_resolvable_gen, _rif_check):
    """All :term:`formulas<RIF formula>` can be used as condition for rules.
    """


class rif_fact(_rif_check, RIF_ACTION, _action_gen, _rule_gen):
    @abc.abstractmethod
    def _create_facts(self) -> Iterable[fact]:
        ...

    @property
    @abc.abstractmethod
    def used_variables(self) -> Iterable[Variable]:
        ...

    def _add_pattern(self, rule: durable_reasoner.rule) -> None:
        rule.orig_pattern.extend(self._create_facts())

    def check(self,
            machine: durable_reasoner.Machine,
            bindings: BINDING_WITH_BLANKS = {},
            ) -> bool:
        test_facts = list(self._create_facts())
        try:
            return machine.check_statement(test_facts, bindings)
        except Exception:
            logger.error("Raised error when executing check of %s" % self)
            logger.error(str(test_facts))
            raise

    def generate_action(self,
                        machine: durable_reasoner.Machine,
                        ) -> Tuple[external | fact, Iterable[Variable]]:
        return self.generate_assert_action(machine), self.used_variables

    def generate_assert_action(self,
                               machine: durable_reasoner.Machine,
                               ) -> external:
        """
        :TODO: Creation of variable is not safe
        """
        #return action_assert(self._create_facts(), machine)
        return external(special_externals.assert_fact.op, self._create_facts())

    def generate_retract_action(self,
                      machine: durable_reasoner.Machine,
                      ) -> external:
        return external(special_externals.retract_fact.op,
                        self._create_facts())
    #return action_retract(self._create_facts(), machine)

    def create_rules(self, machine: durable_reasoner.Machine) -> None:
        """Is called, when frame is direct sub to a Group"""
        action = self.generate_assert_action(machine)
        machine.add_init_action(action)


class _external_gen(_resolvable_gen, _rif_check):
    @property
    @abc.abstractmethod
    def args(self) -> Iterable[ATOM | "_external_gen" | rif_fact]:
        ...

    @property
    @abc.abstractmethod
    def op(self) -> Hashable | URIRef:
        ...

    def check(self,
            machine: durable_reasoner.Machine,
            bindings: BINDING_WITH_BLANKS = {},
            ) -> bool:
        args = list(it.chain.from_iterable(_try_as_machineterm(arg)
                                           for arg in self.args))
        q = external(self.op, args)
        return machine.check_statement([q], bindings)

    def as_machineterm(self) -> external:
        args = list(it.chain.from_iterable(_try_as_machineterm(arg)
                                           for arg in self.args))
        return external(self.op, args)

    def _add_pattern(self, rule: durable_reasoner.rule) -> None:
        m = self.as_machineterm()
        rule.orig_pattern.append(m)


    def __repr__(self) -> str:
        return "external %s (%s)" % (self.op, ", ".join(str(x) for x in self.args))


@overload
def _try_as_machineterm(
        x: Union[rif_fact],
        ) -> Iterable[fact]: ...

@overload
def _try_as_machineterm(
        x: Union[TRANSLATEABLE_TYPES, external, Variable,
                 _resolvable_gen],
        ) -> Iterable[Union[TRANSLATEABLE_TYPES, external, Variable]]: ...

def _try_as_machineterm(
        x: Union[TRANSLATEABLE_TYPES, external, Variable,
                 _resolvable_gen, rif_fact],
        ) -> Iterable[Union[TRANSLATEABLE_TYPES, external, Variable, fact]]:
    """
    :TODO: Split this method into one for facts and one for others
    """
    if isinstance(x, _resolvable_gen):
        return [x.as_machineterm()]
    elif isinstance(x, rif_fact):
        return x._create_facts()
    else:
        return [x]

T = TypeVar('T')
def _generate_object(infograph: Graph, target: IdentifiedNode,
                     type_to_generator: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], T]],
                     ) -> T:
    """
    :raises KeyError:
    """
    target_type = infograph.value(target, RDF.type)
    if not isinstance(target_type, IdentifiedNode):
        raise Exception("Syntaxerror in graph. Missing type for %s" % target)
    try:
        gen = type_to_generator[target_type]
    except KeyError as err:
        raise KeyError("%s missing in generatordict %s"
                       % (target_type, type_to_generator)) from err
    return gen(infograph, target)


def slot2node(infograph: Graph, x: IdentifiedNode,
              ) -> Union[IdentifiedNode, Literal, Variable]:
    """Transforms const and variables to nodes
    :TODO: Local variables are not correctly transformed but instead
        just BNodes are used.
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
        return BNode(_sn_gen=lambda: str(val),
                     _prefix=str(infograph.identifier))
    elif t == RIF.Const:
        raise NotImplementedError(val_info)
    else:
        raise NotImplementedError(t)

class rif_document(_rif_class):
    payload: Optional["rif_group"]
    directives: Iterable["rif_import"]
    def __init__(self, payload: Optional["rif_group"] = None,
                 directives: Iterable["rif_import"] = []) -> None:
        self.payload = payload
        self.directives = list(directives)

    def create_rules(self, machine: durable_reasoner.Machine,
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
            directives_lists = cast(Iterable[IdentifiedNode],
                                    Collection(infograph, directives_node))
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
    profile: Optional[Literal]
    location: URIRef
    def __init__(self,
                 location: Literal | URIRef,
                 profile: Optional[Literal] = None):
        if isinstance(location, URIRef):
            self.location = location
        else:
            self.location = URIRef(location)
        self.profile = profile

    def apply_to(self, machine: durable_reasoner.Machine,
                 ) -> None:
        args: Iterable[Literal | URIRef]
        op = special_externals.import_data.op
        if self.profile is not None:
            args = [self.location, self.profile]
        else:
            args = [self.location]
        machine.apply(external(op, args))

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 extraDocuments: Mapping[IdentifiedNode, Graph] = {},
                 **kwargs: Any) -> "rif_import":
        location, = cast(Iterable[Literal | URIRef],
                         infograph.objects(rootnode, RIF.location))
        profile = cast(Literal, infograph.value(rootnode, RIF.profile))
        #assert isinstance(location, URIRef), repr(location)
        if profile:
            return cls(location, profile)
        return cls(location)


class rif_group(_rule_gen):
    sentences: tuple[Union["rif_forall", "rif_frame", "rif_group", "rif_implies"], ...]
    _sentence_generators: Mapping[IdentifiedNode, RIFGEN[Any]]
    def __init__(self,
                 sentences: Iterable[Union["rif_forall", "rif_frame", "rif_group", "rif_implies"]],
                 ) -> None:
        self.sentences = tuple(sentences)

    def create_rules(self, machine: durable_reasoner.Machine) -> None:
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
            assert isinstance(sentence_type, IdentifiedNode)
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

    def _create_implication(self, machine: durable_reasoner.Machine) -> None:
        newrule = machine.create_rule_builder()
        conditions: list[Callable[[BINDING], Union[Literal, bool]]] = []
        self.formula._add_condition_as_pattern(newrule)
        if isinstance(self.formula.then_, rif_do):
            raise NotImplementedError()
        if len(conditions) == 0:
            implicated_fact = self.formula.then_
            action, q = implicated_fact.generate_action(machine)
        else:
            raise NotImplementedError()
        newrule.set_action(action, q)
        logger.info("create rule %r" % newrule)
        newrule.finalize()

    def create_rules(self, machine: durable_reasoner.Machine) -> None:
        #if self.pattern is None and isinstance(self.formula, rif_implies)\
        #        and isinstance(self.formula.then_, (rif_frame,)):
        #    return self._create_implication(machine)
        if isinstance(self.formula, rif_implies):
            if self.pattern is not None:
                raise NotImplementedError()
            newrule = machine.create_rule_builder()
            self.formula._add_condition_as_pattern(newrule)
            action, used_variables = self.formula.then_.generate_action(machine)
            newrule.set_action(action, used_variables)
            newrule.finalize()
            return
        elif self.pattern is not None:
            raise NotImplementedError()
        else:
            raise NotImplementedError()
            self._create_action(machine)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: IdentifiedNode,
                 **kwargs: Any) -> "rif_forall":
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
    if_: Union[_rif_formula, rif_fact, "rif_ineg", "rif_external"]
    then_: Union[rif_fact, "rif_do"]
    #is set at end of file
    _if_generators: Mapping[IdentifiedNode, RIFGEN[Union[_rif_formula, rif_fact, "rif_ineg", "rif_external"]]]
    _then_generators: Mapping[IdentifiedNode, RIFGEN[Union[rif_fact, "rif_do"]]]
    def __init__(self,
                 if_: Union[_rif_formula, rif_fact, "rif_ineg", "rif_external"],
                 then_: Union[rif_fact, "rif_do"]):
        self.if_ = if_
        self.then_ = then_

    @dataclass
    class conditional(_child_action):
        parent: "rif_implies"
        conditions: list[Callable]
        action: Callable
        machine: durable_reasoner.Machine
        def __call__(self, bindings: BINDING) -> None:
            for c in self.conditions:
                if not c(bindings):
                    self.machine.logger.debug("stopped %s because %s" % (self, c))
                    return
            self.action(bindings)

        def __repr__(self) -> str:
            return f"condition {self.parent}"

    def _add_condition_as_pattern(self, newrule: rule) -> None:
        if isinstance(self.if_, rif_and):
            for pat in self.if_.formulas:
                newrule.orig_pattern.append(pat)
                logger.debug("added pat %s" % pat)
        else:
            newrule.orig_pattern.append(self.if_)

    def create_rules(self, machine: durable_reasoner.Machine) -> None:
        """Create this as a rule for an expertsystem.

        """
        newrule = machine.create_implication_builder()
        self._add_condition_as_pattern(newrule)
        action, used_variables = self.then_.generate_action(machine)
        newrule.set_action(action, used_variables)
        logger.debug("create implication %r" % newrule)
        newrule.finalize()

    @dataclass
    class _conditional:
        condition: Callable[[BINDING], Union[bool, Literal]]
        action: Callable[[BINDING], None]

        def __call__(self, bindings: BINDING) -> None:
            if self.condition(bindings):
                self.action(bindings)


    def generate_action(self,
                        machine: durable_reasoner.Machine,
                        ) -> Tuple[external | fact, Iterable[Variable]]:
        raise NotImplementedError("removed generate_condition completly")
        condition = self.if_.generate_condition(machine)
        implicated_action, used_variables = self.then_.generate_action(machine)
        act = self._conditional(condition, implicated_action)
        return act, used_variables

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: Any,
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
    blank_vars: Iterable[Variable]
    _formula_generators: Mapping[IdentifiedNode, RIFGEN[rif_fact]]
    def __init__(self, formula: rif_fact, blank_vars: Iterable[Variable]):
        self.formula = formula
        self.blank_vars = list(blank_vars)

    def __repr__(self) -> str:
        return "exists %s (%s)" % (", ".join(str(x) for x in self.blank_vars),
                                   self.formula)

    def _add_pattern(self, rule: durable_reasoner.rule) -> None:
        raise NotImplementedError()

    def check(self,
            machine: durable_reasoner.Machine,
            bindings: Optional[BINDING_WITH_BLANKS] = None,
            ) -> bool:
        if bindings is None:
            bindings = {x: None for x in self.blank_vars}
        else:
            bindings.update({x: None for x in self.blank_vars})
        test_facts = list(self.formula._create_facts())
        return machine.check_statement(test_facts, bindings)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: IdentifiedNode,
                 **kwargs: Any,
                 ) -> "rif_exists":
        vars_node, = infograph.objects(rootnode, RIF.vars)
        var_list = rdflib.collection.Collection(infograph, vars_node)
        blank_vars: List[Variable] = []
        for x in var_list:
            assert isinstance(x, IdentifiedNode)
            x_var = slot2node(infograph, x)
            assert isinstance(x_var, Variable)
            blank_vars.append(x_var)
        formula_node, = infograph.objects(rootnode, RIF.formula)
        assert isinstance(formula_node, IdentifiedNode)
        formula = _generate_object(infograph, formula_node,
                                   cls._formula_generators)
        return cls(formula, blank_vars)

class rif_and(_external_gen, _rif_formula):
    formulas: Iterable[_external_gen | rif_fact]
    _formulas_generators: Mapping[IdentifiedNode, RIFGEN[_external_gen | rif_fact]]
    op: Hashable = special_externals.condition_and.op
    def __init__(self, formulas: Iterable[_external_gen | rif_fact]):
        self.formulas = list(formulas)

    @property
    def args(self) -> Iterable[_external_gen | rif_fact]:
        return self.formulas

    def __repr__(self) -> str:
        return "(%s)" % " & ".join(repr(x) for x in self.formulas)

    def check(self,
            machine: durable_reasoner.Machine,
            bindings: BINDING_WITH_BLANKS = {},
            ) -> bool:
        return all(f.check(machine, bindings) for f in self.formulas)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: IdentifiedNode,
                 **kwargs: Any,
                 ) -> "rif_and":
        try:
            formula_list_node, = infograph.objects(rootnode, RIF.formulas)
        except ValueError as err:
            raise Exception("Syntaxerror of RIF document") from err
        formula_list: Iterable[IdentifiedNode] = rdflib.collection.Collection(infograph, formula_list_node) #type: ignore[assignment]
        formulas: list[Union["_external_gen", rif_fact]] = []
        for formula_node in formula_list:
            next_formula = _generate_object(infograph, formula_node, cls._formulas_generators)
            formulas.append(next_formula)
        return cls(formulas)

class rif_do(_action_gen):
    target: List[RIF_ACTION]
    _do_action_generator: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], RIF_ACTION]]
    def __init__(self, actions: Iterable[RIF_ACTION]):
        self.actions = list(actions)

    def generate_action(self,
                        machine: durable_reasoner.Machine,
                        ) -> Tuple[external | fact, Iterable[Variable]]:
        self._all_actions = []
        used_variables: Set[Variable] = set()
        for act in self.actions:
            tmp_act, tmp_vars = act.generate_action(machine)
            self._all_actions.append(tmp_act)
            used_variables.update(tmp_vars)
        return external(special_externals.do.op, list(self._all_actions)),\
                used_variables
        #return self._act, used_variables

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: IdentifiedNode,
                 **kwargs: Any,
                 ) -> "rif_do":
        try:
            target_list_node, = infograph.objects(rootnode, RIF.actions)
        except ValueError as err:
            raise Exception("Syntaxerror of RIF document") from err
        target_list: Iterable[IdentifiedNode] = rdflib.collection.Collection(infograph, target_list_node) #type: ignore[assignment]
        actions: List[Union[rif_assert, "rif_retract", "rif_modify", "rif_execute"]] = []
        for target_node in target_list:
            try:
                next_target = _generate_object(infograph, target_node,
                                           cls._do_action_generator)
            except KeyError as err:
                raise ValueError("Cant generate target for %s." % cls) from err
            assert isinstance(next_target, (rif_assert, rif_retract, rif_modify, rif_execute)), "got unexpected rif object. Invalid RIF document?"
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

    @property
    def used_variables(self) -> Iterable[Variable]:
        return _get_variables((self.op, *self.args))

    def _create_facts(self) -> Iterable[fact]:
        args = list(it.chain.from_iterable(_try_as_machineterm(arg)
                                           for arg in self.args))
        yield machine_facts.atom(self.op, args)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_atom":
        op_node = infograph.value(rootnode, RIF.op)
        assert isinstance(op_node, IdentifiedNode)
        try:
            op = _generate_object(infograph, op_node, cls._atom_op_generator)
        except KeyError as err:
            raise ValueError("Cant generate 'op' for %s." % cls) from err
        assert isinstance(op, IdentifiedNode)
        args: List[RIF_ATOM] = []
        arg_list_node = infograph.value(rootnode, RIF.args)
        if arg_list_node is not None:
            arg_list = rdflib.collection.Collection(infograph, arg_list_node)
            for x in arg_list:
                assert isinstance(x, IdentifiedNode)
                try:
                    x_ = _generate_object(infograph, x,
                                          cls._atom_args_generator)
                except KeyError as err:
                    raise ValueError("Cant generate 'args' for %s."
                                     % cls) from err
                assert isinstance(x_, (IdentifiedNode, Variable, Literal,
                                       rif_external, term_list, rif_list)), x_
                args.append(x_)
        return cls(op, args)

    def __repr__(self) -> str:
        return "%s (%s)" % (self.op, ", ".join(str(x) for x in self.args))

class rif_external(_external_gen):
    _atom_args_generator: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], ATOM]]
    def __init__(self, op: URIRef, args: Iterable[ATOM]) -> None:
        self._op = op
        self._args = list(args)

    @property
    def args(self) -> Sequence[ATOM]:
        return self._args

    @property
    def op(self) -> URIRef:
        return self._op

    def get_replacement_node(self,
                      machine: durable_reasoner.Machine,
            ) -> TRANSLATEABLE_TYPES:
        args = [_get_resolveable(x, machine) for x in self.args]
        return machine.get_replacement_node(self.op, args)

    @property
    def used_variables(self) -> Iterable[Variable]:
        return _get_variables((self.op, *self.args))

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
            assert isinstance(x_type, IdentifiedNode)
            args.append(cls._atom_args_generator[x_type](infograph, x))
        return cls(op, args)

class rif_or(_external_gen, _rif_formula):
    formulas: Iterable[_external_gen | rif_fact]
    _formulas_generators: Mapping[IdentifiedNode,
                                  RIFGEN[_external_gen | rif_fact]]
    op: Hashable = special_externals.condition_or.op
    def __init__(self, formulas: Iterable[_external_gen | rif_fact]):
        self.formulas = list(formulas)

    @property
    def args(self) -> Iterable[_external_gen | rif_fact]:
        return self.formulas

    def check(self,
            machine: durable_reasoner.Machine,
            bindings: BINDING_WITH_BLANKS = {},
            ) -> bool:
        return any(f.check(machine, bindings) for f in self.formulas)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: IdentifiedNode,
                 **kwargs: Any,
                 ) -> "rif_or":
        try:
            formula_list_node, = infograph.objects(rootnode, RIF.formulas)
        except ValueError as err:
            raise Exception("Syntaxerror of RIF document") from err
        formula_list: Iterable[IdentifiedNode] = rdflib.collection.Collection(infograph, formula_list_node) #type: ignore[assignment]
        formulas: list[_external_gen | rif_fact] = []
        for formula_node in formula_list:
            next_formula = _generate_object(infograph, formula_node, cls._formulas_generators)
            formulas.append(next_formula)
        return cls(formulas)


class rif_member(rif_fact):
    cls: ATOM
    instance: ATOM
    _instance_generators: Mapping[IdentifiedNode, RIFGEN[ATOM]]
    _class_generators: Mapping[IdentifiedNode, RIFGEN[ATOM]]

    @property
    def used_variables(self) -> Iterable[Variable]:
        return _get_variables((self.cls, self.instance))

    def __repr__(self) -> str:
        return "rif(%s # %s)" % (self.instance, self.cls)

    def __init__(self, instance: ATOM, cls: ATOM) -> None:
        self.instance = instance
        self.cls = cls

    def _create_facts(self) -> Iterable[machine_facts.member]:
        assert not isinstance(self.instance, rif_fact)
        cls, = _try_as_machineterm(self.cls)
        instance, = _try_as_machineterm(self.instance)
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
        try:
            instance = _generate_object(infograph, instance_node,
                                        cls._instance_generators)
        except KeyError as err:
            raise ValueError("Cant generate 'instance' for %s." % cls) from err
        try:
            class_ = _generate_object(infograph, class_node,
                                      cls._class_generators)
        except KeyError as err:
            raise ValueError("Cant generate 'class' for %s." % cls) from err
        return cls(instance, class_)

class rif_subclass(rif_fact):
    sub_class: ATOM
    super_class: ATOM
    def __init__(self, sub_class: ATOM, super_class: ATOM) -> None:
        self.sub_class = sub_class
        self.super_class = super_class

    @property
    def used_variables(self) -> Iterable[Variable]:
        return _get_variables((self.sub_class, self.super_class))

    def _create_facts(self) -> Iterable[fact]:
        sub_class, = _try_as_machineterm(self.sub_class)
        super_class, = _try_as_machineterm(self.super_class)
        yield machine_facts.subclass(sub_class, super_class)

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

    def __repr__(self) -> str:
        return "%s # %s" % (self.sub_class, self.super_class)


class rif_frame(rif_fact):
    #facts: Iterable[machine_facts.frame]
    obj: ATOM
    slots: Iterable[SLOT]
    _slot_generator: Mapping[IdentifiedNode, RIFGEN[ATOM]]
    def __init__(self, obj: ATOM,
                 slots: Iterable[SLOT],
                 ) -> None:
        self.obj = obj
        self.slots = [(x,y) for x,y in slots]

    @property
    def used_variables(self) -> Iterable[Variable]:
        return _get_variables(it.chain((self.obj,), it.chain(*self.slots)))

    def _create_facts(self) -> Iterable[fact]:
        obj, = _try_as_machineterm(self.obj)
        for slotkey, slotvalue in self.slots:
            sk, = _try_as_machineterm(slotkey)
            sv, = _try_as_machineterm(slotvalue)
            yield machine_facts.frame(obj, sk, sv)

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
            _key = _generate_object(infograph, _slotkey, cls._slot_generator)
            _value = _generate_object(infograph, _slotvalue, cls._slot_generator)
            slotinfo.append((_key, _value))
            #slotinfo.append((slot2node(infograph, _slotkey), slot2node(infograph, _slotvalue)))
        _obj, = infograph.objects(rootnode, RIF.object)
        assert isinstance(_obj, IdentifiedNode)
        obj = slot2node(infograph, _obj)
        assert not isinstance(obj, rif_external),\
                "rif_external not valid as input for frame.obj"
        return cls(obj, slotinfo, **kwargs)

R = TypeVar('R', bound=rif_fact | IdentifiedNode | Variable, covariant=True)

class rif_retract(RIF_ACTION, _action_gen, Generic[R]):
    #fact: Optional[Union[rif_frame]]
    #atom: Optional[Union[IdentifiedNode]]
    _fact_or_atom: R
    _target_generator: Mapping[IdentifiedNode,
                               Callable[[Graph, IdentifiedNode],
                                        IdentifiedNode | rif_fact | Variable | Literal]]
    def __init__(self, fact_or_atom: R) -> None:
        self._fact_or_atom = fact_or_atom
        if isinstance(fact_or_atom, rif_fact):
            self.fact = fact_or_atom
        elif isinstance(fact_or_atom, (IdentifiedNode, Variable)):
            self.atom = fact_or_atom
        else:
            raise TypeError(fact_or_atom, type(fact_or_atom))

    @property
    def used_variables(self) -> Iterable[Variable]:
        if isinstance(self._fact_or_atom, rif_fact):
            for x in (self._fact_or_atom,):
                if isinstance(x, Variable):
                    yield x
                elif isinstance(x, (IdentifiedNode, Literal)):
                    pass
                else:
                    for y in x.used_variables:
                        yield y
        elif isinstance(self._fact_or_atom, Variable):
            yield self._fact_or_atom
            

    def generate_action(self,
                        machine: durable_reasoner.Machine,
                        ) -> Tuple[external | fact, Iterable[Variable]]:
        if isinstance(self._fact_or_atom, rif_fact):
            return self._fact_or_atom.generate_retract_action(machine), self.used_variables
        elif isinstance(self._fact_or_atom, Variable):
            op = special_externals.retract_object.op
            return external(op, [self._fact_or_atom]), [self._fact_or_atom]
        else:
            op = special_externals.retract_object.op
            return external(op, [self._fact_or_atom]), [] #type: ignore[list-item]

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any,
                 ) -> "rif_retract":
        target: rdflib.IdentifiedNode = infograph.value(rootnode, RIF.target) #type: ignore[assignment]
        try:
            fact_or_atom = _generate_object(infograph, target, cls._target_generator)
        except KeyError as err:
            raise ValueError("Cant generate 'fact' for %s." % cls) from err
        assert not isinstance(fact_or_atom, Literal)
        return cls(fact_or_atom, **kwargs) #type: ignore[arg-type]


class rif_ineg(_external_gen):
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
        try:
            target = _generate_object(infograph, target_node,
                                  cls._formula_generator)
        except KeyError as err:
            raise ValueError("Cant generate 'target' for %s." % cls) from err
        return cls(target)

    def _add_pattern(self, rule: durable_reasoner.rule) -> None:
        raise NotImplementedError()

    def check(self,
            machine: durable_reasoner.Machine,
            bindings: BINDING_WITH_BLANKS = {},
            ) -> bool:
        raise NotImplementedError()

    def __repr__(self) -> str:
        return "INeg(%s)" % self.formula

class rif_modify(RIF_ACTION, _action_gen):
    fact: rif_fact
    _target_generator: Mapping[IdentifiedNode,
                               Callable[[Graph, IdentifiedNode], rif_fact]]
    def __init__(self, fact: rif_fact):
        self.fact = fact

    def generate_action(self,
                        machine: durable_reasoner.Machine,
                        ) -> Tuple[external, Iterable[Variable]]:
        """
        :TODO: This is wrong. It should modify and not assert
        """
        #return external(special_externals.modify_fact.op, self._create_facts())
        return self.fact.generate_assert_action(machine), self.fact.used_variables

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_modify":
        target: rdflib.IdentifiedNode = infograph.value(rootnode, RIF.target) #type: ignore[assignment]
        try:
            fact = _generate_object(infograph, target, cls._target_generator)
        except KeyError as err:
            raise ValueError("Cant generate 'fact' for %s." % cls) from err
        return cls(fact, **kwargs)

    def __repr__(self) -> str:
        return "Modify(%s)" % self.fact


class rif_assert(RIF_ACTION, _action_gen):
    fact: rif_fact
    _target_generator: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], rif_fact]]
    def __init__(self, myfact: rif_fact) -> None:
        self.fact = myfact

    def generate_action(self,
                        machine: durable_reasoner.Machine,
                        ) -> Tuple[external, Iterable[Variable]]:
        return self.fact.generate_assert_action(machine),\
                self.fact.used_variables

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_assert":
        target: rdflib.IdentifiedNode = infograph.value(rootnode, RIF.target) #type: ignore[assignment]
        try:
            myfact = _generate_object(infograph, target, cls._target_generator)
        except KeyError as err:
            raise ValueError("Cant generate 'fact' for %s." % cls) from err
        return cls(myfact, **kwargs)

    def __repr__(self) -> str:
        return "Assert( %s )" % self.fact

class rif_equal(_external_gen):
    op = special_externals.equality.op
    _side_generator: Mapping[IdentifiedNode, RIFGEN[ATOM]]
    def __init__(self, left: ATOM, right: ATOM):
        self._args = (left, right)

    @property
    def args(self) -> Tuple[ATOM, ATOM]:
        return self._args

    @property
    def left(self) -> ATOM:
        return self.args[0]

    @property
    def right(self) -> ATOM:
        return self.args[1]

    def __repr__(self) -> str:
        return "(%s = %s)" % (self.left, self.right)

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 **kwargs: typ.Any) -> "rif_equal":
        leftnode = infograph.value(rootnode, RIF.left)
        rightnode = infograph.value(rootnode, RIF.right)
        assert isinstance(leftnode, IdentifiedNode)
        assert isinstance(rightnode, IdentifiedNode)
        left = _generate_object(infograph, leftnode, cls._side_generator)
        right = _generate_object(infograph, rightnode, cls._side_generator)
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
                 **kwargs: Any,
                 ) -> "rif_list":
        info = dict(infograph.predicate_objects(rootnode))
        item_list_node, = infograph.objects(rootnode, RIF.items)
        item_list = rdflib.collection.Collection(infograph, item_list_node)
        items = []
        for item in item_list:
            assert isinstance(item, IdentifiedNode)
            item_type = infograph.value(item, RDF.type)
            assert isinstance(item_type, IdentifiedNode)
            q = cls._item_generator[item_type](infograph, item)
            assert not isinstance(q, (Variable, rif_external))
            items.append(q)
        return cls(items)

    def as_machineterm(self) -> external:
        items = list(it.chain.from_iterable(_try_as_machineterm(x)
                                            for x in self.items))
        return external(special_externals.create_list.op, items)

class rif_execute(RIF_ACTION, _action_gen):
    target: rif_atom
    _target_generator: Mapping[IdentifiedNode, Callable[[Graph, IdentifiedNode], rif_atom]]
    def __init__(self, target: rif_atom):
        self.target = target

    def generate_action(self,
                        machine: durable_reasoner.Machine,
                        ) -> Tuple[external | fact, Iterable[Variable]]:
        args = it.chain.from_iterable(_try_as_machineterm(arg)
                                      for arg in self.target.args)
        return executable(self.target.op, args, machine),\
                self.target.used_variables

    @classmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 rootnode: rdflib.IdentifiedNode,
                 extraDocuments: Mapping[IdentifiedNode, Graph] = {},
                 **kwargs: Any) -> "rif_execute":
        target: rdflib.IdentifiedNode = infograph.value(rootnode, RIF.target) #type: ignore[assignment]
        try:
            fact = _generate_object(infograph, target, cls._target_generator)
        except KeyError as err:
            raise ValueError("Cant generate 'fact' for %s." % cls) from err
        return cls(fact, **kwargs)


rif_implies._if_generators = {
        RIF.And: rif_and.from_rdf,
        RIF.Or: rif_or.from_rdf,
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
        RIF.Subclass: rif_subclass.from_rdf,
        }

rif_and._formulas_generators\
        = {RIF.External: rif_external.from_rdf,
           RIF.Frame: rif_frame.from_rdf,
           RIF.Equal: rif_equal.from_rdf,
           RIF.Atom: rif_atom.from_rdf,
           RIF.Member: rif_member.from_rdf,
           RIF.And: rif_and.from_rdf,
           RIF.Or: rif_or.from_rdf,
           }
rif_or._formulas_generators = dict(rif_and._formulas_generators)
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
        RIF.List: rif_list.from_rdf,
        RIF.External: rif_external.from_rdf,
        }
rif_external._atom_args_generator = _term_generators
rif_atom._atom_op_generator = _term_generators
rif_atom._atom_args_generator = _term_generators
rif_list._item_generator = _term_generators

rif_member._instance_generators = _term_generators
rif_member._class_generators = _term_generators

rif_do._do_action_generator = {
        RIF.Assert: rif_assert.from_rdf,
        RIF.Retract: rif_retract.from_rdf,
        RIF.Modify: rif_modify.from_rdf,
        RIF.Frame: rif_frame.from_rdf,
        RIF.Atom: rif_atom.from_rdf,
        RIF.Member: rif_member.from_rdf,
        RIF.Subclass: rif_subclass.from_rdf,
        RIF.Execute: rif_execute.from_rdf,
        }

rif_assert._target_generator = {
        RIF.Frame: rif_frame.from_rdf,
        RIF.Atom: rif_atom.from_rdf,
        RIF.Member: rif_member.from_rdf,
        RIF.Subclass: rif_subclass.from_rdf,
        }
rif_retract._target_generator = {
        RIF.Frame: rif_frame.from_rdf,
        RIF.Atom: rif_atom.from_rdf,
        RIF.Member: rif_member.from_rdf,
        RIF.Subclass: rif_subclass.from_rdf,
        RIF.Const: slot2node,
        RIF.Var: slot2node,
        }
rif_modify._target_generator = {
        RIF.Frame: rif_frame.from_rdf,
        RIF.Atom: rif_atom.from_rdf,
        RIF.Member: rif_member.from_rdf,
        RIF.Subclass: rif_subclass.from_rdf,
        }
rif_execute._target_generator = {
        RIF.Atom: rif_atom.from_rdf,
        }

rif_frame._slot_generator = rif_equal._side_generator = {
        RIF.Const: slot2node,
        RIF.Var: slot2node,
        RIF.List: rif_list.from_rdf,
        RIF.External: rif_external.from_rdf,
        }


def _get_variables(targetlist: Iterable[ATOM]) -> Iterable[Variable]:
    for x in targetlist:
        if isinstance(x, Variable):
            yield x
        elif isinstance(x, (IdentifiedNode, Literal)):
            pass
        elif isinstance(x, term_list):
            for y in x:
                if isinstance(y, Variable):
                    yield y
        elif isinstance(x, (rif_fact, rif_external)):
            for var in x.used_variables:
                yield var
        else:
            raise NotImplementedError(type(x), x)

def _get_resolveable(x: Union[TRANSLATEABLE_TYPES, _resolvable_gen, Variable], machine: durable_reasoner.Machine) -> RESOLVABLE:
    if isinstance(x, (IdentifiedNode, Literal, Variable, term_list)):
        return x
    elif isinstance(x, Variable):
        raise NotImplementedError()
    raise Exception()
