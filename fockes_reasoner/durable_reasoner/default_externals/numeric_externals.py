from typing import Callable, Union, TypeVar, Iterable, Container, Tuple
import rdflib
import itertools as it
from rdflib import Literal, Variable, XSD, IdentifiedNode, Literal, URIRef
import logging
logger = logging.getLogger()
from dataclasses import dataclass
import math
from ..bridge_rdflib import term_list, _term_list, TRANSLATEABLE_TYPES

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS
from ...shared import pred, func

@dataclass
class numeric_equal:
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings:BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value == right.value) #type: ignore[union-attr]

@dataclass
class literal_equal:
    left: RESOLVABLE
    right: RESOLVABLE

    def __call__(self, bindings:BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        logger.critical((left, right))
        return Literal(left == right)

@dataclass
class numeric_multiply:
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings:BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value * right.value) #type: ignore[union-attr]

@dataclass
class numeric_divide:
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings:BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        try:
            val = left.value / right.value #type: ignore[union-attr]
        except ZeroDivisionError:
            return Literal(math.inf)
        if val.is_integer():
            return Literal(int(val))
        else:
            return Literal(val)

@dataclass
class numeric_integer_divide:
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings:BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        try:
            val = left.value / right.value #type: ignore[union-attr]
        except ZeroDivisionError:
            return Literal(math.inf)
        return Literal(math.floor(val))

@dataclass
class numeric_mod:
    """
    :TODO: Im not sure what n % 0 should be
    """
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings:BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        raise Exception()
        try:
            val = math.remainder(left.value, right.value)
        except ValueError:
            return Literal(math.inf)
        if val < 0:
            val += right.value
        if val.is_integer():
            return Literal(int(val))
        else:
            return Literal(val)

@dataclass
class numeric_integer_mod:
    """
    :TODO: Im not sure what n % 0 should be
    """
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings:BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        try:
            val = math.remainder(left.value, right.value) #type: ignore[union-attr]
        except ValueError:
            return Literal(math.inf)
        if val < 0:
            val += right.value#type: ignore[union-attr]
        return Literal(math.floor(val))

@dataclass
class numeric_add:
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings:BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value + right.value)#type: ignore[union-attr]

@dataclass
class pred_less_than:
    smaller: RESOLVABLE
    bigger: RESOLVABLE
    def __call__(self, bindings:BINDING) -> Literal:
        s = _resolve(self.smaller, bindings)
        b = _resolve(self.bigger, bindings)
        return Literal(s < b)#type: ignore[operator]

@dataclass
class pred_greater_than:
    bigger: RESOLVABLE
    smaller: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        b = _resolve(self.bigger, bindings)
        s = _resolve(self.smaller, bindings)
        return Literal(b > s)# type: ignore[operator]

@dataclass
class func_numeric_subtract:
    first: RESOLVABLE
    second: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        f = _resolve(self.first, bindings)
        s = _resolve(self.second, bindings)
        return Literal(f - s) #type: ignore[operator]

@dataclass
class ascondition_pred_literal_not_identical:
    first: RESOLVABLE
    second: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        f = _resolve(self.first, bindings)
        s = _resolve(self.second, bindings)
        return Literal(f != s)

@dataclass
class is_literal_hexBinary:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype == XSD.hexBinary)#type: ignore[union-attr]


@dataclass
class condition_pred_is_literal_double:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype == XSD.double)#type: ignore[union-attr]

@dataclass
class condition_pred_is_literal_not_double:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype != XSD.double)# type: ignore[union-attr]

@dataclass
class condition_pred_is_literal_float:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype == XSD.float)# type:ignore[union-attr]

@dataclass
class condition_pred_is_literal_not_float:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype != XSD.float)#type: ignore[union-attr]

@dataclass
class condition_pred_is_literal_integer:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        if t.datatype == XSD.integer:
            return Literal(True)
        try:
            if isinstance(t.value, int):
                return Literal(True)
            try:
                return Literal(t.value.is_integer())
            except AttributeError:
                pass #not a float
            try:
                return Literal(t.value.as_integer_ratio()[1] == 1)
            except AttributeError:
                pass #not a decimal.Decimal
        except AttributeError:
            pass
        return Literal(False)

