import pytest
import rdflib
import logging
logger = logging.getLogger(__name__)

from fockes_reasoner.shared import RIF
from rdflib import RDF
from fockes_reasoner.rif_dataobjects import rif_forall, rif_implies, rif_assert, rif_frame, rif_do, rif_group, rif_document
import fockes_reasoner
from fockes_reasoner.class_rdfmodel import rdfmodel

from data.test_suite import PET_Assert, PositiveEntailmentTests

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

def test_PositiveEntailmentTests():
    for x in PositiveEntailmentTests:
        testfile = str(x.premise)
        conclusionfile = str(x.conclusion)
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
