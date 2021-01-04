
import io
import os
import sys
import codecs
import csv
import xml
import pickle

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
# from TangentS.math.symbol_tree import SymbolTree
from TangentS.utility.control import Control
from TangentS.ranking.mathml_cache import MathMLCache
from TangentS.math.math_document import MathDocument

def convert_from_tsv_to_trec(tsv_lines, math_doc, mathml_cache, run_name, best_only, max_k):
    result_lines = []

    current_query = None
    result_rank = 1

    top_expression_per_doc = {}
    unique_formula_ids = {}

    score_rank = 0
    last_score = None

    for line in tsv_lines:
        if len(line) < 2:
            continue

        if line[0] == "Q":
            current_query = line[1]
            result_rank = 1
            score_rank = 0
            last_score = None

            print("Processing: " + current_query.strip(), end="\r", flush=True)

            # new query, reset the top expression per document found ..
            top_expression_per_doc = {}
            unique_formula_ids = {}
        elif line[0] == "R":
            # (on input)
            # R	doc_id	offset	tree	score
            doc_id = int(line[1])
            location = int(line[2])
            expression = line[3]
            score = line[4]

            if 0 <= max_k < result_rank:
                # ignore additional entries for current query once the max K has been reached ....
                continue

            if best_only and doc_id in top_expression_per_doc and top_expression_per_doc[doc_id] != expression:
                # the document has been seen before for this query, and current expression
                # is not identical to the first (top) match, then ignore!
                continue

            if not doc_id in top_expression_per_doc:
                # mark current expression (first match) as top match for this document
                top_expression_per_doc[doc_id] = expression

            if score != last_score:
                # next score in rank, assign new final score ...
                score_rank += 1
                last_score = score

            TREC_score = 1.0 / score_rank

            doc_name = math_doc.find_doc_file(doc_id)
            doc_short_name = doc_name.split("/")[-1]
            doc_short_name = ".".join(doc_short_name.split(".")[:-1])
            if doc_name is None:
                raise Exception("Invalid Control File")

            mathml = mathml_cache.get(doc_id, location, expression)

            elem_content = io.StringIO(mathml)  # treat the string as if a file
            root = xml.etree.ElementTree.parse(elem_content).getroot()

            if ((len(root.attrib) == 0) or (root.attrib["id"] != doc_short_name + ":" + str(location)) or
                (root.attrib["id"] in unique_formula_ids)):
                # get mathml from cache again, this time forcing update for this location ...
                mathml = mathml_cache.get(doc_id, location, expression, True)

                elem_content = io.StringIO(mathml)  # treat the string as if a file
                root = xml.etree.ElementTree.parse(elem_content).getroot()

            formula_id = root.attrib["id"]
            # remove ./ prefix left behind in some documents....
            if formula_id[0:2] == "./":
                formula_id = formula_id[2:]

            if not formula_id in unique_formula_ids:
                unique_formula_ids[formula_id] = True
            else:
                raise Exception("Formula ID repeated: " + doc_name + " (" + str(doc_id) + ") - " + str(location) +
                                " (" + expression + ", " + formula_id + ")")

            # (on output)
            # query_id  unused doc_name:formula_id rank score run_name
            output_line = [current_query, "1", formula_id, str(result_rank), str(TREC_score), run_name]
            result_rank += 1

            result_lines.append(output_line)

    print("")

    return result_lines

def main():
    if len(sys.argv) < 7:
        print("Usage")
        print("\tpython3 convert_tsv_to_TREC_format.py control input_results output_results run_name best_only max_k")
        print("")
        print("Where:")
        print("\tcontrol:\tPath to tangent control file")
        print("\tinput_results:\tPath to input tsv results file")
        print("\toutput_results:\tPath to output TREC results file")
        print("\trun_name:\tName of the run in input file")
        print("\tbest_only:\tSave only top expression per document")
        print("\tMax_K:\t\tMaximum Number of results to output per query (<0 - unlimited)")
        print("")
        return

    control_filename = sys.argv[1]
    input_filename = sys.argv[2]
    output_filename = sys.argv[3]
    run_name = sys.argv[4]
    try:
        best_only = int(sys.argv[5]) > 0
    except:
        print("Invalid value for best_only")
        return

    try:
        max_k = int(sys.argv[6])
    except:
        print("Invalid value for max k")
        return

    # read the control file ...
    control = Control(control_filename)  # control file name (after indexing)
    math_doc = MathDocument(control)

    # read mathml cache file
    mathml_cache_file = control_filename + ".retrieval_2.cache"
    if not os.path.exists(mathml_cache_file):
        mathml_cache = MathMLCache(control_filename)
    else:
        cache_file = open(mathml_cache_file, "rb")
        mathml_cache = pickle.load(cache_file)
        cache_file.close()

    # load original file with results ...
    in_file = open(input_filename, 'r', newline='', encoding='utf-8')
    reader = csv.reader(in_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
    lines = [row for row in reader]
    in_file.close()

    # convert into TREC tool format
    trec_lines = convert_from_tsv_to_trec(lines, math_doc, mathml_cache, run_name, best_only, max_k)

    # save updated cache ....
    cache_file = open(mathml_cache_file, "wb")
    pickle.dump(mathml_cache, cache_file, pickle.HIGHEST_PROTOCOL)
    cache_file.close()

    # save results
    out_file = open(output_filename, 'w', encoding='utf-8')
    for line in trec_lines:
        out_file.write(" ".join(line) + "\n")
    out_file.close()

    print("Finished!")



if __name__ == "__main__":
    if sys.stdout.encoding != 'utf8':
        sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf8':
        sys.stderr = codecs.getwriter('utf8')(sys.stderr.buffer, 'strict')

    main()