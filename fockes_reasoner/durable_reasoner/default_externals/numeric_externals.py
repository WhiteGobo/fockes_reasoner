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
from .shared import RegisterInformation, invert, RegisterHelper

class _check_numerical_equality:
    left: RESOLVABLE
    right: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        """
        :param args: Expects exactly two arguments, left and right.
        """
        self.left, self.right = args

    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value == right.value) #type: ignore[union-attr]

numeric_equal = RegisterInformation(pred["numeric-equal"])
numeric_equal.set_asassign(_check_numerical_equality)
numeric_not_equal = RegisterInformation(pred["numeric-not-equal"])
numeric_not_equal.set_asassign(invert.gen(_check_numerical_equality))

numeric_multiply = RegisterInformation(func["numeric-multiply"])
@numeric_multiply.set_asassign
class _numeric_multiply:
    left: RESOLVABLE
    right: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.left, self.right = args
    def __call__(self, bindings:BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value * right.value) #type: ignore[union-attr]

numeric_divide = RegisterInformation(func["numeric-divide"])
@numeric_divide.set_asassign
class _numeric_divide:
    left: RESOLVABLE
    right: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.left, self.right = args
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

numeric_integer_divide = RegisterInformation(func["numeric-integer-divide"])
@numeric_integer_divide.set_asassign
class _numeric_integer_divide:
    left: RESOLVABLE
    right: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.left, self.right = args
    def __call__(self, bindings:BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        try:
            val = left.value / right.value #type: ignore[union-attr]
        except ZeroDivisionError:
            return Literal(math.inf)
        return Literal(math.floor(val))

numeric_mod = RegisterInformation(func["numeric-mod"])
@numeric_mod.set_asassign
class _numeric_mod:
    """
    :TODO: Im not sure what n % 0 should be
    """
    left: RESOLVABLE
    right: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.left, self.right = args
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

numeric_integer_mod = RegisterInformation(func["numeric-integer-mod"])
@numeric_integer_mod.set_asassign
class _numeric_integer_mod:
    """
    :TODO: Im not sure what n % 0 should be
    """
    left: RESOLVABLE
    right: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.left, self.right = args
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

numeric_add = RegisterInformation(func["numeric-add"])
@numeric_add.set_asassign
class _numeric_add:
    left: RESOLVABLE
    right: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.left, self.right = args
    def __call__(self, bindings:BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value + right.value)#type: ignore[union-attr]

numeric_less_than = RegisterInformation(pred["numeric-less-than"])
@numeric_less_than.set_asassign
class pred_less_than:
    smaller: RESOLVABLE
    bigger: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.smaller, self.bigger = args
    def __call__(self, bindings:BINDING) -> Literal:
        s = _resolve(self.smaller, bindings)
        b = _resolve(self.bigger, bindings)
        return Literal(s < b)#type: ignore[operator]

numeric_greater_than_or_equal = RegisterInformation(
        pred["numeric-greater-than-or-equal"],
        asassign = invert.gen(numeric_less_than.asassign),
        )

numeric_greater_than = RegisterInformation(pred["numeric-greater-than"])
@numeric_greater_than.set_asassign
class pred_greater_than:
    bigger: RESOLVABLE
    smaller: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.bigger, self.smaller = args
    def __call__(self, bindings: BINDING) -> Literal:
        b = _resolve(self.bigger, bindings)
        s = _resolve(self.smaller, bindings)
        return Literal(b > s)# type: ignore[operator]

numeric_less_than_or_equal = RegisterInformation(
        pred["numeric-less-than-or-equal"],
        asassign=invert.gen(numeric_greater_than.asassign),
        )

numeric_subtract = RegisterInformation(func["numeric-subtract"])
@numeric_subtract.set_asassign
class func_numeric_subtract:
    first: RESOLVABLE
    second: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.first, self.second = args
    def __call__(self, bindings: BINDING) -> Literal:
        f = _resolve(self.first, bindings)
        s = _resolve(self.second, bindings)
        return Literal(f - s) #type: ignore[operator]

literal_not_identical = RegisterInformation(pred["literal-not-identical"])
@literal_not_identical.set_asassign
@dataclass
class ascondition_pred_literal_not_identical:
    first: RESOLVABLE
    second: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        f = _resolve(self.first, bindings)
        s = _resolve(self.second, bindings)
        return Literal(f != s)

is_literal_hexBinary = RegisterInformation(pred["is-literal-hexBinary"])
@is_literal_hexBinary.set_asassign
class _is_literal_hexBinary:
    target: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.target, = args
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype == XSD.hexBinary)#type: ignore[union-attr]

is_literal_not_hexBinary = RegisterInformation(
        pred["is-literal-not-hexBinary"],
        asassign = invert.gen(is_literal_hexBinary.asassign),
        )

is_literal_double = RegisterInformation(pred["is-literal-double"])
@is_literal_double.set_asassign
class _is_literal_double:
    target: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.target, = args

    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype == XSD.double)#type: ignore[union-attr]

