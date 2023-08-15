#type: ignore
"""

:TODO: change algo-nodes to be classified so less circles possible.
:TODO: Use local namespaces for simple algorithms
"""
from collections.abc import Iterable
import rdflib
from rdflib import Variable, Literal
from .. import internal_dataobjects as internal
from ..internal_dataobjects import frame_pattern, create_new, execute, assert_frame, external, bind, modify_frame, implies, retract_frame
from ..shared import tmpdata, focke, rif2internal, RIF, RDF, act, func, pred

def _create_internalGroups() -> Iterable[internal.rule]:
    var_obj = rdflib.Variable("obj")
    var_transObj = rdflib.Variable("transObj")
    var_sentences = rdflib.Variable("sentences")
    var_algo = rdflib.Variable("algo")
    var_algonext = rdflib.Variable("algonext")
    var_sentences_in = rdflib.Variable("sentences_in")
    var_sentences_out = rdflib.Variable("sentences_out")
    var_newsentences_in = rdflib.Variable("newsentences_in")
    var_newsentences_out = rdflib.Variable("newsentences_out")
    var_i = rdflib.Variable("i")
    var_nextelement = rdflib.Variable("nextelement")
    var_workqueue = rdflib.Variable("workqueue")
    var_nextsentence = rdflib.Variable("nextsentence")
    patterns = [
            internal.frame_pattern(var_obj, RDF.type, RIF.Group),
            ]
    actions = [
            internal.create_new(var_transObj),
            internal.assert_frame(var_obj, tmpdata.equals, var_transObj),
            internal.assert_frame(var_transObj, RDF.type, rif2internal.group),
            ]
    #yield internal.rule(patterns, actions)
    patterns1 = [
            internal.frame_pattern(var_obj, RDF.type, RIF.Group),
            frame_pattern(var_obj, RIF.sentences, var_sentences_in),
            ]
    actions1 = [
            internal.create_new(var_algo),
            assert_frame(var_algo, tmpdata.centrumGroup, var_obj),
            assert_frame(var_algo, tmpdata.sentences_in, var_sentences_in),
            assert_frame(var_algo, tmpdata.sentences_out,
                         external(getattr(func, "make-list"), [])),
            execute(act.print, [Literal("algo1")]),
            bind(var_nextelement,
                 external(func.get, [var_sentences_in, Literal(0)])),
            assert_frame(var_algo, tmpdata.nextsentence, var_nextelement),
            assert_frame(var_algo, RDF.type, tmpdata.group1),
            #internal.execute(focke.export, [var_algo, var_nextelement]),
            ]
    yield internal.rule(patterns1, actions1)
    patterns2 = [
            frame_pattern(var_algo, tmpdata.centrumGroup, var_obj),
            frame_pattern(var_algo, tmpdata.sentences_in, var_sentences_in),
            frame_pattern(var_algo, tmpdata.sentences_out, var_sentences_out),
            frame_pattern(var_algo, tmpdata.nextsentence, var_nextelement),
            frame_pattern(var_nextelement, tmpdata.equalto, var_nextsentence),
            frame_pattern(var_algo, RDF.type, tmpdata.group1),
            ]
    actions2 = [
            internal.create_new(var_algonext),
            assert_frame(var_algonext, tmpdata.centrumGroup, var_obj),
            bind(var_newsentences_out,
                 external(func["insert-before"],
                          [var_sentences_out, Literal(0), var_nextsentence])),
            bind(var_i, external(func.count, [var_sentences_in])),
            implies(external(pred["numeric-greater-than"],
                             [var_i, Literal(1)]),
                    [assert_frame(var_algonext, tmpdata.sentences_out,
                                  var_newsentences_out),
                     assert_frame(var_algonext, tmpdata.nextsentence,
                                  external(func.get, [var_sentences_in,
                                                      Literal(1)])),
                     bind(var_newsentences_in, external(func.sublist, [var_sentences_in,
                                                          Literal(1)])
                          ),
                     assert_frame(var_algonext, tmpdata.sentences_in,
                                  var_newsentences_in),
                     assert_frame(var_algonext, RDF.type, tmpdata.group1),
                     #internal.execute(focke.export, [var_newsentences_in]),
                     ]),
            implies(external(pred["numeric-equal"], [var_i, Literal(1)]),
                    [assert_frame(var_algonext, tmpdata.sentences,
                                  var_newsentences_out),
                     assert_frame(var_algonext, RDF.type, tmpdata.group2),
                     ]),
            #internal.execute(focke.export, [var_algonext,
            #                                var_newsentences_out]),
            ]
    yield internal.rule(patterns2, actions2)
    patterns3 = [
            frame_pattern(var_algo, tmpdata.centrumGroup, var_obj),
            frame_pattern(var_algo, tmpdata.sentences, var_sentences),
            frame_pattern(var_algo, RDF.type, tmpdata.group2),
            ]
    actions3 = [
            create_new(var_transObj),
            assert_frame(var_obj, tmpdata.equalto, var_transObj),
            assert_frame(var_transObj, rif2internal.sentences, var_sentences),
            assert_frame(var_transObj, RDF.type, rif2internal.group),
            internal.execute(focke.export, [var_transObj, var_sentences]),
            ]
    yield internal.rule(patterns3, actions3)

