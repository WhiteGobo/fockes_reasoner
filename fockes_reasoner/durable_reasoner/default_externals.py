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
        return Literal(b > s)
    return greater_than

def asassign_func_numeric_subtract(first: Union[Literal, Variable], second: Union[Literal, Variable]) -> Callable[[BINDING], Literal]:
    valid1 = first.isnumeric() or isinstance(first, Variable)
    valid2 = second.isnumeric() or isinstance(second, Variable)
    def numeric_subtract(bindings: BINDING) -> Literal:
        f = bindings.get(first, first)
        s = bindings.get(second, second)
        return Literal(f - s)
    return numeric_subtract

def ascondition_pred_literal_not_identical(first, second) -> Callable[[BINDING], bool]:
    return first != second
