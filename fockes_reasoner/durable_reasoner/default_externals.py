from typing import Callable, Union, TypeVar
import rdflib
from rdflib import Literal, Variable, XSD, IdentifiedNode, Literal, URIRef

from .abc_machine import BINDING
from ..shared import pred, func

def _resolve(x, bindings: BINDING):
    """Resolve variables and externals
    """
    if isinstance(x, Variable):
        return bindings[x]
    elif isinstance(x, (IdentifiedNode, Literal)):
        return x
    else:
        return x(bindings)

class invert:
    def __init__(self, to_invert) -> None:
        self.to_invert = to_invert

    def __call__(self, bindings: BINDING):
        b = self.to_invert(bindings)
        return Literal(not b)

    @classmethod
    def gen(cls, to_invert) -> "invert":
        return lambda *args: cls(to_invert(*args))

    def __repr__(self):
        return "invert(%s)" % self.to_invert

class equal:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __call__(bindings:BINDING) -> bool:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left == right)

class pred_less_than:
    def __init__(self, smaller, bigger):
        self.smaller = smaller
        self.bigger = bigger

    def __call__(self, bindings:BINDING) -> Literal:
        s = _resolve(self.smaller, bindings)
        b = _resolve(self.bigger, bindings)
        return Literal(s < b)

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
    def literal_not_identical(bindings: BINDING) -> Literal:
        f = bindings.get(first, first)
        s = bindings.get(second, second)
        return f != s
    return literal_not_identical

def ascondition_is_literal_hexBinary(target) -> Callable[[BINDING], bool]:
    def literal_not_identical(bindings: BINDING) -> Literal:
        t = bindings.get(target, target)
        return target.datatype == XSD.hexBinary
    return literal_not_identical

def ascondition_is_literal_not_hexBinary(target) -> Callable[[BINDING], bool]:
    def literal_not_identical(bindings: BINDING) -> Literal:
        t = bindings.get(target, target)
        return target.datatype != XSD.hexBinary
    return literal_not_identical

class condition_pred_is_literal_double:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        return t.datatype == XSD.double

    def __repr__(self):
        return "pred:is-literal-double(%s)[ascondition]" % self.target

class condition_pred_is_literal_not_double:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        return t.datatype != XSD.double

    def __repr__(self):
        return "pred:is-literal-double(%s)[ascondition]" % self.target

class condition_pred_is_literal_float:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        return t.datatype == XSD.float

    def __repr__(self):
        return "pred:is-literal-float(%s)[ascondition]" % self.target

class condition_pred_is_literal_not_float:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        return t.datatype != XSD.float

    def __repr__(self):
        return "pred:is-literal-float(%s)[ascondition]" % self.target

class condition_pred_is_literal_integer:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        return t.datatype == XSD.integer

    def __repr__(self):
        return "pred:is-literal-integer(%s)[ascondition]" % self.target

class condition_pred_is_literal_not_integer:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        return t.datatype != XSD.integer

    def __repr__(self):
        return "pred:is-literal-integer(%s)[ascondition]" % self.target

class condition_pred_is_literal_long:
    """
    :TODO: The limitsize should be system dependent
    """
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        if t.datatype != XSD.integer:
            return False
        return int(t).bit_length() <= 32

    def __repr__(self):
        return "pred:is-literal-long(%s)[ascondition]" % self.target

class condition_pred_is_literal_not_long:
    """
    :TODO: The limitsize should be system dependent
    """
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        if t.datatype != XSD.integer:
            return True
        return int(t).bit_length() > 32

    def __repr__(self):
        return "pred:is-literal-long(%s)[ascondition]" % self.target

class condition_pred_is_literal_unsignedLong:
    """
    :TODO: The limitsize should be system dependent
    """
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        if t.datatype != XSD.integer:
            return False
        if int(t).bit_length() > 32:
            return False
        return t >= 0

