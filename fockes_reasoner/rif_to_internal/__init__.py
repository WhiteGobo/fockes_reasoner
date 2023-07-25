"""This module supports all groups needed for rif import
"""
from .. import internal_dataobjects as _internal
from .normalize_internal_data import rif2trafo_group
from .export_internal_representation import exportInternalRuleRepresentation_group

group_rif2internal = _internal.group([rif2trafo_group,
                                      exportInternalRuleRepresentation_group,
                                      ])
