
import io
import os
import csv
import sys
import xml
import pickle
import re  # RZ - addition

from src.python.math.math_extractor import MathExtractor
from src.python.math.symbol_tree import SymbolTree
from src.python.ranking.mathml_cache import CompoundMathMLCache
from src.python.ranking.query import Query
from src.python.ranking.reranker import Reranker

class TreeRepMatch:
    def __init__(self, matches_slt=None, matches_opt=None):
        self.matches_slt = []
        if matches_slt is not None:
            if isinstance(matches_slt, list):
                self.matches_slt += matches_slt
            else:
                self.matches_slt.append(matches_slt)

        self.matches_opt = []
        if matches_opt is not None:
            if isinstance(matches_opt, list):
                self.matches_opt += matches_opt
            else:
                self.matches_opt.append(matches_opt)

    @staticmethod
    def Merge(match1, match2):
        matches_slt = list(set.union(set(match1.matches_slt), set(match2.matches_slt)))
        matches_opt = list(set.union(set(match1.matches_opt), set(match2.matches_opt)))

        return TreeRepMatch(matches_slt, matches_opt)


def process_optional_params(optional_parameters):
    result_files = []
    rerank_metrics = []

    pos = 0
    while pos < len(optional_parameters):
        if optional_parameters[pos] == "-r":
            if pos + 2 < len(optional_parameters):
                control_filename = optional_parameters[pos + 1]
                input_filename = optional_parameters[pos + 2]

                result_files.append((control_filename, input_filename))
                pos += 3
            else:
                raise Exception("Incomplete parameters for input set of results")
        elif optional_parameters[pos] == "-m":
            if pos + 2 < len(optional_parameters):
                if optional_parameters[pos + 1].upper() == "OPT":
                    is_OPT = True
                elif optional_parameters[pos + 1].upper() == "SLT":
                    is_OPT = False
                else:
                    raise Exception("Invalid formula represetantion " + optional_parameters[pos + 1])

                try:
                    metric_id = int(optional_parameters[pos + 2])
                except:
                    raise Exception("Invalid metric id " + optional_parameters[pos + 1])

                rerank_metrics.append((is_OPT, metric_id))
                pos += 3
            else:
                raise Exception("Incomplete parameters for metric")
        else:
            print("Unexpected parameter: " + optional_parameters[pos])
            pos += 1

    return result_files, rerank_metrics

