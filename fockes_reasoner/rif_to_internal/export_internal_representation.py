"""
To enable input-output things for information one need methods to label, what
data should be exported. This module labels all information about internaldata
for export.

.. code::

    Document(
      Prefix(rif <http://rif>) 
      Prefix(func <http://func>)
      Prefix(tmp <http://example.com/temporarydata#>)
      Prefix(focke <http://example.com/internaldata#>)
      Prefix(rif2internal <http://example.com/builtin#>)
      Group(
        Forall ?grouppred such that ?grouppred in (focke:ex) (
          Forall ?any ?list
            such that ?any[?grouppred -> ?list](
            Execute (focke:export_list(?list))
          )
        )
      )
    )
"""
from collections.abc import Iterable
import typing as typ
import rdflib
from .. import internal_dataobjects as internal
from rdflib import RDF
from ..shared import tmpdata, focke, rif2internal, RIF


def _create_export_document() -> internal.rule:
    var_document = rdflib.Variable("document")
    var_grouplist = rdflib.Variable("grouplist")
    patterns = [
            internal.frame_pattern(var_document, RIF.sentences, var_grouplist),
            ]
    actions = [internal.execute(focke.export, [var_grouplist])]
    return internal.rule(patterns, actions)

export_document = _create_export_document()
"""Labels all lists that are used for internal datastructures for export.
"""

export_all_internal_presentation_predicates\
        = internal.action([internal.execute(focke.export, [focke.asdf])])
"""Starting action that labels all predicates for export, that
present internal datastructure.
"""

rules: list[typ.Union[internal.rule, internal.action, internal.group]] = [
        #export_document,
        export_all_internal_presentation_predicates,
        ]

exportInternalRuleRepresentation_group = internal.group(rules)
"""Rules to show what part of internal information should be exported, so
that the rule can be loaded by internal framework.
"""
