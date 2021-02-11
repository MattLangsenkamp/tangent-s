import io
import os
import csv
import sys
import xml
import pickle
import re  # RZ - addition
import time
from src.python.math.math_extractor import MathExtractor
from src.python.math.symbol_tree import SymbolTree
from src.python.ranking.mathml_cache import CompoundMathMLCache
from src.python.ranking.query import Query
from src.python.ranking.reranker import Reranker

# RZ: additions for ARQMath id lookup.
from src.python.utility.control import Control
from src.python.math.math_document import MathDocument
from operator import itemgetter

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


def load_result_files(result_files):  # RZ: mod #, comp_mathml_cache):

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

        # RZ: Prepare to access ARQMath ids for result formulas.
        cntl = Control(control_filename)
        md = MathDocument(cntl)
        print("   Operator tree: " + str(md.operator_tree))

        # read all results to re-rank
        for idx, parts in enumerate(lines):
            if len(parts) == 2 and parts[0][0] == "Q":
                current_query_name = parts[1]

                print("--> Current query: " + current_query_name, end="\r", flush=True)

                # query_offset = int(re.split("\.|-", current_query_name)[-1]) - 1
                if current_query_name not in queries:
                    # RZ: Hack to support ARQMath results directly.
                    
                    queries[current_query_name] = {
                        # REMOVE all fields involving formula data, which can be
                        # found elsewhere.
                        "slt_str": '',
                        "opt_str": '',
                        "candidates": {}
                    }

            elif len(parts) == 2 and parts[0][0] == "E":
                qformula = parts[1]
                if not md.operator_tree:
                    queries[current_query_name]["slt_str"] = qformula
                else:
                    queries[current_query_name]["opt_str"] = qformula

            elif len(parts) == 5 and parts[0][0] == "R":
                if current_query_name is None:
                    raise Exception("Result listed before a query, file " + result_filename + " line " + str(idx))

                location = int(parts[1])
                formula_mml = md.find_doc_file(location)
                file_name_with_ext = os.path.basename(formula_mml)
                # file_name_with_ext = os.path.split(formula_mml)[1]

                # this only accounts for when the file names are numbers - MLang
                no_ext = os.path.splitext(file_name_with_ext)[0]
                formula_id = int(no_ext)
                # keeping name as string should only have the effect of searching the candidates be slower
                #formula_id = file_name_with_ext

                # DEBUG
                # print(  "doc_id: " + parts[1] )
                # print(formula_mml)
                # print(os.path.splitext( os.path.split( formula_mml )[1] )[0]) 
                if not formula_id in queries[current_query_name]["candidates"]:
                    score_list = list(map(float, parts[4].replace(" ","").replace("[","")\
                            .replace("]","").split(",")))
                    if len(score_list) < 2:
                        print('Invalid result file -- not a reranked result: ' + result_filename)
                        sys.exit(1)

                    # DEBUG
                    # print(score_list)

                    # Play it safe; exactly six scores.
                    if md.operator_tree:
                        score_list = [0,0,0] + score_list
                    else:
                        score_list = score_list + [0,0,0]
                    queries[current_query_name]["candidates"][formula_id] = {
                        "slt_str": parts[3] if not md.operator_tree else "",
                        "opt_str": parts[3] if md.operator_tree else "",
                        "scores" : score_list
                    }
                else:
                    # Update an entry, vs. create one.
                    current_slt = queries[current_query_name]["candidates"][formula_id]\
                            ["slt_str"]
                    current_opt = queries[current_query_name]["candidates"][formula_id]\
                            ["opt_str"]
                    new_scores = queries[current_query_name]["candidates"][formula_id]\
                            ["scores"]

                    # Copy scores at appropriate location.
                    score_list = list(map(float, parts[4].replace(" ","").replace("[","")\
                            .replace("]","").split(",")))
                    score_offset = 0
                    if md.operator_tree:
                        score_offset = 3
                    for score in score_list:
                        new_scores[score_offset] = score
                        score_offset += 1

                    queries[current_query_name]["candidates"][formula_id] = {
                        "slt_str": parts[3] if not md.operator_tree else \
                                current_slt,
                        "opt_str": parts[3] if md.operator_tree else \
                                current_opt,
                        "scores" : new_scores
                               
                    }


        print("")

    return queries

