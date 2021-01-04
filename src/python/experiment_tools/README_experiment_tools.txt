Instructions for using the tools for experiments with Tangent S
===================================================================

Different tools are provided for computing distinct metrics used to evaluate the Tangent system and each of them is briefly described here.

Many of these tools are designed to compare the outputs from the core and the reranker produced by the system after running on different conditions. The tools asume a naming convention for these files which helps them identify the parameters set for each run. The convention is as follows:

{source}_m{method_id}_w{window_size}_e{EOL}.tsv

{source}	: Source of the output file. It can be "core" or "reranked".
{method_id}	: Similarity metric used. Note that MSS is metric #4.
{window_size}	: Window size used for pair generation.
{EOL}		: 1 if EOL were active and 0 otherwise.

For example, if the EOL pairs were active (e=1) and the results were reranked with MSS (method_id = 4), and the current window size is 2, the output files expected are:

Core results:		core_m4_w2_e1.tsv
Reranked results:	reranked_m4_w2_e1.tsv

Tools available:
====================================

** Changing system settings 

Window size used for indexing can be set in the tangent control file. Input documents are pre-processed and stored in an intermediate representation which includes information about the window size that will be used by the indexing program. It is possible to change the window size configuration on these intermediate files to avoid pre-processing the input dataset multiple times. For this purpose use change_window.py.

Usage
	python3 experiment_tools/change_window.py window [input_files]

Where:
	window:		New value for window parameter
	input_files:	Input files to modify

      
** Evaluation tools

Different tools are provided for evaluation. There are some important differences between the internal representation of formulas used by our system and the TREC format used by the  benchmark tasks like the NTCIR-12 MathIR Wikipedia task. We provide the tools required to extend and modify our raw result files into new formats that are compatible with the NTCIR-12 Wikipedia task benchmark.

The convert_tsv_to_TREC_format.py tool converts our internal TSV representation to a more general format used by the TREC eval tool that identifies formulas using the original ids
in the source mathml.

Usage
	python3 convert_tsv_to_TREC_format.py control input_results output_results run_name best_only max_k

Where:
	control:	Path to tangent control file
	input_results:	Path to input tsv results file
	output_results:	Path to output TREC results file
	run_name:	Name of the run in input file
	best_only:	Save only top expression per document
	Max_K:		Maximum Number of results to output per query (<0 - unlimited)

Precision@K and nDCG@K can be computed using eval_metrics_from_TREC_format.py.  The tool
allows to compute these metrics by custom query groups. 

Usage:
	python eval_metrics_from_TREC_format.py relevance results sort top_k min_rel show_detail [groups]

Where

	relevance:	File with non-aggregated relevance assessments
	results:	Results to evaluate in TREC file format
	sort:		If positive, ties will be broken by document name
	top_k:		Top-K results to consider for metrics
	min_rel:	Minimum relevance value for relevant documents
	show_detail:	Show per query evaluation results
	groups:		Optional. File with query groups


The qrels_to_tsv.py tool can be used to generate our internal TSV representation format from
a set of documents with the corresponding relevance assessments (qrels)

Usage
    python3 qrels_to_tsv.py qrels_agg control output_results

Where
	qrels_agg:	Path to Aggregated judgments for topics
	control:	Path to control file
	output_results:	Path to store tsv results



The TREC_format_to_tsv.py allows converting a set of results in TREC format to our internal
representation in TSV format.


Usage
    python3 TREC_format_to_tsv.py trec_input qrels_agg control max_k tsv_output

Where
	trec_input:	Path to input results in TREC format
	qrels_agg:	Path to Aggregated judgments for topics
	control:	Path to control file
	max_k:		Max results to output per query (<0 = Unlimited)
	tsv_output:	Path to store tsv results



