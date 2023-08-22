import pytest
import rdflib
import logging
logger = logging.getLogger(__name__)

from fockes_reasoner.shared import RIF
from rdflib import RDF
from fockes_reasoner.rif_dataobjects import rif_forall, rif_implies, rif_assert, rif_frame, rif_do, rif_group, rif_document, rif_subclass, rif_member
import fockes_reasoner
from fockes_reasoner.class_rdfmodel import rdfmodel

from data.test_suite import PET_Assert, PositiveEntailmentTests, PET_AssertRetract, PET_Modify, PET_Modify_loop, PET_AssertRetract2
import data.test_suite

_rif_type_to_constructor = {RIF.Frame: rif_frame.from_rdf,
                            #RIF.External: rif_external.from_rdf,
                            RIF.Subclass: rif_subclass.from_rdf,
                            RIF.Member: rif_member.from_rdf,
                            }

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
    rif_facts = [f for f in rdfmodel().import_graph(conc_graph) if not isinstance(f, rdflib.term.Node)]
    assert rif_facts, "couldnt load conclusion rif_facts directly"
    assert q.check(rif_facts), "Missing expected conclusions"


@pytest.mark.parametrize("testinfo",[
    pytest.param(data.test_suite.PET_Assert),
    pytest.param(data.test_suite.PET_AssertRetract, marks=pytest.mark.skip("implications are not supported yet")),
    pytest.param(data.test_suite.PET_AssertRetract2),
    pytest.param(data.test_suite.PET_Modify),
    pytest.param(data.test_suite.PET_Modify_loop),
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
    rif_facts = [f for f in rdfmodel().import_graph(conc_graph) if not isinstance(f, rdflib.term.Node)]
    logger.info("All facts after machine has run:\n%s\n\nexpected "
            "facts:\n%s" % (list(q.machine.get_facts()), rif_facts))
    assert rif_facts, "couldnt load conclusion rif_facts directly"
    assert q.check(rif_facts), "Missing expected conclusions"

@pytest.mark.parametrize("testinfo",[
    pytest.param(data.test_suite.NET_Retract),
    pytest.param(data.test_suite.NET_RDF_Combination_SubClass_5, id="NET_RDF_Combination_SubClass_5"),
    ])
def test_NegativeEntailmentTests(testinfo):
    logger.info("premise located: %s\nnonconclusion located: %s"
                %(testinfo.premise, testinfo.nonconclusion))
    try:
        g = rdflib.Graph().parse(testinfo.premise, format="rif")
        nonconc_graph = rdflib.Graph().parse(testinfo.nonconclusion, format="rif")
    except rdflib.plugin.PluginException:
        pytest.skip("Need rdflib parser plugin to load RIF-file")
    logger.info("premise in ttl:\n%s" % g.serialize())

    #filepath.suffix is eg ".rif" so filepath.suffix[1:]=="rif"
    extra_documents = {uri: rdflib.Graph().parse(str(filepath), format=filepath.suffix[1:]) for uri, filepath in testinfo.importedDocuments.items()}
    q = fockes_reasoner.simpleLogicMachine.from_rdf(g, extra_documents)
    myfacts = q.run()
    logger.info("Not expected conclusions in ttl:\n%s"
                % nonconc_graph.serialize())
    rif_facts = []
    for typeref, generator in _rif_type_to_constructor.items():
        for node in nonconc_graph.subjects(RDF.type, typeref):
            rif_facts.append(generator(nonconc_graph, node))
    #rif_facts = [f for f in rdfmodel().import_graph(nonconc_graph)
    #             if not isinstance(f, rdflib.term.Node)]
    logger.info("All facts after machine has run:\n%s\n\nNot expected "
            "facts:\n%s" % (list(q.machine.get_facts()), rif_facts))
    assert rif_facts, "couldnt load conclusion rif_facts directly"
    for f in rif_facts:
        assert not q.check([f]), "Not expected conclusion %s found" % f