class condition_pred_is_literal_not_unsignedLong:
    """
    :TODO: The limitsize should be system dependent
    """
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        return not condition_pred_is_literal_not_unsignedLong.__call__(self, bindings)

class condition_pred_is_literal_unsignedInt:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        if t.datatype != XSD.integer:
            return False
        if int(t).bit_length() > 16:
            return False
        return t >= 0

    def __repr__(self):
        return "pred:is-literal-long(%s)[ascondition]" % self.target


class condition_pred_is_literal_unsignedShort:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        if t.datatype != XSD.integer:
            return False
        if int(t).bit_length() > 8:
            return False
        return t >= 0

    def __repr__(self):
        return "pred:is-literal-unsignedShort(%s)[ascondition]" % self.target

class condition_pred_is_literal_int:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        if t.datatype != XSD.integer:
            return False
        return int(t).bit_length() <= 16

    def __repr__(self):
        return "pred:is-literal-int(%s)[ascondition]" % self.target

class condition_pred_is_literal_not_int:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        if t.datatype == XSD.integer:
            return False
        elif int(t).bit_length() <= 16:
            return False
        return True

    def __repr__(self):
        return "pred:is-literal-int(%s)[ascondition]" % self.target

class condition_pred_is_literal_short:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        if t.datatype != XSD.integer:
            return False
        return int(t).bit_length() <= 8

    def __repr__(self):
        return "pred:is-literal-short(%s)[ascondition]" % self.target

class condition_pred_is_literal_not_short:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        return not condition_pred_is_literal_short.__call__(self, bindings)

    def __repr__(self):
        return "pred:is-literal-short(%s)[ascondition]" % self.target

class condition_pred_is_literal_negativeInteger:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        if t.datatype != XSD.integer:
            return False
        return t < 0

class condition_pred_is_literal_not_negativeInteger:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        return not condition_pred_is_literal_negativeInteger.__call__(self, bindings)

class condition_pred_is_literal_not_nonNegativeInteger:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        return not condition_pred_is_literal_nonNegativeInteger.__call__(self, bindings)

class condition_pred_is_literal_positiveInteger:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        if t.datatype != XSD.integer:
            return False
        return t >= 0

class condition_pred_is_literal_not_positiveInteger:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        return not condition_pred_is_literal_not_positiveInteger.__call__(self, bindings)

class condition_pred_is_literal_decimal:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        return t.isdecimal()

    def __repr__(self):
        return "pred:is-literal-float(%s)[ascondition]" % self.target

class condition_pred_is_literal_base64Binary:
    def __init__(self, target) -> None:
        self.target = target

    def __call__(self, bindings: BINDING) -> bool:
        t = _resolve(self.target, bindings)
        return t.datatype == XSD.base64Binary

    def __repr__(self):
        return "pred:is-literal-base64Binary(%s)[ascondition]" % self.target

def ascondition_is_literal_not_base64Binary(target) -> Callable[[BINDING], bool]:
    def literal_not_identical(bindings: BINDING) -> Literal:
        t = bindings.get(target, target)
        return target.datatype != XSD.base64Binary
    return literal_not_identical


def asassign_xs_base64Binary(target: Union[Literal, Variable],
                             ) -> Callable[[BINDING], Literal]:
    def numeric_subtract(bindings: BINDING) -> Literal:
        t = _resolve(target, bindings)
        return Literal(t, datatype=XSD.base64Binary)
    return numeric_subtract

def asassign_xs_double(target: Union[Literal, Variable],
                             ) -> Callable[[BINDING], Literal]:
    def numeric_subtract(bindings: BINDING) -> Literal:
        t = _resolve(target, bindings)
        return Literal(t, datatype=XSD.double)
    return numeric_subtract

class assign_rdflib:
    def __init__(self, target, type_uri):
        self.target = target
        self.type_uri = type_uri

    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t, datatype=self.type_uri)

    @classmethod
    def gen(cls, type_uri: URIRef):
        return lambda target: cls(target, type_uri)
