import pytest
from pytest import param, mark, skip, raises
from importlib.resources import files

from ...blueprints_tests import blueprint_test_logicmachine
from ..mydata import PositiveEntailmentTest, NegativeEntailmentTest

from .PositiveEntailmentTest import \
        Builtin_literalnotidentical,\
        Builtins_Binary,\
        Builtins_List,\
        Builtins_Numeric,\
        Builtins_PlainLiteral,\
        Builtins_String,\
        Builtins_Time,\
        Builtins_XMLLiteral,\
        Builtins_anyURI,\
        Builtins_boolean,\
        Chaining_strategy_numericadd_1,\
        Chaining_strategy_numericsubtract_2,\
        EBusiness_Contract,\
        Factorial_Forward_Chaining,\
        Frame_slots_are_independent,\
        Frames,\
        Guards_and_subtypes,\
        IRI_from_RDF_Literal,\
        Modeling_Brain_Anatomy,\
        OWL_Combination_Vocabulary_Separation_Inconsistency_1,\
        OWL_Combination_Vocabulary_Separation_Inconsistency_2,\
        Positional_Arguments,\
        RDF_Combination_Blank_Node,\
        RDF_Combination_Constant_Equivalence_1,\
        RDF_Combination_Constant_Equivalence_2,\
        RDF_Combination_Constant_Equivalence_3,\
        RDF_Combination_Constant_Equivalence_4,\
        RDF_Combination_Constant_Equivalence_Graph_Entailment,\
        RDF_Combination_SubClass_2

tmp = files(Builtin_literalnotidentical)
PET_Builtin_literal_not_identical = PositiveEntailmentTest(
        tmp.joinpath("Builtin_literal-not-identical-premise.rif"),
        tmp.joinpath("Builtin_literal-not-identical-conclusion.rif"),
        )

tmp = files(Builtins_Binary)
PET_Builtins_Binary = PositiveEntailmentTest(
        tmp.joinpath("Builtins_Binary-premise.rif"),
        tmp.joinpath("Builtins_Binary-conclusion.rif"),
        )

tmp = files(Builtins_List)
PET_Builtins_List = PositiveEntailmentTest(
        tmp.joinpath("Builtins_List-premise.rif"),
        tmp.joinpath("Builtins_List-conclusion.rif"),
        )

tmp = files(Builtins_Numeric)
PET_Builtins_Numeric = PositiveEntailmentTest(
        tmp.joinpath("Builtins_Numeric-premise.rif"),
        tmp.joinpath("Builtins_Numeric-conclusion.rif"),
        )

tmp = files(Builtins_PlainLiteral)
PET_Builtins_PlainLiteral  = PositiveEntailmentTest(
        tmp.joinpath("Builtins_PlainLiteral-premise.rif"),
        tmp.joinpath("Builtins_PlainLiteral-conclusion.rif"),
        )

tmp = files(Builtins_String)
PET_Builtins_String = PositiveEntailmentTest(
        tmp.joinpath("Builtins_String-premise.rif"),
        tmp.joinpath("Builtins_String-conclusion.rif"),
        )

tmp = files(Builtins_Time)
PET_Builtins_Time = PositiveEntailmentTest(
        tmp.joinpath("Builtins_Time-premise.rif"),
        tmp.joinpath("Builtins_Time-conclusion.rif"),
        )

tmp = files(Builtins_XMLLiteral)
PET_Builtins_XMLLiteral = PositiveEntailmentTest(
        tmp.joinpath("Builtins_XMLLiteral-premise.rif"),
        tmp.joinpath("Builtins_XMLLiteral-conclusion.rif"),
        )

tmp = files(Builtins_anyURI)
PET_Builtins_anyURI = PositiveEntailmentTest(
        tmp.joinpath("Builtins_anyURI-premise.rif"),
        tmp.joinpath("Builtins_anyURI-conclusion.rif"),
        )

tmp = files(Builtins_boolean)
PET_Builtins_boolean = PositiveEntailmentTest(
        tmp.joinpath("Builtins_boolean-premise.rif"),
        tmp.joinpath("Builtins_boolean-conclusion.rif"),
        )

tmp = files(Chaining_strategy_numericadd_1)
PET_Chaining_strategy_numeric_add_1 = PositiveEntailmentTest(
        tmp.joinpath("Chaining_strategy_numeric-add_1-premise.rif"),
        tmp.joinpath("Chaining_strategy_numeric-add_1-conclusion.rif"),
        )

