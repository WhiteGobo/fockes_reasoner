from typing import Callable, Union, TypeVar, Iterable, Container, Tuple
import rdflib
import itertools as it
from rdflib import Literal, Variable, XSD, IdentifiedNode, Literal, URIRef
import logging
logger = logging.getLogger()
from dataclasses import dataclass
import math
from ..bridge_rdflib import term_list, _term_list, TRANSLATEABLE_TYPES

from ..abc_machine import BINDING, RESOLVABLE, _resolve, RESOLVER, abc_pattern, ATOM_ARGS, _assignment
from ...shared import pred, func

_externals: Iterable

def _register_timeExternals(machine):
    for x in _externals:
        as_ = {}
        for t in ["aspattern", "asassign", "asbinding"]:
            foo = getattr(x, t, None)
            if foo is not None:
                as_[t] = foo
        machine.register(x.op, **as_)

@dataclass
class is_literal_date:
    op = pred["is-literal-date"]

@dataclass
class is_literal_dateTime:
    op = pred["is-literal-dateTime"]

@dataclass
class is_literal_dateTimeStamp:
    op = pred["is-literal-dateTimeStamp"]

@dataclass
class is_literal_time:
    op = pred["is-literal-time"]

@dataclass
class is_literal_dayTimeDuration:
    op = pred["is-literal-dayTimeDuration"]

@dataclass
class is_literal_yearMonthDuration:
    op = pred["is-literal-yearMonthDuration"]

@dataclass
class is_literal_date:
    op = pred["is-literal-date"]


@dataclass
class year_from_dateTime:
    op = func["year-from-dateTime"]

@dataclass
class month_from_dateTime:
    op = func["month-from-dateTime"]

@dataclass
class day_from_dateTime:
    op = func["day-from-dateTime"]

@dataclass
class hours_from_dateTime:
    op = func["hours-from-dateTime"]

@dataclass
class minutes_from_dateTime:
    op = func["minutes-from-dateTime"]

@dataclass
class seconds_from_dateTime:
    op = func["seconds-from-dateTime"]

@dataclass
class year_from_date:
    op = func["year-from-date"]

@dataclass
class month_from_date:
    op = func["month-from-date"]

@dataclass
class day_from_date:
    op = func["day-from-date"]

@dataclass
class hours_from_time:
    op = func["hours-from-time"]

@dataclass
class minutes_from_time:
    op = func["minutes-from-time"]

@dataclass
class seconds_from_time:
    op = func["seconds-from-time"]

@dataclass
class timezone_from_dateTime:
    op = func["timezone_from_dateTime"]

@dataclass
class timezone_from_date:
    op = func["timezone_from_date"]

@dataclass
class timezone_from_time:
    op = func["timezone_from_time"]

@dataclass
class years_from_duration:
    op = func["years-from-duration"]

@dataclass
class months_from_duration:
    op = func["months-from-duration"]

@dataclass
class days_from_duration:
    op = func["days-from-duration"]
@dataclass
class hours_from_duration:
    op = func["hours-from-duration"]
@dataclass
class minutes_from_duration:
    op = func["minutes-from-duration"]
@dataclass
class seconds_from_duration:
    op = func["seconds-from-duration"]

@dataclass
class subtract_dateTimes:
    op = func["subtract-dateTimes"]

@dataclass
class subtract_dates:
    op = func["subtract-dates"]

@dataclass
class subtract_times:
    op = func["subtract-times"]

@dataclass
class add_yearMonthDurations:
    op = func["add-yearMonthDurations"]

@dataclass
class subtract_yearMonthDurations:
    op = func["subtract-yearMonthDurations"]


@dataclass
class divide_yearMonthDurations:
    op = func["divide-yearMonthDurations"]

@dataclass
class multiply_yearMonthDurations:
    op = func["multiply-yearMonthDurations"]

@dataclass
class divide_yearMonthDurations_by_yearMonthDuration:
    op = func["divide-yearMonthDurations-by-yearMonthDuration"]

@dataclass
class add_dayTimeDurations:
    op = func["add-dayTimeDurations"]

@dataclass
class subtract_dayTimeDurations:
    op = func["subtract-dayTimeDurations"]

@dataclass
class multiply_dayTimeDurations:
    op = func["multiply-dayTimeDurations"]

@dataclass
class divide_dayTimeDurations:
    op = func["divide-dayTimeDurations"]

@dataclass
class divide_dayTimeDurations_by_dayTimeDuration:
    op = func["divide-dayTimeDurations-by-dayTimeDuration"]

@dataclass
class add_yearMonthDuration_to_dateTime:
    op = func["add_yearMonthDuration_to_dateTime"]

@dataclass
class add_yearMonthDuration_to_date:
    op = func["add_yearMonthDuration_to_date"]

