import pytest
from pytest import param, mark, skip, raises
from importlib.resources import files

from ...blueprints_tests import blueprint_test_logicmachine
from ....class_officialTestCases import PositiveEntailmentTest, NegativeEntailmentTest, ImportRejectionTest, PositiveSyntaxTest, NegativeSyntaxTest
from fockes_reasoner import BLD_logicMachine, AlgorithmRejection

from .PositiveEntailmentTest import \
        Arbitrary_Entailment,\
        Chaining_strategy_numericadd_2,\
        Chaining_strategy_numericsubtract_1,\
        Class_Membership,\
        Classificationinheritance,\
        ElementEqualityFromListEquality,\
        EntailEverything,\
        Equality_in_conclusion_1,\
        Equality_in_conclusion_2,\
        Equality_in_conclusion_3,\
        Equality_in_condition,\
        Factorial_Functional,\
        Factorial_Relational,\
        IRI_from_IRI,\
        Inconsistent_Entailment,\
        IndividualData_Separation_Inconsistency,\
        ListConstantEquality,\
        ListEqualityFromElementEquality,\
        ListLiteralEquality,\
        Multiple_IRIs_from_String,\
        Multiple_Strings_from_IRI,\
        Named_Arguments,\
        RDF_Combination_Member_1,\
        RDF_Combination_SubClass_4,\
        RDF_Combination_SubClass_6,\
        YoungParentDiscount_1

tmp = files(Arbitrary_Entailment)
PET_Arbitrary_Entailment = PositiveEntailmentTest(
        tmp.joinpath("Arbitrary_Entailment-premise.rif"),
        tmp.joinpath("Arbitrary_Entailment-conclusion.rif"),
        )

tmp = files(Chaining_strategy_numericadd_2)
PET_Chaining_strategy_numericadd_2 = PositiveEntailmentTest(
        tmp.joinpath("Chaining_strategy_numeric-add_2-premise.rif"),
        tmp.joinpath("Chaining_strategy_numeric-add_2-conclusion.rif"),
        )
tmp = files(Chaining_strategy_numericsubtract_1)
PET_Chaining_strategy_numericsubtract_1 = PositiveEntailmentTest(
        tmp.joinpath("Chaining_strategy_numeric-subtract_1-premise.rif"),
        tmp.joinpath("Chaining_strategy_numeric-subtract_1-conclusion.rif"),
        )
tmp = files(Class_Membership)
PET_Class_Membership = PositiveEntailmentTest(
        tmp.joinpath("Class_Membership-premise.rif"),
        tmp.joinpath("Class_Membership-conclusion.rif"),
        )
tmp = files(Classificationinheritance)
PET_Classificationinheritance = PositiveEntailmentTest(
        tmp.joinpath("Classification-inheritance-premise.rif"),
        tmp.joinpath("Classification-inheritance-conclusion.rif"),
        )
tmp = files(ElementEqualityFromListEquality)
PET_ElementEqualityFromListEquality = PositiveEntailmentTest(
        tmp.joinpath("ElementEqualityFromListEquality-premise.rif"),
        tmp.joinpath("ElementEqualityFromListEquality-conclusion.rif"),
        )
tmp = files(EntailEverything)
PET_EntailEverything = PositiveEntailmentTest(
        tmp.joinpath("EntailEverything-premise.rif"),
        tmp.joinpath("EntailEverything-conclusion.rif"),
        )
tmp = files(Equality_in_conclusion_1)
PET_Equality_in_conclusion_1 = PositiveEntailmentTest(
        tmp.joinpath("Equality_in_conclusion_1-premise.rif"),
        tmp.joinpath("Equality_in_conclusion_1-conclusion.rif"),
        )
tmp = files(Equality_in_conclusion_2)
PET_Equality_in_conclusion_2 = PositiveEntailmentTest(
        tmp.joinpath("Equality_in_conclusion_2-premise.rif"),
        tmp.joinpath("Equality_in_conclusion_2-conclusion.rif"),
        )