tmp = files(Chaining_strategy_numericsubtract_2)
PET_Chaining_strategy_numeric_subtract_2 = PositiveEntailmentTest(
        tmp.joinpath("Chaining_strategy_numeric-subtract_2-premise.rif"),
        tmp.joinpath("Chaining_strategy_numeric-subtract_2-conclusion.rif"),
        )

tmp = files(EBusiness_Contract)
PET_EBusiness_Contract = PositiveEntailmentTest(
        tmp.joinpath("EBusiness_Contract-premise.rif"),
        tmp.joinpath("EBusiness_Contract-conclusion.rif"),
        )

tmp = files(Factorial_Forward_Chaining)
PET_Factorial_Forward_Chaining = PositiveEntailmentTest(
        tmp.joinpath("Factorial_Forward_Chaining-premise.rif"),
        tmp.joinpath("Factorial_Forward_Chaining-conclusion.rif"),
        )

tmp = files(Frame_slots_are_independent)
PET_Frame_slots_are_independent = PositiveEntailmentTest(
        tmp.joinpath("Frame_slots_are_independent-premise.rif"),
        tmp.joinpath("Frame_slots_are_independent-conclusion.rif"),
        )

tmp = files(Frames)
PET_Frames = PositiveEntailmentTest(
        tmp.joinpath("Frames-premise.rif"),
        tmp.joinpath("Frames-conclusion.rif"),
        )

tmp = files(Guards_and_subtypes)
PET_Guards_and_subtypes = PositiveEntailmentTest(
        tmp.joinpath("Guards_and_subtypes-premise.rif"),
        tmp.joinpath("Guards_and_subtypes-conclusion.rif"),
        )

tmp = files(IRI_from_RDF_Literal)
PET_IRI_from_RDF_Literal = PositiveEntailmentTest(
        tmp.joinpath("IRI_from_RDF_Literal-premise.rif"),
        tmp.joinpath("IRI_from_RDF_Literal-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/IRI_from_RDF_Literal/IRI_from_RDF_Literal-import001":
         tmp.joinpath("IRI_from_RDF_Literal-import001.ttl")},
        )

tmp = files(Modeling_Brain_Anatomy)
PET_Modeling_Brain_Anatomy = PositiveEntailmentTest(
        tmp.joinpath("Modeling_Brain_Anatomy-premise.rif"),
        tmp.joinpath("Modeling_Brain_Anatomy-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/Modeling_Brain_Anatomy/Modeling_Brain_Anatomy-import001.rdf":
        tmp.joinpath("Modeling_Brain_Anatomy-import001.rdf")},
        )

tmp = files(OWL_Combination_Vocabulary_Separation_Inconsistency_1)
PET_OWL_Combination_Vocabulary_Separation_Inconsistency_1 = PositiveEntailmentTest(
        tmp.joinpath("OWL_Combination_Vocabulary_Separation_Inconsistency_1-premise.rif"),
        tmp.joinpath("OWL_Combination_Vocabulary_Separation_Inconsistency_1-conclusion.rif"),
        )

tmp = files(OWL_Combination_Vocabulary_Separation_Inconsistency_2)
PET_OWL_Combination_Vocabulary_Separation_Inconsistency_2 = PositiveEntailmentTest(
        tmp.joinpath("OWL_Combination_Vocabulary_Separation_Inconsistency_2-premise.rif"),
        tmp.joinpath("OWL_Combination_Vocabulary_Separation_Inconsistency_2-conclusion.rif"),
        )

tmp = files(Positional_Arguments)
PET_Positional_Arguments = PositiveEntailmentTest(
        tmp.joinpath("Positional_Arguments-premise.rif"),
        tmp.joinpath("Positional_Arguments-conclusion.rif"),
        )

tmp = files(RDF_Combination_Blank_Node)
PET_RDF_Combination_Blank_Node = PositiveEntailmentTest(
        tmp.joinpath("RDF_Combination_Blank_Node-premise.rif"),
        tmp.joinpath("RDF_Combination_Blank_Node-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_Blank_Node/RDF_Combination_Blank_Node-import001":
         tmp.joinpath("RDF_Combination_Blank_Node-import001.ttl")}
        )

tmp = files(RDF_Combination_Constant_Equivalence_1)
PET_RDF_Combination_Constant_Equivalence_1 = PositiveEntailmentTest(
        tmp.joinpath("RDF_Combination_Constant_Equivalence_1-premise.rif"),
        tmp.joinpath("RDF_Combination_Constant_Equivalence_1-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_Constant_Equivalence_1/RDF_Combination_Constant_Equivalence_1-import001":
         tmp.joinpath("RDF_Combination_Constant_Equivalence_1-import001.ttl")}
        )

