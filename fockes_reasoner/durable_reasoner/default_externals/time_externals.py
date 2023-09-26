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

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS, _assignment
from ...shared import pred, func
from .shared import is_datatype, invert, assign_rdflib
from .numeric_externals import literal_equal, pred_less_than, pred_greater_than

_externals: Iterable
_datatypes: Iterable[URIRef] = [
        XSD.date,
        XSD.dateTime,
        XSD.time,
        XSD.dateTimeStamp,
        XSD.dayTimeDuration,
        XSD.yearMonthDuration,
        ]

def _register_timeExternals(machine):
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
    op = pred["is-literal-date"]
    asassign = lambda dt: is_datatype(XSD.date, dt)


@dataclass
class is_literal_not_date:
    op = pred["is-literal-not-date"]
    asassign = invert.gen(lambda dt: is_datatype(XSD.date, dt))

@dataclass
class is_literal_dateTime:
    op = pred["is-literal-dateTime"]
    asassign = lambda dt: is_datatype(XSD.dateTime, dt)

@dataclass
class is_literal_not_dateTime:
    op = pred["is-literal-not-dateTime"]
    asassign = invert.gen(lambda dt: is_datatype(XSD.dateTime, dt))

@dataclass
class is_literal_dateTimeStamp:
    op = pred["is-literal-dateTimeStamp"]
    asassign = lambda dt: is_datatype(XSD.dateTimeStamp, dt)

@dataclass
class is_literal_not_dateTimeStamp:
    op = pred["is-literal-not-dateTimeStamp"]
    asassign = invert.gen(lambda dt: is_datatype(XSD.dateTimeStamp, dt))

@dataclass
class is_literal_time:
    op = pred["is-literal-time"]
    asassign = lambda dt: is_datatype(XSD.time, dt)

@dataclass
class is_literal_not_time:
    op = pred["is-literal-not-time"]
    asassign = invert.gen(lambda dt: is_datatype(XSD.time, dt))

@dataclass
class is_literal_dayTimeDuration:
    op = pred["is-literal-dayTimeDuration"]
    asassign = lambda dt: is_datatype(XSD.dayTimeDuration, dt)

@dataclass
class is_literal_not_dayTimeDuration:
    op = pred["is-literal-not-dayTimeDuration"]
    asassign = invert.gen(lambda dt: is_datatype(XSD.dayTimeDuration, dt))

@dataclass
class is_literal_yearMonthDuration:
    op = pred["is-literal-yearMonthDuration"]
    asassign = lambda dt: is_datatype(XSD.yearMonthDuration, dt)

@dataclass
class is_literal_not_yearMonthDuration:
    op = pred["is-literal-not-yearMonthDuration"]
    asassign = invert.gen(lambda dt: is_datatype(XSD.yearMonthDuration, dt))

@dataclass
class year_from_dateTime:
    op = func["year-from-dateTime"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.year)


@dataclass
class month_from_dateTime:
    op = func["month-from-dateTime"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.month)

@dataclass
class day_from_dateTime:
    op = func["day-from-dateTime"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.day)

@dataclass
class hours_from_dateTime:
    op = func["hours-from-dateTime"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.hour)

@dataclass
class minutes_from_dateTime:
    op = func["minutes-from-dateTime"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.minute)

@dataclass
class seconds_from_dateTime:
    op = func["seconds-from-dateTime"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.second)

@dataclass
class year_from_date:
    op = func["year-from-date"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.year)

@dataclass
class month_from_date:
    op = func["month-from-date"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.month)

@dataclass
class day_from_date:
    op = func["day-from-date"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.day)

@dataclass
class hours_from_time:
    op = func["hours-from-time"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.hour)

@dataclass
class minutes_from_time:
    op = func["minutes-from-time"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.minute)

