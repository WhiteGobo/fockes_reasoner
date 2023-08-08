from collections.abc import Iterable
import rdflib
from rdflib import Variable, Literal
from .. import internal_dataobjects as internal
from ..internal_dataobjects import frame_pattern, create_new, execute, assert_frame, external, bind, modify_frame, implies, retract_frame
from ..shared import tmpdata, focke, rif2internal, RIF, RDF, act, func, pred

def _create_internalGroups() -> internal.rule:
    var_obj = rdflib.Variable("obj")
    var_transObj = rdflib.Variable("transObj")
    patterns = [
            internal.frame_pattern(var_obj, RDF.type, RIF.Group),
            ]
    actions = [
            internal.create_new(var_transObj),
            internal.assert_frame(var_obj, tmpdata.equals, var_transObj),
            internal.assert_frame(var_transObj, RDF.type, rif2internal.Group),
            internal.execute(focke.export, [var_transObj]),
            ]
    return internal.rule(patterns, actions)

internalGroups = _create_internalGroups()
"""Create internal objects representing each group.
"""

def _create_internalRules() -> internal.rule:
    var_obj = rdflib.Variable("obj")
    var_transObj = rdflib.Variable("transObj")
    patterns = [
            internal.frame_pattern(var_obj, RDF.type, RIF.Forall),
            ]
    actions = [
            internal.create_new(var_transObj),
            internal.assert_frame(var_obj, tmpdata.equals, var_transObj),
            internal.assert_frame(var_transObj, RDF.type, rif2internal.forall),
            internal.execute(focke.export, [var_transObj]),
            ]
    return internal.rule(patterns, actions)

internalRules = _create_internalRules()
"""Create internal objects representing each forall
"""

def _create_internalImplies() -> Iterable[internal.rule]:
    var_obj = rdflib.Variable("obj")
    var_transObj = rdflib.Variable("transObj")
    var_cond = rdflib.Variable("cond")
    var_action = rdflib.Variable("action")
    patterns1 = [
            internal.frame_pattern(var_obj, RDF.type, RIF.Implies),
            internal.frame_pattern(var_obj, RIF["if"], var_cond),
            internal.frame_pattern(var_obj, RIF["then"], var_action),
            ]
    actions1 = [
            internal.create_new(var_transObj),
            internal.assert_frame(var_obj, tmpdata.equals, var_transObj),
            internal.assert_frame(var_transObj, RDF.type,
                                  rif2internal.Implies),
            internal.assert_frame(var_transObj, tmpdata.use_as_condition,
                                  var_cond),
            internal.assert_frame(var_transObj, tmpdata.use_as_action,
                                  var_action),
            internal.execute(focke.export, [var_transObj]),
            ]
    yield internal.rule(patterns1, actions1)

internalImplies = list(_create_internalImplies())
"""Rules for transforming implies"""

def _create_internalFramePattern() -> Iterable[internal.rule]:
    var_obj = rdflib.Variable("obj")
    var_cond = rdflib.Variable("cond")
    var_transObj = rdflib.Variable("transObj")
    var_parent = rdflib.Variable("parent")
    var_frameobj = rdflib.Variable("frameobj")
    var_transactionlist = rdflib.Variable("vartransactionlist")
    patterns1 = [
            internal.frame_pattern(var_parent, tmpdata.use_as_condition,
                                   var_obj),
            internal.frame_pattern(var_obj, RDF.type, RIF.Frame),
            internal.frame_pattern(var_obj, RIF.object, var_frameobj),
            ]
    actions1 = [
            internal.create_new(var_transObj),
            internal.assert_frame(var_transObj, RDF.type,
                                  rif2internal.frame_exists),
            internal.assert_frame(var_parent, focke.condition,
                                  var_transObj),
            internal.assert_frame(var_transObj, tmpdata.obj, var_frameobj),
            internal.execute(focke.export, [var_transObj, var_frameobj]),
            ]
    yield internal.rule(patterns1, actions1)
    patterns1 = [
            internal.frame_pattern(var_parent, RDF.type, RIF.Assert),
            internal.frame_pattern(var_parent, RIF.target, var_obj),
            internal.frame_pattern(var_obj, RDF.type, RIF.Frame),
            ]
    actions1 = [
            internal.create_new(var_transObj),
            bind(var_transactionlist,
                 external(getattr(func, "make-list"), [var_transObj])),
            internal.assert_frame(var_transObj, RDF.type,
                                  rif2internal.assert_frame),
            internal.assert_frame(var_parent, tmpdata.actions,
                                  var_transactionlist),
            internal.execute(focke.export,
                             [var_transObj, var_transactionlist]),
            internal.execute(focke.export, [var_parent]),
            ]
    yield internal.rule(patterns1, actions1)

