
import re
import os
import sys
import csv
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))

from src.python.utility.control import Control
from src.python.math.math_document import MathDocument
from src.python.math.math_extractor import MathExtractor
from src.python.math.symbol_tree import SymbolTree

def load_trec_format(trec_filename, rel_col, max_k):
    input_file = open(trec_filename, "r")
    input_lines = input_file.readlines()
    input_file.close()

    results_per_query = {}
    input_rank = 1
    for line in input_lines:
        parts = re.split(" |\t", line)

        if len(parts) < rel_col + 1:
            # ignore ...
            continue

        query_name = parts[0].strip()
        formula_id = parts[2].strip()
        relevance = float(parts[rel_col])

        if not query_name in results_per_query:
            results_per_query[query_name] = {}
            input_rank = 1

        if max_k < 0 or len(results_per_query[query_name]) < max_k:
            # add result only if the limit of K hasn't been reached.
            results_per_query[query_name][formula_id] = (input_rank, relevance)
            input_rank += 1

    return results_per_query

def load_query_file(query_filename):
    in_file = open(query_filename, 'r', newline='', encoding='utf-8')
    reader = csv.reader(in_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
    lines = [row for row in reader]
    in_file.close()

    current_query = None
    file_queries = {}
    for parts in lines:
        if len(parts) == 2 and parts[0] == "Q":
            current_query = parts[1]

        if len(parts) == 3 and parts[0] == "E" and current_query is not None:
            file_queries[current_query] = parts[1]

    return file_queries

def identify_ids_per_document(qrels):
    ids_per_doc = {}

    for query_id in qrels:
        for formula_id in qrels[query_id]:
            id_parts = formula_id.split(":")
            doc_name = ":".join(id_parts[:-1])
            final_id = id_parts[-1]

            if not doc_name in ids_per_doc:
                ids_per_doc[doc_name] = [final_id]
            else:
                ids_per_doc[doc_name].append(final_id)

    return ids_per_doc

def doc_names_to_doc_ids(doc_list_filename, doc_names):
    # load the complete list of documents ....
    found_doc_ids = {}
    with open(doc_list_filename, "r", encoding="utf-8") as doc_list_file:
        for doc_id, line in enumerate(doc_list_file):
            filename = line.strip().split("/")[-1]
            doc_name = ".".join(filename.split(".")[:-1])

            if doc_name in doc_names:
                found_doc_ids[doc_name] = doc_id

    return found_doc_ids


def get_document_mathml(math_doc, doc_filename):
    (ext, content) = math_doc.read_doc_file(doc_filename)

    # now, get the mathml for each formula id
    all_mathml = MathExtractor.math_tokens(content)

    per_id_mathml = {}
    for idx, mathml in enumerate(all_mathml):
        parsed_xml = BeautifulSoup(mathml, "lxml")
        math_root = parsed_xml.find("math")  # namespaces have been removed (FWT)

        # ignore math tags without ids
        if math_root.has_attr("id"):
            formula_id = math_root["id"]
            if formula_id[0:2] == "./":
                formula_id = formula_id[2:]

            # [formula_id] = (loc, mathml)
            per_id_mathml[formula_id] = (idx, mathml)

    return per_id_mathml


def get_information_per_formula_id(control, ids_per_doc, doc_ids):
    doc = MathDocument(control)
    is_OPT = control.read("tree_model", num=False, default="layout").lower() == "operator"

    info_per_formula_id = {}
    for doc_idx, doc_name in enumerate(ids_per_doc):
        print("Processing: Document " + str(doc_idx + 1) + " out of " + str(len(ids_per_doc)), end="\r", flush=True)
        # print("Processing: Document " + str(doc_idx + 1) + " out of " + str(len(ids_per_doc)), flush=True)
        doc_id = doc_ids[doc_name]

        # check if extracted doc id is correct...
        doc_filename = doc.find_doc_file(doc_id)
        other_doc_name = ".".join(doc_filename.split("/")[-1].split(".")[:-1])

        # print(doc_filename)
        # print(doc_id)

        # they must match!!
        assert other_doc_name == doc_name

        # [formula_id] = (loc, mathml)
        mathml_per_id = get_document_mathml(doc, doc_filename)

        for final_id in ids_per_doc[doc_name]:
            formula_id = doc_name + ":" + str(final_id)

            if not formula_id in mathml_per_id:
                print("Could not find " + formula_id + " in " + doc_filename)
                return
            else:
                # use loaded mathml ...
                loc, mathml = mathml_per_id[formula_id]

                # parse accordingly to current mode
                if is_OPT:
                    content_mathml = MathExtractor.isolate_cmml(mathml)
                    tree = SymbolTree(MathExtractor.convert_to_semanticsymbol(content_mathml))
                else:
                    presentation_mathml = MathExtractor.isolate_pmml(mathml)
                    tree = SymbolTree(MathExtractor.convert_to_layoutsymbol(presentation_mathml))

                # get string representation
                tree_str = tree.tostring()

                # the final elements required for format conversion: SLT/OPT string, doc_id and location.
                info_per_formula_id[formula_id] = {"tree": tree_str, "doc": doc_id, "loc": loc}

    return info_per_formula_id


def save_qrels_to_tsv_file(output_filename, results, qrels, all_queries, info_per_formula_id):
    out_file = open(output_filename, 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(out_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")

    csv_writer.writerow(["I", "read", "1"])

    for query_id in sorted(results.keys(), key=lambda x: int(x.split("-")[-1])):
        csv_writer.writerow([])

        # write the query ....
        csv_writer.writerow(["Q", query_id])
        csv_writer.writerow(["E", all_queries[query_id]])

        # write all results
        sorted_results = sorted([(results[query_id][formula_id], formula_id) for formula_id in results[query_id]])

        for (rank, relevance), formula_id in sorted_results:
            info = info_per_formula_id[formula_id]
            if formula_id in qrels[query_id]:
                ideal_relevance = qrels[query_id][formula_id][1]
            else:
                ideal_relevance = -1

            csv_writer.writerow(["R", str(info["doc"]), str(info["loc"]), info["tree"], "[{0:f},{1:f}]".format(relevance, ideal_relevance)])

        # write fake stats
        csv_writer.writerow(['I', 'qt', '0'])
        csv_writer.writerow(['I', 'post', '0'])
        csv_writer.writerow(['I', 'postsk', '0'])
        csv_writer.writerow(['I', 'expr', '0'])
        csv_writer.writerow(['I', 'exprsk', '0'])
        csv_writer.writerow(['I', 'doc', '0'])

    # last fake stats on file
    csv_writer.writerow([])
    csv_writer.writerow(['I', 'dictDocIDs', "0"])
    csv_writer.writerow(['I', 'dictExpressions'	"0"])
    csv_writer.writerow(['I', 'dictTerms', "0"])
    csv_writer.writerow(['I', 'dictRelationships', "0"])
    csv_writer.writerow(['I', 'lexTokenTuples', "0", "0", "0", "0"])
    csv_writer.writerow(['I', 'subExprDoc', "0"])
    csv_writer.writerow(['X'])

    out_file.close()

def main():
    if len(sys.argv) < 6:
        print("Usage")
        print("    python3 TREC_format_to_tsv.py trec_input qrels_agg control max_k tsv_output")
        print("")
        print("\ttrec_input:\tPath to input results in TREC format")
        print("\tqrels_agg:\tPath to Aggregated judgments for topics")
        print("\tcontrol:\tPath to control file")
        print("\tmax_k:\t\tMax results to output per query (<0 = Unlimited)")
        print("\ttsv_output:\tPath to store tsv results")
        return

    # parameters
    trec_input_filename = sys.argv[1]
    qrels_filename = sys.argv[2]
    control_filename = sys.argv[3]
    try:
        max_K = int(sys.argv[4])
    except:
        print("Invalid value for max K")
        return

    output_filename = sys.argv[5]

    # load the input ....
    input_results = load_trec_format(trec_input_filename, 4, max_K)

    # read the file containing the qrels
    qrels = load_trec_format(qrels_filename, 3, -1)

    # read the query definition from db-index
    control = Control(control_filename)  # control file name (after indexing)

    # ... query file names
    db_name = control.read("database")
    query_file_ids = control.read("query_fileids")
    query_file_ids = [int(part) for part in query_file_ids.strip()[1:-1].split(",")]

    query_filenames = ["db-index/" + db_name + "_q_" + str(file_id) + ".tsv" for file_id in query_file_ids]

    # ... reading queries ....
    all_queries = {}
    for query_file in query_filenames:
        file_queries = load_query_file(query_file)
        all_queries.update(file_queries)

    # Now, identify all unique formula ids in input results
    ids_per_doc = identify_ids_per_document(input_results)

    print("Total unique docs found in input: " + str(len(ids_per_doc)))
    print("Total unique formulas in input: " + str(sum([len(ids_per_doc[doc_id]) for doc_id in ids_per_doc])))

    # find the corresponding doc_id for each unique document
    print("Findind corresponding doc_id per document ...")
    doc_list_filename = control.read("doc_list")
    doc_ids = doc_names_to_doc_ids(doc_list_filename, list(ids_per_doc.keys()))

    # find the corresponding loc and mathml for each formula id
    print("Extracting and parsing mathml per formula ...")
    info_per_formula_id = get_information_per_formula_id(control, ids_per_doc, doc_ids)

    # generate tsv file
    save_qrels_to_tsv_file(output_filename, input_results, qrels, all_queries, info_per_formula_id)

    print("Finished!")


if __name__ == '__main__':
    main()