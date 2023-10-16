import pytest
from ..conftest import ExpectedFailure
from typing import Union, Iterable
from rdflib import Graph
from rdflib.compare import to_isomorphic, graph_diff

import logging
logger = logging.getLogger(__name__)

class blueprint_test_logicmachine:
    def test_check_facts(self, logicmachine_after_PET,
                         rif_facts_PET: Union[Graph, Iterable["rif_fact"]]):
        logger.debug("expected facts:\n%s" % rif_facts_PET)
        if isinstance(logicmachine_after_PET, ExpectedFailure):
            return
        assert rif_facts_PET, "couldnt load conclusion rif_facts directly"
        if isinstance(rif_facts_PET, Graph):
            datagraph = logicmachine_after_PET.export_rdflib()
            isodata = to_isomorphic(datagraph)
            isocomp = to_isomorphic(rif_facts_PET)
            in_both, in_data, in_comp = graph_diff(isodata, isocomp)
            assert not list(in_data) and not list(in_comp)
        else:
            assert logicmachine_after_PET.check(rif_facts_PET),\
                    "Missing expected conclusions"

    def test_check_nonfacts(self, logicmachine_after_NET, rif_facts_NET):
        if isinstance(logicmachine_after_NET, ExpectedFailure):
            return
        assert rif_facts_NET, "couldnt load nonconclusion rif_facts directly"
        for f in rif_facts_NET:
            assert not logicmachine_after_NET.check([f]),\
                    "Not expected conclusion %s found" % f

    def test_importFailed(self, logicmachine_after_IRT):
        assert isinstance(logicmachine_after_IRT, ExpectedFailure),\
                "Unexpected successful import"

    def test_checkSyntaxFailed(self, logicmachine_after_NST):
        assert isinstance(logicmachine_after_NST, ExpectedFailure),\
                "Unexpected accepted Syntax"

    def test_checkSyntaxAccepted(self, logicmachine_after_PST):
        if isinstance(logicmachine_after_PST, ExpectedFailure):
            return
