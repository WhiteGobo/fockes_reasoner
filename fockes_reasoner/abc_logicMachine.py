import abc
from typing import Iterable, Optional, Mapping
import rdflib
from .rif_dataobjects import rif_fact

class AlgorithmRejection(Exception):
    """If given algorithm cant be run by this logicMachine.
    """
    ...

class ImportReject(Exception):
    """
    :TODO: This must be placed somewhere else
    """
    ...

class logicMachine(abc.ABC):
    @abc.abstractmethod
    def check(self, rif_facts: Iterable[rif_fact]) -> bool:
        ...

    @classmethod
    @abc.abstractmethod
    def from_rdf(cls, infograph: rdflib.Graph,
                 extraDocuments: Optional[Mapping[str, rdflib.Graph]] = None,
                 ) -> "logicMachine":
        """
        :raises AlgorithmRejection:
        """
        ...

    @abc.abstractmethod
    def run(self) -> None:
        ...


class PRD_logicMachine(logicMachine):
    ...


class BLD_logicMachine(logicMachine):
    ...