internalFramePattern = list(_create_internalFramePattern())
"""Rules for transforming frame patterns as condition"""

def _create_collectRules() -> Iterable[internal.rule]:
    var_group = rdflib.Variable("group")
    var_rule = rdflib.Variable("rule")
    var_origgroup = rdflib.Variable("origgroup")
    var_origrule = rdflib.Variable("origrule")
    var_rulelist = rdflib.Variable("rulelist")
    var_transrulelist = rdflib.Variable("transrulelist")
    var_newtransrulelist = rdflib.Variable("newtransrulelist")
    var_workqueue = rdflib.Variable("workqueue")
    var_i = rdflib.Variable("i")
    var_nextelement = rdflib.Variable("nextelement")
    patterns1 = [
            frame_pattern(var_group, RDF.type, rif2internal.Group),
            frame_pattern(var_origgroup, tmpdata.equals, var_group),
            frame_pattern(var_origgroup, RIF.sentences, var_rulelist),
            ]
    actions1 = [
            bind(var_workqueue,
                 external(func.sublist, [var_rulelist, Literal(0)])),
            bind(var_transrulelist,
                 external(getattr(func, "make-list"), [])),
            assert_frame(var_transrulelist, RDF.type, tmpdata.transrulelist),
            assert_frame(var_transrulelist, tmpdata.rulesfrom, var_rulelist),
            assert_frame(var_group, tmpdata.sentences, var_transrulelist),
            #execute(act.print, [var_workqueue]),
            assert_frame(var_transrulelist, tmpdata.workqueue, var_workqueue),
            #execute(focke.export, [var_transrulelist]),
            #execute(focke.export, [var_workqueue]),
            #execute(act.print, [Literal("my helperprint")]),
            #execute(act.print, [var_workqueue]),
            ]
    yield internal.rule(patterns1, actions1)
    patterns2 = [
            frame_pattern(var_group, RDF.type, rif2internal.Group),
            frame_pattern(var_group, tmpdata.sentences, var_newtransrulelist),
            frame_pattern(var_transrulelist, tmpdata.workqueue, var_workqueue)
            ]
    actions2 = [
            bind(var_nextelement,
                 external(func.get, [var_workqueue, Literal(0)])),
            bind(var_newtransrulelist,
                 external(func.append,
                          [var_newtransrulelist, var_nextelement]),
                 ),
            bind(var_i, external(func.count, [var_workqueue])),
            implies(external(getattr(pred, "numeric-greater-than"),
                             [var_i, Literal(1)]),
                    [modify_frame(var_group, tmpdata.sentences,
                                  var_newtransrulelist),
                     assert_frame(var_newtransrulelist,
                                  tmpdata.workqueue,
                                  external(func.sublist,
                                           [var_workqueue, Literal(1)])),
                     ]),
            implies(external(getattr(pred, "numeric-equal"),
                             [var_i, Literal(1)]),
                    [assert_frame(var_group, focke.sentences,
                                  var_newtransrulelist),
                     retract_frame(var_group, tmpdata.sentences,
                                   var_transrulelist),
                     execute(focke.export, [var_newtransrulelist]),
                     ]),
            ]
    yield internal.rule(patterns2, actions2)

collectRules = _create_collectRules()
"""Create internal objects representing each forall
"""

rules: list[internal.rule] = [
        internalGroups,
        internalRules,
        *collectRules,
        *internalImplies,
        *internalFramePattern,
        ]

rif2trafo_group2 = internal.group(rules)
