import pytest
import rdflib
from rdflib import RDF
import logging
logger = logging.getLogger(__name__)
from pytest import param, mark, skip, raises
import fockes_reasoner
from .test_rif_basic import _rif_type_to_constructor, _import_graph
from .class_officialTestCases import PositiveEntailmentTest, NegativeEntailmentTest, ImportRejectionTest, PositiveSyntaxTest, NegativeSyntaxTest

class ExpectedFailure(Exception):
    ...

@pytest.fixture(params=[
    param(fockes_reasoner.simpleLogicMachine),
    ])
def logic_machine(request):
    return request.param


@pytest.fixture
def logicmachine_after_PET(PET_testdata, logic_machine, valid_exceptions):
    try:
        return logicmachine_after_run(PET_testdata, logic_machine,
                                  valid_exceptions)
    except ExpectedFailure as err:
        return err

@pytest.fixture
def logicmachine_after_NET(NET_testdata, logic_machine, valid_exceptions):
    try:
        return logicmachine_after_run(NET_testdata, logic_machine,
                                  valid_exceptions)
    except ExpectedFailure as err:
        return err

@pytest.fixture
def logicmachine_after_NST(NST_testdata, logic_machine, valid_exceptions):
    try:
        return logicmachine_after_run(NST_testdata, logic_machine,
                                  (fockes_reasoner.SyntaxReject, *valid_exceptions))
    except ExpectedFailure as err:
        return err

@pytest.fixture
def logicmachine_after_PST(PST_testdata, logic_machine, valid_exceptions):
    try:
        return logicmachine_after_run(PST_testdata, logic_machine,
                                  valid_exceptions)
    except ExpectedFailure as err:
        return err

@pytest.fixture
def logicmachine_after_IRT(IRT_testdata, logic_machine, valid_exceptions):
    try:
        return logicmachine_after_run(IRT_testdata, logic_machine,
                                  (fockes_reasoner.ImportReject, *valid_exceptions))
    except ExpectedFailure as err:
        return err

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
        logger.debug("Running Machine ... ")
        myfacts = q.run()
    except valid_exceptions as err:
        raise ExpectedFailure() from err
    logger.info("All facts after machine has run:\n%s"
                % list(q.machine.get_facts()))
    return q

@pytest.fixture
def rif_facts_PET(logicmachine_after_PET, PET_testdata):
    conclusionfile = str(PET_testdata.conclusion)
    logger.debug("Conclusion: %s" % conclusionfile)
    return rif_facts(conclusionfile)

@pytest.fixture
def rif_facts_NET(logicmachine_after_NET, NET_testdata):
    nonconclusionfile = str(NET_testdata.nonconclusion)
    logger.debug("Nonconclusion: %s" % nonconclusionfile)
    return rif_facts(nonconclusionfile)

def rif_facts(conclusionfile):
    try:
        conc_graph = rdflib.Graph().parse(conclusionfile, format="rif")
    except rdflib.plugin.PluginException:
        pytest.skip("Need rdflib parser plugin to load RIF-file %s"
                    % conclusionfile)
    #logger.debug("Expected conclusions in ttl:\n%s" % conc_graph.serialize())
    rif_facts = []

    _objs = set(conc_graph.objects())
    subjects = set(x for x in conc_graph.subjects() if x not in _objs)
    for fact_root in subjects:
        t, = conc_graph.objects(fact_root, RDF.type)
        generator = _rif_type_to_constructor[t]
        rif_facts.append(generator(conc_graph, fact_root))
    logger.info("Expected facts:\n%s" % rif_facts)
    return rif_facts