def load_result_files(result_files, comp_mathml_cache):

    # query index by query name ....
    # for each query, record {name as index, full mathml, SLT, OPT, candidates={}}
    # for each candidate, record {Formula ID, full mathml, SLT, OPT}
    queries = {}

    for control_filename, result_filename in result_files:
        print("-> File: " + result_filename + " (" + control_filename + ")", flush=True)

        in_file = open(result_filename, 'r', newline='', encoding='utf-8')
        reader = csv.reader(in_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
        lines = [row for row in reader]
        in_file.close()

        current_query_name = None

        # read all results to re-rank
        for idx, parts in enumerate(lines):
            if len(parts) == 2 and parts[0][0] == "Q":
                current_query_name = parts[1]

                print("--> Current query: " + current_query_name, end="\r", flush=True)

                if current_query_name not in queries:
                    # load query data ....
                    # ... offset ...
                    #query_offset = int(current_query_name.split("-")[-1]) - 1

                    # RZ: Hack to support ARQMath results directly.
                    query_offset = int(re.split("\.|-", current_query_name)[-1]) - 1
                    # ... get mathml ....
                    mathml = comp_mathml_cache.get(control_filename, -1, query_offset)
                    
                    #print(current_query_name)
                    #print("OFFSET: " + str(query_offset))
                    #print(mathml)

                    # ... obtain SLT and OPT (trees)

                    presentation_mathml = MathExtractor.isolate_pmml(mathml)
                    content_mathml = MathExtractor.isolate_cmml(mathml)

                    SLT = SymbolTree(MathExtractor.convert_to_layoutsymbol(presentation_mathml))
                    #print("SLT:")
                    OPT = SymbolTree(MathExtractor.convert_to_semanticsymbol(content_mathml))

                    queries[current_query_name] = {
                        "mathml": mathml,
                        "slt_tree": SLT,
                        "slt_const": Query.create_default_constraints(SLT),
                        "slt_str": SLT.tostring(),
                        "opt_tree": OPT,
                        "opt_const": Query.create_default_constraints(OPT),
                        "opt_str": OPT.tostring(),
                        "candidates": {},
                    }

            if len(parts) == 5 and parts[0][0] == "R":
                if current_query_name is None:
                    raise Exception("Result listed before a query, file " + result_filename + " line " + str(idx))

                doc_id = int(parts[1])
                location = int(parts[2])

                mathml = comp_mathml_cache.get(control_filename, doc_id, location)

                # get formula id ....
                elem_content = io.StringIO(mathml)  # treat the string as if a file
                root = xml.etree.ElementTree.parse(elem_content).getroot()
                formula_id = root.attrib["id"]
                if formula_id[0:2] == "./":
                    formula_id = formula_id[2:]

                if not formula_id in queries[current_query_name]["candidates"]:
                    presentation_mathml = MathExtractor.isolate_pmml(mathml)
                    content_mathml = MathExtractor.isolate_cmml(mathml)

                    SLT = SymbolTree(MathExtractor.convert_to_layoutsymbol(presentation_mathml))
                    OPT = SymbolTree(MathExtractor.convert_to_semanticsymbol(content_mathml))

                    queries[current_query_name]["candidates"][formula_id] = {
                        "mathml": mathml,
                        "slt_tree": SLT,
                        "slt_str": SLT.tostring(),
                        "opt_tree": OPT,
                        "opt_str": OPT.tostring(),
                        "scores" : [],
                    }

        print("")

    return queries

def compute_scores(queries, rerank_metrics):
    # Avoid computing re-ranking scores for unique formulas multiple times ...
    # indexing: {'OPT' or 'SLT', metric, Query id, SLT or OPT String} = values
    score_cache = {"opt" : {}, "slt": {}}

    for is_OPT, metric_id in rerank_metrics:
        if is_OPT:
            tree_type = "opt"
        else:
            tree_type = "slt"

        # add the metric if not in the current cache ...
        if not metric_id in score_cache[tree_type]:
            score_cache[tree_type][metric_id] = {}

        print("\nComputing Metric #" + str(metric_id) + " (" + tree_type + ")", flush=True)
        reranker = Reranker.CreateFromMetricID(metric_id, is_OPT, {})

        # compute per query ...
        for query_id in sorted(queries.keys(), key=lambda x: int(x.split("-")[-1])):
            # check if query has to be added to the score cache for this metric
            if not query_id in score_cache[tree_type][metric_id]:
                score_cache[tree_type][metric_id][query_id] = {}

            local_cache = score_cache[tree_type][metric_id][query_id]

            current_query = queries[query_id]
            current_candidates = current_query["candidates"]

            query_tree = current_query[tree_type + "_tree"]
            query_const = current_query[tree_type + "_const"]

            for idx, formula_id in enumerate(current_candidates):
                print("Processing: {0:s}, formula {1:d} of {2:d}".format(query_id, idx, len(current_candidates)), end="\r")

                candidate_tree = current_candidates[formula_id][tree_type + "_tree"]
                candidate_str = current_candidates[formula_id][tree_type + "_str"]

                if candidate_str not in local_cache:
                    # compute score once, and store in the cache for this particular unique expression ...
                    local_cache[candidate_str] = reranker.score_match(query_tree, candidate_tree, query_const)

                # add scores for current candidate ...
                try:
                    current_candidates[formula_id]["scores"] += local_cache[candidate_str].scores
                except:
                    print("Failed ")
                    print("MathML")
                    print(current_query["mathml"])
                    print(current_candidates[formula_id]["mathml"])
                    print("SLT")
                    print(current_query["slt_str"])
                    print(current_candidates[formula_id]["slt_str"])
                    print("OPT")
                    print(current_query["opt_str"])
                    print(current_candidates[formula_id]["opt_str"])

                    raise  Exception("Computing scores failed")

            print("" * 100, end="\r")
    return score_cache

def group_result_trees(queries):
    groups = {}
    for query_id in sorted(queries.keys(), key=lambda x: int(x.split("-")[-1])):
        current_query = queries[query_id]
        current_candidates = current_query["candidates"]

        per_slt_groups = {}
        per_opt_groups = {}
        for formula_id in current_candidates:
            slt_str = current_candidates[formula_id]["slt_str"]
            opt_str = current_candidates[formula_id]["opt_str"]

            # create new if required ....
            if (not slt_str in per_slt_groups) and (not opt_str in per_opt_groups):
                # add and link both ....
                new_group = TreeRepMatch(slt_str, opt_str)
                per_slt_groups[slt_str] = new_group
                per_opt_groups[opt_str] = new_group

            # separated groups ... (will be merged)
            if not slt_str in per_slt_groups:
                per_slt_groups[slt_str] = TreeRepMatch(slt_str, None)

            if not opt_str in per_opt_groups:
                per_opt_groups[opt_str] = TreeRepMatch(None, opt_str)

            # check if merge ...
            if per_slt_groups[slt_str] != per_opt_groups[opt_str]:
                # create merged group ...
                merged = TreeRepMatch.Merge(per_slt_groups[slt_str], per_opt_groups[opt_str])

                # link slts to new group
                for slt_str in merged.matches_slt:
                    per_slt_groups[slt_str] = merged

                # link opts to new group
                for opt_str in merged.matches_opt:
                    per_opt_groups[opt_str] = merged

        # get the final set of groups
        groups[query_id] = list(set(per_slt_groups.values()))

    return groups


def save_results(queries, output_file):

    out_lines = []
    for query_id in sorted(queries.keys(), key=lambda x: int(x.split("-")[-1])):
        candidates = queries[query_id]["candidates"]

        for formula_id in candidates:
            line = [query_id, formula_id] + [str(score) for score in candidates[formula_id]["scores"]]
            out_lines.append(line)

    out_file = open(output_file, 'w', encoding='utf-8')
    for line in out_lines:
        out_file.write("\t".join(line) + "\n")
    out_file.close()


def main():
    # The goal of this script is to take separate sets of results (usually from the core)
    # and combine them into a single file while computing the set of specified metrics for each ....
    # Output will include each result represented by its unique formula identifier and the corresponding scores

    if len(sys.argv) < 9:
        print("Usage")
        print("    python3 combine_rankings.py output_file cache_file [-r control input_file] [-m repr metric]")
        print("")
        print("Where:")
        print("    output_file:\tPath to output file for combined results")
        print("    cache_file:\tPath to compound cache file. Will be created if non-existent")
        print("")
        print("Optional:")
        print("")
        print("    Use -r to specify one input set of results. Must specify at least one")
        print("        control:\tPath to tangent control file used to generate the result file")
        print("        input_file:\tPath to file with results to combine")
        print("")
        print("    Use -m to specify one metric. Must specify at least one")
        print("        repr:\t\tRepresentation for the metric: SLT or OPT")
        print("        metric:\t\tSimilarity metric to use")
        print("")
        return

    # input parameters ....
    output_filename = sys.argv[1]
    cache_filename = sys.argv[2]

    # for input result sets and ranking metrics
    result_files, rerank_metrics = process_optional_params(sys.argv[3:])

    # load the compound cache file if exist, or create a new one if not....
    if os.path.exists(cache_filename):
        in_file = open(cache_filename, 'rb')
        mathml_cache = pickle.load(in_file)
        in_file.close()
    else:
        mathml_cache = CompoundMathMLCache()


    # then, for each file, load the results, use cache to avoid reading the sources everytime ....
    print("Processing input result files....", flush=True)
    queries = load_result_files(result_files, mathml_cache)

    print("Total unique queries found: " + str(len(queries)))
    print("Total matches found per query (might contain multiple instances of same formula)")
    for idx, query_id in enumerate(sorted(queries.keys(), key=lambda x : int(x.split("-")[-1]))):
        ending = "\n" if (idx + 1) % 5 == 0 else ""

        offset = query_id.split("-")[-1]
        print("#" + offset + " = " + str(len(queries[query_id]["candidates"])) + "\t", end=ending)


    # save updated cache ....
    out_file = open(cache_filename, 'wb')
    pickle.dump(mathml_cache, out_file, pickle.HIGHEST_PROTOCOL)
    out_file.close()

    # check groups ....
    tree_groups = group_result_trees(queries)
    for idx, query_id in enumerate(sorted(queries.keys(), key=lambda x: int(x.split("-")[-1]))):
        for tree_group in tree_groups[query_id]:
            if len(tree_group.matches_slt) > 1 and len(tree_group.matches_opt) > 1:
                # found a not 1-to-1 mapping between SLTs and OPTs
                print("\nOn Query: " + query_id)
                print("SLTs = " + str(tree_group.matches_slt))
                print("OPTs = " + str(tree_group.matches_opt))

    # Compute each metric
    score_cache = compute_scores(queries, rerank_metrics)

    for tree_type in ["slt", "opt"]:
        type_metrics = list(score_cache[tree_type].keys())

        if len(type_metrics) == 0:
            print("No metrics computed for Tree Type: " + tree_type)
            continue

        print("")
        print("Tree Type: " + tree_type + ", total metrics = " + str(len(type_metrics)))
        print("-> Total Unique Candidates: ")
        first_metric = type_metrics[0]

        for idx, query_id in enumerate(sorted(queries.keys(), key=lambda x: int(x.split("-")[-1]))):
            ending = "\n" if (idx + 1) % 5 == 0 else ""

            unique_candidates = len(score_cache[tree_type][first_metric][query_id])
            offset = query_id.split("-")[-1]

            print("#" + offset + " = " + str(unique_candidates) + "\t", end=ending)

    print("")

    # Output results
    save_results(queries, output_filename)

    print("Complete!")

if __name__ == '__main__':
    main()
