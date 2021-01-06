Instructions for installing and running Tangent-S
====================================================

Tangent uses python version 3, including the requests and beautiful soup modules.  Portions of the system also use LaTeXML for data conversion and various utilities (available through collections like MacPorts).

make (use dmake on Windows):
   creates executable for prototype search engine

### PREPARING FOR INDEXING

python index.py help
   displays help text for creating tuples for indexing

python index.py 
    creates list of tuples for indexing as tangent/version033/db-index/test_i_*.tsv
    This uses the default tangent.cntl as the control file.

python index.py my-own-file.cntl
    This uses the my-own-file.cntl as the control file, which must exist and have the few
    appropriate lines in it to specify database name, mapping file name, etc. See the help
    text for more detailed information.

### QUERYING

python query.py help
   displays help text for creating tuples for searching

python query.py
   creates list of tuples for searching as tangent/version032/db-index/test_q_*.tsv
   again, uses tangent.cntl as the default control file to provide parameters

cat db-index/* | ./mathindex.exe > mathresults.tsv
   prototype generation of results from searching using files under db-index
   [N.B. assumes that all index files and all search files under db-index are to be used.
    Repeated calls to index.py and query.py with the same documents will produce
    duplicates, so change the argument to cat to specify just which files are desired.]

python3 rerank_results.py 
    Reranks initial search results by detail similarity metrices. Optionally produces .html results pages.
    Run the command without arguments for information on usage.

python combine_rankings.py 
   Used for optional merging of list of results in TSV format, and computes multiple similarity scores as requested.
   Usage of this tool is required before regression reranking. The tool can also be used for combination of results
   from more than one representation (SLT and OPT) or to combine scores from different similarity score vectors. 
   Run the command without arguments for information on usage.

python3 regression_reranking.py
    Optional reranking using linear regression. Requieres existing relevance assessments for learning of 
    regresion weights. Run the command without arguments for information on usage.



### UTILITIES

python get_mathml.py <cntl> <docnum> <position>
   reads the MathML stored in the ith document at the jth relative position.
   Code like that can be inserted into any module desired to provide this functionality.
   (The module MathDocument is also used by index.py to read the documents for parsing.)
   N.B. using -1 in place of docnum retrieves the **query** expression at position j.

python docids2doclist.py <cntl> <docnums> <docnames>
   converts sets of document numbers into a list of filenames.
   Useful for debugging: error messages produced by index.py contain document numbers,
      but index.py requires a list of filenames as input




Documentation:
==============

Doxygen documentation of the source code in html can be viewed at:

doc/html/index.html

Currently Python, C and C++ code will be included in the doxygen files.

To update the documentation, make sure that doxygen is installed, and
then from the current directory issue:

    make docs    (on Windows: dmake docs)

Tangent S Code Organization:
===============================

tangent:
    Makefile    makefile to create search engine and documentation
    mathindex.cpp    search engine code (layer 1)

    index.py    stand-alone routine to parse data documents
    query.py    stand-alone routine to parse query documents
    rerank_results.py    stand-alone routine to process query results (layer 2)
    combine_rankings.py  stand-alone routine to process query results (pre-layer 3)
    regression_reranking.py  stand-alone routine to process query results (layer 3)

    docids2doclist.py
    get_mathml.py

    tangent.cntl    sample cntl file (SLT)
    tangent-OPT.cntl    sample cntl file (OPT)

    README.txt    this file

tangent/TangentS/math:    routines to extract math expressions from documents
    exceptions.py
    latex_mml.py
    layout_symbol.py
    math_extractor.py
    math_document.py
    mathml.py
    math_symbol.py
    mws.sty.ltxml
    semantic_symbol.py
    symbol_tree.py
    version03_index.py

tangent/TangentS/ranking:    routines to rerank and process query results
    alignment.py
    alignment_matching.py
    constraint_info.py
    document_rank_info.py
    matching_helper.py
    matching_result.py
    mathml_cache.py
    pairs_matching.py
    query.py
    reranker.py
    results.py
    scoring_helper.py
    wildcard_alignment.py

tangent/TangentS/text:	handling of queries involving text (not available in this release)
    porter.py
    text_engine_client.py
    TextResult.py

tangent/TangentS/utility:    various support routines
    compy_query.py
    control.py    read, access, and update .cntl file
    read_result.py
    Stats.py    collect parsing problems and statistics
    text_query.py
     

tangent/testing:    test data (documents) and test queries
    test_data
    semantic_test_data
    test_queries
    testlist.txt    sample list of test files
    semantic_testlist.txt

tangent/experiment_tools:	Other utilities
    change_window.py
    convert_tsv_to_TREC_format.py
    eval_metrics_from_TREC_format.py
    qrels_to_tsv.py
    TREC_format_to_tsv.py


Interface to backend search engine:
===================================

Format of Files:

db-index/*_i_*.tsv
W	window
D	docID
E	expression	positions
E	expression	positions
...
D	docID
...
X

db-index/*_q_*.tsv
K	top-k
W	window
Q	queryID
E	expression	positions
E	expression	positions
...
T	keyword
T	keyword
...
Q	queryID
...
X

results.tsv
I	it	index-time(ms)

Q	queryID
E	queryExpr
R	docID	expression	score
R	docID	expression	score
...
I	qt	query-time(ms)
I	post	count
I	expr	count
I	doc	count

Q	queryID
...
X

where positions are expressed as [1] or [0, 5, 12] etc.
