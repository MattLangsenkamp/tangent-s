import argparse


def read_result_file(res1_filepath):
    """
    Reading result files into a dictionary with min-max normalization being applied to scores.
    @param res1_filepath:
    @return:
    """
    file = open(res1_filepath)
    line = file.readline()
    dictionary_result = {}
    while line:
        try:
            res_parts = line.split("\t")
            query_id = res_parts[0]
            answer_id = res_parts[1]
            score = float(res_parts[3])
            if query_id in dictionary_result:
                dictionary_result[query_id][answer_id] = score
            else:
                temp_dic = {answer_id: score}
                dictionary_result[query_id] = temp_dic
            line = file.readline()
        except:
            print(line)
            line = file.readline()
    for query_id in dictionary_result:
        temp_dic = dictionary_result[query_id]
        max_value = max(temp_dic.values())
        min_value = min(temp_dic.values())
        diff = (max_value-min_value)
        if diff == 0:
            diff = 1
            min_value = 0
        for doc_id in temp_dic:
            temp_dic[doc_id] = (temp_dic[doc_id] - min_value) / diff
        temp_dic = {k: v for k, v in sorted(temp_dic.items(), key=lambda item: item[1], reverse=True)}
        dictionary_result[query_id] = temp_dic
    return dictionary_result


def get_combined_result(res_1, res_2):
    temp_dic = res_1.copy()
    for item in res_2:
        if item in temp_dic:
            temp_dic[item] += res_2[item]
        else:
            temp_dic[item] = res_2[item]
    return {k: v for k, v in sorted(temp_dic.items(), key=lambda item: item[1], reverse=True)}


def linear_combination(res1_filepath, res2_filepath, new_result_file):
    """

    @param res1_filepath:
    @param res2_filepath:
    @param new_result_file:
    @return:
    """
    dictionary_result1 = read_result_file(res1_filepath)
    dictionary_result2 = read_result_file(res2_filepath)
    file = open(new_result_file, "w")
    for query_id in dictionary_result1:
        res_1 = dictionary_result1[query_id]
        res_2 = dictionary_result2[query_id]
        combined_result = get_combined_result(res_1, res_2)
        rank = 1
        for item in combined_result:
            if (item in dictionary_result2[query_id]) and (item in dictionary_result1[query_id]):
                print(item)
                print(query_id)
            file.write(str(query_id)+"\t"+str(item)+"\t"+str(rank)+"\t"+str(combined_result[item])+"\tCOMBINED_TAN_S_TF_IDF\n")
            rank += 1
            if rank == 1001:
                break
    file.close()


def main():
    """
        Sample command:
        python linear_combination.py
        -tan TangentS_Res.tsv
        -te tf_idf_task1_final.tsv
        -res combined_tf_idf_tangents
    """
    parser = argparse.ArgumentParser(description='Takes in TangentS and TF-IDF and return the combination of them')

    parser.add_argument('-tan', help='TangentS result file', required=True)
    parser.add_argument('-te', help='TF-IDF result file', required=True)
    parser.add_argument('-res', help='Final combined result')
    args = vars(parser.parse_args())

    tangent_s_result = args['tan']
    tf_idf_result = args['te']
    res_final = args['res']

    linear_combination(tangent_s_result, tf_idf_result, res_final)


if __name__ == "__main__":
    main()
