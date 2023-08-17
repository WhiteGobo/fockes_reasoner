import pytest
import rdflib
import logging
logger = logging.getLogger(__name__)

from fockes_reasoner.shared import RIF
from rdflib import RDF
from fockes_reasoner.rif_dataobjects import rif_forall, rif_implies, rif_assert, rif_frame, rif_do, rif_group, rif_document
import fockes_reasoner
from fockes_reasoner.class_rdfmodel import rdfmodel

from data.test_suite import PET_Assert, PositiveEntailmentTests, PET_AssertRetract, PET_Modify, PET_Modify_loop, PET_AssertRetract2
import data.test_suite

def test_simpletestrun():
    """Small testrun for the machine and a simple task"""
    testfile = str(PET_Assert.premise)
    conclusionfile = str(PET_Assert.conclusion)
    try:
        g = rdflib.Graph().parse(testfile, format="rif")
        conc_graph = rdflib.Graph().parse(conclusionfile, format="rif")
    except rdflib.plugin.PluginException:
        pytest.skip("Need rdflib parser plugin to load RIF-file")

    q = fockes_reasoner.simpleLogicMachine.from_rdf(g)
    myfacts = q.run()
    logger.info("Expected conclusions in ttl:\n%s" % conc_graph.serialize())
    logger.info("All facts after machine has run:\n%s" % list(q.machine.get_facts()))
    rif_facts = list(rdfmodel().import_graph(conc_graph))
    assert rif_facts, "couldnt load conclusion rif_facts directly"
    assert q.check(rif_facts), "Missing expected conclusions"


@pytest.mark.parametrize("testinfo",[
    pytest.param(data.test_suite.PET_Assert),
    pytest.param(data.test_suite.PET_AssertRetract, marks=pytest.mark.skip("implications are not supported yet")),
    pytest.param(data.test_suite.PET_AssertRetract2),
    pytest.param(data.test_suite.PET_Modify),
    pytest.param(data.test_suite.PET_Modify_loop, marks=pytest.mark.skip("modify isnt implemented yet")),
    ])
def test_PositiveEntailmentTests(testinfo):
    testfile = str(testinfo.premise)
    conclusionfile = str(testinfo.conclusion)
    try:
        g = rdflib.Graph().parse(testfile, format="rif")
        conc_graph = rdflib.Graph().parse(conclusionfile, format="rif")
    except rdflib.plugin.PluginException:
        pytest.skip("Need rdflib parser plugin to load RIF-file")
    logger.info("premise in ttl:\n%s" % g.serialize())

    q = fockes_reasoner.simpleLogicMachine.from_rdf(g)
    myfacts = q.run()
    logger.info("Expected conclusions in ttl:\n%s" % conc_graph.serialize())
    rif_facts = list(rdfmodel().import_graph(conc_graph))
    logger.info("All facts after machine has run:\n%s\n\nexpected "
            "facts:\n%s" % (list(q.machine.get_facts()), rif_facts))
    assert rif_facts, "couldnt load conclusion rif_facts directly"
    assert q.check(rif_facts), "Missing expected conclusions"
