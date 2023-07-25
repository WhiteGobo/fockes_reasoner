from collections import namedtuple
import importlib.resources

from . import PRD
_PRD = importlib.resources.files(PRD)

PositiveEntailmentTest = namedtuple("PositiveEntailmentTest", ("premise", "conclusion"))
PET_Assert = PositiveEntailmentTest(
        _PRD.joinpath("PositiveEntailmentTest/Assert/Assert-premise.rif"),
        _PRD.joinpath("PositiveEntailmentTest/Assert/Assert-conclusion.rif"),
        )
PositiveEntailmenttests = [PET_Assert]
