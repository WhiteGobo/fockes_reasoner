import fockes_reasoner
from dataclasses import dataclass
import pytest
from pytest import param, fixture
from fockes_reasoner.durable_reasoner import _resolve
from rdflib import URIRef, Graph, Namespace, Literal, XSD
import logging
logger = logging.getLogger(__name__)

@pytest.fixture(params=[
    param(fockes_reasoner.simpleLogicMachine),
    ])
def logic_machine(request) -> "extensible_machine":
    return request.param

def test_register_new_action(logic_machine):
    data = """
Document(
 Prefix(ex <http://example.org/example#>)
 Prefix(xs <http://www.w3.org/2001/XMLSchema#>) 
 Prefix(act <http://www.w3.org/2007/rif-builtin-action#>)

 Group ( 
  Forall ?X (
   If 
      ?X[ex:status -> "gold"] 
   Then Do ( 
      Execute (act:save("Hello World"))
   )
  )

  ex:John[ex:status -> "gold"]

 )
)
    """
    g = Graph().parse(data=data, format="rifps")
    act = Namespace("http://www.w3.org/2007/rif-builtin-action#")
    asd = []

    @dataclass
    class myact:
        def __init__(self, machine, *args) -> None:
            self.args = args

        def __call__(self, bindings) -> None:
            logger.info("Called the new implemented method")
            args = tuple(_resolve(x, bindings) for x in self.args)
            asd.append(True)

    expects_actions = False

    mymachine = fockes_reasoner.machineWithImport()
    mymachine.register(act.save,
            asaction=(myact, expects_actions),
            #asassign=,
            #aspattern=,
            #asbinding=,
            )

    mek = logic_machine.from_rdf(g, {}, machine=mymachine)
    mek.run()

    datagraph = mek.export_rdflib()
    assert True in asd
    #assert Literal("Hello World", datatype=XSD.string) in asd
