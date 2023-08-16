from collections import namedtuple
import importlib.resources

from . import PRD
_PRD = importlib.resources.files(PRD)

PositiveEntailmentTest = namedtuple("PositiveEntailmentTest", ("premise", "conclusion"))
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

PositiveEntailmentTests = [PET_Assert,
        #PET_AssertRetract,
        PET_AssertRetract2,
        #PET_Modify,
        #PET_Modify_loop,
        ]
