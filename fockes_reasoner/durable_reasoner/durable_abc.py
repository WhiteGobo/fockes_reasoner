import abc
import typing as typ
import durable.lang as rls
import durable.engine
from collections.abc import Sequence, MutableMapping, Iterable, Callable, Mapping
import rdflib

ATOMLABEL = str
"""All labels within an atom are typed as this"""
FACTTYPE: ATOMLABEL = "type"
"""Labels in where the type of fact is saved"""

FRAME: ATOMLABEL = "frame"
"""facttype :term:`frames` are labeled with this"""
FRAME_OBJ: ATOMLABEL = "obj"
FRAME_SLOTKEY: ATOMLABEL = "slotkey"
FRAME_SLOTVALUE: ATOMLABEL = "slotvalue"
EXECUTE: ATOMLABEL = "execute"
"""facttype :term:`execute` are labeled with this"""
MEMBER: ATOMLABEL = "member"
"""facttype :term:`member` are labeled with this."""
SUBCLASS: ATOMLABEL = "subclass"
"""facttype :term:`subclass` are labeled with this."""
EXTERNAL: ATOMLABEL = "external"
"""facttype :term:`external` are labeled with this."""
LIST: ATOMLABEL = "list"
"""All facts that represent :term:`list` are labeled with this."""
LIST_ID: ATOMLABEL = "id"
"""Facts that represent :term:`list` may have a label of which represent them
in RDF.
"""
LIST_MEMBERS: ATOMLABEL = "member"
""":term:`list` enlist all their members under this label."""

TRANSLATEABLE_TYPES = typ.Union[rdflib.Variable,
                                rdflib.URIRef,
                                rdflib.BNode,
                                rdflib.Literal,
                                ]

VARIABLE_LOCATOR: "typ.TypeAlias" = Callable[[typ.Union[durable.engine.Closure, None]], TRANSLATEABLE_TYPES]
CLOSURE_BINDINGS: "typ.TypeAlias" = MutableMapping[rdflib.Variable, VARIABLE_LOCATOR]

#BINDING = MutableMapping[rdflib.Variable, TRANSLATEABLE_TYPES]
BINDING = MutableMapping[rdflib.Variable, str]

class notFulfilledCondition(Exception):
    """Raise this if a :term:`condition` fails."""

class notBoundedVariable(Exception):
    """Raise this if a :term:`variable` was loaded, which was bound yet."""

class pattern(abc.ABC):
    """All patterns used in a rule are a subclass of this"""
    @abc.abstractmethod
    def _generate_durable_pattern(self, bindings: CLOSURE_BINDINGS,
                                  factname: str) -> rls.value:
        """Used to generate a pattern for when_all method of durable"""

class frame_pattern(pattern):
    """Pattern that for all kinds of :term:`frame`.

    :TODO: making all slots subtype to all rdflib.Identifier vertraegt sich
        nicht mit rdf spezifikation. eg slotkey cant be a Literal
    """
    obj: TRANSLATEABLE_TYPES
    slotkey: TRANSLATEABLE_TYPES
    slotvalue: TRANSLATEABLE_TYPES

    fact_type: str = FRAME
    label_obj: str = FRAME_OBJ
    label_slotkey: str = FRAME_SLOTKEY
    label_slotvalue: str = FRAME_SLOTVALUE


class Member_pattern(pattern):
    """Pattern that works for all kins of :term:`member`

    :TODO: making all slots subtype to all rdflib.Identifier vertraegt sich
        nicht mit rdf spezifikation. eg slotkey cant be a Literal
    """
    obj: TRANSLATEABLE_TYPES
    cls: TRANSLATEABLE_TYPES

class Subclass_pattern(pattern):
    """Pattern that works for all kins of :term:`subclass`

    :TODO: making all slots subtype to all rdflib.Identifier vertraegt sich
        nicht mit rdf spezifikation. eg slotkey cant be a Literal
    """
    obj: TRANSLATEABLE_TYPES
    cls: TRANSLATEABLE_TYPES

class External_pattern(pattern):
    """Pattern that works for all kins of :term:`external`

    :TODO: making all slots subtype to all rdflib.Identifier vertraegt sich
        nicht mit rdf spezifikation. eg slotkey cant be a Literal
    """
    obj: TRANSLATEABLE_TYPES
    atoms: Sequence[TRANSLATEABLE_TYPES]


class function(abc.ABC):
    """All :term:`functions` used in a rule are a subclass of this.
    Everything that is used within the executable part of 
    the rule is a function.
    """
    @abc.abstractmethod
    def __call__(self, c: durable.engine.Closure,
                 bindings: BINDING = {},
                 ) -> typ.Union[None, TRANSLATEABLE_TYPES, bool]:
        """Generic call function for all subtypes"""