def group_result_trees(queries):
    groups = {}
    # RZ: mod
    for query_id in sorted(queries.keys(), key=lambda x: int(re.split("\.|-",x)[-1])):
        time1 = time.time()
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
        time2 = time.time()
        print(query_id)
        print(time2 - time1)
    return groups


# RZ: NOTE - these are the average NTCIR (cross-validated) bias + 6 weights for
# SLT and OPT scoring vector elements.
# 0.2930	0.0861	-0.1694	1.8469	0.9657	-0.0153	-0.3301

# This writes a trec_eval - style flat file for evaluation.
def save_results(queries, output_file):
    out_lines = []
    for query_id in sorted(queries.keys(), key=lambda x: int(re.split("\.|-",x)[-1])):
        candidates = queries[query_id]["candidates"]
     
        cand_lines = []
        for formula_id in candidates:
            line = [str(query_id), str(formula_id)] 

            # Get dot product of Tangent-s average regressed weights from NTCIR-12 and
            # 6 SLT/OPT score (+ bias term)
            scores = [1] +  [ score for score in candidates[formula_id]["scores"]]
            weights = [ 0.2930,	0.0861,	-0.1694, 1.8469, 0.9657, -0.0153, -0.3301 ]
            weighted_score = sum(pair[0] * pair[1] for pair in zip(scores, weights))

            line += [ str(weighted_score) ]
            # UNCOMMENT LINE BELOW TO SEE THE 6 RAW SCORES.
            # line += [str(score) for score in candidates[formula_id]["scores"]]

            #out_lines.append(line)
            cand_lines.append(line)

        # Reverse sort by weighted score to avoid errors.
        out_lines += sorted(cand_lines, key=itemgetter(2), reverse=True)

    out_file = open(output_file, 'w', encoding='utf-8')
    for line in out_lines:
        out_file.write("\t".join(line) + "\n")
    out_file.close()


def main():
    # The goal of this script is to take separate sets of results (usually from the core)
    # and combine them into a single file while computing the set of specified metrics for each ....
    # Output will include each result represented by its unique formula identifier and the corresponding scores
    time.time()
    if len(sys.argv) < 6:
        print("Usage")
        print("    python3 combine_rankings.py output_file cache_file [-r control input_file]")
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
        return

    # input parameters ....
    output_filename = sys.argv[1]
    cache_filename = sys.argv[2]

    # for input result sets and ranking metrics
    result_files, rerank_metrics = process_optional_params(sys.argv[3:])

    # then, for each file, load the results, use cache to avoid reading the sources everytime ....
    print("Processing input result files....", flush=True)
    queries = load_result_files(result_files) # RZ: mod: #, mathml_cache)

    print("Total unique queries found: " + str(len(queries)))
    print("Total matches found per query (might contain multiple instances of same formula)")
    # RZ: mod for ARQMath
    for idx, query_id in enumerate(sorted(queries.keys(), key=lambda x : int(re.split("\.|-",x)[-1]))):
        ending = "\n" if (idx + 1) % 5 == 0 else ""

        # RZ mod.
        offset = re.split("\.|-",query_id)[-1]
        print("#" + offset + " = " + str(len(queries[query_id]["candidates"])) + "\t", end=ending)
    print("")

    # check groups ....
    tree_groups = group_result_trees(queries)
    print("")
    for idx, query_id in enumerate(sorted(queries.keys(), key=lambda x: int(re.split("\.|-",x)[-1]))):
        for tree_group in tree_groups[query_id]:
            if len(tree_group.matches_slt) > 1 and len(tree_group.matches_opt) > 1:
                # found a not 1-to-1 mapping between SLTs and OPTs
                print("Query: " + query_id +\
                    "    SLTs: " + str(len(tree_group.matches_slt)) + "    OPTs: " + str(len(tree_group.matches_opt)))

    print("")

    # Output results
    save_results(queries, output_filename)
    print("Complete!")


if __name__ == '__main__':
    main()
