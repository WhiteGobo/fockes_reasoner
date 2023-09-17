from collections import namedtuple
import importlib.resources
from importlib.resources import files

from . import PRD
_PRD = importlib.resources.files(PRD)
from . import Core
_Core = importlib.resources.files(Core)
from . import BLD

#PositiveEntailmentTest = namedtuple("PositiveEntailmentTest", ("premise", "conclusion"))
class PositiveEntailmentTest:
    def __init__(self, premise, conclusion, importedDocuments={}):
        self.premise = str(premise)
        self.conclusion = str(conclusion)
        self.importedDocuments = {x: y for x, y in dict(importedDocuments).items()}
#NegativeEntailmentTest = namedtuple("NegativeEntailmentTest", ("premise", "conclusion"))
class NegativeEntailmentTest:
    def __init__(self, premise, nonconclusion, importedDocuments={}):
        self.premise = str(premise)
        self.nonconclusion = str(nonconclusion)
        self.importedDocuments = {x: y for x, y in dict(importedDocuments).items()}

    def __iter__(self):
        yield self.premise
        yield self.nonconclusion
        yield self.importedDocuments


class ImportRejectionTest:
    def __init__(self, premise, importedDocuments={}):
        self.premise = str(premise)
        self.importedDocuments = {x: y for x, y in dict(importedDocuments).items()}

class PositiveSyntaxTest:
    def __init__(self, premise, importedDocuments={}):
        self.premise = str(premise)
        self.importedDocuments = {x: y for x, y in dict(importedDocuments).items()}

class NegativeSyntaxTest:
    def __init__(self, premise, importedDocuments={}):
        self.premise = str(premise)
        self.importedDocuments = {x: y for x, y in dict(importedDocuments).items()}

from .Core.PositiveEntailmentTest import\
        Modeling_Brain_Anatomy,\
        IRI_from_RDF_Literal,\
        RDF_Combination_Blank_Node,\
        RDF_Combination_Constant_Equivalence_1,\
        RDF_Combination_Constant_Equivalence_2,\
        RDF_Combination_Constant_Equivalence_3,\
        RDF_Combination_Constant_Equivalence_4,\
        RDF_Combination_Constant_Equivalence_Graph_Entailment,\
        RDF_Combination_SubClass_2

PET_Assert = PositiveEntailmentTest(
        _PRD.joinpath("PositiveEntailmentTest/Assert/Assert-premise.rif"),
        _PRD.joinpath("PositiveEntailmentTest/Assert/Assert-conclusion.rif"),
        )

PET_AssertRetract = PositiveEntailmentTest(
        _PRD.joinpath("PositiveEntailmentTest/AssertRetract/AssertRetract-premise.rif"),
        _PRD.joinpath("PositiveEntailmentTest/AssertRetract/AssertRetract-conclusion.rif"),
        )

PET_AssertRetract2 = PositiveEntailmentTest(
        _PRD.joinpath("PositiveEntailmentTest/AssertRetract2/AssertRetract2-premise.rif"),
        _PRD.joinpath("PositiveEntailmentTest/AssertRetract2/AssertRetract2-conclusion.rif"),
        )

PET_Modify = PositiveEntailmentTest(
        _PRD.joinpath("PositiveEntailmentTest/Modify/Modify-premise.rif"),
        _PRD.joinpath("PositiveEntailmentTest/Modify/Modify-conclusion.rif"),
        )

PET_Modify_loop = PositiveEntailmentTest(
        _PRD.joinpath("PositiveEntailmentTest/Modify_loop/Modify_loop-premise.rif"),
        _PRD.joinpath("PositiveEntailmentTest/Modify_loop/Modify_loop-conclusion.rif"),
        )

PET_Builtin_literal_not_identical = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Builtin_literal-not-identical/Builtin_literal-not-identical-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Builtin_literal-not-identical/Builtin_literal-not-identical-conclusion.rif"),
        )

PET_Builtins_Binary = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Builtins_Binary/Builtins_Binary-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Builtins_Binary/Builtins_Binary-conclusion.rif"),
        )

PET_Builtins_List = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Builtins_List/Builtins_List-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Builtins_List/Builtins_List-conclusion.rif"),
        )

PET_Builtins_Numeric = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Builtins_Numeric/Builtins_Numeric-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Builtins_Numeric/Builtins_Numeric-conclusion.rif"),
        )

PET_Builtins_Numeric = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Builtins_Numeric/Builtins_Numeric-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Builtins_Numeric/Builtins_Numeric-conclusion.rif"),
        )

PET_Builtins_PlainLiteral  = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Builtins_PlainLiteral/Builtins_PlainLiteral-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Builtins_PlainLiteral/Builtins_PlainLiteral-conclusion.rif"),
        )

