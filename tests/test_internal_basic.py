import pytest
import durable.lang as rls
import rdflib
import logging
logger = logging.getLogger(__name__)

import fockes_reasoner
from fockes_reasoner import rif_to_internal as rif2int
from fockes_reasoner import internal_dataobjects as internal
from fockes_reasoner.durable_reasoner.durable_abc import FACTTYPE, FRAME
from fockes_reasoner import rule_importer
from fockes_reasoner import rif2internal
from rdflib import RDF

import pathlib
import os.path
import importlib.resources
from data.test_suite import PET_Assert

def test_simple():
    ruleset = rls.ruleset("test")
    logger.debug(rif2int.rif2trafo_group)
    rif2int.rif2trafo_group.generate_rules(ruleset)


def test_basic_internal_reasoner():
    """Basic test if internal objects work.
    """
    ex = rdflib.Namespace("http://example.org/example#")
    var_x = rdflib.Variable("X")
    patterns = [
            internal.frame_pattern(var_x, ex.status, rdflib.Literal("gold")) ,
            ]
    actions = [
            internal.assert_frame(var_x, ex.discount, rdflib.Literal("10")),
            ]
    testrule = internal.rule(patterns, actions)
    action = internal.assert_frame(ex.John, ex.status, rdflib.Literal("gold"))
    testassert = internal.action([action])
    mygroup = internal.group([testrule, testassert])
    logger.debug(mygroup)

    ruleset = rls.ruleset("test")
    failure = []

    with ruleset:
        @rls.when_all(+rls.s.exception)
        def second(c) -> None:
            logger.critical(c.s.exception)
            failure.append(str(c.s.exception))
            c.s.exception = None

        @rls.when_all(+getattr(rls.m, FACTTYPE))
        def accept_all_frametypes(c) -> None:
            #logger.critical(str(c))
            pass

    q = mygroup.generate_rules(ruleset)
    #logger.warning(list(rls.get_facts(ruleset.name)))
    if failure:
        raise Exception(failure)

def _rulegrouptest(mygroup):
    ruleset = rls.ruleset("test")
    failure = []

    with ruleset:
        @rls.when_all(+rls.s.exception)
        def second(c) -> None:
            f = str(c.s.exception).replace(r"\n", "\n")
            f = f.replace(r"', '", "")
            f = f.replace("traceback [\' ", "traceback:\n")
            logger.error(f)
            failure.append(f)
            c.s.exception = None

        @rls.when_all(+getattr(rls.m, FACTTYPE))
        def accept_all_frametypes(c) -> None:
            #logger.critical(str(c))
            pass

        @rls.when_all(+rls.m.machinestate)
        def accept_machinestate(c) -> None:
            pass

    q = mygroup.generate_rules(ruleset)
    if failure: 
        raise Exception("During work of logic framework exceptions were "
                        "raised. See logging for more information.")
    rls.assert_fact("test", {"machinestate": "running"})
    myfacts = rls.get_facts(ruleset.name)
    f1 = {'type': 'frame', 'obj': '<http://example.org/example#John>', 'slotkey': '<http://example.org/example#status>', 'slotvalue': "'gold'^^<http://www.w3.org/2001/XMLSchema#string>"}
    f2 = {'type': 'frame', 'obj': '<http://example.org/example#John>', 'slotkey': '<http://example.org/example#discount>', 'slotvalue': "'10'^^<http://www.w3.org/2001/XMLSchema#string>"}
    try:
        assert f1 in myfacts, "logic failed to generate the init-fact from action"
    except AssertionError as err:
        raise Exception(myfacts)
    try:
        f2_result, = (f for f in myfacts if f != f1 and f.get("type"))
    except StopIteration as err:
        raise Exception("logic failed to generate the implication.") from err
    try:
        assert all(f2[x] == f2_result.get(x) for x in f2.keys())
    except AssertionError as err:
        raise Exception(f"expected something like: {[f1, f2]}\n"
                        f" but got: {myfacts}") from err

