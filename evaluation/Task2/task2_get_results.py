import os
from subprocess import check_output
import argparse


def calculated_measures(directory, trec_eval_tool_file_path, qrel_file_path):
    result = {}
    submission_files = os.listdir(directory)
    if ".gitkeep" in submission_files: submission_files.remove(".gitkeep")
    for file in submission_files:
        output = check_output([trec_eval_tool_file_path, qrel_file_path, directory+file, "-m", "ndcg"])
        output = output.decode('utf-8')
        ndcg = output.split("\t")[2].strip()
        output = check_output([trec_eval_tool_file_path, qrel_file_path, directory + file, "-l2", "-m", "map"])
        output = output.decode('utf-8')
        map = output.split("\t")[2].strip()
        output = check_output([trec_eval_tool_file_path, qrel_file_path, directory + file, "-l2", "-m", "P"])
        output = output.decode('utf-8').split("\n")[1]
        p_at_10 = output.split("\t")[2].strip()

        submission = file.split(".")[0]
        result[submission] = [ndcg, map, p_at_10]
    return result


def get_result(dir_deduplicated, final_res, trec_eval_tool_file_path, qrel_file_path):
    file_res = open(final_res, "w")
    submission_result = calculated_measures(dir_deduplicated, trec_eval_tool_file_path, qrel_file_path)
    file_res.write("System\tnDCG'\tmAP'\tp@10\n")
    for sub in submission_result:
        file_res.write(
            str(sub) + "\t" + str(submission_result[sub][0]) + "\t" + str(submission_result[sub][1]) + "\t" +
            str(submission_result[sub][2]) + "\n")
    file_res.close()


def main():
    """
    Sample command :
    python task2_get_results.py -eva "trec_eval" -qre "qrel_task2.tsv"
    -de "/home/bm3302/PycharmProjects/ARQMathCode/results/All_Results_Deduplicated/" -res "task2.tsv"
    """
    parser = argparse.ArgumentParser(description='Specify the trec_eval file path, qrel file, '
                                                 'deduplicate results directory and result file file path')

    parser.add_argument('-eva', help='trec_eval tool file path', required=True)
    parser.add_argument('-qre', help='qrel file path', required=True)
    parser.add_argument('-de', help='deduplicated results directory', required=True)
    parser.add_argument('-res', help='evaluation result file', required=True)
    args = vars(parser.parse_args())
    trec_eval_tool = args['eva']
    qre_file_path = args['qre']
    deduplicated_result_dir = args['de']
    evaluation_result_file = args['res']

    get_result(deduplicated_result_dir, evaluation_result_file, trec_eval_tool, qre_file_path)


if __name__ == "__main__":
    main()
