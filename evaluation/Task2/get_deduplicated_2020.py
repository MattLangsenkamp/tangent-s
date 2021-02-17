import operator
import sys
import os
import csv
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))


def read_latex_files(latex_dir):
    """
    Reading the latex representation of formulas in a dictionary of formula id and latex
    @param latex_dir: the directory in which the latex representations provided by the organizers are located
    @return: dictionary (formula id, latex)
    """
    dic_formula_latex = {}
    for filename in os.listdir(latex_dir):
        with open(latex_dir + filename, mode='r', encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter='\t')
            next(csv_reader)
            for row in csv_reader:
                formula_id = row[0]
                latex = row[4]
                "removes any white space from the formula latex string"
                latex = "".join(latex.split())
                "the formulas in the comments are ignored"
                if row[3] == "comment":
                    continue
                dic_formula_latex[formula_id] = latex
    return dic_formula_latex


def read_slt_file(slt_file_path):
    """
    Reading the formula slt representations in dictionary, returns dictionary (formula id, slt string)
    @param slt_file_path: file path of the slt string provided by the organizers
    @return: dictionary of (formula id, slt string)
    """
    dic_formula_slt = {}
    with open(slt_file_path, mode='r', encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter='\t')
        for row in csv_reader:
            formula_id = row[0]
            slt_string = row[2]
            dic_formula_slt[formula_id] = slt_string
    return dic_formula_slt


def read_qrel_to_dictionary(qrel_file_path):
    """
    Read the qrel file into a dictionary of topic id and list of formula ids
    @param qrel_file_path: qrel file path
    @return: dictionary of (topics id, lst of formula ids)
    """
    res_map = {}
    result_file = open(qrel_file_path, newline='', encoding="utf-8")
    csv_reader = csv.reader(result_file, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
    for row in csv_reader:
        topic_id = row[0]
        formula_id = row[2]
        if topic_id in res_map:
            res_map[topic_id].append(formula_id)
        else:
            res_map[topic_id] = [formula_id]
    return res_map


def order_by_score(file_name):
    """
    Takes in the retrieval result file, reads the files and return the retrieval results sorted by scores.
    @param file_name: retrieval results file
    @return: dictionary of (topic id, dictionary (formula id, score)) and the run id.
    """
    res = {}
    result_file = open(file_name, newline='', encoding="utf-8")
    csv_reader = csv.reader(result_file, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
    for row in csv_reader:
        topic_id = row[0]
        formula_id = row[1]
        score = float(row[4])
        run_id = row[5]
        if topic_id in res:
            res[topic_id][formula_id] = score
        else:
            res[topic_id] = {formula_id: score}

    for topic_id in res:
        sorted_dict = dict(sorted(res[topic_id].items(), key=operator.itemgetter(1), reverse=True))
        res[topic_id] = sorted_dict

    return res, run_id


def read_visual_file(visual_ids_file_path):
    dic_formula_visual_id = {}
    with open(visual_ids_file_path, mode='r', encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter='\t')
        for row in csv_reader:
            visual_id = row[0]
            formula_ids = row[1:]
            for formula_id in formula_ids:
                dic_formula_visual_id[formula_id] = visual_id
    return dic_formula_visual_id


def convert_result_files_to_trec(submission_dir, qrel_result_dic, final_res_prime, dic_formula_id_latex,
                                 dic_formula_id_slt, visual_ids_file_path):
    """
    this method reads all the results files and convert them to trec_format, both with and without unjudged
    @param submission_dir: the directory in which the submitted run files exist
    @param qrel_result_dic: the qrel dictionary
    @param final_res_prime: deduplicated directory to save files
    @param dic_formula_id_latex: dictionary of formula id, latex string
    @param dic_formula_id_slt: dictionary of formula id, slt string
    @param visual_ids_file_path: path to visual formula id file
    """
    visual_map = read_visual_file(visual_ids_file_path)
    for file in os.listdir(submission_dir):
        result_file = open(final_res_prime + file, "w", newline='', encoding="utf-8")
        csv_writer = csv.writer(result_file, delimiter='\t', quoting=csv.QUOTE_MINIMAL)

        "sorting the retrieval results based on the scores"
        ordered_results_by_score, run_id = order_by_score(submission_dir + file)
        for topic_id in ordered_results_by_score:

            "ignoring the topics that are not in the qrel file"
            if topic_id not in qrel_result_dic:
                continue

            rank = 1
            "list used to check if the formula has been visited before by comparing the slt string"
            visited_slts = []
            "list used to check if the formula has been visited before by comparing the latex string"
            visited_latexs = []

            for formula_id in ordered_results_by_score[topic_id]:
                "If the formula is not in the qrel will ignore it"
                if formula_id not in qrel_result_dic[topic_id]:
                    continue
                "Check if the slt string is available for this formula"
                if formula_id in dic_formula_id_slt:
                    slt = dic_formula_id_slt[formula_id]
                    "check if the formula is visited before"
                    if slt in visited_slts:
                        continue
                    "if the formula is not visited before will add it to visited list"
                    visited_slts.append(slt)
                    csv_writer.writerow([str(topic_id), "Q0", str(visual_map[formula_id]), str(rank),
                                         str(ordered_results_by_score[topic_id][formula_id]), str(run_id)])
                elif formula_id in dic_formula_id_latex:
                    latex = dic_formula_id_latex[formula_id]
                    if latex in visited_latexs:
                        continue
                    visited_latexs.append(latex)
                    csv_writer.writerow([str(topic_id), "Q0", str(visual_map[formula_id]), str(rank),
                                         str(ordered_results_by_score[topic_id][formula_id]), str(run_id)])
                rank += 1
        result_file.close()


def main():
    """
    sample_command:
    python get_deduplicated_2020.py -sub ./sub/ -de ./deduplicated/ -lat /home/mattlangsenkamp/Documents/dprl/latex_representation_v2/ -slt formulas_slt_string.tsv -qre qrel_task2.tsv -v qrel_official_visual_ids_2020.tsv
    """
    parser = argparse.ArgumentParser(description='Takes in the qrel file and the original submitted file to arqmath'
                                                 'and creates the deduplicated files')

    parser.add_argument('-sub', help='Directory path in which there are the submitted files', required=True)
    parser.add_argument('-de', help='Directory path to save deduplicated files', required=True)
    parser.add_argument('-lat', help='formula latex representation directory', required=True)
    parser.add_argument('-slt', help='slt string of formulas file path', required=True)
    parser.add_argument('-qre', help='qrel file path', required=True)
    parser.add_argument('-v', help='path to the visual file', required=True)
    args = vars(parser.parse_args())

    qrel_file_path = args['qre']
    qrel_dictionary = read_qrel_to_dictionary(qrel_file_path)
    latex_dir = args['lat']
    slt_string_file = args['slt']
    dic_formula_id_latex = read_latex_files(latex_dir)
    dic_formula_id_slt = read_slt_file(slt_string_file)
    source_submitted_files_dir = args['sub']
    visual_file_path = args['v']
    destination_trec_formattd_de_duplicated_dir = args['de']
    convert_result_files_to_trec(source_submitted_files_dir, qrel_dictionary,
                                 destination_trec_formattd_de_duplicated_dir
                                 , dic_formula_id_latex, dic_formula_id_slt, visual_file_path)


if __name__ == "__main__":
    main()
