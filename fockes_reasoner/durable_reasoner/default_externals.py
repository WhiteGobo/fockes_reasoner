from typing import Callable, Union, TypeVar, Iterable
import rdflib
import itertools as it
from rdflib import Literal, Variable, XSD, IdentifiedNode, Literal, URIRef
import logging
logger = logging.getLogger()
from dataclasses import dataclass
import math
from .bridge_rdflib import term_list, _term_list, TRANSLATEABLE_TYPES

from .abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER
from ..shared import pred, func


@dataclass
class invert:
    to_invert: RESOLVER
    def __call__(self, bindings: BINDING) -> Literal:
        b = self.to_invert(bindings)
        return Literal(not b)

    @classmethod
    def gen(cls, to_invert: Callable[..., RESOLVER]) -> Callable[..., "invert"]:
        return lambda *args: cls(to_invert(*args))

@dataclass
class is_list:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        target = _resolve(self.target, bindings)
        return Literal(isinstance(target, term_list))

@dataclass
class list_contains:
    container: RESOLVABLE
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        container = _resolve(self.container, bindings)
        if not isinstance(container, term_list):
            raise TypeError("Expected a list: %s" % container)
        target = _resolve(self.target, bindings)
        return Literal(target in container)

class make_list:
    items: Iterable[RESOLVABLE]
    def __init__(self, *items: RESOLVABLE) -> None:
        self.items = items

    def __call__(self, bindings: BINDING) -> _term_list:
        items = [_resolve(item, bindings) for item in self.items]
        return _term_list(items)

@dataclass
class count:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        target = _resolve(self.target, bindings)
        return Literal(len(target))

@dataclass
class list_get:
    target: RESOLVABLE
    index: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        index = int(_resolve(self.index, bindings))#type: ignore[arg-type]
        return target[index]

@dataclass
class sublist:
    target: RESOLVABLE
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        left = int(_resolve(self.left, bindings))#type: ignore[arg-type]
        right = int(_resolve(self.right, bindings))#type: ignore[arg-type]
        return target[left: right]

class append:
    target: RESOLVABLE
    items: Iterable[RESOLVABLE]
    def __init__(self, target: RESOLVABLE, *items: RESOLVABLE,
                 ) -> None:
        self.target = target
        self.items = items

    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        items = (_resolve(item, bindings) for item in self.items)
        return _term_list(list(it.chain(target, items)))


@dataclass
class union:
    """
    :TODO: This is currently the same as concatenate
    """
    first: RESOLVABLE
    second: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        first = _resolve(self.first, bindings)
        assert isinstance(first, term_list)
        second = _resolve(self.second, bindings)
        assert isinstance(second, term_list)
        return _term_list(list(it.chain(first, second)))

@dataclass
class distinct_values:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        return _term_list(list(set(target)))

@dataclass
class intersect:
    first: RESOLVABLE
    second: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        first = _resolve(self.first, bindings)
        assert isinstance(first, term_list)
        second = _resolve(self.second, bindings)
        assert isinstance(second, term_list)
        return _term_list([x for x in first if x in second])

@dataclass
class list_except:
    target: RESOLVABLE
    switch: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        switch = _resolve(self.switch, bindings)
        assert isinstance(switch, term_list)
        return _term_list([x for x in target if x not in switch])


@dataclass
class concatenate:
    first: RESOLVABLE
    second: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        first = _resolve(self.first, bindings)
        assert isinstance(first, term_list)
        second = _resolve(self.second, bindings)
        assert isinstance(second, term_list)
        return _term_list(list(it.chain(first, second)))

@dataclass
class insert_before:
    target: RESOLVABLE
    index: RESOLVABLE
    item: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        index = int(_resolve(self.index, bindings))#type: ignore[arg-type]
        item = _resolve(self.item, bindings)
        newlist = list(target)
        newlist.insert(index, item)
        return _term_list(newlist)

@dataclass
class remove:
    target: RESOLVABLE
    index: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        index = int(_resolve(self.index, bindings))#type: ignore[arg-type]
        newlist = list(target)
        newlist.pop(index)
        return _term_list(newlist)


@dataclass
class reverse_list:
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        newlist = list(target)
        newlist.reverse()
        return _term_list(newlist)


@dataclass
class index_of:
    target: RESOLVABLE
    item: RESOLVABLE
    def __call__(self, bindings: BINDING) -> TRANSLATEABLE_TYPES:
        target = _resolve(self.target, bindings)
        assert isinstance(target, term_list)
        item = _resolve(self.item, bindings)
        indices = (Literal(i) for i, x in enumerate(target) if x == item)
        return _term_list(list(indices))


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
class ascondition_pred_greater_than:
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
        logger.critical(type(t.value))
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

@dataclass
class assign_rdflib:
    target: RESOLVABLE
    type_uri: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        type_uri = _resolve(self.type_uri, bindings)
        assert isinstance(type_uri, URIRef)
        return Literal(t, datatype=type_uri)

    def __repr__(self) -> str:
        return "%s: %s" % (self.type_uri, self.target)

    @classmethod
    def gen(cls, type_uri: URIRef) -> Callable[..., "assign_rdflib"]:
        return lambda target: cls(target, type_uri)
