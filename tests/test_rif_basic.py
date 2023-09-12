import pytest
from pytest import param, mark
import rdflib
import traceback
import logging
logger = logging.getLogger(__name__)

from fockes_reasoner.shared import RIF
from rdflib import RDF
from fockes_reasoner.rif_dataobjects import (rif_forall,
                                             rif_implies,
                                             rif_assert,
                                             rif_frame,
                                             rif_do,
                                             rif_group,
                                             rif_document,
                                             rif_subclass,
                                             rif_member,
                                             rif_atom,
                                             )
import fockes_reasoner
from fockes_reasoner.class_rdfmodel import rdfmodel

from data.test_suite import \
        (PET_Assert,
         PET_AssertRetract,
         PET_Modify,
         PET_Modify_loop,
         PET_AssertRetract2,
         PET_Builtin_literal_not_identical,
         PET_Builtins_Binary,
         PET_Builtins_List,
         PET_Builtins_Numeric,
         PET_Builtins_Numeric,
         PET_Builtins_PlainLiteral,
         PET_Builtins_String,
         PET_Builtins_Time,
         PET_Builtins_XMLLiteral,
         PET_Builtins_anyURI,
         PET_Builtins_boolean,
         PET_Chaining_strategy_numeric_add_1,
         PET_Chaining_strategy_numeric_subtract_2,
         PET_EBusiness_Contract,
         PET_Factorial_Forward_Chaining,
         PET_Frame_slots_are_independent,
         PET_Frames,
         PET_Guards_and_subtypes,
         PET_IRI_from_RDF_Literal,
         PET_Modeling_Brain_Anatomy,
         PET_OWL_Combination_Vocabulary_Separation_Inconsistency_1,
         PET_OWL_Combination_Vocabulary_Separation_Inconsistency_2,
         PET_Positional_Arguments,
         PET_RDF_Combination_Blank_Node,
         PET_RDF_Combination_Constant_Equivalence_1,
         PET_RDF_Combination_Constant_Equivalence_2,
         PET_RDF_Combination_Constant_Equivalence_3,
         PET_RDF_Combination_Constant_Equivalence_4,
         PET_RDF_Combination_Constant_Equivalence_Graph_Entailment,
         PET_RDF_Combination_SubClass_2,
         NET_Local_Constant,
         NET_Local_Predicate,
         NET_NestedListsAreNotFlatLists,
         NET_Non_Annotation_Entailment,
         NET_RDF_Combination_SubClass,
         )
import data.test_suite

def _import_graph(filepath) -> rdflib.Graph:
    fp = str(filepath)
    formats = (filepath.suffix[1:], "xml")
    for f in formats:
        try:
            return rdflib.Graph().parse(fp, format=f)
        except rdflib.plugin.PluginException as err:
            logger.debug(traceback.format_exc())
    raise Exception("No rdf plugin succesfull. See logging(debug) "
                    "for more info")


_rif_type_to_constructor = {RIF.Frame: rif_frame.from_rdf,
                            #RIF.External: rif_external.from_rdf,
                            RIF.Subclass: rif_subclass.from_rdf,
                            RIF.Member: rif_member.from_rdf,
                            RIF.Atom: rif_atom.from_rdf,
                            }

def test_simpletestrun():
    """Small testrun for the machine and a simple task"""
    testfile = str(PET_Assert.premise)
    conclusionfile = str(PET_Assert.conclusion)
    try:
        g = rdflib.Graph().parse(testfile, format="rif")
        conc_graph = rdflib.Graph().parse(conclusionfile, format="rif")
    except rdflib.plugin.PluginException:
        pytest.skip("Need rdflib parser plugin to load RIF-file")

    q = fockes_reasoner.simpleLogicMachine.from_rdf(g)
    myfacts = q.run()
    logger.info("Expected conclusions in ttl:\n%s" % conc_graph.serialize())
    logger.info("All facts after machine has run:\n%s" % list(q.machine.get_facts()))
    rif_facts = [f for f in rdfmodel().import_graph(conc_graph) if not isinstance(f, rdflib.term.Node)]
    assert rif_facts, "couldnt load conclusion rif_facts directly"
    assert q.check(rif_facts), "Missing expected conclusions"


