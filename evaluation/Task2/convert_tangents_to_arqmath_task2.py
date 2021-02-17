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


def convert_tangents_arqmath(tangent_s_result):
    """
    Convert TangentS results to ARQMath format by converting the formula ids to post ids
    @param tangent_s_result: dictionary representing tangents results
    @return: sorted arqmath format result
    """
    arq_math_result = {}
    for topic_id in tangent_s_result:
        retrieval_result = tangent_s_result[topic_id]
        temp_dic = {}
        for formula_id in retrieval_result:
            temp_dic[formula_id] = retrieval_result[formula_id]
        temp_dic = {k: v for k, v in sorted(temp_dic.items(), key=lambda item: item[1], reverse=True)}
        arq_math_result[topic_id] = temp_dic
    return arq_math_result


def main():
    """
    example: python3 convert_tangents_to_arqmath_task2.py -res "slt-opt-combined.tsv"
    -arq "arq_math_tangents.tsv"
    @return:
    """
    parser = argparse.ArgumentParser(description='Convert TangentS resutls to ARQMath format for ARQMath Task 2')

    parser.add_argument('-res', help='Tangents result file', required=True)
    parser.add_argument('-arq', help='Arqmath format retsult file', required=True)

    args = vars(parser.parse_args())
    tangents_result_file = args['res']
    arqmath_result_file = args['arq']

    tangent_s_result = read_result_file(tangents_result_file)
    arq_math_result = convert_tangents_arqmath(tangent_s_result)

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