tmp = files(RDF_Combination_Constant_Equivalence_2)
PET_RDF_Combination_Constant_Equivalence_2 = PositiveEntailmentTest(
        tmp.joinpath("RDF_Combination_Constant_Equivalence_2-premise.rif"),
        tmp.joinpath("RDF_Combination_Constant_Equivalence_2-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_Constant_Equivalence_2/RDF_Combination_Constant_Equivalence_2-import001":
         tmp.joinpath("RDF_Combination_Constant_Equivalence_2-import001.ttl")}
        )

tmp = files(RDF_Combination_Constant_Equivalence_3)
PET_RDF_Combination_Constant_Equivalence_3 = PositiveEntailmentTest(
        tmp.joinpath("RDF_Combination_Constant_Equivalence_3-premise.rif"),
        tmp.joinpath("RDF_Combination_Constant_Equivalence_3-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_Constant_Equivalence_3/RDF_Combination_Constant_Equivalence_3-import001":
         tmp.joinpath("RDF_Combination_Constant_Equivalence_3-import001.ttl")}
        )

tmp = files(RDF_Combination_Constant_Equivalence_4)
PET_RDF_Combination_Constant_Equivalence_4 = PositiveEntailmentTest(
        tmp.joinpath("RDF_Combination_Constant_Equivalence_4-premise.rif"),
        tmp.joinpath("RDF_Combination_Constant_Equivalence_4-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_Constant_Equivalence_4/RDF_Combination_Constant_Equivalence_4-import001":
         tmp.joinpath("RDF_Combination_Constant_Equivalence_4-import001.ttl")}
        )

tmp = files(RDF_Combination_Constant_Equivalence_Graph_Entailment)
PET_RDF_Combination_Constant_Equivalence_Graph_Entailment = PositiveEntailmentTest(
        tmp.joinpath("RDF_Combination_Constant_Equivalence_Graph_Entailment-premise.rif"),
        tmp.joinpath("RDF_Combination_Constant_Equivalence_Graph_Entailment-conclusion.rdf"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_Constant_Equivalence_Graph_Entailment/RDF_Combination_Constant_Equivalence_Graph_Entailment-import001":
         tmp.joinpath("RDF_Combination_Constant_Equivalence_Graph_Entailment-import001.rdf")},
        )

tmp = files(RDF_Combination_SubClass_2)
PET_RDF_Combination_SubClass_2 = PositiveEntailmentTest(
        tmp.joinpath("RDF_Combination_SubClass_2-premise.rif"),
        tmp.joinpath("RDF_Combination_SubClass_2-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_SubClass_2/RDF_Combination_SubClass_2-import001":
         tmp.joinpath("RDF_Combination_SubClass_2-import001.ttl")},
        )



from .NegativeEntailmentTest import \
        Local_Constant,\
        Local_Predicate,\
        NestedListsAreNotFlatLists,\
        NonAnnotation_Entailment,\
        RDF_Combination_SubClass

tmp = files(Local_Constant)
NET_Local_Constant = NegativeEntailmentTest(
        tmp.joinpath("Local_Constant-premise.rif"),
        tmp.joinpath("Local_Constant-nonconclusion.rif"))

tmp = files(Local_Predicate)
NET_Local_Predicate = NegativeEntailmentTest(
        tmp.joinpath("Local_Predicate-premise.rif"),
        tmp.joinpath("Local_Predicate-nonconclusion.rif"),
        )

tmp = files(NestedListsAreNotFlatLists)
NET_NestedListsAreNotFlatLists = NegativeEntailmentTest(
        tmp.joinpath("NestedListsAreNotFlatLists-premise.rif"),
        tmp.joinpath("NestedListsAreNotFlatLists-nonconclusion.rif"),
        )

tmp = files(NonAnnotation_Entailment)
NET_Non_Annotation_Entailment = NegativeEntailmentTest(
        tmp.joinpath("Non-Annotation_Entailment-premise.rif"),
        tmp.joinpath("Non-Annotation_Entailment-nonconclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/Non-Annotation_Entailment/Non-Annotation_Entailment-import001":
         tmp.joinpath("Non-Annotation_Entailment-import001.ttl")},
        )

tmp = files(RDF_Combination_SubClass)
NET_RDF_Combination_SubClass = NegativeEntailmentTest(
        tmp.joinpath("RDF_Combination_SubClass-premise.rif"),
        tmp.joinpath("RDF_Combination_SubClass-nonconclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_SubClass/RDF_Combination_SubClass-import001":
        tmp.joinpath("RDF_Combination_SubClass-import001.ttl")},
        )

