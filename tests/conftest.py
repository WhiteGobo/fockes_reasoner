import pytest
import itertools as it
from typing import Iterable, Any, Union, Optional
import rdflib
from rdflib import RDF, Graph
import logging
logger = logging.getLogger(__name__)
from pytest import param, mark, skip, raises
import rdflib_rif
import fockes_reasoner
from .test_rif_basic import _import_graph
from .class_officialTestCases import PositiveEntailmentTest, NegativeEntailmentTest, ImportRejectionTest, PositiveSyntaxTest, NegativeSyntaxTest

from fockes_reasoner.shared import RIF
from fockes_reasoner import rif_dataobjects as rif_obj
_rif_type_to_constructor = {RIF.Frame: rif_obj.rif_frame.from_rdf,
                            #RIF.External: rif_obj.rif_external.from_rdf,
                            RIF.Subclass: rif_obj.rif_subclass.from_rdf,
                            RIF.Member: rif_obj.rif_member.from_rdf,
                            RIF.Atom: rif_obj.rif_atom.from_rdf,
                            RIF.And: rif_obj.rif_and.from_rdf,
                            RIF.Exists: rif_obj.rif_exists.from_rdf,
                            RIF.Equal: rif_obj.rif_equal.from_rdf,
                            }


class ExpectedFailure(Exception):
    ...

@pytest.fixture(params=[
    param(fockes_reasoner.simpleLogicMachine),
    ])
def logic_machine(request):
    return request.param


@pytest.fixture
def logicmachine_after_PET(PET_testdata, logic_machine, valid_exceptions,
                           steplimit,
                           rif_facts_PET: Union[Iterable["rif_fact"], Graph]):
    def _q(f):
        try:
            return f._create_facts()
        except AttributeError:
            pass
        try:
            return [f.as_machineterm()]
        except AttributeError:
            pass
        return []
    if isinstance(rif_facts_PET, Graph):
        try:
            return logicmachine_after_run(PET_testdata, logic_machine,
                                          valid_exceptions, steplimit,
                                          [], compare_graph=rif_facts_PET)
        except ExpectedFailure as err:
            return err
    else:
        expected_facts = list(it.chain.from_iterable(_q(f)
                                                     for f in rif_facts_PET))
        try:
            return logicmachine_after_run(PET_testdata, logic_machine,
                                          valid_exceptions, steplimit,
                                          expected_facts)
        except ExpectedFailure as err:
            return err

@pytest.fixture
def logicmachine_after_NET(NET_testdata, logic_machine, valid_exceptions, steplimit):
    try:
        return logicmachine_after_run(NET_testdata, logic_machine,
                                  valid_exceptions, steplimit)
    except ExpectedFailure as err:
        return err

@pytest.fixture
def logicmachine_after_NST(NST_testdata, logic_machine, valid_exceptions, steplimit):
    try:
        return logicmachine_after_run(NST_testdata, logic_machine,
                                  (fockes_reasoner.SyntaxReject, *valid_exceptions), steplimit)
    except ExpectedFailure as err:
        return err

@pytest.fixture
def logicmachine_after_PST(PST_testdata, logic_machine, valid_exceptions, steplimit):
    try:
        return logicmachine_after_run(PST_testdata, logic_machine,
                                  valid_exceptions, steplimit)
    except ExpectedFailure as err:
        return err

@pytest.fixture
def logicmachine_after_IRT(IRT_testdata, logic_machine, valid_exceptions, steplimit):
    try:
        return logicmachine_after_run(IRT_testdata, logic_machine,
                                  (fockes_reasoner.ImportReject, *valid_exceptions), steplimit)
    except ExpectedFailure as err:
        return err

@pytest.fixture
def steplimit():
    return 30

def _load_graph(testfile):
    for f in ["rif", None, "rifps"]:
        try:
            return rdflib.Graph().parse(testfile, format=f)
        except Exception: #rdflib.plugin.PluginException:
            pass
    pytest.skip("Need rdflib parser plugin to load RIF-file")


def logicmachine_after_run(testdata, logic_machine,
                           valid_exceptions, steplimit_,
                           stop_conditions=[],
                           step_limit=None,
                           compare_graph: Optional[Graph] = None,
                           ) -> Any:
    testfile = str(testdata.premise)
    logger.debug("Premise: %s" % testdata)
    g = _load_graph(testfile)
    #logger.debug("premise in ttl:\n%s" % g.serialize())

    extra_documents = {uri: _import_graph(filepath)
                       for uri, filepath
                       in testdata.importedDocuments.items()}
    try:
        q = logic_machine.from_rdf(g, extra_documents)
        if stop_conditions:
            q.add_stop_condition(stop_conditions)
        logger.debug("Running Machine ... ")
        myfacts = q.run()
    except valid_exceptions as err:
        raise ExpectedFailure() from err
    logger.info("All facts after machine has run:\n%s"
                % "\n".join(str(x) for x in q.machine.get_facts()))
    return q

class _LoadingError(Exception):
    ...

#def rif_facts_PET(logicmachine_after_PET, PET_testdata):
@pytest.fixture
def rif_facts_PET(PET_testdata):
    conclusionfile = str(PET_testdata.conclusion)
    logger.debug("Conclusion: %s" % conclusionfile)
    try:
        return rif_facts(conclusionfile)
    except rdflib_rif.BadSyntax as err:
        pass
    except _LoadingError as err1:
        raise

    g = rdflib.Graph().parse(conclusionfile)
    return g

@pytest.fixture
def rif_facts_NET(logicmachine_after_NET, NET_testdata):
    nonconclusionfile = str(NET_testdata.nonconclusion)
    logger.debug("Nonconclusion: %s" % nonconclusionfile)
    try:
        return rif_facts(nonconclusionfile)
    except _LoadingError as err1:
        raise

def rif_facts(conclusionfile):
    try:
        conc_graph = rdflib.Graph().parse(conclusionfile, format="rif")
    except rdflib.plugin.PluginException:
        pytest.skip("Need rdflib parser plugin to load RIF-file %s"
                    % conclusionfile)
    except rdflib_rif.BadSyntax:
        raise
    except Exception:
        logger.critical("failed at when loading %s" % conclusionfile)
        raise
    #logger.debug("Expected conclusions in ttl:\n%s" % conc_graph.serialize())
    rif_facts = []

    _objs = set(conc_graph.objects())
    subjects = set(x for x in conc_graph.subjects() if x not in _objs)
    for fact_root in subjects:
        try:
            t, = conc_graph.objects(fact_root, RDF.type)
            generator = _rif_type_to_constructor[t]
        except (KeyError, ValueError) as err:
            logger.critical(conc_graph.serialize())
            logger.critical(conclusionfile)
            raise _LoadingError("Couldnt find constructur for rootnode %r"
                                % fact_root) from err
        rif_facts.append(generator(conc_graph, fact_root))
    logger.info("Expected facts:\n%s" % rif_facts)
    return rif_facts
