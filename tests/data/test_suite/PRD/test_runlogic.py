import pytest
from pytest import param, mark, skip, raises
from importlib.resources import files

from ...blueprints_tests import blueprint_test_logicmachine
from ....class_officialTestCases import PositiveEntailmentTest, NegativeEntailmentTest, ImportRejectionTest, PositiveSyntaxTest, NegativeSyntaxTest
from .PositiveEntailmentTest import Assert,Assert2, AssertRetract, AssertRetract2, Modify, Modify_loop
from fockes_reasoner import PRD_logicMachine, AlgorithmRejection

tmp = files(Assert)
PET_Assert = PositiveEntailmentTest(
        tmp.joinpath("Assert-premise.rif"),
        tmp.joinpath("Assert-conclusion.rif"),
        )

tmp = files(Assert2)
PET_Assert2 = PositiveEntailmentTest(
        tmp.joinpath("Assert2-premise.ttl"),
        tmp.joinpath("Assert2-conclusion.rif"),
        )

tmp = files(AssertRetract)
PET_AssertRetract = PositiveEntailmentTest(
        tmp.joinpath("AssertRetract-premise.rif"),
        tmp.joinpath("AssertRetract-conclusion.rif"),
        )

tmp = files(AssertRetract2)
PET_AssertRetract2 = PositiveEntailmentTest(
        tmp.joinpath("AssertRetract2-premise.rif"),
        tmp.joinpath("AssertRetract2-conclusion.rif"),
        )

tmp = files(Modify)
PET_Modify = PositiveEntailmentTest(
        tmp.joinpath("Modify-premise.rif"),
        tmp.joinpath("Modify-conclusion.rif"),
        )

tmp = files(Modify_loop)
PET_Modify_loop = PositiveEntailmentTest(
        tmp.joinpath("Modify_loop-premise.rif"),
        tmp.joinpath("Modify_loop-conclusion.rif"),
        )

from .NegativeEntailmentTest import Retract, RDF_Combination_SubClass_5
tmp = files(Retract)
NET_Retract = NegativeEntailmentTest(
        tmp.joinpath("Retract-premise.rif"),
        tmp.joinpath("Retract-nonconclusion.rif"),
        )

tmp = files(RDF_Combination_SubClass_5)
NET_RDF_Combination_SubClass_5 = NegativeEntailmentTest(
        tmp.joinpath("RDF_Combination_SubClass_5-premise.rif"),
        tmp.joinpath("RDF_Combination_SubClass_5-nonconclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_SubClass_5/RDF_Combination_SubClass_5-import001":
        tmp.joinpath("RDF_Combination_SubClass_5-import001.ttl")},
        )

@pytest.fixture(params=[
    pytest.param(PET_Assert,
                 id="Assert"),
    pytest.param(PET_Assert2,
                 id="Assert2_with_executeprint"),
    pytest.param(PET_AssertRetract,
                 marks=mark.skip("implies not frame is not implemented."),
                 id="PET_AssertRetract"),
    pytest.param(PET_AssertRetract2,
                 id="PET_AssertRetract2"),
    pytest.param(PET_Modify,
                 id="modify"),
    pytest.param(PET_Modify_loop,
                 id="modify_loop"),
    ])
def PET_testdata(request):
    return request.param

@pytest.fixture(params=[
    param(NET_Retract,
          id="NET_Retract"),
    param(NET_RDF_Combination_SubClass_5,
          id="NET_RDF_Combination_SubClass_5"),
    ])
def NET_testdata(request):
    return request.param

@pytest.fixture(params=[])
def IRT_testdata(request):
    return request.param

@pytest.fixture(params=[])
def NST_testdata(request):
    return request.param

@pytest.fixture(params=[])
def PST_testdata(request):
    return request.param

@pytest.fixture
def valid_exceptions(logic_machine):
    if isinstance(logic_machine, PRD_logicMachine):
        return Tuple()
    else:
        return (AlgorithmRejection,)


class TestPRD(blueprint_test_logicmachine):
    pass