@dataclass
class add_dayTimeDuration_to_dateTime:
    op = func["add-dayTimeDuration-to-dateTime"]

@dataclass
class add_dayTimeDuration_to_date:
    op = func["add-dayTimeDuration-to-date"]

@dataclass
class add_dayTimeDuration_to_time:
    op = func["add-dayTimeDuration-to-time"]

@dataclass
class subtract_yearMonthDuration_from_dateTime:
    op = func["subtract-yearMonthDuration-from-dateTime"]
@dataclass
class subtract_yearMonthDuration_from_date:
    op = func["subtract-yearMonthDuration-from-date"]
@dataclass
class subtract_yearMonthDuration_from_time:
    op = func["subtract-yearMonthDuration-from-time"]

@dataclass
class dateTime_equal:
    op = pred["dateTime-equal"]

@dataclass
class dateTime_less_than:
    op = pred["dateTime-less-than"]
@dataclass
class dateTime_greater_than:
    op = pred["dateTime-greater-than"]
@dataclass
class date_equal:
    op = pred["date-equal"]
@dataclass
class date_less_than:
    op = pred["date-less-than"]
@dataclass
class date_greater_than:
    op = pred["date-greater-than"]
@dataclass
class time_equal:
    op = pred["time-equal"]
@dataclass
class time_less_than:
    op = pred["time-less-than"]
@dataclass
class time_greater_than:
    op = pred["time-greater-than"]
@dataclass
class duration_equal:
    op = pred["duration-equal"]
@dataclass
class yearMonthDuration_less_than:
    op = pred["yearMonthDuration-less-than"]
@dataclass
class yearMonthDuration_greater_than:
    op = pred["yearMonthDuration-greater-than"]
@dataclass
class dayTimeDuration_less_than:
    op = pred["dayTimeDuration-less-than"]
@dataclass
class dayTimeDuration_greater_than:
    op = pred["dayTimeDuration-greater-than"]

@dataclass
class dateTime_not_equal:
    op = pred["dateTime-not-equal"]
@dataclass
class dateTime_less_than_or_equal:
    op = pred["dateTime-less-than-or-equal"]
@dataclass
class dateTime_not_equal:
    op = pred["dateTime-greater-than-or-equal"]
@dataclass
class date_not_equal:
    op = pred["date-not-equal"]
@dataclass
class date_less_than_or_equal:
    op = pred["date-less-than-or-equal"]
@dataclass
class date_not_equal:
    op = pred["date-greater-than-or-equal"]
@dataclass
class time_not_equal:
    op = pred["time-not-equal"]
@dataclass
class time_less_then_or_equal:
    op = pred["time-less-than-or-equal"]
@dataclass
class time_greater_then_or_equal:
    op = pred["time-greater-than-or-equal"]

@dataclass
class duration_not_equal:
    op = pred["duration-not-equal"]

@dataclass
class yearMonthDuration_less_than_or_equal:
    op = pred["yearMonthDuration-less-than-or-equal"]
@dataclass
class yearMonthDuration_greater_than_or_equal:
    op = pred["yearMonthDuration-greater-than-or-equal"]
@dataclass
class dayTimeDuration_less_than_or_equal:
    op = pred["dayTimeDuration-less-than-or-equal"]
@dataclass
class dayTimeDuration_greater_than_or_equal:
    op = pred["dayTimeDuration-greater-than-or-equal"]

_externals = [
        is_literal_date,
        is_literal_dateTime,
        is_literal_dateTimeStamp,
        is_literal_time,
        is_literal_dayTimeDuration,
        is_literal_yearMonthDuration,
        is_literal_date,
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
        timezone_from_date,
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
        divide_yearMonthDurations,
        multiply_yearMonthDurations,
        divide_yearMonthDurations_by_yearMonthDuration,
        add_dayTimeDurations,
        subtract_dayTimeDurations,
        multiply_dayTimeDurations,
        divide_dayTimeDurations,
        divide_dayTimeDurations_by_dayTimeDuration,
        add_yearMonthDuration_to_dateTime,
        add_yearMonthDuration_to_date,
        add_dayTimeDuration_to_dateTime,
        add_dayTimeDuration_to_date,
        add_dayTimeDuration_to_time,
        subtract_yearMonthDuration_from_dateTime,
        subtract_yearMonthDuration_from_date,
        subtract_yearMonthDuration_from_time,
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
        dateTime_not_equal,
        date_not_equal,
        date_less_than_or_equal,
        date_not_equal,
        time_not_equal,
        time_less_then_or_equal,
        time_greater_then_or_equal,
        duration_not_equal,
        yearMonthDuration_less_than_or_equal,
        yearMonthDuration_greater_than_or_equal,
        dayTimeDuration_less_than_or_equal,
        dayTimeDuration_greater_than_or_equal,
        ]
