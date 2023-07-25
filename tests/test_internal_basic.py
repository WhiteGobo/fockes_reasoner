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
