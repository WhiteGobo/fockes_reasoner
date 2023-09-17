import abc
from typing import Iterable, Optional, Mapping
import rdflib
from .rif_dataobjects import rif_fact

class logicMachine(abc.ABC):
    @abc.abstractmethod
    def check(self, rif_facts: Iterable[rif_fact]) -> bool:
        ...

    @classmethod
    @abc.abstractmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 extraDocuments: Optional[Mapping[str, rdflib.Graph]] = None,
                 ) -> "logicMachine":
        ...

    @abc.abstractmethod
    def run(self) -> None:
        ...
