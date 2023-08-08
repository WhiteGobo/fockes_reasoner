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

def _create_internalRules() -> Iterable[internal.rule]:
    var_obj = rdflib.Variable("obj")
    var_formulas = rdflib.Variable("formulas")
    var_rule = rdflib.Variable("rule")
    var_transObj = rdflib.Variable("transObj")
    var_algo = rdflib.Variable("algo")
    var_algonext = rdflib.Variable("algonext")
    var_conditions = rdflib.Variable("conditions")
    var_newconditions = rdflib.Variable("newconditions")
    var_actions = rdflib.Variable("actions")
    var_patterns = rdflib.Variable("patterns")
    var_newpatterns = rdflib.Variable("newpatterns")
    var_possibleNextPattern = rdflib.Variable("possibleNextPattern")
    var_i = rdflib.Variable("i")
    patterns1 = [
            internal.frame_pattern(var_obj, RDF.type, RIF.Forall),
            ]
    actions1 = [
            internal.create_new(var_algo),
            internal.assert_frame(var_algo, tmpdata.centrumRules, var_obj),
            assert_frame(var_algo, RDF.type, tmpdata.start),
            ]
    yield internal.rule(patterns1, actions1)
    patterns2 = [
            frame_pattern(var_obj, RDF.type, RIF.Forall),
            frame_pattern(var_obj, RIF.formula, var_rule),
            #frame_pattern(var_obj, RIF.pattern, var_formulas),
            frame_pattern(var_rule, tmpdata.conditions, var_conditions),
            frame_pattern(var_rule, tmpdata.actions, var_actions),
            frame_pattern(var_algo, tmpdata.centrumRules, var_obj),
            frame_pattern(var_algo, RDF.type, tmpdata.start),
            ]
    actions2 = [
            assert_frame(var_algo, tmpdata.actionsfrom1, var_actions),
            assert_frame(var_algo, tmpdata.conditionsfrom1, var_conditions),
            ]
    yield internal.rule(patterns2, actions2)
    patterns3 = [
            frame_pattern(var_obj, RDF.type, RIF.Forall),
            frame_pattern(var_algo, tmpdata.centrumRules, var_obj),
            frame_pattern(var_algo, tmpdata.actionsfrom1, var_actions),
            frame_pattern(var_algo, tmpdata.conditionsfrom1, var_conditions),
            ]
    actions3 = [
            internal.create_new(var_algonext),
            assert_frame(var_algonext, RDF.type, tmpdata.state3),
            assert_frame(var_algonext, tmpdata.centrumRules, var_obj),
            assert_frame(var_algonext, tmpdata.conditionsfrom, var_conditions),
            assert_frame(var_algonext, tmpdata.actions, var_actions),
            bind(var_patterns,
                 external(getattr(func, "make-list"), [])),
            assert_frame(var_algonext, tmpdata.patternsfrom, var_patterns),
            ]
    yield internal.rule(patterns3, actions3)
    patterns4 = [
            frame_pattern(var_obj, RDF.type, RIF.Forall),
            frame_pattern(var_algo, tmpdata.centrumRules, var_obj),
            frame_pattern(var_algo, tmpdata.conditionsfrom, var_conditions),
            #frame_pattern(var_algo, tmpdata.actionsfrom, var_actions),
            #frame_pattern(var_algonext, tmpdata.patternsfrom, var_patterns),
            ]
    actions4 = [
            bind(var_possibleNextPattern,
                 external(func.get, [var_conditions, Literal(0)])),
            assert_frame(var_algo, tmpdata.possibleNextPattern,
                         var_possibleNextPattern),
            ]
    yield internal.rule(patterns4, actions4)
    #change frame_exists as pattern to a condition, maybe
    patterns5 = [
            frame_pattern(var_obj, RDF.type, RIF.Forall),
            frame_pattern(var_algo, RDF.type, tmpdata.state3),
            frame_pattern(var_algo, tmpdata.centrumRules, var_obj),
            frame_pattern(var_algo, tmpdata.conditionsfrom, var_conditions),
            frame_pattern(var_algo, tmpdata.actions, var_actions),
            frame_pattern(var_algonext, tmpdata.patternsfrom, var_patterns),
            frame_pattern(var_algo, tmpdata.possibleNextPattern,
                          var_possibleNextPattern),
            frame_pattern(var_possibleNextPattern, RDF.type,
                          rif2internal.frame_exists),
            ]
    actions5 = [
            internal.create_new(var_algonext),
            assert_frame(var_algonext, tmpdata.centrumRules, var_obj),
            assert_frame(var_algonext, tmpdata.actions, var_actions),
            bind(var_newpatterns,
                 external(func.append,
                          [var_patterns, var_possibleNextPattern]),
                 ),
            bind(var_i, external(func.count, [var_conditions])),
            implies(external(getattr(pred, "numeric-greater-than"),
                             [var_i, Literal(1)]),
                    [bind(var_newconditions,
                          external(func.sublist, [var_conditions,
                                                  Literal(1)])),
                     assert_frame(var_algonext, tmpdata.conditionsfrom,
                                  var_newconditions),
                     assert_frame(var_algonext, tmpdata.patternsfrom,
                                  var_newpatterns),
                     assert_frame(var_algonext, RDF.type, tmpdata.state3),
                     ]),
            implies(external(getattr(pred, "numeric-equal"),
                             [var_i, Literal(1)]),
                    [assert_frame(var_algonext, tmpdata.patterns,
                                  var_newpatterns),
                     assert_frame(var_algonext, RDF.type, tmpdata.state4),
                     ]),
            internal.execute(focke.export, [var_obj, var_algonext]),
            ]
    yield internal.rule(patterns5, actions5)
    patterns6 = [
            frame_pattern(var_obj, RDF.type, RIF.Forall),
            frame_pattern(var_algo, tmpdata.centrumRules, var_obj),
            frame_pattern(var_algo, tmpdata.actions, var_actions),
            frame_pattern(var_algo, tmpdata.patterns, var_patterns),
            ]
    actions6 = [
            assert_frame(var_obj, tmpdata.actions, var_actions),
            assert_frame(var_obj, tmpdata.patterns, var_patterns),
            ]
    yield internal.rule(patterns6, actions6)


