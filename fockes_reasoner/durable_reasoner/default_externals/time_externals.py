from typing import Callable, Union, TypeVar, Iterable, Container, Tuple
import rdflib
import itertools as it
from rdflib import Literal, Variable, XSD, IdentifiedNode, Literal, URIRef
import logging
logger = logging.getLogger()
from dataclasses import dataclass
import math
from decimal import Decimal
from ..bridge_rdflib import term_list, _term_list, TRANSLATEABLE_TYPES
import datetime
import isodate

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS
from .. import abc_machine
from ...shared import pred, func
from .shared import is_datatype, invert, assign_rdflib
from .numeric_externals import pred_less_than, pred_greater_than

_externals: Iterable
_datatypes: Iterable[URIRef] = [
        XSD.date,
        XSD.dateTime,
        XSD.time,
        XSD.dateTimeStamp,
        XSD.dayTimeDuration,
        XSD.yearMonthDuration,
        ]

def _register_timeExternals(machine: abc_machine.extensible_Machine) -> None:
    for dt in _datatypes:
        machine.register(dt, asassign=assign_rdflib.gen(dt))
    for x in _externals:
        as_ = {}
        for t in ["asassign", "aspattern", "asbinding"]:
            if hasattr(x, t):
                foo = getattr(x, t)
                if foo is not None:
                    as_[t] = foo
                else:
                    as_[t] = x
        machine.register(x.op, **as_)

