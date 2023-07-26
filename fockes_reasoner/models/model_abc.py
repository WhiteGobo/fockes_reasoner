import abc
from collections.abc import Iterator, Container, Mapping, Iterable
import rdflib


class export_model(abc.ABC):
    @abc.abstractmethod
    def export(self, factiterator: Iterable[Mapping[str, str]],
               ) -> Iterator[tuple]:
        ...

#class import_model(abc.ABC):
#    @abc.abstractmethod
#    def import(self, graph: Iterable) -> None:
#        ...
