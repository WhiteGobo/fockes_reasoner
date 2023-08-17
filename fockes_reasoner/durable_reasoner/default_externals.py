from typing import Callable, Union
import rdflib
from rdflib import Literal, Variable

from .abc_machine import BINDING

def ascondition_pred_greater_than(bigger: Union[Literal, Variable], smaller: Union[Literal, Variable]) -> Callable[[BINDING], bool]:
    valid1 = bigger.isnumeric() or isinstance(bigger, Variable)
    valid2 = smaller.isnumeric() or isinstance(smaller, Variable)
    if (not valid1) and (not valid2):
        raise ValueError("Can only compare two literals (or variables): %s"
                    % ([(bigger, valid1), (smaller, valid2)]))
    def greater_than(bindings: BINDING) -> bool:
        b = bindings.get(bigger, bigger)
        s = bindings.get(smaller, smaller)
        return b > s
    return greater_than
