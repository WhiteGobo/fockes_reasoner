import pytest
import rdflib

from fockes_reasoner.shared import RIF
from rdflib import RDF
from fockes_reasoner.rif_dataobjects import rif_forall, rif_implies, rif_assert, rif_frame, rif_do, rif_group, rif_document
import fockes_reasoner

from data.test_suite import PET_Assert

def test_simple():
    testfile = str(PET_Assert.premise)
    try:
        g = rdflib.Graph().parse(testfile, format="rif")
    except rdflib.plugin.PluginException:
        pytest.skip("Need rdflib parser plugin to load RIF-file")

    q = fockes_reasoner.simpleLogicMachine.from_rdf(g)
    myfacts = q.run()
    raise Exception(myfacts)