@dataclass
class is_literal_date:
    #asassign = lambda dt: is_datatype(XSD.date, dt)
    asassign = None
    target: RESOLVABLE
    op: URIRef = pred["is-literal-date"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        assert isinstance(t, Literal)
        return Literal(t.datatype == XSD.date)


@dataclass
class is_literal_not_date:
    asassign = invert.gen(lambda dt: is_datatype(XSD.date, dt))
    op: URIRef = pred["is-literal-not-date"]

@dataclass
class is_literal_dateTime:
    asassign = lambda dt: is_datatype(XSD.dateTime, dt)
    op: URIRef = pred["is-literal-dateTime"]

@dataclass
class is_literal_not_dateTime:
    asassign = invert.gen(lambda dt: is_datatype(XSD.dateTime, dt))
    op: URIRef = pred["is-literal-not-dateTime"]

@dataclass
class is_literal_dateTimeStamp:
    asassign = lambda dt: is_datatype(XSD.dateTimeStamp, dt)
    op: URIRef = pred["is-literal-dateTimeStamp"]

@dataclass
class is_literal_not_dateTimeStamp:
    asassign = invert.gen(lambda dt: is_datatype(XSD.dateTimeStamp, dt))
    op: URIRef = pred["is-literal-not-dateTimeStamp"]

@dataclass
class is_literal_time:
    asassign = lambda dt: is_datatype(XSD.time, dt)
    op: URIRef = pred["is-literal-time"]

@dataclass
class is_literal_not_time:
    asassign = invert.gen(lambda dt: is_datatype(XSD.time, dt))
    op: URIRef = pred["is-literal-not-time"]

@dataclass
class is_literal_dayTimeDuration:
    asassign = lambda dt: is_datatype(XSD.dayTimeDuration, dt)
    op: URIRef = pred["is-literal-dayTimeDuration"]

@dataclass
class is_literal_not_dayTimeDuration:
    asassign = invert.gen(lambda dt: is_datatype(XSD.dayTimeDuration, dt))
    op: URIRef = pred["is-literal-not-dayTimeDuration"]

@dataclass
class is_literal_yearMonthDuration:
    asassign = lambda dt: is_datatype(XSD.yearMonthDuration, dt)
    op: URIRef = pred["is-literal-yearMonthDuration"]

@dataclass
class is_literal_not_yearMonthDuration:
    asassign = invert.gen(lambda dt: is_datatype(XSD.yearMonthDuration, dt))
    op: URIRef = pred["is-literal-not-yearMonthDuration"]

@dataclass
class year_from_dateTime:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["year-from-dateTime"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        #assert isinstance(t, Literal)
        return Literal(t.value.year) #type: ignore[union-attr]


@dataclass
class month_from_dateTime:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["month-from-dateTime"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.month) #type: ignore[union-attr]

@dataclass
class day_from_dateTime:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["day-from-dateTime"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.day) #type: ignore[union-attr]

@dataclass
class hours_from_dateTime:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["hours-from-dateTime"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.hour) #type: ignore[union-attr]

@dataclass
class minutes_from_dateTime:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["minutes-from-dateTime"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.minute) #type: ignore[union-attr]

@dataclass
class seconds_from_dateTime:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["seconds-from-dateTime"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.second) #type: ignore[union-attr]

@dataclass
class year_from_date:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["year-from-date"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.year) #type: ignore[union-attr]

@dataclass
class month_from_date:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["month-from-date"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.month) #type: ignore[union-attr]

@dataclass
class day_from_date:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["day-from-date"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.day) #type: ignore[union-attr]

@dataclass
class hours_from_time:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["hours-from-time"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.hour) #type: ignore[union-attr]

@dataclass
class minutes_from_time:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["minutes-from-time"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.minute) #type: ignore[union-attr]

@dataclass
class seconds_from_time:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["seconds-from-time"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.second) #type: ignore[union-attr]

@dataclass
class timezone_from_dateTime:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["timezone-from-dateTime"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        v: datetime.datetime = t.value #type: ignore[union-attr]
        timezone: isodate.tzinfo.tzinfo = v.tzinfo
        q: datetime.timedelta = timezone.utcoffset(None)
        return Literal(q)

class timezone_from_time:
    op: URIRef = func["timezone-from-time"]
    asassign = timezone_from_dateTime

@dataclass
class years_from_duration:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["years-from-duration"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        y, m = t.value.years, t.value.months #type: ignore[union-attr]
        return Literal(int(y + int(m/12)))

@dataclass
class months_from_duration:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["months-from-duration"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        dur: Union[isodate.duration.Duration, datetime.timedelta]\
                = t.value #type: ignore[union-attr]
        if isinstance(dur, datetime.timedelta):
            raise NotImplementedError()
        else:
            return Literal(int(dur.months%12))

@dataclass
class days_from_duration:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["days-from-duration"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        dur: Union[isodate.duration.Duration, datetime.timedelta]\
                = t.value #type: ignore[union-attr]
        if isinstance(dur, datetime.timedelta):
            return Literal(dur.days)
        elif isinstance(dur, isodate.duration.Duration):
            q = Literal(dur.days)
            if isinstance(q, Decimal):
                return Literal(q if q.integer_ratio()[1] == 1 else int(q))
            else:
                return Literal(q)
        raise NotImplementedError(repr(dur), repr(t))

@dataclass
class hours_from_duration:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["hours-from-duration"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(int(t.value.seconds/3600)) #type: ignore[union-attr]

@dataclass
class minutes_from_duration:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["minutes-from-duration"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(int(t.value.seconds/60)%60 ) #type: ignore[union-attr]
@dataclass
class seconds_from_duration:
    asassign = None
    target: RESOLVABLE
    op: URIRef = func["seconds-from-duration"]
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        sec, msec = t.value.seconds, t.value.microseconds#type: ignore[union-attr]
        ms_in_seconds = Decimal(msec) / 1000000
        q = Decimal(sec) % 60 + ms_in_seconds
        if q.as_integer_ratio()[1] == 1:
            return Literal(int(q))
        else:
            return Literal(q)


@dataclass
class subtract_dateTimes:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["subtract-dateTimes"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        first: datetime.datetime = left.value
        second: datetime.datetime = right.value
        return Literal(first - second)

@dataclass
class subtract_dates:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["subtract-dates"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        return Literal(left.value - right.value)

@dataclass
class subtract_times:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["subtract-times"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        date_l = datetime.datetime.combine(datetime.date(2,1,1), left.value)
        date_r = datetime.datetime.combine(datetime.date(2,1,1), right.value)
        dt = date_l - date_r
        return Literal(dt)

@dataclass
class add_yearMonthDurations:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["add-yearMonthDurations"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        q: isodate.duration.Duration = left.value + right.value
        q.years = q.years + int(q.months/12)
        q.months = q.months%12
        return Literal(q, datatype=XSD.yearMonthDuration)

@dataclass
class subtract_yearMonthDurations:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["subtract-yearMonthDurations"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        q: isodate.duration.Duration = left.value - right.value
        q.years = q.years + int(q.months/12)
        q.months = q.months%12
        if q.years < 0:
            q.months = q.months - 12
            q.years = q.years + 1
        return Literal(q, datatype=XSD.yearMonthDuration)


@dataclass
class divide_yearMonthDuration:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["divide-yearMonthDuration"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        months = (left.value.months + (left.value.years * 12)) / right.value# type: ignore[union-attr]
        if months > 0:
            q = isodate.duration.Duration(
                    years=int(months/12),
                    months=int((months % 12) + Decimal(0.5)))
        else:
            q = isodate.duration.Duration(
                    years=int(months/12),
                    months=int((months % -12) - Decimal(0.5)))
        return Literal(q, datatype=XSD.yearMonthDuration)

@dataclass
class multiply_yearMonthDuration:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["multiply-yearMonthDuration"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        if left.datatype == XSD.yearMonthDuration:
            months = (left.value.months + (left.value.years * 12))\
                    * right.value
        else:
            months = (right.value.months + (right.value.years * 12))\
                    * left.value
        if months > 0:
            q = isodate.duration.Duration(
                    years=int(months/12),
                    months=int((months % 12) + Decimal(0.5)))
        else:
            q = isodate.duration.Duration(
                    years=int(months/12),
                    months=int((months % -12) - Decimal(0.5)))
        return Literal(q, datatype=XSD.yearMonthDuration)

@dataclass
class divide_yearMonthDuration_by_yearMonthDuration:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["divide-yearMonthDuration-by-yearMonthDuration"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        left_months = left.value.months + (left.value.years * 12)
        right_months = right.value.months + (right.value.years * 12)
        return Literal(left_months / right_months)

@dataclass
class add_dayTimeDurations:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["add-dayTimeDurations"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        return Literal(left.value + right.value)

@dataclass
class subtract_dayTimeDurations:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["subtract-dayTimeDurations"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        return Literal(left.value - right.value)

@dataclass
class subtract_dayTimeDuration_from_dateTime:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["subtract-dayTimeDuration-from-dateTime"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        date, delta = left.value, right.value
        return Literal(date-delta)

@dataclass
class subtract_dayTimeDuration_from_date:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["subtract-dayTimeDuration-from-date"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        date, delta = left.value, right.value
        return Literal(date-delta)

@dataclass
class subtract_dayTimeDuration_from_time:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["subtract-dayTimeDuration-from-time"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        date, delta = left.value, right.value
        d = datetime.datetime(2,1,1,date.hour, date.minute, date.second, date.microsecond)
        d2 = d - delta
        return Literal(datetime.time(d2.hour, d2.minute, d2.second, d2.microsecond, date.tzinfo))

@dataclass
class multiply_dayTimeDuration:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["multiply-dayTimeDuration"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        if isinstance(left.value, datetime.timedelta):
            seconds = (left.value.seconds + (86400*left.value.days) )\
                    * right.value
        elif isinstance(right.value, datetime.timedelta):
            seconds = (right.value.seconds + (86400*right.value.days) )\
                    * left.value
        else:
            raise NotImplementedError(left, right)
        days = int(seconds/86400)
        seconds = int(seconds%86400)
        microseconds = int((seconds%1)*1000000)
        return Literal(datetime.timedelta(days, seconds, microseconds))

@dataclass
class divide_dayTimeDuration:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["divide-dayTimeDuration"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        if isinstance(left.value, datetime.timedelta):
            seconds = (left.value.seconds + (86400*left.value.days) )\
                    / right.value
        elif isinstance(right.value, datetime.timedelta):
            seconds = (right.value.seconds + (86400*right.value.days) )\
                    / left.value
        else:
            raise NotImplementedError(left, right)
        days = int(seconds/86400)
        seconds = int(seconds%86400)
        microseconds = int((seconds%1)*1000000)
        return Literal(datetime.timedelta(days, seconds, microseconds))

@dataclass
class divide_dayTimeDuration_by_dayTimeDuration:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["divide-dayTimeDuration-by-dayTimeDuration"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        leftseconds = left.value.seconds + (86400*left.value.days)
        rightseconds = right.value.seconds + (86400*right.value.days)
        q = leftseconds / rightseconds
        if q.as_integer_ratio()[1] == 1:
            return Literal(int(q))
        else:
            return Literal(q)

@dataclass
class add_yearMonthDuration_to_dateTime:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["add-yearMonthDuration-to-dateTime"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        return Literal(left.value + right.value)

@dataclass
class add_yearMonthDuration_to_date:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["add-yearMonthDuration-to-date"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        return Literal(left.value + right.value)

@dataclass
class add_dayTimeDuration_to_dateTime:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["add-dayTimeDuration-to-dateTime"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        return Literal(left.value + right.value, datatype=XSD.dayTime)

@dataclass
class add_dayTimeDuration_to_date:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["add-dayTimeDuration-to-date"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        return Literal(left.value + right.value)

@dataclass
class add_dayTimeDuration_to_time:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["add-dayTimeDuration-to-time"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        date, delta = left.value, right.value
        microseconds = date.microsecond + delta.microseconds
        seconds = date.second + delta.seconds + int(microseconds/1000000)
        minute = date.minute + int(seconds/60)
        hour = (date.hour + int(minute/60))%24
        newdate = datetime.time(int(hour%24), int(minute%60),
                                int(seconds%60), int(microseconds%1000000),
                                tzinfo = date.tzinfo)
        return Literal(newdate)

@dataclass
class subtract_yearMonthDuration_from_dateTime:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["subtract-yearMonthDuration-from-dateTime"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        date, delta = left.value, right.value
        return Literal(date-delta)

@dataclass
class subtract_yearMonthDuration_from_date:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = func["subtract-yearMonthDuration-from-date"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        date, delta = left.value, right.value
        return Literal(date-delta)


@dataclass
class dateTime_equal:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = pred["dateTime-equal"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        dt = left.value - right.value
        return Literal(dt.total_seconds() == 0.0)

class dateTime_less_than:
    op: URIRef = pred["dateTime-less-than"]
    asassign = pred_less_than

class dateTime_greater_than:
    op: URIRef = pred["dateTime-greater-than"]
    asassign = pred_greater_than

class date_equal:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = pred["date-equal"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        dt = left.value - right.value
        return Literal(dt.total_seconds() == 0.0)

class date_less_than:
    op: URIRef = pred["date-less-than"]
    asassign = pred_less_than

class date_greater_than:
    op: URIRef = pred["date-greater-than"]
    asassign = pred_greater_than

@dataclass
class time_equal:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = pred["time-equal"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        date_l = datetime.datetime.combine(datetime.date(2,1,1), left.value)
        date_r = datetime.datetime.combine(datetime.date(2,1,1), right.value)
        dt = date_l - date_r
        return Literal(dt.total_seconds() == 0.0)

class time_less_than:
    op: URIRef = pred["time-less-than"]
    asassign = pred_less_than

class time_greater_than:
    op: URIRef = pred["time-greater-than"]
    asassign = pred_greater_than

@dataclass
class duration_equal:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = pred["duration-equal"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        q = datetime.datetime(5000,1,1) + left.value - right.value
        return Literal(q == datetime.datetime(5000,1,1))

@dataclass
class yearMonthDuration_less_than:
    #asassign = pred_less_than
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = pred["yearMonthDuration-less-than"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        extime = datetime.datetime(5000,1,1)
        d1 = left.value.totimedelta(extime)
        d2 = right.value.totimedelta(extime)
        return Literal(d1 < d2)

@dataclass
class yearMonthDuration_greater_than:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = pred["yearMonthDuration-greater-than"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        extime = datetime.datetime(5000,1,1)
        d1 = left.value.totimedelta(extime)
        d2 = right.value.totimedelta(extime)
        return Literal(d1 > d2)

@dataclass
class dayTimeDuration_less_than:
    #asassign = pred_less_than
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = pred["dayTimeDuration-less-than"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        return Literal(left.value < right.value)

@dataclass
class dayTimeDuration_greater_than:
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    op: URIRef = pred["dayTimeDuration-greater-than"]
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        assert isinstance(left, Literal)
        assert isinstance(right, Literal)
        return Literal(left.value > right.value)

class dateTime_not_equal:
    op: URIRef = pred["dateTime-not-equal"]
    asassign = invert.gen(dateTime_equal)

class dateTime_less_than_or_equal:
    op: URIRef = pred["dateTime-less-than-or-equal"]
    asassign = invert.gen(pred_greater_than)

class dateTime_greater_than_or_equal:
    op: URIRef = pred["dateTime-greater-than-or-equal"]
    asassign = invert.gen(pred_less_than)

class date_not_equal:
    op: URIRef = pred["date-not-equal"]
    asassign = invert.gen(dateTime_equal)

class date_less_than_or_equal:
    op: URIRef = pred["date-less-than-or-equal"]
    asassign = invert.gen(pred_greater_than)

class date_greater_than_or_equal:
    op: URIRef = pred["date-greater-than-or-equal"]
    asassign = invert.gen(pred_less_than)

class time_not_equal:
    op: URIRef = pred["time-not-equal"]
    asassign = invert.gen(time_equal)

class time_less_then_or_equal:
    op: URIRef = pred["time-less-than-or-equal"]
    asassign = invert.gen(pred_greater_than)

class time_greater_then_or_equal:
    op: URIRef = pred["time-greater-than-or-equal"]
    asassign = invert.gen(pred_less_than)

class duration_not_equal:
    op: URIRef = pred["duration-not-equal"]
    asassign = invert.gen(duration_equal)

class yearMonthDuration_less_than_or_equal:
    op: URIRef = pred["yearMonthDuration-less-than-or-equal"]
    asassign = invert.gen(yearMonthDuration_greater_than)

class yearMonthDuration_greater_than_or_equal:
    op: URIRef = pred["yearMonthDuration-greater-than-or-equal"]
    asassign = invert.gen(yearMonthDuration_less_than)

class dayTimeDuration_less_than_or_equal:
    op: URIRef = pred["dayTimeDuration-less-than-or-equal"]
    asassign = invert.gen(dayTimeDuration_greater_than)

class dayTimeDuration_greater_than_or_equal:
    op: URIRef = pred["dayTimeDuration-greater-than-or-equal"]
    asassign = invert.gen(dayTimeDuration_less_than)

_externals = [
        is_literal_date,
        is_literal_dateTime,
        is_literal_dateTimeStamp,
        is_literal_time,
        is_literal_dayTimeDuration,
        is_literal_yearMonthDuration,
        is_literal_not_date,
        is_literal_not_dateTime,
        is_literal_not_dateTimeStamp,
        is_literal_not_time,
        is_literal_not_dayTimeDuration,
        is_literal_not_yearMonthDuration,
        year_from_dateTime,
        month_from_dateTime,
        day_from_dateTime,
        hours_from_dateTime,
        minutes_from_dateTime,
        seconds_from_dateTime,
        year_from_date,
        month_from_date,
        day_from_date,
        hours_from_time,
        minutes_from_time,
        seconds_from_time,
        timezone_from_dateTime,
        timezone_from_time,
        years_from_duration,
        months_from_duration,
        days_from_duration,
        hours_from_duration,
        minutes_from_duration,
        seconds_from_duration,
        subtract_dateTimes,
        subtract_dates,
        subtract_times,
        add_yearMonthDurations,
        subtract_yearMonthDurations,
        divide_yearMonthDuration,
        multiply_yearMonthDuration,
        divide_yearMonthDuration_by_yearMonthDuration,
        add_dayTimeDurations,
        subtract_dayTimeDurations,
        subtract_dayTimeDuration_from_dateTime,
        subtract_dayTimeDuration_from_date,
        subtract_dayTimeDuration_from_time,
        multiply_dayTimeDuration,
        divide_dayTimeDuration,
        divide_dayTimeDuration_by_dayTimeDuration,
        add_yearMonthDuration_to_dateTime,
        add_yearMonthDuration_to_date,
        add_dayTimeDuration_to_dateTime,
        add_dayTimeDuration_to_date,
        add_dayTimeDuration_to_time,
        subtract_yearMonthDuration_from_dateTime,
        subtract_yearMonthDuration_from_date,
        dateTime_equal,
        dateTime_less_than,
        dateTime_greater_than,
        date_equal,
        date_less_than,
        date_greater_than,
        time_equal,
        time_less_than,
        time_greater_than,
        duration_equal,
        yearMonthDuration_less_than,
        yearMonthDuration_greater_than,
        dayTimeDuration_less_than,
        dayTimeDuration_greater_than,
        dateTime_not_equal,
        dateTime_less_than_or_equal,
        dateTime_greater_than_or_equal,
        date_not_equal,
        date_less_than_or_equal,
        date_greater_than_or_equal,
        time_not_equal,
        time_less_then_or_equal,
        time_greater_then_or_equal,
        duration_not_equal,
        yearMonthDuration_less_than_or_equal,
        yearMonthDuration_greater_than_or_equal,
        dayTimeDuration_less_than_or_equal,
        dayTimeDuration_greater_than_or_equal,
        ]
