"""Module that can produce a transformer for rif-graphs to graph representing
internal information.

:TODO: Move all information to rif_to_internal after the
    class graph_transformer is transferred to endpoint
"""
from collections.abc import Iterable, Callable, Mapping, MutableMapping, Container
import typing as typ
import rdflib
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
from .shared import focke, string2rdflib, rdflib2string

class graph_transformer:
    """parses information equal to rdflib.Graph.
    Information that is produced can be extracted via __iter__ or serialize.
    """
    ruleset: rls.ruleset
    """Durable Ruleset used logic"""
    maingroup: typ.Any
    failures: list[str]
    """A list of the failures intercept by durable rules"""
    _symbols_for_export: set[str]

    def __init__(self, maingroup: typ.Any, rulename: typ.Union[str, None]=None):
        """
        :TODO: changed automatic rulename assignment
        """
        self.failures = []
        if rulename is None:
            rulename = str(uuid.uuid4())
        elif not rulename:
            raise SyntaxError("rulename cant be ''")
        self._symbols_for_export = set()
        self.maingroup = maingroup
        self.ruleset = self._init_ruleset(rulename)

    def _label_for_export(
            self,
            bindings: MutableMapping,
            args: Iterable[typ.Union[str, dur_abc.TRANSLATEABLE_TYPES]],
            ) -> None:
        """
        :TODO: integrate model to translate from internal datastructure
            to returned axioms.
        """
        logger.info("export got bindings %s and args %s" %(bindings, args))
        t_args = [bindings.get(x,x) for x in args]
        for x in t_args:
            if isinstance(x,
                          dur_abc.TRANSLATEABLE_TYPES): #type: ignore[arg-type]
                self._symbols_for_export.add(rdflib2string(x))
            else:
                self._symbols_for_export.add(x)

    @property
    def external_resolution(self) -> Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], Callable]:
        return {focke.export: self._label_for_export}

    def register_external_function(self, func: Callable) -> None:
        raise NotImplementedError()

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
            raise Exception("Something went wrong", self.failures)

    def serialize(self) -> str:
        rls.get_facts(self.rulename)
        raise Exception()

    def __iter__(self) -> Iterable:
        logger.critical(", ".join(repr(x) for x  in self._symbols_for_export))
        for fact in rls.get_facts(self.rulename):
            #logger.critical(repr(fact))
            if fact[dur_abc.FACTTYPE] == dur_abc.FRAME:
                if fact[dur_abc.FRAME_SLOTKEY] in self._symbols_for_export:
                    #Here the model should translate the frame to a rdf axiom
                    s = string2rdflib(fact[dur_abc.FRAME_OBJ])
                    p = string2rdflib(fact[dur_abc.FRAME_SLOTKEY])
                    o = string2rdflib(fact[dur_abc.FRAME_SLOTVALUE])
                    yield (s, p, o)
            elif fact[dur_abc.FACTTYPE] == dur_abc.LIST:
                #logger.info("found list: %s" % fact[dur_abc.LIST_ID])
                if fact[dur_abc.LIST_ID] in self._symbols_for_export:
                    #logger.info("found list for export: %s" % fact[dur_abc.LIST_ID])
                    g = rdflib.Graph()
                    b = string2rdflib(fact[dur_abc.LIST_ID])
                    q = [string2rdflib(x) for x in fact[dur_abc.LIST_MEMBERS]]
                    rdflib.collection.Collection(g, b, q)
                    for ax in g:
                        yield ax


    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.maingroup})"


def create_RIF2internal_transformer() -> graph_transformer:
    #return graph_transformer(rif2internal.rif2trafo_group)
    return graph_transformer(rif2internal.group_rif2internal)
