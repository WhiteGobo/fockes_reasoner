"""

.. code::

    Document(
      Prefix(xs <http://www.w3.org/2001/XMLSchema#>) 
      Prefix(rif <http://rif>) 
      Prefix(func <http://func>)
      Prefix(tmp <http://example.com/temporarydata#>)
      Prefix(focke <http://example.com/internaldata#>)
      Prefix(rif2internal <http://example.com/builtin#>)
      Prefix(rdf <http://www.w3.org/1999/02/22-rdf-syntax-ns#>)

      (* rif2internal:BasicGroupTranslation *)
      Forall ?obj ?transObj such that ?obj[rdf:type -> rif:Group](
        Do ( (?transObj New())
          ?obj[tmp:equals -> ?transObj]
          ?transObj[rdf:type -> rif2internal:Group]
        )
      )

      Forall ?obj such that ?obj[rdf:type -> rif:Group](
        Do ( (?transObj New())
          ?obj[tmp:equals -> ?transObj]
          ?transObj[rdf:type -> rif2internal:Group]
        )
      )
    )
"""
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
            execute(focke.export, [var_transrulelist]),
            execute(focke.export, [var_workqueue]),
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
            execute(act.print, [Literal("brubru"), external(func.get, [var_workqueue, Literal(0)])]),
            bind(var_newtransrulelist,
                 external(func.append,
                          [var_newtransrulelist,
                           external(func.get, [var_workqueue, Literal(0)])]),
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
    patterns = [
            internal.frame_pattern(var_group, RDF.type, rif2internal.group),
            internal.frame_pattern(var_rule, RDF.type, rif2internal.forall),
            internal.frame_pattern(var_origgroup, tmpdata.equals, var_group),
            internal.frame_pattern(var_origrule, tmpdata.equals, var_rule),
            #internal.frame_pattern(var_origgroup, sentences, var_group),
            ]
    #actions = [
            #internal.create_new(var_transObj),
            #internal.assert_frame(var_obj, tmpdata.equals, var_transObj),
            #internal.assert_frame(var_transObj, RDF.type, rif2internal.forall),
            #internal.execute(focke.export, [var_transObj]),
    #        ]
    #return internal.rule(patterns, actions)

collectRules = _create_collectRules()
"""Create internal objects representing each forall
"""

rules: list[internal.rule] = [
        internalGroups,
        internalRules,
        *collectRules,
        ]

rif2trafo_group2 = internal.group(rules)