tmp = files(Equality_in_conclusion_3)
PET_Equality_in_conclusion_3 = PositiveEntailmentTest(
        tmp.joinpath("Equality_in_conclusion_3-premise.rif"),
        tmp.joinpath("Equality_in_conclusion_3-conclusion.rif"),
        )
tmp = files(Equality_in_condition)
PET_Equality_in_condition = PositiveEntailmentTest(
        tmp.joinpath("Equality_in_condition-premise.rif"),
        tmp.joinpath("Equality_in_condition-conclusion.rif"),
        )
tmp = files(Factorial_Functional)
PET_Factorial_Functional = PositiveEntailmentTest(
        tmp.joinpath("Factorial_Functional-premise.rif"),
        tmp.joinpath("Factorial_Functional-conclusion.rif"),
        )
tmp = files(Factorial_Relational)
PET_Factorial_Relational = PositiveEntailmentTest(
        tmp.joinpath("Factorial_Relational-premise.rif"),
        tmp.joinpath("Factorial_Relational-conclusion.rif"),
        )
tmp = files(IRI_from_IRI)
PET_IRI_from_IRI = PositiveEntailmentTest(
        tmp.joinpath("IRI_from_IRI-premise.rif"),
        tmp.joinpath("IRI_from_IRI-conclusion.rif"),
        )
tmp = files(Inconsistent_Entailment)
PET_Inconsistent_Entailment = PositiveEntailmentTest(
        tmp.joinpath("Inconsistent_Entailment-premise.rif"),
        tmp.joinpath("Inconsistent_Entailment-conclusion.rif"),
        )
tmp = files(IndividualData_Separation_Inconsistency)
PET_IndividualData_Separation_Inconsistency = PositiveEntailmentTest(\
        tmp.joinpath("IndividualData_Separation_Inconsistency-premise.rif"),
        tmp.joinpath("IndividualData_Separation_Inconsistency-conclusion.rif"),
        )
tmp = files(ListConstantEquality)
PET_ListConstantEquality = PositiveEntailmentTest(
        tmp.joinpath("ListConstantEquality-premise.rif"),
        tmp.joinpath("ListConstantEquality-conclusion.rif"),
        )
tmp = files(ListEqualityFromElementEquality)
PET_ListEqualityFromElementEquality = PositiveEntailmentTest(
        tmp.joinpath("ListEqualityFromElementEquality-premise.rif"),
        tmp.joinpath("ListEqualityFromElementEquality-conclusion.rif"),
        )
tmp = files(ListLiteralEquality)
PET_ListLiteralEquality = PositiveEntailmentTest(
        tmp.joinpath("ListLiteralEquality-premise.rif"),
        tmp.joinpath("ListLiteralEquality-conclusion.rif"),
        )
tmp = files(Multiple_IRIs_from_String)
PET_Multiple_IRIs_from_String = PositiveEntailmentTest(
        tmp.joinpath("Multiple_IRIs_from_String-premise.rif"),
        tmp.joinpath("Multiple_IRIs_from_String-conclusion.rif"),
        )
tmp = files(Multiple_Strings_from_IRI)
PET_Multiple_Strings_from_IRI = PositiveEntailmentTest(
        tmp.joinpath("Multiple_Strings_from_IRI-premise.rif"),
        tmp.joinpath("Multiple_Strings_from_IRI-conclusion.rif"),
        )
tmp = files(Named_Arguments)
PET_Named_Arguments = PositiveEntailmentTest(
        tmp.joinpath("Named_Arguments-premise.rif"),
        tmp.joinpath("Named_Arguments-conclusion.rif"),
        )
tmp = files(RDF_Combination_Member_1)
PET_RDF_Combination_Member_1 = PositiveEntailmentTest(
        tmp.joinpath("RDF_Combination_Member_1-premise.rif"),
        tmp.joinpath("RDF_Combination_Member_1-conclusion.rif"),
        )
tmp = files(RDF_Combination_SubClass_4)
PET_RDF_Combination_SubClass_4 = PositiveEntailmentTest(
        tmp.joinpath("RDF_Combination_SubClass_4-premise.rif"),
        tmp.joinpath("RDF_Combination_SubClass_4-conclusion.rif"),
        )