@dataclass
class condition_pred_is_literal_long:
    """
    :TODO: The limitsize should be system dependent
    """
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype == XSD.long:#type: ignore[union-attr]
            return Literal(True)
        elif t.datatype == XSD.integer:#type: ignore[union-attr]
            if t.value.bit_length() <= 32:#type: ignore[union-attr]
                return Literal(True)
        return Literal(False)

@dataclass
class condition_pred_is_literal_unsignedLong:
    """
    :TODO: The limitsize should be system dependent
    """
    target: RESOLVABLE

    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype not in {XSD.integer, XSD.long, XSD.unsignedLong}:#type: ignore[union-attr, operator]
            return Literal(False)
        if t.value.bit_length() > 32:#type: ignore[union-attr]
            return Literal(False)
        return Literal(t.value >= 0)#type: ignore[union-attr]

@dataclass
class condition_pred_is_literal_unsignedInt:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype not in (XSD.integer, XSD.int, XSD.unsignedInt):#type: ignore[union-attr, operator]
            return Literal(False)
        if t.value.bit_length() > 16:#type: ignore[union-attr]
            return Literal(False)
        return Literal(t.value >= 0)#type: ignore[union-attr]


@dataclass
class condition_pred_is_literal_unsignedShort:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype == XSD.unsignedShort:#type: ignore[union-attr]
            return Literal(True)
        elif t.datatype == XSD.integer and t.value.bit_length() <= 8 and t.value >= 0:#type:ignore[union-attr]
            return Literal(True)
        return Literal(False)

@dataclass
class condition_pred_is_literal_unsignedByte:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype == XSD.unsignedByte:#type: ignore[union-attr]
            return Literal(True)
        elif t.datatype == XSD.integer and t.value.bit_length() <= 8 and t.value >= 0:#type: ignore[union-attr]
            return Literal(True)
        return Literal(False)

@dataclass
class condition_pred_is_literal_int:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype == XSD.int:#type: ignore[union-attr]
            return Literal(True)
        elif t.datatype == XSD.integer:#type: ignore[union-attr]
            if t.value.bit_length() <= 16:#type: ignore[union-attr]
                return Literal(True)
        return Literal(False)

@dataclass
class condition_pred_is_literal_short:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype == XSD.short:#type: ignore[union-attr]
            return Literal(True)
        elif t.datatype == XSD.integer:#type: ignore[union-attr]
            return Literal(t.value.bit_length() <= 8)#type: ignore[union-attr]
        return Literal(False)

@dataclass
class condition_pred_is_literal_byte:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype == XSD.byte:#type: ignore[union-attr]
            return Literal(True)
        elif t.datatype == XSD.integer:#type: ignore[union-attr]
            return Literal(t.value.bit_length() <= 8)#type: ignore[union-attr]
        return Literal(False)


@dataclass
class condition_pred_is_literal_negativeInteger:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype not in (XSD.integer, XSD.nonPositiveInteger, XSD.negativeInteger, XSD.long, XSD.short, XSD.byte, XSD.int):#type: ignore[union-attr, operator]
            return Literal(False)
        return Literal(t.value < 0)#type: ignore[union-attr]


@dataclass
class condition_pred_is_literal_positiveInteger:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype not in (XSD.integer, XSD.int, XSD.short, XSD.byte, XSD.long, XSD.nonNegativeInteger, XSD.positiveInteger):#type: ignore[union-attr, operator]
            return Literal(False)
        return Literal(t.value >= 0)#type:ignore[union-attr]

@dataclass
class condition_pred_is_literal_decimal:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.isdecimal())#type: ignore[union-attr]

@dataclass
class condition_pred_is_literal_base64Binary:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype == XSD.base64Binary)#type: ignore[union-attr]

@dataclass
class ascondition_is_literal_not_base64Binary:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype != XSD.base64Binary)#type: ignore[union-attr]


@dataclass
class asassign_xs_base64Binary:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t, datatype=XSD.base64Binary)