internalGroups = list(_create_internalGroups())
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
    var_newFrame = rdflib.Variable("newFrame")
    var_newOrder = rdflib.Variable("newOrder")
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

            internal.create_new(var_newFrame),
            assert_frame(var_newFrame, RDF.type, rif2internal.frame_pattern),
            internal.create_new(var_newOrder),
            assert_frame(var_newOrder, RDF.type, tmpdata.transferFrame),
            assert_frame(var_newOrder, tmpdata["from"],
                         var_possibleNextPattern),
            assert_frame(var_newOrder, tmpdata.to, var_newFrame),
            assert_frame(var_newOrder, tmpdata["index"], Literal(0)),
            bind(var_newpatterns,
                 external(func.append,
                          [var_patterns, var_newFrame]),
                 ),
            internal.execute(focke.export, [var_newFrame]),
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
            ]
    yield internal.rule(patterns5, actions5)
    patterns6 = [
            frame_pattern(var_obj, RDF.type, RIF.Forall),
            frame_pattern(var_algo, tmpdata.centrumRules, var_obj),
            frame_pattern(var_algo, tmpdata.actions, var_actions),
            frame_pattern(var_algo, tmpdata.patterns, var_patterns),
            ]
    actions6 = [
            internal.create_new(var_transObj),
            assert_frame(var_transObj, rif2internal.actions, var_actions),
            assert_frame(var_transObj, rif2internal.patterns, var_patterns),
            assert_frame(var_transObj, RDF.type, rif2internal.forall),
            assert_frame(var_obj, tmpdata.equalto, var_transObj),
            #assert_frame(var_obj, focke.actions, var_actions),
            #assert_frame(var_obj, focke.patterns, var_patterns),
            #assert_frame(var_obj, RDF.type, rif2internal.forall),
            internal.execute(focke.export, [var_transObj, var_actions, var_patterns]),
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
            #internal.execute(focke.export, [var_transObj]),
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
    var_Order = rdflib.Variable("Order")
    var_from = rdflib.Variable("from")
    var_to = rdflib.Variable("to")
    var_framekey = rdflib.Variable("framekey")
    var_framevalue = rdflib.Variable("framevalue")
    var_newOrder = rdflib.Variable("newOrder")
    var_i = rdflib.Variable("i")
    var_slots = rdflib.Variable("slots")
    var_slot = rdflib.Variable("slot")
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
            #internal.assert_frame(var_transObj, tmpdata.parentframe,
            #                      var_obj),
            internal.create_new(var_newOrder),
            assert_frame(var_newOrder, RDF.type, tmpdata.transferFrame),
            assert_frame(var_newOrder, tmpdata["from"], var_obj),
            assert_frame(var_newOrder, tmpdata.to, var_transObj),
            assert_frame(var_newOrder, tmpdata["index"], Literal(0)),
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
            #internal.assert_frame(var_transObj, tmpdata.parentframe,
            #                      var_obj),
            internal.execute(focke.export, [var_transObj]),
            #internal.execute(focke.export, [var_parent]),
            internal.create_new(var_newOrder),
            assert_frame(var_newOrder, RDF.type, tmpdata.transferFrame),
            assert_frame(var_newOrder, tmpdata["from"], var_obj),
            assert_frame(var_newOrder, tmpdata.to, var_transObj),
            assert_frame(var_newOrder, tmpdata["index"], Literal(0)),
            ]
    yield internal.rule(patterns2, actions2)
    """rule to transfer information from rif.frame to internal.frame
    :TODO:  missing slot transfer
    """
    var_actionObj = rdflib.Variable("actionObj")
    patterns4 = [
            #internal.frame_pattern(var_parent, RDF.type, RIF.Group),
            internal.frame_pattern(var_parent, tmpdata.nextsentence, var_obj),
            internal.frame_pattern(var_obj, RDF.type, RIF.Frame),
            ]
    actions4 = [
            internal.create_new(var_transObj),
            assert_frame(var_obj, tmpdata.equalto, var_transObj),
            assert_frame(var_transObj, RDF.type, rif2internal.action),
            internal.create_new(var_actionObj),
            bind(var_transactionlist,
                 external(getattr(func, "make-list"), [var_actionObj])),
            assert_frame(var_transObj, rif2internal.functions,
                         var_transactionlist),
            internal.assert_frame(var_actionObj, RDF.type,
                                  rif2internal.assert_frame),
            #internal.assert_frame(var_actionObj, tmpdata.parentframe,
            #                      var_obj),
            internal.create_new(var_newOrder),
            assert_frame(var_newOrder, RDF.type, tmpdata.transferFrame),
            assert_frame(var_newOrder, tmpdata["from"], var_obj),
            assert_frame(var_newOrder, tmpdata.to, var_actionObj),
            assert_frame(var_newOrder, tmpdata["index"], Literal(0)),
            internal.execute(focke.export,
                             [var_transObj, var_transactionlist, var_actionObj]),
            #internal.execute(focke.export, [var_newOrder, var_obj]),
            ]
    yield internal.rule(patterns4, actions4)
    patterns_transfer1 = [
            frame_pattern(var_Order, RDF.type, tmpdata.transferFrame),
            frame_pattern(var_Order, tmpdata["from"], var_from),
            frame_pattern(var_Order, tmpdata.to, var_to),
            frame_pattern(var_Order, tmpdata["index"], Literal(0)),
            frame_pattern(var_from, tmpdata.obj, var_frameobj),
            frame_pattern(var_from, tmpdata.slotkey, var_framekey),
            frame_pattern(var_from, tmpdata.slotvalue, var_framevalue),
            ]
    actions_transfer1 = [
            assert_frame(var_to, tmpdata.obj, var_frameobj),
            assert_frame(var_to, tmpdata.slotkey, var_framekey),
            assert_frame(var_to, tmpdata.slotvalue, var_framevalue),
            assert_frame(var_to, rif2internal.object, var_frameobj),
            assert_frame(var_to, rif2internal.slotkey, var_framekey),
            assert_frame(var_to, rif2internal.slotvalue, var_framevalue),
            ]
    yield internal.rule(patterns_transfer1, actions_transfer1)
    patterns_transfer2 = [
            frame_pattern(var_Order, RDF.type, tmpdata.transferFrame),
            frame_pattern(var_Order, tmpdata["from"], var_from),
            frame_pattern(var_Order, tmpdata["index"], var_i),
            frame_pattern(var_from, RIF.object, var_frameobj),
            frame_pattern(var_from, RIF.slots, var_slots),
            ]
    actions_transfer2 = [
            assert_frame(var_Order, tmpdata.obj, var_frameobj),
            assert_frame(var_Order, tmpdata.usedSlot,
                         external(func.get, [var_slots, var_i])),
            ]
    yield internal.rule(patterns_transfer2, actions_transfer2)
    patterns_transfer3 = [
            frame_pattern(var_Order, RDF.type, tmpdata.transferFrame),
            frame_pattern(var_Order, tmpdata["to"], var_to),
            frame_pattern(var_Order, tmpdata.obj, var_frameobj),
            frame_pattern(var_Order, tmpdata.usedSlot, var_slot),
            frame_pattern(var_slot, RIF.slotkey, var_framekey),
            frame_pattern(var_slot, RIF.slotvalue, var_framevalue),
            ]
    actions_transfer3 = [
            assert_frame(var_to, tmpdata.obj, var_frameobj),
            assert_frame(var_to, tmpdata.slotkey, var_framekey),
            assert_frame(var_to, tmpdata.slotvalue, var_framevalue),
            assert_frame(var_to, rif2internal.object, var_frameobj),
            assert_frame(var_to, rif2internal.slotkey, var_framekey),
            assert_frame(var_to, rif2internal.slotvalue, var_framevalue),
            execute(focke.export, [var_frameobj, var_framekey, var_framevalue]),
            ]
    yield internal.rule(patterns_transfer3, actions_transfer3)

internalFramePattern = list(_create_internalFramePattern())
"""Rules for transforming frame patterns as condition"""


def _create_rootgroup() -> Iterable[internal.rule]:
    var_group = rdflib.Variable("group")
    var_parentgroup = rdflib.Variable("parentgroup")
    var_list = rdflib.Variable("list")
    patterns1 = [
            frame_pattern(var_parentgroup, rif2internal.sentences, var_list),
            frame_pattern(var_group, RDF.type, rif2internal.group),
            ]
    actions1 = [
            implies(external(func["list-contains"], [var_list, var_group]),
                    [assert_frame(var_group, RDF.type, rif2internal.subgroup)]),
            ]
    yield internal.rule(patterns1, actions1)
rootgroup = list(_create_rootgroup())

rules: list[internal.rule] = [
        *internalGroups,
        *internalRules,
        *internalImplies,
        *internalFramePattern,
        *internalDo,
        *rootgroup,
        ]

rif2trafo_group2 = internal.group(rules)
