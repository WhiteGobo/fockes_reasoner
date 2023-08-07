"""Module that can produce a transformer for rif-graphs to graph representing
internal information.

:TODO: Move all information to rif_to_internal after the
    class graph_transformer is transferred to endpoint
"""
from collections.abc import Iterable, Callable, Mapping, MutableMapping, Container
import typing as typ
import rdflib
from rdflib import Variable
import durable.lang as rls
import durable.engine
import logging
logger = logging.getLogger(__name__)
from .durable_reasoner.durable_abc import FACTTYPE
from . import durable_reasoner as dur_reasoner
import uuid
from . import rif_to_internal as rif2internal
from . import internal_dataobjects as internal
from .durable_reasoner import durable_abc as dur_abc
from .shared import focke, string2rdflib, rdflib2string, act, func, pred
from . import models

class _builtin_functions:
    """Enables all functionability for external functions.
    """
    standard_symbols_for_export = [
            focke.Group,
            #focke.action,
            #focke.forall,
            #focke.frame_pattern,
            #focke.member_pattern,
            #focke.subclass_pattern,
            #focke.external_pattern,
            #focke.frame_condition,
            #focke.member_condition,
            #focke.subclass_condition,
            #focke.external_condition,
            #focke.execute,
            #focke.assert_frame,
            #focke.assert_member,
            #focke.assert_subclass,
            #focke.assert_external,
            ]
    """Standard symbols for export. This will not be here anymore because
    this is a basic class for other purposes, than translate rif to internal.
    """
    _symbols_for_export: set[str]
    """Will be initialized with standard_symbols_for_export"""

    def __init__(self) -> None:
        self._symbols_for_export = set(rdflib2string(x) for x
                                       in self.standard_symbols_for_export)

    def _label_for_export(
            self,
            bindings: dur_abc.BINDING,
            args: Iterable[dur_abc.TRANSLATEABLE_TYPES],
            ) -> None:
        """
        :TODO: integrate model to translate from internal datastructure
            to returned axioms.
        """
        #logger.info("export got bindings %s and args %s" %(bindings, args))
        t_args = [bindings[x] if isinstance(x, Variable) else rdflib2string(x)
                  for x in args]
        logger.info("labeling for export: %r" % t_args)
        self._symbols_for_export.update(t_args)

    @property
    def external_resolution(self) -> Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], Callable]:
        return {focke.export: self._label_for_export,
                act.print: self._print_string,
                func.sublist: self._get_sublist,
                func.append: self._append,
                func.get: self._get,
                func.count: self._count,
                getattr(func, "make-list"): self._make_list,
                getattr(pred, "numeric-greater-than"): self._greater_than,
                getattr(pred, "numeric-equal"): self._numeric_equal_to,
                }

    def _count(
            self,
            bindings: dur_abc.BINDING,
            args: Iterable[dur_abc.TRANSLATEABLE_TYPES],
            ) -> rdflib.Literal:
        targetedlist, = (bindings[x] if isinstance(x, Variable) else x
                         for x in args)
        for fact in rls.get_facts(self.rulename):#type: ignore[attr-defined]
            if fact.get(dur_abc.FACTTYPE) == dur_abc.LIST:
                if fact[dur_abc.LIST_ID] == targetedlist:
                    return rdflib.Literal(len(fact[dur_abc.LIST_MEMBERS]))
        raise Exception("couldnt find targeted list %r" % targetedlist)

    def _numeric_equal_to(
            self,
            bindings: dur_abc.BINDING,
            args: Iterable[dur_abc.TRANSLATEABLE_TYPES],
            ) -> rdflib.Literal:
        first, second = (string2rdflib(bindings[x]) if isinstance(x, Variable)
                         else x
                         for x in args)
        return rdflib.Literal(float(first) == float(second))

    def _greater_than(
            self,
            bindings: dur_abc.BINDING,
            args: Iterable[dur_abc.TRANSLATEABLE_TYPES],
            ) -> rdflib.Literal:
        first, second = (string2rdflib(bindings[x]) if isinstance(x, Variable)
                         else x
                         for x in args)
        return rdflib.Literal(first > second)

    def _get(
            self,
            bindings: dur_abc.BINDING,
            args: Iterable[dur_abc.TRANSLATEABLE_TYPES],
            ) -> dur_abc.TRANSLATEABLE_TYPES:
        x, y = iter(args)
        if isinstance(x, Variable):
            targetedlist = bindings[x]
        else:
            targetedlist = rdflib2string(x)
        if isinstance(y, Variable):
            index = string2rdflib(bindings[y])
        else:
            index = y
        for fact in rls.get_facts(self.rulename):#type: ignore[attr-defined]
            if fact.get(dur_abc.FACTTYPE) == dur_abc.LIST:
                if fact[dur_abc.LIST_ID] == targetedlist:
                    try:
                        return string2rdflib(\
                                fact[dur_abc.LIST_MEMBERS][int(index)])
                    except IndexError as err:
                        raise IndexError("Cant retrieve element %r from list %r" % (index, fact[dur_abc.LIST_MEMBERS])) from err
        raise Exception("couldnt find targeted list %r" % targetedlist)

    def _append(
            self,
            bindings: dur_abc.BINDING,
            args: Iterable[dur_abc.TRANSLATEABLE_TYPES],
            ) -> rdflib.BNode:
        t_args = [bindings[x] if isinstance(x, Variable) else rdflib2string(x)
                  for x in args]
        targetedlist = t_args[0]
        newelements = t_args[1:]
        for fact in rls.get_facts(self.rulename):#type: ignore[attr-defined]
            if fact.get(dur_abc.FACTTYPE) == dur_abc.LIST:
                if fact[dur_abc.LIST_ID] == targetedlist:
                    newlist = fact[dur_abc.LIST_MEMBERS] + newelements
                    return self._make_list({}, newlist)
        raise Exception("couldnt find targeted list %r" % targetedlist)

    def _get_sublist(
            self,
            bindings: dur_abc.BINDING,
            args: Iterable[dur_abc.TRANSLATEABLE_TYPES],
            ) -> rdflib.BNode:
        _args = iter(args)
        x = _args.__next__()
        targetedlist = bindings[x] if isinstance(x, Variable)\
                else rdflib2string(x)
        t_args = [int(string2rdflib(bindings[x])) if isinstance(x, Variable)
                  else int(x)
                  for x in _args]
        start = t_args[0]
        try:
            end = int(t_args[1])
        except IndexError:
            end = None
        for fact in rls.get_facts(self.rulename):#type: ignore[attr-defined]
            if fact.get(dur_abc.FACTTYPE) == dur_abc.LIST:
                if fact[dur_abc.LIST_ID] == targetedlist:
                    if end is None:
                        newlist = fact[dur_abc.LIST_MEMBERS][start:]
                    else:
                        newlist = fact[dur_abc.LIST_MEMBERS][start:end]
                    return self._make_list({}, newlist)
        raise Exception("couldnt find targeted list %r" % targetedlist)

    def _make_list(
            self,
            bindings: dur_abc.BINDING,
            args: Iterable[dur_abc.TRANSLATEABLE_TYPES],
            ) -> rdflib.BNode:
        newid = rdflib.BNode()
        elems = [string2rdflib(bindings[x]) if isinstance(x, Variable) else x
                 for x in args]
        newfact = {dur_abc.FACTTYPE: dur_abc.LIST,
                   dur_abc.LIST_ID: rdflib2string(newid),
                   dur_abc.LIST_MEMBERS: elems,
                   }
        rls.assert_fact(self.rulename, newfact) #type: ignore[attr-defined]
        return newid

    def _print_string(
            self,
            bindings: dur_abc.BINDING,
            args: Iterable[dur_abc.TRANSLATEABLE_TYPES],
            ) -> None:
        """
        :TODO: replace raised Exception with exception that stops the program
        :TODO: replace print with logger with standardoutput stdout
        """
        arg = [string2rdflib(bindings[x]) if isinstance(x, Variable) else x
               for x in args]
        print(" ".join(arg))

    def register_external_function(self, func: Callable) -> None:
        raise NotImplementedError()