is_literal_not_double = RegisterInformation(
        pred["is-literal-not-double"],
        asassign=invert.gen(is_literal_double.asassign),
        )


is_literal_float = RegisterInformation(pred["is-literal-float"])
@is_literal_float.set_asassign
class condition_pred_is_literal_float:
    target: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.target, = args

    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype == XSD.float)# type:ignore[union-attr]

is_literal_not_float = RegisterInformation(
        pred["is-literal-not-float"],
        asassign=invert.gen(is_literal_float.asassign),
        )

is_literal_integer = RegisterInformation(pred["is-literal-integer"])
@is_literal_integer.set_asassign
class condition_pred_is_literal_integer:
    target: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.target, = args

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

is_literal_not_integer = RegisterInformation(
        pred["is-literal-not-integer"],
        asassign = invert.gen(is_literal_integer.asassign),
        )

is_literal_long = RegisterInformation(pred["is-literal-long"])
@is_literal_long.set_asassign
class condition_pred_is_literal_long:
    """
    :TODO: The limitsize should be system dependent
    """
    target: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.target, = args
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype == XSD.long:#type: ignore[union-attr]
            return Literal(True)
        elif t.datatype == XSD.integer:#type: ignore[union-attr]
            if t.value.bit_length() <= 32:#type: ignore[union-attr]
                return Literal(True)
        return Literal(False)

is_literal_not_long = RegisterInformation(
        pred["is-literal-not-long"],
        asassign = invert.gen(is_literal_long.asassign),
        )

is_literal_unsignedLong = RegisterInformation(pred["is-literal-unsignedLong"])
@is_literal_unsignedLong.set_asassign
class condition_pred_is_literal_unsignedLong:
    """
    :TODO: The limitsize should be system dependent
    """
    target: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.target, = args

    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype not in {XSD.integer, XSD.long, XSD.unsignedLong}:#type: ignore[union-attr, operator]
            return Literal(False)
        if t.value.bit_length() > 32:#type: ignore[union-attr]
            return Literal(False)
        return Literal(t.value >= 0)#type: ignore[union-attr]

is_literal_not_unsignedLong = RegisterInformation(
        pred["is-literal-not-unsignedLong"],
        asassign = invert.gen(is_literal_unsignedLong.asassign),
        )

is_literal_unsignedInt = RegisterInformation(pred["is-literal-unsignedInt"])
@is_literal_unsignedInt.set_asassign
class condition_pred_is_literal_unsignedInt:
    target: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.target, = args
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype not in (XSD.integer, XSD.int, XSD.unsignedInt):#type: ignore[union-attr, operator]
            return Literal(False)
        if t.value.bit_length() > 16:#type: ignore[union-attr]
            return Literal(False)
        return Literal(t.value >= 0)#type: ignore[union-attr]

is_literal_not_unsignedInt = RegisterInformation(
        pred["is-literal-not-unsignedInt"],
        asassign = invert.gen(is_literal_unsignedInt.asassign),
        )


is_literal_unsignedShort = RegisterInformation(
        pred["is-literal-unsignedShort"])
@is_literal_unsignedShort.set_asassign
class condition_pred_is_literal_unsignedShort:
    target: RESOLVABLE
    def __init__(self, *args: RESOLVABLE) -> None:
        self.target, = args
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype == XSD.unsignedShort:#type: ignore[union-attr]
            return Literal(True)
        elif t.datatype == XSD.integer and t.value.bit_length() <= 8 and t.value >= 0:#type:ignore[union-attr]
            return Literal(True)
        return Literal(False)

is_literal_not_unsignedShort = RegisterInformation(
        pred["is-literal-not-unsignedShort"],
        asassign = invert.gen(is_literal_unsignedShort.asassign),
        )

is_literal_unsignedByte = RegisterInformation(pred["is-literal-unsignedByte"])
@is_literal_unsignedByte.set_asassign
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

is_literal_not_unsignedByte = RegisterInformation(
        pred["is-literal-not-unsignedByte"],
        asassign = invert.gen(is_literal_unsignedByte.asassign),
        )

is_literal_int = RegisterInformation(pred["is-literal-int"])
@is_literal_int.set_asassign
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

is_literal_not_int = RegisterInformation(
        pred["is-literal-not-int"],
        asassign=invert.gen(is_literal_int.asassign),
        )

is_literal_short = RegisterInformation(pred["is-literal-short"])
@is_literal_short.set_asassign
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

is_literal_not_short = RegisterInformation(
        pred["is-literal-not-short"],
        asassign = invert.gen(is_literal_short.asassign),
        )

is_literal_byte = RegisterInformation(pred["is-literal-byte"])
@is_literal_byte.set_asassign
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

is_literal_not_byte = RegisterInformation(
        pred["is-literal-not-byte"],
        asassign = invert.gen(is_literal_byte.asassign),
        )


