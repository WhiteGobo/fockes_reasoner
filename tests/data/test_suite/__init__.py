from collections import namedtuple
import importlib.resources

from . import PRD
_PRD = importlib.resources.files(PRD)

PositiveEntailmentTest = namedtuple("PositiveEntailmentTest", ("premise", "conclusion"))
NegativeEntailmentTest = namedtuple("PositiveEntailmentTest", ("premise", "conclusion"))
class NegativeEntailmentTest:
    def __init__(self, premise, nonconclusion, importedDocuments={}):
        self.premise = str(premise)
        self.nonconclusion = str(nonconclusion)
        self.importedDocuments = {x: y for x, y in dict(importedDocuments).items()}

    def __iter__(self):
        yield self.premise
        yield self.nonconclusion
        yield self.importedDocuments

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

PositiveEntailmentTests = [PET_Assert,
        #PET_AssertRetract,
        PET_AssertRetract2,
        #PET_Modify,
        #PET_Modify_loop,
        ]