class graph_transformer(_builtin_functions):
    """parses information equal to rdflib.Graph.
    Information that is produced can be extracted via __iter__ or serialize.
    """
    ruleset: rls.ruleset
    """Durable Ruleset used logic"""
    maingroup: typ.Any
    failures: list[str]
    """A list of the failures intercept by durable rules"""

    def __init__(self, maingroup: typ.Any, rulename: typ.Union[str, None]=None):
        """
        :TODO: changed automatic rulename assignment
        """
        super().__init__()
        self.failures = []
        if rulename is None:
            rulename = str(uuid.uuid4())
        elif not rulename:
            raise SyntaxError("rulename cant be ''")
        self.maingroup = maingroup
        self.ruleset = self._init_ruleset(rulename)


    def _init_ruleset(self, rulename: str) -> rls.ruleset:
        ruleset = dur_reasoner.get_standard_ruleset(rulename,
                                                    self.failures.append)

        logger.debug("creating rules for group %r" % self.maingroup)
        self.maingroup.generate_rules(
                ruleset,
                external_resolution=self.external_resolution)
        return ruleset

    @property
    def rulename(self) -> str:
        return self.ruleset.name #type: ignore[no-any-return]

    def parse(self) -> None:
        raise Exception()

    def load_from_graph(self, graph: rdflib.Graph) -> None:
        actions = []
        for ax in graph:
            actions.append(internal.assert_frame(*ax)) #type: ignore[arg-type]
        testassert = internal.action(actions)
        mygroup = internal.group([testassert])
        mygroup.generate_rules(self.ruleset,
                               external_resolution=self.external_resolution)
        if self.failures:
            raise Exception("Loading of data produced an error.",
                            self.failures)

    def run(self, t: typ.Union[int, None] = None) -> None:
        if t is None:
            rls.assert_fact(self.rulename, {"machinestate": "running"})
            rls.retract_fact(self.rulename, {"machinestate": "running"})
        else:
            raise NotImplementedError()
        if self.failures:
            raise Exception("Rules produced an error.", self.failures)

    def _get_internal_info(self) -> Iterable:
        return rls.get_facts(self.rulename) #type: ignore[no-any-return]

    def serialize(self) -> str:
        rls.get_facts(self.rulename)
        raise Exception()

    def __iter__(self) -> Iterable:
        expo_model = models.filtered_rdf_export()
        return expo_model.export(rls.get_facts(self.rulename), #type: ignore[no-any-return]
                                 self._symbols_for_export)


    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.maingroup})"


def create_RIF2internal_transformer() -> graph_transformer:
    #return graph_transformer(rif2internal.rif2trafo_group)
    return graph_transformer(rif2internal.group_rif2internal)