@dataclass
class seconds_from_time:
    op = func["seconds-from-time"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(t.value.second)

@dataclass
class timezone_from_dateTime:
    op = func["timezone-from-dateTime"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        v: datetime.datetime = t.value
        timezone: isodate.tzinfo.tzinfo = v.tzinfo
        q: datetime.timedelta = timezone.utcoffset(None)
        return Literal(q)

@dataclass
class timezone_from_time:
    op = func["timezone-from-time"]
    asassign = timezone_from_dateTime

@dataclass
class years_from_duration:
    op = func["years-from-duration"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(int(t.value.years + int(t.value.months/12)))

@dataclass
class months_from_duration:
    op = func["months-from-duration"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        dur: Union[isodate.duration.Duration, datetime.timedelta] = t.value
        return Literal(int(t.value.months%12))

@dataclass
class days_from_duration:
    op = func["days-from-duration"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        dur: Union[isodate.duration.Duration, datetime.timedelta] = t.value
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
    op = func["hours-from-duration"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(int(t.value.seconds/3600))
@dataclass
class minutes_from_duration:
    op = func["minutes-from-duration"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        return Literal(int(t.value.seconds/60)%60 )
@dataclass
class seconds_from_duration:
    op = func["seconds-from-duration"]
    asassign = None
    target: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        t = _resolve(self.target, bindings)
        ms_in_seconds = Decimal(t.value.microseconds) / 1000000
        q = Decimal(t.value.seconds) % 60 + ms_in_seconds
        if q.as_integer_ratio()[1] == 1:
            return Literal(int(q))
        else:
            return Literal(q)


@dataclass
class subtract_dateTimes:
    op = func["subtract-dateTimes"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        first: datetime.datetime = left.value
        second: datetime.datetime = right.value
        return Literal(first - second)

@dataclass
class subtract_dates:
    op = func["subtract-dates"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value - right.value)

@dataclass
class subtract_times:
    op = func["subtract-times"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        date_l = datetime.datetime.combine(datetime.date(2,1,1), left.value)
        date_r = datetime.datetime.combine(datetime.date(2,1,1), right.value)
        dt = date_l - date_r
        return Literal(dt)

@dataclass
class add_yearMonthDurations:
    op = func["add-yearMonthDurations"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        q: isodate.duration.Duration = left.value + right.value
        q.years = q.years + int(q.months/12)
        q.months = q.months%12
        return Literal(q, datatype=XSD.yearMonthDuration)

@dataclass
class subtract_yearMonthDurations:
    op = func["subtract-yearMonthDurations"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        q: isodate.duration.Duration = left.value - right.value
        q.years = q.years + int(q.months/12)
        q.months = q.months%12
        if q.years < 0:
            q.months = q.months - 12
            q.years = q.years + 1
        return Literal(q, datatype=XSD.yearMonthDuration)


@dataclass
class divide_yearMonthDuration:
    op = func["divide-yearMonthDuration"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        months = (left.value.months + (left.value.years * 12)) / right.value
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
    op = func["multiply-yearMonthDuration"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
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
    op = func["divide-yearMonthDuration-by-yearMonthDuration"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        left_months = left.value.months + (left.value.years * 12)
        right_months = right.value.months + (right.value.years * 12)
        return Literal(left_months / right_months)

@dataclass
class add_dayTimeDurations:
    op = func["add-dayTimeDurations"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value + right.value)

@dataclass
class subtract_dayTimeDurations:
    op = func["subtract-dayTimeDurations"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value - right.value)

@dataclass
class subtract_dayTimeDuration_from_dateTime:
    op = func["subtract-dayTimeDuration-from-dateTime"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        date, delta = left.value, right.value
        return Literal(date-delta)

@dataclass
class subtract_dayTimeDuration_from_date:
    op = func["subtract-dayTimeDuration-from-date"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        date, delta = left.value, right.value
        return Literal(date-delta)

@dataclass
class subtract_dayTimeDuration_from_time:
    op = func["subtract-dayTimeDuration-from-time"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        date, delta = left.value, right.value
        d = datetime.datetime(2,1,1,date.hour, date.minute, date.second, date.microsecond)
        d2 = d - delta
        return Literal(datetime.time(d2.hour, d2.minute, d2.second, d2.microsecond, date.tzinfo))

@dataclass
class multiply_dayTimeDuration:
    op = func["multiply-dayTimeDuration"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
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
    op = func["divide-dayTimeDuration"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
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
    op = func["divide-dayTimeDuration-by-dayTimeDuration"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        leftseconds = left.value.seconds + (86400*left.value.days)
        rightseconds = right.value.seconds + (86400*right.value.days)
        q = leftseconds / rightseconds
        if q.as_integer_ratio()[1] == 1:
            return Literal(int(q))
        else:
            return Literal(q)

@dataclass
class add_yearMonthDuration_to_dateTime:
    op = func["add-yearMonthDuration-to-dateTime"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value + right.value)

@dataclass
class add_yearMonthDuration_to_date:
    op = func["add-yearMonthDuration-to-date"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value + right.value)

@dataclass
class add_dayTimeDuration_to_dateTime:
    op = func["add-dayTimeDuration-to-dateTime"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value + right.value, datatype=XSD.dayTime)

@dataclass
class add_dayTimeDuration_to_date:
    op = func["add-dayTimeDuration-to-date"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value + right.value)

@dataclass
class add_dayTimeDuration_to_time:
    op = func["add-dayTimeDuration-to-time"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
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
    op = func["subtract-yearMonthDuration-from-dateTime"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        date, delta = left.value, right.value
        return Literal(date-delta)

@dataclass
class subtract_yearMonthDuration_from_date:
    op = func["subtract-yearMonthDuration-from-date"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        date, delta = left.value, right.value
        return Literal(date-delta)


@dataclass
class dateTime_equal:
    op = pred["dateTime-equal"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        dt = left.value - right.value
        return Literal(dt.total_seconds() == 0.0)

@dataclass
class dateTime_less_than:
    op = pred["dateTime-less-than"]
    asassign = pred_less_than
@dataclass
class dateTime_greater_than:
    op = pred["dateTime-greater-than"]
    asassign = pred_greater_than
@dataclass
class date_equal:
    op = pred["date-equal"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        dt = left.value - right.value
        return Literal(dt.total_seconds() == 0.0)
@dataclass
class date_less_than:
    op = pred["date-less-than"]
    asassign = pred_less_than
@dataclass
class date_greater_than:
    op = pred["date-greater-than"]
    asassign = pred_greater_than
@dataclass
class time_equal:
    op = pred["time-equal"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        date_l = datetime.datetime.combine(datetime.date(2,1,1), left.value)
        date_r = datetime.datetime.combine(datetime.date(2,1,1), right.value)
        dt = date_l - date_r
        return Literal(dt.total_seconds() == 0.0)
@dataclass
class time_less_than:
    op = pred["time-less-than"]
    asassign = pred_less_than
@dataclass
class time_greater_than:
    op = pred["time-greater-than"]
    asassign = pred_greater_than
@dataclass
class duration_equal:
    op = pred["duration-equal"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        q = datetime.datetime(5000,1,1) + left.value - right.value
        return Literal(q == datetime.datetime(5000,1,1))

@dataclass
class yearMonthDuration_less_than:
    op = pred["yearMonthDuration-less-than"]
    #asassign = pred_less_than
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        extime = datetime.datetime(5000,1,1)
        d1 = left.value.totimedelta(extime)
        d2 = right.value.totimedelta(extime)
        return Literal(d1 < d2)

@dataclass
class yearMonthDuration_greater_than:
    op = pred["yearMonthDuration-greater-than"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        extime = datetime.datetime(5000,1,1)
        d1 = left.value.totimedelta(extime)
        d2 = right.value.totimedelta(extime)
        return Literal(d1 > d2)

@dataclass
class dayTimeDuration_less_than:
    op = pred["dayTimeDuration-less-than"]
    #asassign = pred_less_than
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value < right.value)
@dataclass
class dayTimeDuration_greater_than:
    op = pred["dayTimeDuration-greater-than"]
    asassign = None
    left: RESOLVABLE
    right: RESOLVABLE
    def __call__(self, bindings: BINDING) -> Literal:
        left = _resolve(self.left, bindings)
        right = _resolve(self.right, bindings)
        return Literal(left.value > right.value)

@dataclass
class dateTime_not_equal:
    op = pred["dateTime-not-equal"]
    asassign = invert.gen(dateTime_equal)
@dataclass
class dateTime_less_than_or_equal:
    op = pred["dateTime-less-than-or-equal"]
    asassign = invert.gen(pred_greater_than)
@dataclass
class dateTime_greater_than_or_equal:
    op = pred["dateTime-greater-than-or-equal"]
    asassign = invert.gen(pred_less_than)
@dataclass
class date_not_equal:
    op = pred["date-not-equal"]
    asassign = invert.gen(dateTime_equal)
@dataclass
class date_less_than_or_equal:
    op = pred["date-less-than-or-equal"]
    asassign = invert.gen(pred_greater_than)
@dataclass
class date_greater_than_or_equal:
    op = pred["date-greater-than-or-equal"]
    asassign = invert.gen(pred_less_than)
@dataclass
class time_not_equal:
    op = pred["time-not-equal"]
    asassign = invert.gen(time_equal)
@dataclass
class time_less_then_or_equal:
    op = pred["time-less-than-or-equal"]
    asassign = invert.gen(pred_greater_than)
@dataclass
class time_greater_then_or_equal:
    op = pred["time-greater-than-or-equal"]
    asassign = invert.gen(pred_less_than)

@dataclass
class duration_not_equal:
    op = pred["duration-not-equal"]
    asassign = invert.gen(duration_equal)

@dataclass
class yearMonthDuration_less_than_or_equal:
    op = pred["yearMonthDuration-less-than-or-equal"]
    asassign = invert.gen(yearMonthDuration_greater_than)
@dataclass
class yearMonthDuration_greater_than_or_equal:
    op = pred["yearMonthDuration-greater-than-or-equal"]
    asassign = invert.gen(yearMonthDuration_less_than)
@dataclass
class dayTimeDuration_less_than_or_equal:
    op = pred["dayTimeDuration-less-than-or-equal"]
    asassign = invert.gen(dayTimeDuration_greater_than)
@dataclass
class dayTimeDuration_greater_than_or_equal:
    op = pred["dayTimeDuration-greater-than-or-equal"]
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