@pytest.mark.parametrize("testinfo",[
    pytest.param(data.test_suite.PET_Assert),
    pytest.param(data.test_suite.PET_AssertRetract,
                 marks=pytest.mark.skip("implications are not supported yet"),
                 id="PET AssertRetract"),
    pytest.param(data.test_suite.PET_AssertRetract2,
                 id="PET_AssertRetract2"),
    pytest.param(data.test_suite.PET_Modify),
    pytest.param(data.test_suite.PET_Modify_loop),
    pytest.param(PET_Builtin_literal_not_identical,),
    pytest.param(PET_Builtins_Binary,),
    pytest.param(PET_Builtins_List),
    pytest.param(PET_Builtins_Numeric, id="PET Builtins_Numeric"),
    pytest.param(PET_Builtins_PlainLiteral,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_Builtins_String,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_Builtins_Time,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_Builtins_XMLLiteral,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_Builtins_anyURI,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_Builtins_boolean,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_Chaining_strategy_numeric_add_1),
    pytest.param(PET_Chaining_strategy_numeric_subtract_2),
    pytest.param(PET_EBusiness_Contract,
                 marks=mark.skip("First have to implemente builtin time")),
    pytest.param(PET_Factorial_Forward_Chaining,
                 marks=mark.skip("Uses rif_equal to bind variables. nyi")),
    pytest.param(PET_Frame_slots_are_independent,),
    pytest.param(PET_Frames,),
    pytest.param(PET_Guards_and_subtypes),
    pytest.param(PET_IRI_from_RDF_Literal,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_Modeling_Brain_Anatomy,
                 marks=mark.skip("No owl implemented yet.")),
    pytest.param(PET_OWL_Combination_Vocabulary_Separation_Inconsistency_1,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_OWL_Combination_Vocabulary_Separation_Inconsistency_2,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_Positional_Arguments,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_RDF_Combination_Blank_Node,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_RDF_Combination_Constant_Equivalence_1,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_RDF_Combination_Constant_Equivalence_2,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_RDF_Combination_Constant_Equivalence_3,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_RDF_Combination_Constant_Equivalence_4,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_RDF_Combination_Constant_Equivalence_Graph_Entailment,
                 marks=mark.skip("not yet implemented")),
    pytest.param(PET_RDF_Combination_SubClass_2,
                 marks=mark.skip("not yet implemented")),
    ])
def test_PositiveEntailmentTests(testinfo):
    testfile = str(testinfo.premise)
    conclusionfile = str(testinfo.conclusion)
    logger.debug("Premise: %s\nConclusion: %s" %(testfile, conclusionfile))
    try:
        g = rdflib.Graph().parse(testfile, format="rif")
        conc_graph = rdflib.Graph().parse(conclusionfile, format="rif")
    except rdflib.plugin.PluginException:
        pytest.skip("Need rdflib parser plugin to load RIF-file")
    logger.debug("premise in ttl:\n%s" % g.serialize())

    extra_documents = {uri: _import_graph(filepath)
                       for uri, filepath in testinfo.importedDocuments.items()}
    q = fockes_reasoner.simpleLogicMachine.from_rdf(g, extra_documents)
    logger.debug("Running Machine ... ")
    myfacts = q.run()
    logger.debug("Expected conclusions in ttl:\n%s" % conc_graph.serialize())
    rif_facts = []
    for typeref, generator in _rif_type_to_constructor.items():
        for node in conc_graph.subjects(RDF.type, typeref):
            rif_facts.append(generator(conc_graph, node))
    logger.info("All facts after machine has run:\n%s\n\nexpected "
                "facts:\n%s" % (list(q.machine.get_facts()), rif_facts))
    assert rif_facts, "couldnt load conclusion rif_facts directly"
    assert q.check(rif_facts), "Missing expected conclusions"


@pytest.mark.parametrize("testinfo",[
    pytest.param(data.test_suite.NET_Retract,
                 id="NET_Retract"),
    pytest.param(data.test_suite.NET_RDF_Combination_SubClass_5,
                 marks=pytest.mark.skip("version of rdflib_rif is too old"),
                 id="NET_RDF_Combination_SubClass_5"),
    param(NET_Local_Constant, marks=mark.skip("not yet implemented")),
    param(NET_Local_Predicate, marks=mark.skip("not yet implemented")),
    param(NET_NestedListsAreNotFlatLists,
          marks=mark.skip("not yet implemented")),
    param(NET_Non_Annotation_Entailment,
          marks=mark.skip("not yet implemented")),
    param(NET_RDF_Combination_SubClass,
          marks=mark.skip("not yet implemented")),
    ])
def test_NegativeEntailmentTests(testinfo):
    logger.info("premise located: %s\nnonconclusion located: %s"
                %(testinfo.premise, testinfo.nonconclusion))
    try:
        g = rdflib.Graph().parse(testinfo.premise, format="rif")
        nonconc_graph = rdflib.Graph().parse(testinfo.nonconclusion, format="rif")
    except rdflib.plugin.PluginException:
        pytest.skip("Need rdflib parser plugin to load RIF-file")
    logger.info("premise in ttl:\n%s" % g.serialize())

    #filepath.suffix is eg ".rif" so filepath.suffix[1:]=="rif"
    extra_documents = {uri: rdflib.Graph().parse(str(filepath),
                                                 format=filepath.suffix[1:])
                       for uri, filepath in testinfo.importedDocuments.items()}
    q = fockes_reasoner.simpleLogicMachine.from_rdf(g, extra_documents)
    myfacts = q.run()
    logger.info("Not expected conclusions in ttl:\n%s"
                % nonconc_graph.serialize())
    rif_facts = []
    for typeref, generator in _rif_type_to_constructor.items():
        for node in nonconc_graph.subjects(RDF.type, typeref):
            rif_facts.append(generator(nonconc_graph, node))
    #rif_facts = [f for f in rdfmodel().import_graph(nonconc_graph)
    #             if not isinstance(f, rdflib.term.Node)]
    logger.info("All facts after machine has run:\n%s\n\nNot expected "
            "facts:\n%s" % (list(q.machine.get_facts()), rif_facts))
    assert rif_facts, "couldnt load conclusion rif_facts directly"
    for f in rif_facts:
        assert not q.check([f]), "Not expected conclusion %s found" % f
