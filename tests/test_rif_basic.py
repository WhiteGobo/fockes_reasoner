import pytest
from pytest import param, mark, skip
import rdflib
import traceback
import logging
logger = logging.getLogger(__name__)

from fockes_reasoner.shared import RIF
from rdflib import RDF
from fockes_reasoner.rif_dataobjects import (rif_forall,
                                             rif_implies,
                                             rif_assert,
                                             rif_frame,
                                             rif_do,
                                             rif_group,
                                             rif_document,
                                             rif_subclass,
                                             rif_member,
                                             rif_atom,
                                             rif_and,
                                             rif_exists,
                                             )
import fockes_reasoner


from .data.test_suite import PET_Assert
from .data import test_suite

def _import_graph(filepath) -> rdflib.Graph:
    fp = str(filepath)
    formats = (filepath.suffix[1:], "xml")
    for f in formats:
        try:
            return rdflib.Graph().parse(fp, format=f)
        except rdflib.plugin.PluginException as err:
            logger.debug("Failed at loading '%s' with format %s. Cause:\n%s"
                         %(filepath, f, traceback.format_exc()))
    raise Exception("No rdf plugin succesfull. See logging(debug) "
                    "for more info")


def test_simpletestrun():
    """Small testrun for the machine and a simple task"""
    pytest.skip("removed model")
    testfile = str(PET_Assert.premise)
    conclusionfile = str(PET_Assert.conclusion)
    try:
        g = rdflib.Graph().parse(testfile, format="rif")
        conc_graph = rdflib.Graph().parse(conclusionfile, format="rif")
    except rdflib.plugin.PluginException:
        pytest.skip("Need rdflib parser plugin to load RIF-file")

    q = fockes_reasoner.simpleLogicMachine.from_rdf(g)
    myfacts = q.run()
    #logger.info("Expected conclusions in ttl:\n%s" % conc_graph.serialize())
    logger.info("All facts after machine has run:\n%s"
                % list(q.machine.get_facts()))
    rif_facts = [f for f in rdfmodel().import_graph(conc_graph)
                 if not isinstance(f, rdflib.term.Node)]
    assert rif_facts, "couldnt load conclusion rif_facts directly"
    assert q.check(rif_facts), "Missing expected conclusions"
