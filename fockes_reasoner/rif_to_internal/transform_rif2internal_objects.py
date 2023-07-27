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
      Forall ?obj such that ?obj[rdf:type -> rif:Group](
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
from rdflib import RDF
from ..shared import tmpdata, focke, rif2internal


rules: list[internal.rule] = [
        ]

rif2trafo_group2 = internal.group(rules)
