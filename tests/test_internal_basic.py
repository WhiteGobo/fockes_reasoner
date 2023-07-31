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

def test_RDFimport():
    """Tests if a simple example of the internal rulestructure can be load
    when the structure is given in the rdf representation of the internal
    data.
    """
    my = rdflib.Namespace("http://example.com/mythingies#")
    testgraph = rdflib.Graph()
    testgraph.parse(format="ttl", data=f"""
        @prefix xs: <http://www.w3.org/2001/XMLSchema#> .
        @prefix rif: <http://rif> .
        @prefix func: <http://func> .
        @prefix ex: <http://example.org/example#> .
        @prefix tmp: <http://example.com/temporarydata#> .
        @prefix focke: <http://example.com/internaldata#> .
        @prefix rif2internal: <http://example.com/builtin#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix my: <{my}> .

        my:group a focke:group;
            focke:sentences ( my:forall1 my:action1 ).

        my:action1 a focke:action;
            focke:functions ( my:makegold ) .

        my:forall1 a focke:forall;
            focke:patterns ( my:statusisgold ) ;
            focke:functions ( my:givediscount ) .

        my:statusisgold a focke:frame_pattern ;
            focke:object [a focke:Variable; focke:variablename "X"] ;
            focke:slotkey ex:status ;
            focke:slotvalue "gold" .

        my:givediscount a focke:assert_frame ;
            focke:object [a focke:Variable; focke:variablename "X"] ;
            focke:slotkey ex:discount ;
            focke:slotvalue "10" .

        my:makegold a focke:assert_frame ;
            focke:object ex:John ;
            focke:slotkey ex:status ;
            focke:slotvalue "gold" .
    """)
    mygroup = internal.group.from_rdf(testgraph, my.group)
    logger.debug(repr(mygroup))

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

    q = mygroup.generate_rules(ruleset)
    if failure: 
        raise Exception("During work of logic framework exceptions were "
                        "raised. See logging for more information.")
    myfacts = rls.get_facts(ruleset.name)
    f1 = {'type': 'frame', 'obj': '<http://example.org/example#John>', 'slotkey': '<http://example.org/example#status>', 'slotvalue': "'gold'"}
    try:
        assert f1 in myfacts
        f2_result = (f for f in myfacts if f != f1).__next__()
        f2 = {'type': 'frame', 'obj': '<http://example.org/example#John>', 'slotkey': '<http://example.org/example#discount>', 'slotvalue': "'10'"}
        assert all(f2[x] == f2_result[x] for x in f2.keys())
    except Exception as err:
        raise Exception(f"expected something like: {[f1, f2]}\n"
                        f" but got: {myfacts}") from err


def test_RIFimport():
    testfile = str(PET_Assert.premise)
    try:
        g = rdflib.Graph().parse(testfile, format="rif")
    except rdflib.plugin.PluginException:
        pytest.skip("Need rdflib parser plugin to load RIF-file")

    trafo = rule_importer.create_RIF2internal_transformer()
    #trafo.parse(testfile, format="rif")
    trafo.load_from_graph(g)
    logger.info("symbols labeled for export: %s" % trafo._symbols_for_export)
    g = rdflib.Graph()
    for ax in trafo:
        g.add(ax)
    #logger.info("asdfqwer %s" % list(trafo))
    logger.info(g.serialize())
    if trafo.failures:
        logger.critical("Errors during run: %s" % trafo.failures)
        raise Exception("Errors happened but no error was raised automaticly")
    #logger.critical(rls.get_facts(trafo.rulename))
    logger.info(trafo._symbols_for_export)
    raise Exception()