internalRules = list(_create_internalRules())
"""Create internal objects representing each forall
"""

def _create_internalDo() -> Iterable[internal.rule]:
    var_obj = rdflib.Variable("obj")
    var_transObj = rdflib.Variable("transObj")
    var_actionlist = rdflib.Variable("actionlist")
    var_transList = rdflib.Variable("transList")
    var_newtransList = rdflib.Variable("newtransList")
    var_algo = rdflib.Variable("algo")
    var_workqueue = rdflib.Variable("workqueue")
    var_newworkqueue = rdflib.Variable("newworkqueue")
    var_i = rdflib.Variable("i")
    var_nextelement = rdflib.Variable("nextelement")
    var_actionList = rdflib.Variable("actionList")
    var_algonext = rdflib.Variable("algonext")
    patterns1 = [
            internal.frame_pattern(var_obj, RDF.type, RIF.Do),
            internal.frame_pattern(var_obj, RIF.actions, var_actionlist),
            ]
    actions1 = [
            internal.create_new(var_algo),
            bind(var_transList,
                 external(getattr(func, "make-list"), [])),
            internal.assert_frame(var_algo, tmpdata.centrum, var_obj),
            internal.assert_frame(var_algo, RDF.type, tmpdata.algo1),
            internal.assert_frame(var_algo, tmpdata.actionsfrom,
                                  var_actionlist),
            internal.assert_frame(var_algo, tmpdata.actionsto,
                                  var_transList),
            #internal.execute(focke.export, [var_obj, var_transList]),
            ]
    yield internal.rule(patterns1, actions1)
    patterns2 = [
            frame_pattern(var_algo, tmpdata.actionsfrom, var_workqueue),
            frame_pattern(var_algo, tmpdata.actionsto, var_transList),
            frame_pattern(var_algo, tmpdata.centrum, var_obj),
            ]
    actions2 = [
            bind(var_i, external(func.count, [var_workqueue])),
            implies(external(getattr(pred, "numeric-greater-than"),
                             [var_i, Literal(0)]),
                    [bind(var_nextelement,
                          external(func.get, [var_workqueue, Literal(0)])),
                     assert_frame(var_algo, tmpdata.transfer_actions_from,
                                  var_nextelement),
                     ]),
            implies(external(getattr(pred, "numeric-equal"),
                             [var_i, Literal(0)]),
                    [assert_frame(var_obj, tmpdata.actions, var_transList)]),
            ]
    yield internal.rule(patterns2, actions2)
    patterns3 = [
            frame_pattern(var_algo, tmpdata.actionsfrom, var_workqueue),
            frame_pattern(var_algo, tmpdata.actionsto, var_transList),
            frame_pattern(var_algo, tmpdata.centrum, var_obj),
            frame_pattern(var_algo, tmpdata.transfer_actions_from,
                          var_nextelement),
            frame_pattern(var_nextelement, tmpdata.actions, var_actionList),
            ]
    actions3 = [
            internal.create_new(var_algonext),
            assert_frame(var_algonext, tmpdata.centrum, var_obj),
            bind(var_newtransList,
                 external(func["concatenate"],
                          [var_transList, var_actionList]),
                 ),
            bind(var_newworkqueue,
                 external(func.sublist, [var_workqueue, Literal(1)])),
            assert_frame(var_algonext, tmpdata.actionsfrom, var_newworkqueue),
            assert_frame(var_algonext, tmpdata.actionsto, var_newtransList),
            ]
    yield internal.rule(patterns3, actions3)