is_literal_negativeInteger = RegisterInformation(
        pred["is-literal-negativeInteger"])
@is_literal_negativeInteger.set_asassign
@dataclass
class condition_pred_is_literal_negativeInteger:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype not in (XSD.integer, XSD.nonPositiveInteger, XSD.negativeInteger, XSD.long, XSD.short, XSD.byte, XSD.int):#type: ignore[union-attr, operator]
            return Literal(False)
        return Literal(t.value < 0)#type: ignore[union-attr]
is_literal_not_negativeInteger = RegisterInformation(
        pred["is-literal-not-negativeInteger"],
        asassign = invert.gen(is_literal_negativeInteger.asassign),
        )
is_literal_nonPositiveInteger = RegisterInformation(
        pred["is-literal-nonPositiveInteger"],
        asassign = is_literal_negativeInteger.asassign,
        )
is_literal_not_nonPositiveInteger = RegisterInformation(
        pred["is-literal-not-nonPositiveInteger"],
        asassign = invert.gen(is_literal_negativeInteger.asassign),
        )


is_literal_positiveInteger = RegisterInformation(pred["is-literal-positiveInteger"])
@is_literal_positiveInteger.set_asassign
@dataclass
class condition_pred_is_literal_positiveInteger:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        if t.datatype not in (XSD.integer, XSD.int, XSD.short, XSD.byte, XSD.long, XSD.nonNegativeInteger, XSD.positiveInteger):#type: ignore[union-attr, operator]
            return Literal(False)
        return Literal(t.value >= 0)#type:ignore[union-attr]
is_literal_not_positiveInteger = RegisterInformation(
        pred["is-literal-not-positiveInteger"],
        asassign = invert.gen(is_literal_positiveInteger.asassign),
        )
is_literal_nonNegativeInteger = RegisterInformation(
        pred["is-literal-nonNegativeInteger"],
        asassign = is_literal_positiveInteger.asassign,
        )
is_literal_not_nonNegativeInteger = RegisterInformation(
        pred["is-literal-not-nonNegativeInteger"],
        asassign = invert.gen(is_literal_positiveInteger.asassign),
        )

is_literal_decimal = RegisterInformation(pred["is-literal-decimal"])
@is_literal_decimal.set_asassign
@dataclass
class condition_pred_is_literal_decimal:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.isdecimal())#type: ignore[union-attr]
is_literal_not_decimal = RegisterInformation(
        pred["is-literal-not-decimal"],
        asassign = invert.gen(is_literal_decimal.asassign),
        )

is_literal_base64Binary = RegisterInformation(pred["is-literal-base64Binary"])
@is_literal_base64Binary.set_asassign
@dataclass
class condition_pred_is_literal_base64Binary:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.datatype == XSD.base64Binary)#type: ignore[union-attr]
is_literal_not_base64Binary = RegisterInformation(
        pred["is-literal-not-base64Binary"],
        asassign = invert.gen(is_literal_base64Binary.asassign),
        )


register_numeric_externals = RegisterHelper(
        [XSD.base64Binary, XSD.double, XSD.float, XSD.hexBinary, XSD.decimal,
         XSD.integer, XSD.positiveInteger, XSD.nonPositiveInteger, 
         XSD.negativeInteger, XSD.nonNegativeInteger, XSD.unsignedLong,
         XSD.long, XSD.int, XSD.unsignedInt, XSD.short, XSD.unsignedShort,
         XSD.byte, XSD.unsignedByte],
        [numeric_equal, numeric_not_equal, numeric_multiply, numeric_divide,
         numeric_integer_divide, numeric_subtract, numeric_mod,
         numeric_integer_mod, numeric_add, numeric_less_than,
         numeric_greater_than_or_equal, numeric_greater_than,
         numeric_less_than_or_equal, 
         is_literal_hexBinary, is_literal_double, is_literal_float,
         is_literal_integer, is_literal_long,
         is_literal_unsignedLong, is_literal_unsignedInt,
         is_literal_unsignedShort, is_literal_unsignedByte,
         is_literal_int, is_literal_short,
         is_literal_not_hexBinary, is_literal_not_double, is_literal_not_float,
         is_literal_not_integer, is_literal_not_long,
         is_literal_not_unsignedLong, is_literal_not_unsignedInt,
         is_literal_not_unsignedShort, is_literal_not_unsignedByte,
         is_literal_not_int, is_literal_not_short,
         is_literal_base64Binary, is_literal_not_base64Binary,
         is_literal_decimal, is_literal_not_decimal,
         is_literal_byte, is_literal_not_byte,
         is_literal_positiveInteger, is_literal_not_positiveInteger,
         is_literal_negativeInteger, is_literal_not_negativeInteger,
         is_literal_nonPositiveInteger, is_literal_not_nonPositiveInteger,
         is_literal_nonNegativeInteger, is_literal_not_nonNegativeInteger,
         literal_not_identical,
        ])
