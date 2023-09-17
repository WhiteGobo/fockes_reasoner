from urllib.parse import urlparse
from os.path import basename

class PositiveEntailmentTest:
    def __init__(self, premise, conclusion, importedDocuments={}):
        self.premise = str(premise)
        self.conclusion = str(conclusion)
        self.importedDocuments = {x: y for x, y in dict(importedDocuments).items()}
        try:
            self.name = basename(urlparse(self.premise).path)
        except Exception:
            self.name = None
#NegativeEntailmentTest = namedtuple("NegativeEntailmentTest", ("premise", "conclusion"))
class NegativeEntailmentTest:
    def __init__(self, premise, nonconclusion, importedDocuments={}):
        self.premise = str(premise)
        self.nonconclusion = str(nonconclusion)
        self.importedDocuments = {x: y for x, y in dict(importedDocuments).items()}
        try:
            self.name = basename(urlparse(self.premise).path)
        except Exception:
            self.name = None

    def __iter__(self):
        yield self.premise
        yield self.nonconclusion
        yield self.importedDocuments


class ImportRejectionTest:
    def __init__(self, input, importedDocuments={}):
        self.input = str(input)
        self.premise = self.input
        self.importedDocuments = {x: y for x, y in dict(importedDocuments).items()}
        try:
            self.name = basename(urlparse(self.premise).path)
        except Exception:
            self.name = None

class PositiveSyntaxTest:
    def __init__(self, premise, importedDocuments={}):
        self.premise = str(premise)
        self.importedDocuments = {x: y for x, y in dict(importedDocuments).items()}
        try:
            self.name = basename(urlparse(self.premise).path)
        except Exception:
            self.name = None

class NegativeSyntaxTest:
    def __init__(self, premise, importedDocuments={}):
        self.premise = str(premise)
        self.importedDocuments = {x: y for x, y in dict(importedDocuments).items()}
        try:
            self.name = basename(urlparse(self.premise).path)
        except Exception:
            self.name = None