PET_Builtins_String = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Builtins_String/Builtins_String-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Builtins_String/Builtins_String-conclusion.rif"),
        )

PET_Builtins_Time = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Builtins_Time/Builtins_Time-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Builtins_Time/Builtins_Time-conclusion.rif"),
        )

PET_Builtins_XMLLiteral = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Builtins_XMLLiteral/Builtins_XMLLiteral-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Builtins_XMLLiteral/Builtins_XMLLiteral-conclusion.rif"),
        )

PET_Builtins_anyURI = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Builtins_anyURI/Builtins_anyURI-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Builtins_anyURI/Builtins_anyURI-conclusion.rif"),
        )

PET_Builtins_boolean = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Builtins_boolean/Builtins_boolean-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Builtins_boolean/Builtins_boolean-conclusion.rif"),
        )

PET_Chaining_strategy_numeric_add_1 = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Chaining_strategy_numeric-add_1/Chaining_strategy_numeric-add_1-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Chaining_strategy_numeric-add_1/Chaining_strategy_numeric-add_1-conclusion.rif"),
        )

PET_Chaining_strategy_numeric_subtract_2 = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Chaining_strategy_numeric-subtract_2/Chaining_strategy_numeric-subtract_2-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Chaining_strategy_numeric-subtract_2/Chaining_strategy_numeric-subtract_2-conclusion.rif"),
        )

PET_EBusiness_Contract = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/EBusiness_Contract/EBusiness_Contract-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/EBusiness_Contract/EBusiness_Contract-conclusion.rif"),
        )

PET_Factorial_Forward_Chaining = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Factorial_Forward_Chaining/Factorial_Forward_Chaining-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Factorial_Forward_Chaining/Factorial_Forward_Chaining-conclusion.rif"),
        )

PET_Frame_slots_are_independent = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Frame_slots_are_independent/Frame_slots_are_independent-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Frame_slots_are_independent/Frame_slots_are_independent-conclusion.rif"),
        )

PET_Frames = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Frames/Frames-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Frames/Frames-conclusion.rif"),
        )

PET_Guards_and_subtypes = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Guards_and_subtypes/Guards_and_subtypes-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Guards_and_subtypes/Guards_and_subtypes-conclusion.rif"),
        )

tmp = files(IRI_from_RDF_Literal)
PET_IRI_from_RDF_Literal = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/IRI_from_RDF_Literal/IRI_from_RDF_Literal-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/IRI_from_RDF_Literal/IRI_from_RDF_Literal-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/IRI_from_RDF_Literal/IRI_from_RDF_Literal-import001":
         tmp.joinpath("IRI_from_RDF_Literal-import001.ttl")},
        )

tmp = files(Modeling_Brain_Anatomy)
PET_Modeling_Brain_Anatomy = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Modeling_Brain_Anatomy/Modeling_Brain_Anatomy-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Modeling_Brain_Anatomy/Modeling_Brain_Anatomy-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/Modeling_Brain_Anatomy/Modeling_Brain_Anatomy-import001.rdf":
        tmp.joinpath("Modeling_Brain_Anatomy-import001.rdf")},
        )

PET_OWL_Combination_Vocabulary_Separation_Inconsistency_1 = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/OWL_Combination_Vocabulary_Separation_Inconsistency_1/OWL_Combination_Vocabulary_Separation_Inconsistency_1-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/OWL_Combination_Vocabulary_Separation_Inconsistency_1/OWL_Combination_Vocabulary_Separation_Inconsistency_1-conclusion.rif"),
        )

PET_OWL_Combination_Vocabulary_Separation_Inconsistency_2 = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/OWL_Combination_Vocabulary_Separation_Inconsistency_2/OWL_Combination_Vocabulary_Separation_Inconsistency_2-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/OWL_Combination_Vocabulary_Separation_Inconsistency_2/OWL_Combination_Vocabulary_Separation_Inconsistency_2-conclusion.rif"),
        )

PET_Positional_Arguments = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/Positional_Arguments/Positional_Arguments-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/Positional_Arguments/Positional_Arguments-conclusion.rif"),
        )

tmp = files(RDF_Combination_Blank_Node)
PET_RDF_Combination_Blank_Node = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/RDF_Combination_Blank_Node/RDF_Combination_Blank_Node-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/RDF_Combination_Blank_Node/RDF_Combination_Blank_Node-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_Blank_Node/RDF_Combination_Blank_Node-import001":
         tmp.joinpath("RDF_Combination_Blank_Node-import001.ttl")}
        )

tmp = files(RDF_Combination_Constant_Equivalence_1)
PET_RDF_Combination_Constant_Equivalence_1 = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/RDF_Combination_Constant_Equivalence_1/RDF_Combination_Constant_Equivalence_1-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/RDF_Combination_Constant_Equivalence_1/RDF_Combination_Constant_Equivalence_1-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_Constant_Equivalence_1/RDF_Combination_Constant_Equivalence_1-import001":
         tmp.joinpath("RDF_Combination_Constant_Equivalence_1-import001.ttl")}
        )

