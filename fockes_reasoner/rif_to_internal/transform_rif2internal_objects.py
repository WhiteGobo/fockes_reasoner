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
from .. import internal_dataobjects as internal
from ..shared import tmpdata, focke, rif2internal, RIF, RDF

def _create_internalGroups() -> internal.rule:
    var_obj = rdflib.Variable("obj")
    var_transObj = rdflib.Variable("transObj")
    patterns = [
            internal.frame_pattern(var_obj, RDF.type, RIF.Group),
            ]
    actions = [
            internal.create_new(var_transObj),
            internal.assert_frame(var_obj, tmpdata.equals, var_transObj),
            internal.assert_frame(var_transObj, RDF.type, rif2internal.Group)
            ]
    return internal.rule(patterns, actions)

internalGroups = _create_internalGroups()
"""Create internal objects representing each group.
"""

rules: list[internal.rule] = [
        internalGroups,
        ]

rif2trafo_group2 = internal.group(rules)
