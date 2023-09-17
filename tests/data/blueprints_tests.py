import pytest
from ..conftest import ExpectedFailure

class blueprint_test_logicmachine:
    def test_check_facts(self, logicmachine_after_PET, rif_facts_PET):
        if isinstance(logicmachine_after_PET, ExpectedFailure):
            return
        assert rif_facts_PET, "couldnt load conclusion rif_facts directly"
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
        assert isinstance(logicmachine_after_IRT, ExpectedFailure)

    def test_checkSyntaxFailed(self, logicmachine_after_NST):
        assert isinstance(logicmachine_after_NST, ExpectedFailure)

    def test_checkSyntaxAccepted(self, logicmachine_after_PST):
        if isinstance(logicmachine_after_PST, ExpectedFailure):
            return
