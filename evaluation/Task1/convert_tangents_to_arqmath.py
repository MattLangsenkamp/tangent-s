import argparse
import csv
import os


def read_result_file(file_path):
    """
    Reading Tangent-S combined result file. Note that in Tangent-S we get formula ids not post ids
    @param file_path: file path to Tangent-S results
    @return: dictionary of topic ids and results. results is dictionary of formula id and their score.
    """
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
    """
    Reading latex tsv files to create map of fomrula id to post ids -- note that Tangent-S return formula ids
    @param latex_dir: directory in which latex tsv files are located
    @return: dictionary of formula id : post id
    """
    result = {}
    for filename in os.listdir(latex_dir):
        with open(latex_dir + filename, mode='r', encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter='\t')
            next(csv_reader)
            for row in csv_reader:
                formula_id = row[0]
                post_id = row[1]
                if row[3] != "answer":
                    continue
                result[formula_id] = post_id
    return result


def convert_tangents_arqmath(tangent_s_result, dic_formula_id_to_answer_id):
    """
    Convert TangentS results to ARQMath format by converting the formula ids to post ids
    @param tangent_s_result: dictionary representing tangents results
    @param dic_formula_id_to_answer_id: dictionary of formula id post ids.
    @return: sorted arqmath format result
    """
    arq_math_result = {}
    for topic_id in tangent_s_result:
        retrieval_result = tangent_s_result[topic_id]
        temp_dic = {}
        for formula_id in retrieval_result:
            if formula_id not in dic_formula_id_to_answer_id:
                continue
            answer_id = dic_formula_id_to_answer_id[formula_id]
            temp_dic[answer_id] = retrieval_result[formula_id]
        temp_dic = {k: v for k, v in sorted(temp_dic.items(), key=lambda item: item[1], reverse=True)}
        arq_math_result[topic_id] = temp_dic
    return arq_math_result


def main():
    """
    example: python3 get_tangents_results_task1.py -ldir "/home/bm3302/latex_representation_v2/" -res "slt-opt-combined.tsv"
    -arq "arq_math_tangents.tsv"
    @return:
    """
    parser = argparse.ArgumentParser(description='Convert TangentS resutls to ARQMath format for ARQMath Task 1')

    parser.add_argument('-ldir', help='latex files directory', required=True)
    parser.add_argument('-res', help='Tangents result file', required=True)
    parser.add_argument('-arq', help='Arqmath format retsult file', required=True)

    args = vars(parser.parse_args())
    latex_files_directory = args['ldir']
    tangents_result_file = args['res']
    arqmath_result_file = args['arq']

    dic_formula_id_to_answer_id = read_latex_files(latex_files_directory)
    tangent_s_result = read_result_file(tangents_result_file)
    arq_math_result = convert_tangents_arqmath(tangent_s_result, dic_formula_id_to_answer_id)

    csv_file_path = arqmath_result_file
    result_file = open(csv_file_path, "w", newline='', encoding="utf-8")
    csv_writer = csv.writer(result_file, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
    for topic_id in arq_math_result:
        rank = 1
        retrieval_results = arq_math_result[topic_id]
        for answer_id in retrieval_results:
            csv_writer.writerow(
                [str(topic_id), str(answer_id), str(rank), str(retrieval_results[answer_id]), "Tangent_S"])
            rank += 1
            if rank > 1001:
                break


if __name__ == "__main__":
    main()