def test_RDFimport():
    """Tests if a simple example of the internal rulestructure can be load
    when the structure is given in the rdf representation of the internal
    data.
    """
    my = rdflib.Namespace("http://example.com/mythingies#")
    testgraph = rdflib.Graph()
    testgraph.parse(format="ttl", data=f"""
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        @prefix rif: <http://www.w3.org/2007/rif#> .
        @prefix func: <http://func> .
        @prefix ex: <http://example.org/example#> .
        @prefix tmp: <http://example.com/temporarydata#> .
        @prefix focke: <http://example.com/internaldata#> .
        @prefix rif2internal: <http://example.com/builtin#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix my: <{my}> .

        my:group a rif2internal:group;
            rif2internal:sentences ( my:forall1 my:action1 ).

        my:action1 a rif2internal:action;
            rif2internal:functions ( my:makegold ) .

        my:forall1 a rif2internal:forall;
            rif2internal:patterns ( my:statusisgold ) ;
            rif2internal:functions ( my:givediscount ) .

        my:statusisgold a rif2internal:frame_pattern ;
            rif2internal:object [a rif:Var; rif:varname "X"] ;
            rif2internal:slotkey [ a rif:Const ; rif:constIRI "http://example.org/example#status"^^xsd:anyURI ] ;
            rif2internal:slotvalue [ a rif:Const ; rif:value "gold"^^xsd:string ].
            #rif2internal:slotkey ex:status ;
            #rif2internal:slotvaluea "gold" .

        my:givediscount a rif2internal:assert_frame ;
            rif2internal:object [a rif:Var; rif:varname "X"] ;
            #rif2internal:slotkey ex:discount ;
            #rif2internal:slotvalue "10" .
            rif2internal:slotkey [ a rif:Const ; rif:constIRI "http://example.org/example#discount"^^xsd:anyURI ];
            rif2internal:slotvalue [ a rif:Const ; rif:value "10"^^xsd:string ].

        my:makegold a rif2internal:assert_frame ;
            #rif2internal:object ex:John ;
            #rif2internal:slotkey ex:status ;
            #rif2internal:slotvalue "gold" .
            rif2internal:object [ a rif:Const ; rif:constIRI "http://example.org/example#John"^^xsd:anyURI ] ;
            rif2internal:slotkey [ a rif:Const ; rif:constIRI "http://example.org/example#status"^^xsd:anyURI ] ;
            rif2internal:slotvalue [ a rif:Const ; rif:value "gold"^^xsd:string ].
    """)
    mygroup = internal.group.from_rdf(testgraph, my.group)
    logger.debug(repr(mygroup))

    _rulegrouptest(mygroup)


def test_RIFimport():
    testfile = str(PET_Assert.premise)
    try:
        g = rdflib.Graph().parse(testfile, format="rif")
    except rdflib.plugin.PluginException:
        pytest.skip("Need rdflib parser plugin to load RIF-file")

    logger.info(g.serialize())
    trafo = rule_importer.create_RIF2internal_transformer()
    #trafo.parse(testfile, format="rif")
    try:
        trafo.load_from_graph(g)
    except Exception:
        logger.info("internal information during loading: %s"
                    % "\n".join(str(x) for x in trafo._get_internal_info()))
        raise
    #logger.info("internal information after loading: %s"
    #                % "\n".join(str(x) for x in trafo._get_internal_info()))
    try:
        trafo.run()
    except Exception:
        #logger.info("internal information during running: %s"
        #            % "\n".join(str(x) for x in trafo._get_internal_info()))
        raise
    logger.info("symbols labeled for export: %s" % trafo._symbols_for_export)
    try:
        internal_rule_graph = rdflib.Graph()
        for ax in trafo:
            internal_rule_graph.add(ax)
    except Exception:
        logger.info("internal information during export: %s"
                    % "\n".join(str(x) for x in trafo._get_internal_info()))
        raise
    #logger.info("asdfqwer %s" % list(trafo))
    #logger.info(g.serialize())
    _subgroups = set(internal_rule_graph.subjects(RDF.type,
                                                  rif2internal.subgroup))
    try:
        rootgroup, = (g for g in internal_rule_graph.subjects(RDF.type, rif2internal.group)
                      if g not in _subgroups)
    except ValueError:
        logger.info("Exported graph:\n%s" % internal_rule_graph.serialize())
        raise Exception("couldnt find exactly one rootgroup.") from err
    #logger.info(trafo._symbols_for_export)
    #logger.info("internal information during export: %s"
    #            % "\n".join(str(x) for x in trafo._get_internal_info()))
    logger.info(internal_rule_graph.serialize())

    mygroup = internal.group.from_rdf(internal_rule_graph, rootgroup)
    logger.info(repr(mygroup))
    raise Exception(rootgroup)
