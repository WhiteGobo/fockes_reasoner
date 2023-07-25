"""We need a ruleset which translates :term:`RIF` to a representation
of the :term:`internal datastructure`.
This module provides a python implementation of this ruleset.

.. code::

    Document(
      Prefix(xs <http://www.w3.org/2001/XMLSchema#>) 
      Prefix(rif <http://rif>) 
      Prefix(func <http://func>)
      Prefix(tmp <http://example.com/temporarydata#>)
      Prefix(focke <http://example.com/internaldata#>)
      Prefix(rif2internal <http://example.com/builtin#>)

      (* rif2internal:combinePattern *)
      Group(
        (* rif2internal:combinePatternFormulas*)
        Forall ?first ?first_pattern such that And(
          ?first[rdf:first -> ?first_formula]
          ?first[rdf:rest -> rdf:nil]
          ?first_formula[tmp:pattern -> ?first_pattern]
        )(
          Assert( ?first[tmp:concat_pattern -> ?first_pattern] )
        )
        Forall ?formulas ?first ?second ?first_formula ?second_formula ?conc_pattern ?first_pattern ?second_pattern such that And(
          ?first[rdf:first -> ?first_formula]
          ?first[rdf:rest -> ?second]
          ?second[rdf:first -> ?second_formula]
          ?first_formula[tmp:pattern -> ?first_pattern]
          ?second_formula[tmp:concat_pattern -> ?second_pattern]
        )(
          ?conc_pattern = func:concate(?first_formula, ?second_pattern)
          ?first[tmp:concat_pattern -> ?conc_pattern]
        )
        Forall ?rule ?formulas ?formulas_pattern ?action ?action_pattern such that And(
          ?rule # rif:Forall
          ?rule[rif:formulas -> ?formulas]
          ?first_formula = func:get(?formulas 0)
          ?first_formula[tmp:concat_pattern -> ?formula_pattern]
          ?rule[rif:rules -> ?action]
          ?action[tmp:pattern -> ?action_pattern]
        )(
          ?conc_pattern = func:concate(?formula_pattern ?action_pattern)
          ?rule[focke:pattern -> ?conc_pattern]
        )
      )
    )
"""
from collections.abc import Iterable
import rdflib
from .. import internal_dataobjects as internal
from rdflib import RDF
from ..shared import tmpdata, focke, rif2internal

def _create_initializeConcatePattern() -> internal.rule:
    var_first = rdflib.Variable("first")
    var_first_pattern = rdflib.Variable("first_pattern")
    patterns = [
            internal.frame_pattern(RDF.first, RDF.first, RDF.first),
            #internal.frame_pattern(var_first, RDF.first, var_first_pattern),
            #internal.frame_pattern(var_first, RDF.rest, RDF.nil),
            #internal.frame_pattern(var_first, tmpdata.pattern,
            #                       var_first_pattern),
            ]
    actions = [internal.assert_frame(var_first, tmpdata.concat_pattern,
                                     var_first_pattern)]
    return internal.rule(patterns, actions)
initializeConcatePattern = _create_initializeConcatePattern()

def _create_combinePatternFormulas() -> internal.rule:
    var_rule = rdflib.Variable("rule")
    internal.frame_pattern
    return internal.rule([], [])

combinePatternFormulas = _create_combinePatternFormulas()

rules: list[internal.rule] = [
        initializeConcatePattern,
        #combinePatternFormulas,
        ]

rif2trafo_group = internal.group(rules)
"""Rules that translate rif files to internal data
"""