class contextless_function(function):
    """All :term:`functions` used in a rule are a subclass of this.
    Everything that is used within the executable part of 
    the rule is a function.
    """
    @abc.abstractmethod
    def __call__(self, c: typ.Union[durable.engine.Closure, str],
                 bindings: BINDING = {},
                 ) -> typ.Union[None, TRANSLATEABLE_TYPES, bool]:
        ...


class condition(function):
    """All :term:`conditions` used in a rule are a subclass of this.
    This is also a function because it is used within the executable part
    of the rule."""

    def __call__(self, c:durable.engine.Closure, bindings: BINDING = {},
                 ) -> None:
        """Break the run of the function with raising notFulfilledCondition

        :raises notFulfilledCondition:
        """

class frame_condition(condition):
    """:term:`Condition` that for all kinds of :term:`frame`.

    :TODO: making all slots subtype to all rdflib.Identifier vertraegt sich
        nicht mit rdf spezifikation. eg slotkey cant be a Literal
    """
    obj: TRANSLATEABLE_TYPES
    slotkey: TRANSLATEABLE_TYPES
    slotvalue: TRANSLATEABLE_TYPES


class member_condition(condition):
    """:term:`Condition` that works for all kins of :term:`member`

    :TODO: making all slots subtype to all rdflib.Identifier vertraegt sich
        nicht mit rdf spezifikation. eg slotkey cant be a Literal
    """
    obj: TRANSLATEABLE_TYPES
    cls: TRANSLATEABLE_TYPES

class subclass_condition(condition):
    """:term:`Condition` that works for all kins of :term:`subclass`

    :TODO: making all slots subtype to all rdflib.Identifier vertraegt sich
        nicht mit rdf spezifikation. eg slotkey cant be a Literal
    """
    obj: TRANSLATEABLE_TYPES
    cls: TRANSLATEABLE_TYPES

class external_condition(condition):
    """:term:`Condition` that works for all kins of :term:`external`

    :TODO: making all slots subtype to all rdflib.Identifier vertraegt sich
        nicht mit rdf spezifikation. eg slotkey cant be a Literal
    """
    obj: TRANSLATEABLE_TYPES
    atoms: Sequence[TRANSLATEABLE_TYPES]

class framework_bridge(contextless_function):
    """Every function, which handles the framework is a subtype to this."""

class execute(framework_bridge):
    op: TRANSLATEABLE_TYPES
    args: tuple[TRANSLATEABLE_TYPES, ...]

    @abc.abstractmethod
    def __call__(self, c: typ.Union[durable.engine.Closure, str],
                 bindings: BINDING = {},
                 external_resolution: Mapping[typ.Union[rdflib.URIRef, rdflib.BNode], typ.Any] = {},
                 ) -> typ.Union[None, TRANSLATEABLE_TYPES, bool]:
        ...

    #fact_type: str = EXECUTE
    #label_op: str = "op"
    #label_args: str = "args"

class assert_frame(framework_bridge):
    """If you :term:`assert` a :term:`frame` use this."""
    obj: TRANSLATEABLE_TYPES
    slotkey: TRANSLATEABLE_TYPES
    slotvalue: TRANSLATEABLE_TYPES

    fact_type: str = FRAME
    label_obj: str = FRAME_OBJ
    label_slotkey: str = FRAME_SLOTKEY
    label_slotvalue: str = FRAME_SLOTVALUE

class assert_member(framework_bridge):
    """If you :term:`assert` a frame use this."""
    obj: TRANSLATEABLE_TYPES
    cls: TRANSLATEABLE_TYPES

class assert_subclass(framework_bridge):
    """If you :term:`assert` a frame use this."""
    obj: TRANSLATEABLE_TYPES
    cls: TRANSLATEABLE_TYPES

class assert_external(framework_bridge):
    """If you :term:`assert` a frame use this."""
    obj: TRANSLATEABLE_TYPES
    atoms: Sequence[TRANSLATEABLE_TYPES]

#T = TypeVar("T")

class value_function(function):
    """Every function, that should return an arbitrary value is a subclass
    to this.
    """
    #_returntype: T
    #
    #def __call__(self, bindings) -> type[T]:
    #    ...

class binding(function):
    """This will be used, when variables are bound to a value within the
    function part. Should be able to bind multiple variables at the same
    time.
    Uses other functions to determine the value.
    """
    used_function: value_function
    variable_mapping: Sequence[rdflib.Variable]

class rule:
    """internal implementation equal to a :term:`rule`."""
    patterns: Iterable[pattern]
    functions: Iterable[function]

class action:
    """internal implementation of a single action."""
    functions: Iterable[function]

class group:
    """internal implementation equal to a :term:`group`."""
    sentences: Iterable[typ.Union[rule, "group"]]
