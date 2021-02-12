import csv
import os


def read_result_file(file_path):
    result = {}
    with open(file_path, newline='') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter='\t')
        for row in csv_reader:
            topic_id = row[0]
            formula_id = row[1]
            score = float(row[2])
            if topic_id in result:
                result[topic_id][formula_id] = score
            else:
                result[topic_id] = {formula_id: score}
    return result


def read_latex_files(latex_dir):
    result = {}
    for filename in os.listdir(latex_dir):
        with open(latex_dir + filename, mode='r', encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter='\t')
            next(csv_reader)
            for row in csv_reader:
                formula_id = row[0]
                post_id = row[1]
                if row[3] == "comment":
                    continue
                result[formula_id] = post_id
    return result


def get_top_1000(retrieval_results, dic_formula_id_to_answer_id):
    retrieval_results = {k: v for k, v in sorted(retrieval_results.items(), key=lambda item: item[1], reverse=True)}
    result = {}
    for formula_id in retrieval_results:
        if formula_id not in dic_formula_id_to_answer_id:
            continue
        answer_id = dic_formula_id_to_answer_id[formula_id]
        result[answer_id] = retrieval_results[formula_id]
    return {k: v for k, v in sorted(result.items(), key=lambda item: item[1], reverse=True)}


def main():
    dic_formula_id_to_answer_id = read_latex_files("/home/mattlangsenkamp/Documents/dprl/latex_representation_v2/")
    tangent_s = read_result_file("/home/mattlangsenkamp/Documents/dprl/tangent-s/results/arq-slt-opt-results.tsv")
    csv_file_path = "TangentS_Res_Task1-matt"
    result_file = open(csv_file_path, "w", newline='', encoding="utf-8")
    csv_writer = csv.writer(result_file, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
    for topic_id in tangent_s:
        rank = 1
        retrieval_results = tangent_s[topic_id]
        dic_retrieved_answer_id_score = get_top_1000(retrieval_results, dic_formula_id_to_answer_id)
        for answer_id in dic_retrieved_answer_id_score:
            csv_writer.writerow(
                [str(topic_id), str(answer_id), str(rank), str(dic_retrieved_answer_id_score[answer_id]), "Tangent_S"])
            rank += 1
            if rank > 1000:
                break

main()