@pytest.fixture(params=[
    pytest.param(PET_Builtin_literal_not_identical,
                 id="builtin literal not identical"),
    pytest.param(PET_Builtins_Binary, id="builtins binary"),
    pytest.param(PET_Builtins_List, id="builtins list"),
    pytest.param(PET_Builtins_Numeric, id="PET Builtins_Numeric"),
    pytest.param(PET_Builtins_PlainLiteral,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_Builtins_String,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_Builtins_Time,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_Builtins_XMLLiteral,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_Builtins_anyURI,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_Builtins_boolean,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_Chaining_strategy_numeric_add_1,
                 id="chaining strategy numeric add 1"),
    pytest.param(PET_Chaining_strategy_numeric_subtract_2,
                 id="chaining strategy numeric subtract 2"),
    pytest.param(PET_EBusiness_Contract,
                 marks=mark.skip("First have to implemente builtin time"),
                 id="PET_EBusiness_Contract"),
    pytest.param(PET_Factorial_Forward_Chaining,
                 marks=mark.skip("Uses rif_equal to bind variables. nyi"),
                 id="PET_Factorial_Forward_Chaining"),
    pytest.param(PET_Frame_slots_are_independent,
                 id="independent frame slots"),
    pytest.param(PET_Frames, id="Frames"),
    pytest.param(PET_Guards_and_subtypes, id="guards and subtypes"),
    pytest.param(PET_IRI_from_RDF_Literal, id="IRI_from_RDF_Literal"),
    pytest.param(PET_Modeling_Brain_Anatomy,
                 marks=mark.skip("No owl implemented yet."),
                 id="PET_Modeling_Brain_Anatomy"),
    pytest.param(PET_OWL_Combination_Vocabulary_Separation_Inconsistency_1,
                 marks=mark.skip("not yet implemented"),
                 id="PET_OWL_Comb Vocabulary_Separation_Inconsistency_1"),
    pytest.param(PET_OWL_Combination_Vocabulary_Separation_Inconsistency_2,
                 marks=mark.skip("not yet implemented"),
                 id="PET_OWL_Comb Vocabulary_Separation_Inconsistency_2"),
    pytest.param(PET_Positional_Arguments, id="Positional Arguments"),
    pytest.param(PET_RDF_Combination_Blank_Node, id="RDF Comb Blank Node"),
    pytest.param(PET_RDF_Combination_Constant_Equivalence_1,
                 id="RDF_Combination_Constant_Equivalence_1"),
    pytest.param(PET_RDF_Combination_Constant_Equivalence_2,
                 id="RDF_Combination_Constant_Equivalence_2"),
    pytest.param(PET_RDF_Combination_Constant_Equivalence_3,
                 id="RDF_Combination_Constant_Equivalence_3"),
    pytest.param(PET_RDF_Combination_Constant_Equivalence_4,
                 id="RDF_Combination_Constant_Equivalence_4"),
    pytest.param(PET_RDF_Combination_Constant_Equivalence_Graph_Entailment,
                 marks=mark.skip("The test uses conclusion format ttl"),
                 id="RDF Combination Constant Equivalence Graph Entailment"),
    pytest.param(PET_RDF_Combination_SubClass_2,
                 id="RDF Combination SubClass 2"),
    ])
def PET_testdata(request):
    return request.param

@pytest.fixture(params=[
    param(NET_Local_Constant,
          marks=pytest.mark.skip("No local variables supported yet"),
          id="NET_Local_Constant"),
    param(NET_Local_Predicate,
          marks=pytest.mark.skip("No local variables supported yet"),
          id="NET_Local_Predicate"),
    param(NET_NestedListsAreNotFlatLists,
          id="NET NestedListsAreNotFlatLists"),
    param(NET_Non_Annotation_Entailment,
          marks=mark.skip("Owl not yet implemented"),
          id="NET_Non_Annotation_Entailment"),
    param(NET_RDF_Combination_SubClass,
          id="NET_RDF_Combination_SubClass"),
    ])
def NET_testdata(request):
    return request.param

@pytest.fixture
def valid_exceptions_PET(PET_testdata, logic_machine):
    return tuple()
    #return (TypeError,)

@pytest.fixture
def valid_exceptions_NET(NET_testdata, logic_machine):
    return tuple()


class TestPRD(blueprint_test_logicmachine):
    pass
