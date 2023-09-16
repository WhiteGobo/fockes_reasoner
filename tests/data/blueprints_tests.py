import pytest

class blueprint_test_logicmachine:
    def test_check_facts(self, logicmachine_after_PET, rif_facts_PET):
        assert rif_facts_PET, "couldnt load conclusion rif_facts directly"
        assert logicmachine_after_PET.check(rif_facts_PET),\
                "Missing expected conclusions"

    def test_check_nonfacts(self, logicmachine_after_NET, rif_facts_NET):
        assert rif_facts_NET, "couldnt load nonconclusion rif_facts directly"
        for f in rif_facts_NET:
            assert not logicmachine_after_NET.check([f]),\
                    "Not expected conclusion %s found" % f
