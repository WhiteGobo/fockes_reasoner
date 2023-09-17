import pytest
import rdflib
from rdflib import RDF
import logging
logger = logging.getLogger(__name__)
from pytest import param, mark, skip, raises
import fockes_reasoner
from .test_rif_basic import _rif_type_to_constructor, _import_graph

@pytest.fixture(params=[
    param(fockes_reasoner.simpleLogicMachine),
    ])
def logic_machine(request):
    return request.param


@pytest.fixture
def logicmachine_after_PET(PET_testdata, logic_machine, valid_exceptions):
    return logicmachine_after_run(PET_testdata, logic_machine,
                                  valid_exceptions)

@pytest.fixture
def logicmachine_after_NET(NET_testdata, logic_machine, valid_exceptions):
    return logicmachine_after_run(NET_testdata, logic_machine,
                                  valid_exceptions)

@pytest.fixture
def logicmachine_after_NST(NST_testdata, logic_machine, valid_exceptions):
    return logicmachine_after_run(NST_testdata, logic_machine,
                                  valid_exceptions)

@pytest.fixture
def logicmachine_after_PST(PST_testdata, logic_machine, valid_exceptions):
    return logicmachine_after_run(PST_testdata, logic_machine,
                                  valid_exceptions)

@pytest.fixture
def logicmachine_after_IRT(IRT_testdata, logic_machine, valid_exceptions):
    return logicmachine_after_run(IRT_testdata, logic_machine,
                                  valid_exceptions)

def logicmachine_after_run(testdata, logic_machine, valid_exceptions):
    testfile = str(testdata.premise)
    logger.debug("Premise: %s" % testdata)
    try:
        g = rdflib.Graph().parse(testfile, format="rif")
    except rdflib.plugin.PluginException:
        pytest.skip("Need rdflib parser plugin to load RIF-file")
    #logger.debug("premise in ttl:\n%s" % g.serialize())

    extra_documents = {uri: _import_graph(filepath)
                       for uri, filepath
                       in testdata.importedDocuments.items()}
    try:
        q = logic_machine.from_rdf(g, extra_documents)
    except valid_exceptions:
        return
    logger.debug("Running Machine ... ")
    myfacts = q.run()
    logger.info("All facts after machine has run:\n%s"
                % list(q.machine.get_facts()))
    return q

@pytest.fixture
def rif_facts_PET(logicmachine_after_PET, PET_testdata):
    conclusionfile = str(PET_testdata.conclusion)
    return rif_facts(conclusionfile)

@pytest.fixture
def rif_facts_NET(logicmachine_after_NET, NET_testdata):
    nonconclusionfile = str(NET_testdata.nonconclusion)
    return rif_facts(nonconclusionfile)

def rif_facts(conclusionfile):
    logger.debug("Conclusion: %s" % conclusionfile)
    try:
        conc_graph = rdflib.Graph().parse(conclusionfile, format="rif")
    except rdflib.plugin.PluginException:
        pytest.skip("Need rdflib parser plugin to load RIF-file")
    #logger.debug("Expected conclusions in ttl:\n%s" % conc_graph.serialize())

    rif_facts = []
    for typeref, generator in _rif_type_to_constructor.items():
        for node in conc_graph.subjects(RDF.type, typeref):
            if not (None, None, node) in conc_graph:
                rif_facts.append(generator(conc_graph, node))
    logger.info("Expected facts:\n%s" % rif_facts)
    return rif_facts