tmp = files(RDF_Combination_Constant_Equivalence_2)
PET_RDF_Combination_Constant_Equivalence_2 = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/RDF_Combination_Constant_Equivalence_2/RDF_Combination_Constant_Equivalence_2-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/RDF_Combination_Constant_Equivalence_2/RDF_Combination_Constant_Equivalence_2-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_Constant_Equivalence_2/RDF_Combination_Constant_Equivalence_2-import001":
         tmp.joinpath("RDF_Combination_Constant_Equivalence_2-import001.ttl")}
        )

tmp = files(RDF_Combination_Constant_Equivalence_3)
PET_RDF_Combination_Constant_Equivalence_3 = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/RDF_Combination_Constant_Equivalence_3/RDF_Combination_Constant_Equivalence_3-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/RDF_Combination_Constant_Equivalence_3/RDF_Combination_Constant_Equivalence_3-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_Constant_Equivalence_3/RDF_Combination_Constant_Equivalence_3-import001":
         tmp.joinpath("RDF_Combination_Constant_Equivalence_3-import001.ttl")}
        )

tmp = files(RDF_Combination_Constant_Equivalence_4)
PET_RDF_Combination_Constant_Equivalence_4 = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/RDF_Combination_Constant_Equivalence_4/RDF_Combination_Constant_Equivalence_4-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/RDF_Combination_Constant_Equivalence_4/RDF_Combination_Constant_Equivalence_4-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_Constant_Equivalence_4/RDF_Combination_Constant_Equivalence_4-import001":
         tmp.joinpath("RDF_Combination_Constant_Equivalence_4-import001.ttl")}
        )

tmp = files(RDF_Combination_Constant_Equivalence_Graph_Entailment)
PET_RDF_Combination_Constant_Equivalence_Graph_Entailment = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/RDF_Combination_Constant_Equivalence_Graph_Entailment/RDF_Combination_Constant_Equivalence_Graph_Entailment-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/RDF_Combination_Constant_Equivalence_Graph_Entailment/RDF_Combination_Constant_Equivalence_Graph_Entailment-conclusion.rdf"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_Constant_Equivalence_Graph_Entailment/RDF_Combination_Constant_Equivalence_Graph_Entailment-import001":
         tmp.joinpath("RDF_Combination_Constant_Equivalence_Graph_Entailment-import001.rdf")},
        )

tmp = files(RDF_Combination_SubClass_2)
PET_RDF_Combination_SubClass_2 = PositiveEntailmentTest(
        _Core.joinpath("PositiveEntailmentTest/RDF_Combination_SubClass_2/RDF_Combination_SubClass_2-premise.rif"),
        _Core.joinpath("PositiveEntailmentTest/RDF_Combination_SubClass_2/RDF_Combination_SubClass_2-conclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_SubClass_2/RDF_Combination_SubClass_2-import001":
         tmp.joinpath("RDF_Combination_SubClass_2-import001.ttl")},
        )



NET_Retract = NegativeEntailmentTest(
        _PRD.joinpath("NegativeEntailmentTest/Retract/Retract-premise.rif"),
        _PRD.joinpath("NegativeEntailmentTest/Retract/Retract-nonconclusion.rif"),
        )

NET_RDF_Combination_SubClass_5 = NegativeEntailmentTest(
        _PRD.joinpath("NegativeEntailmentTest/RDF_Combination_SubClass_5/RDF_Combination_SubClass_5-premise.rif"),
        _PRD.joinpath("NegativeEntailmentTest/RDF_Combination_SubClass_5/RDF_Combination_SubClass_5-nonconclusion.rif"),
        {"http://www.w3.org/2005/rules/test/repository/tc/RDF_Combination_SubClass_5/RDF_Combination_SubClass_5-import001":
        _PRD.joinpath("NegativeEntailmentTest/RDF_Combination_SubClass_5/RDF_Combination_SubClass_5-import001.ttl")},
        )

from .Core.NegativeEntailmentTest import\
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


from .BLD.PositiveEntailmentTest import\
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

from .BLD.NegativeEntailmentTest import\
        Classification_noninheritance,\
        Named_Argument_Uniterms_nonpolymorphic,\
        OpenLists,\
        RDF_Combination_SubClass_3,\
        RDF_Combination_SubClass_5

tmp = files(Classification_noninheritance)
tmp = files(Named_Argument_Uniterms_nonpolymorphic)
tmp = files(OpenLists)
tmp = files(RDF_Combination_SubClass_3)
tmp = files(RDF_Combination_SubClass_5)

from .BLD.NegativeSyntaxTest import No_free_variables

tmp = files(No_free_variables)
