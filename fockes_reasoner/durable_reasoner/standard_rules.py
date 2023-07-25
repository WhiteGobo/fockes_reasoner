import durable.lang as rls
from rdflib import RDF
import durable.engine
from .durable_abc import FACTTYPE, FRAME, FRAME_OBJ, FRAME_SLOTKEY, FRAME_SLOTVALUE, LIST, LIST_ID, LIST_MEMBERS
from collections.abc import Callable
from ..shared import rdflib2string
import logging
logger = logging.getLogger(__name__)

def get_standard_ruleset(rulename: str, save_error: Callable) -> rls.ruleset:
    ruleset = rls.ruleset(rulename)
    NIL = rdflib2string(RDF.nil)
    REST = rdflib2string(RDF.rest)
    FIRST = rdflib2string(RDF.first)
    with ruleset:
        @rls.when_all(+rls.s.exception)
        def second(c: durable.engine.Closure) -> None:
            logger.critical(c.s.exception)
            save_error(str(c.s.exception))
            c.s.exception = None

        @rls.when_all(+getattr(rls.m, FACTTYPE))
        def accept_all_frametypes(c: durable.engine.Closure) -> None:
            #logger.critical(str(c))
            pass

        @rls.when_all(
                rls.c.base << (getattr(rls.m, FRAME_SLOTVALUE) == NIL)
                & (getattr(rls.m, FACTTYPE) == FRAME)
                & (getattr(rls.m, FRAME_SLOTKEY) == REST),
                rls.c.lastelem << (getattr(rls.m, FRAME_OBJ)
                                   == getattr(rls.c.base, FRAME_OBJ))
                & (getattr(rls.m, FRAME_SLOTKEY) == FIRST)
                )
        def start_list(c: durable.engine.Closure) -> None:
            l = c.lastelem[FRAME_OBJ]
            elem = c.lastelem[FRAME_SLOTVALUE]
            logger.debug("found list %s" % l)
            c.assert_fact({FACTTYPE: LIST,
                           LIST_ID: l,
                           LIST_MEMBERS: [elem]})
            c.retract_fact(c.base)
            c.retract_fact(c.lastelem)

        @rls.when_all(
                rls.c.list << (getattr(rls.m, FACTTYPE) == LIST),
                rls.c.base << (getattr(rls.m, FRAME_SLOTKEY) == REST)
                & (getattr(rls.m, FRAME_SLOTVALUE)
                                == getattr(rls.c.list, LIST_ID))
                & (getattr(rls.m, FACTTYPE) == FRAME),
                rls.c.element << (getattr(rls.m, FACTTYPE) == FRAME)
                & (getattr(rls.m, FRAME_SLOTKEY) == FIRST),
                )
        def combine_list(c: durable.engine.Closure) -> None:
            newid = c.base[FRAME_OBJ]
            elem = c.element[FRAME_SLOTVALUE]
            logger.debug(f"combining list with {elem}\n{newid}\n{c.list[LIST_ID]}")
            c.retract_fact(c.list)
            c.retract_fact(c.base)
            c.retract_fact(c.element)
            c.assert_fact({FACTTYPE: LIST,
                           LIST_ID: newid,
                           LIST_MEMBERS: list(c.list[LIST_MEMBERS]) + [elem]})
    return ruleset