internalDo = list(_create_internalDo())

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
    var_then = rdflib.Variable("then")
    var_parent = rdflib.Variable("parent")
    var_actions = rdflib.Variable("actions")
    patterns2 = [
            internal.frame_pattern(var_parent, RDF.type, RIF.Implies),
            internal.frame_pattern(var_parent, RIF["then"], var_then),
            internal.frame_pattern(var_then, tmpdata.actions, var_actions),
            ]
    actions2 = [
            internal.assert_frame(var_parent, tmpdata.actions, var_actions),
            ]
    yield internal.rule(patterns2, actions2)

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
            internal.frame_pattern(var_parent, RDF.type, RIF.Implies),
            internal.frame_pattern(var_parent, RIF["if"], var_obj),
            internal.frame_pattern(var_obj, RDF.type, RIF.Frame),
            ]
    actions1 = [
            internal.create_new(var_transObj),
            bind(var_transactionlist,
                 external(getattr(func, "make-list"), [var_transObj])),
            internal.assert_frame(var_transObj, RDF.type,
                                  rif2internal.frame_exists),
            internal.assert_frame(var_parent, tmpdata.conditions,
                                  var_transactionlist),
            internal.assert_frame(var_transObj, tmpdata.parentframe,
                                  var_obj),
            internal.execute(focke.export,
                             [var_transObj, var_transactionlist]),
            internal.execute(focke.export, [var_parent]),
            ]
    yield internal.rule(patterns1, actions1)
    patterns2 = [
            internal.frame_pattern(var_parent, RDF.type, RIF.Assert),
            internal.frame_pattern(var_parent, RIF.target, var_obj),
            internal.frame_pattern(var_obj, RDF.type, RIF.Frame),
            ]
    actions2 = [
            internal.create_new(var_transObj),
            bind(var_transactionlist,
                 external(getattr(func, "make-list"), [var_transObj])),
            internal.assert_frame(var_transObj, RDF.type,
                                  rif2internal.assert_frame),
            internal.assert_frame(var_parent, tmpdata.actions,
                                  var_transactionlist),
            internal.assert_frame(var_transObj, tmpdata.parentframe,
                                  var_obj),
            internal.execute(focke.export,
                             [var_transObj, var_transactionlist]),
            internal.execute(focke.export, [var_parent]),
            ]
    yield internal.rule(patterns2, actions2)
    """rule to transfer information from rif.frame to internal.frame
    :TODO:  missing slot transfer
    """
    patterns3 = [
            internal.frame_pattern(var_transObj, tmpdata.parentframe,
                                   var_obj),
            internal.frame_pattern(var_obj, RIF.object, var_frameobj),
            ]
    actions3 = [
            internal.assert_frame(var_transObj, tmpdata.obj, var_frameobj),
            internal.execute(focke.export, [var_frameobj]),
            ]
    yield internal.rule(patterns3, actions3)

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
        *internalRules,
        *collectRules,
        *internalImplies,
        *internalFramePattern,
        *internalDo,
        ]

rif2trafo_group2 = internal.group(rules)