tmp = files(RDF_Combination_SubClass_6)
PET_RDF_Combination_SubClass_6 = PositiveEntailmentTest(
        tmp.joinpath("RDF_Combination_SubClass_6-premise.rif"),
        tmp.joinpath("RDF_Combination_SubClass_6-conclusion.rif"),
        )
tmp = files(YoungParentDiscount_1)
PET_YoungParentDiscount_1 = PositiveEntailmentTest(
        tmp.joinpath("YoungParentDiscount_1-premise.rif"),
        tmp.joinpath("YoungParentDiscount_1-conclusion.rif"),
        )


from .NegativeEntailmentTest import \
        Classification_noninheritance,\
        Named_Argument_Uniterms_nonpolymorphic,\
        OpenLists,\
        RDF_Combination_SubClass_3,\
        RDF_Combination_SubClass_5

#NET_Retract = NegativeEntailmentTest(
#        tmp.joinpath("Retract-premise.rif"),
#        tmp.joinpath("Retract-nonconclusion.rif"),
#        )
tmp = files(Classification_noninheritance)
tmp = files(Named_Argument_Uniterms_nonpolymorphic)
tmp = files(OpenLists)
tmp = files(RDF_Combination_SubClass_3)
tmp = files(RDF_Combination_SubClass_5)

@pytest.fixture(params=[
    param(PET_Arbitrary_Entailment,
          marks=mark.skip("not yet implemented")),
    param(PET_Chaining_strategy_numericadd_2,
          marks=mark.skip("not yet implemented")),
    param(PET_Chaining_strategy_numericsubtract_1,
          marks=mark.skip("not yet implemented")),
    param(PET_Class_Membership,
          marks=mark.skip("not yet implemented")),
    param(PET_Classificationinheritance,
          id="PET_Classificationinheritance"),
    param(PET_ElementEqualityFromListEquality,
          marks=mark.skip("not yet implemented")),
    param(PET_EntailEverything,
          marks=mark.skip("not yet implemented")),
    param(PET_Equality_in_conclusion_1,
          marks=mark.skip("not yet implemented")),
    param(PET_Equality_in_conclusion_2,
          marks=mark.skip("not yet implemented")),
    param(PET_Equality_in_conclusion_3,
          marks=mark.skip("not yet implemented")),
    param(PET_Equality_in_condition,
          marks=mark.skip("Doesnt work with"),
          id="PET_Equality_in_condition"),
    param(PET_Factorial_Functional,
          marks=mark.skip("not yet implemented")),
    param(PET_Factorial_Relational,
          marks=mark.skip("not yet implemented")),
    param(PET_IRI_from_IRI,
          marks=mark.skip("not yet implemented")),
    param(PET_Inconsistent_Entailment,
          marks=mark.skip("not yet implemented")),
    param(PET_IndividualData_Separation_Inconsistency,
          marks=mark.skip("not yet implemented")),
    param(PET_ListConstantEquality,
          marks=mark.skip("not yet implemented")),
    param(PET_ListEqualityFromElementEquality,
          marks=mark.skip("not yet implemented")),
    param(PET_ListLiteralEquality,
          marks=mark.skip("not yet implemented")),
    param(PET_Multiple_IRIs_from_String,
          marks=mark.skip("not yet implemented")),
    param(PET_Multiple_Strings_from_IRI,
          marks=mark.skip("not yet implemented")),
    param(PET_Named_Arguments,
          marks=mark.skip("not yet implemented")),
    param(PET_RDF_Combination_Member_1,
          marks=mark.skip("not yet implemented")),
    param(PET_RDF_Combination_SubClass_4,
          marks=mark.skip("not yet implemented")),
    param(PET_RDF_Combination_SubClass_6,
          marks=mark.skip("not yet implemented")),
    param(PET_YoungParentDiscount_1,
          marks=mark.skip("not yet implemented")),
    ])
def PET_testdata(request):
    return request.param

@pytest.fixture(params=[
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
    if isinstance(logic_machine, BLD_logicMachine):
        return Tuple()
    else:
        return (AlgorithmRejection,)


class TestPRD(blueprint_test_logicmachine):
    pass
