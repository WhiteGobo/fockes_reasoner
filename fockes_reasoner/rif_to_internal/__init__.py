"""This module supports all groups needed for rif import
"""
from .. import internal_dataobjects as _internal
from .normalize_internal_data import rif2trafo_group
from .transform_rif2internal_objects import rif2trafo_group2
from .export_internal_representation import exportInternalRuleRepresentation_group

group_rif2internal = _internal.group([rif2trafo_group,
                                      rif2trafo_group2,
                                      exportInternalRuleRepresentation_group,
                                      ])
