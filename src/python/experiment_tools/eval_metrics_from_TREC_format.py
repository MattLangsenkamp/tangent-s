
import re
import sys
import csv
import codecs
import math

def load_file(filename, separator_pattern):
    input_file = open(filename, "r", encoding="utf-8")
    lines = input_file.readlines()
    input_file.close()

    content = []
    lines_splitted = False

    for line in lines:
        parts = re.split(separator_pattern, line)
        #parts = line.strip().split(separator)
        if len(parts) > 0 and len(line) > 0:
            content.append(parts)

        if len(parts) >= 2:
            lines_splitted = True

    return content, lines_splitted


def group_relevance(raw_relevance):

    groups = {}
    for sample in raw_relevance:
        # Query, Document, Relevance, Annotator, X?
        query_id = sample[0]
        document_id = sample[1]

        if sample[2] == "Not-Relevant":
            relevance = 0
        elif sample[2] == "Partially-Relevant":
            relevance = 1
        elif sample[2] == "Relevant":
            relevance = 2
        else:
            raise Exception("Invalid Relevance value found: " + sample[2])

        if not query_id in groups:
            groups[query_id] = {}

        if not document_id in groups[query_id]:
            groups[query_id][document_id] = []

        groups[query_id][document_id].append(relevance)

    return groups


def show_relevance_group_stats(groups):
    query_sizes = []
    docs_by_assesments = []
    total_docs = 0

    for query_id in groups:
        query_offset = int(query_id.split("-")[-1])
        query_sizes.append((query_offset, len(groups[query_id])))

        total_docs += len(groups[query_id])

        for document_id in groups[query_id]:
            while len(docs_by_assesments) < len(groups[query_id][document_id]):
                docs_by_assesments.append(0)

            docs_by_assesments[len(groups[query_id][document_id]) - 1] += 1
    query_sizes = sorted(query_sizes)

    print("Documents evaluated per query: ")
    step_size = 5
    for i in range(0,len(groups),step_size):
        print("\t\t".join([str(offset) + ": " + str(count) for offset, count in query_sizes[i:i+step_size]]))

    print("Total queries: " + str(len(groups)))
    print("Total documents: " + str(total_docs))
    for i in range(len(docs_by_assesments)):
        if docs_by_assesments[i] > 0:
            print("Documents with " + str(i + 1) + " rating(S): " + str(docs_by_assesments[i]))

def compute_doc_relevance(relevance_groups):
    doc_relevance = {}

    for query_id in relevance_groups:
        doc_relevance[query_id] = {}

        for document_id in relevance_groups[query_id]:
            values = relevance_groups[query_id][document_id]

            # normalization
            weight = 2.0 / len(values)

            final = 0.0
            for value in values:
                final += value * weight

            doc_relevance[query_id][document_id] = final

    return doc_relevance


def group_results(raw_results, sort_results):
    # Query, one?, doc_id, rank, score, group
    results_groups = {}
    for result in raw_results:
        query_id = result[0]
        document_id = result[2]
        rank = int(result[3])
        score = float(result[4])

        if query_id not in results_groups:
            results_groups[query_id] = {}

        if not sort_results:
            # use given rank directly
            results_groups[query_id][rank] = document_id
        else:
            if score in results_groups[query_id]:
                results_groups[query_id][score].append(document_id)
            else:
                results_groups[query_id][score] = [document_id]

    if sort_results:
        for query_id in results_groups:
            docs_per_score = results_groups[query_id]

            all_scores = sorted(list(docs_per_score.keys()), reverse=True)

            reranked_results = []
            for score in all_scores:
                reranked_results += sorted(docs_per_score[score])

            results_groups[query_id] = {}
            for idx, doc_id in enumerate(reranked_results):
                results_groups[query_id][idx + 1] = doc_id

    return results_groups


def match_relevance(results_group, doc_relevance):
    results_relevance = {}
    for query_id in results_group:
        results_relevance[query_id] = {}
        for rank in results_group[query_id]:
            document_id = results_group[query_id][rank]

            if document_id in doc_relevance[query_id]:
                results_relevance[query_id][rank] = doc_relevance[query_id][document_id]
            else:
                results_relevance[query_id][rank] = None

    return results_relevance


def sort_by_relevance(results_groups, results_relevance):
    sorted_relevance = {}
    for query_id in results_relevance:
        tempo_res = []
        for rank in results_relevance[query_id]:
            if results_relevance[query_id][rank] is None:
                # unknow, assume irrelevant
                tempo_res.append(0.0)
            else:
                tempo_res.append(results_relevance[query_id][rank])

        tempo_res = sorted(tempo_res, reverse=True)
        sorted_relevance[query_id] = {rank + 1: relevance for rank, relevance in enumerate(tempo_res)}
    
    return sorted_relevance

def ideal_relevance(doc_relevance):
    ideal_relevance = {}

    for query_id in doc_relevance:
        ideal_relevance[query_id] = {}

        docs = [ (doc_relevance[query_id][doc_id], doc_id) for doc_id in doc_relevance[query_id]]
        docs = sorted(docs, reverse=True)

        for rank, (score, doc_id) in enumerate(docs):
            ideal_relevance[query_id][rank + 1] = score
        
    return ideal_relevance


def show_precision_at_topk(results_relevance, top_k, min_relevance, query_groups, show_detail):
    query_offsets = sorted([(int(query_id.split("-")[-1]), query_id) for query_id in results_relevance])

    avg_prec = 0.0
    group_index = {}
    group_avg_prec = {}
    if query_groups is not None:
        for group_name in query_groups:
            group_avg_prec[group_name] = 0.0

            for query_id in query_groups[group_name]:
                group_index[query_id] = group_name        

    total_missing = 0
    detail_string = ""
    for offset, query_id in query_offsets:
        current_values = []
        for rank in range(top_k):
            if rank + 1 in results_relevance[query_id]:
                if results_relevance[query_id][rank + 1] is not None:
                    current_values.append(results_relevance[query_id][rank + 1])
                else:
                    # not evaluated ...
                    current_values.append(-2.0)
            else:
                # print("Missing Rank {0:d} for Query {1:s}".format(rank + 1, query_id))
                current_values.append(-1.0)

        count_rel = 0
        for value in current_values:
            if value < 0.0:
                total_missing += 1
            elif value >= min_relevance:
                count_rel += 1

        precision = count_rel / float(top_k)
        avg_prec += precision

        if query_groups is not None:
            group_avg_prec[group_index[str(offset)]] += precision

        if show_detail:
            str_values = ["{0:.1f}".format(value) for value in current_values]
            detail_string += str(offset) + "\t({0:.5f})\t".format(precision) + "\t".join(str_values) + "\n"

    base_str = "P @ {0:d}:\t{1:.4f}".format(top_k, float(avg_prec) / len(query_offsets))

    if query_groups is not None:
        group_str = ""
        for group_name in sorted(query_groups.keys()):
            p_at_k = group_avg_prec[group_name] / float(len(query_groups[group_name]))
            group_str += "\t{0:.4f}".format(p_at_k)
    else:
        group_str = ""

    print(base_str + group_str)

    if show_detail:
        print(detail_string)

    return total_missing

def show_bpref_topk(results_relevance, ideal_results, top_k, min_relevance, query_groups, show_detail):
    r_sum = 0.0

    """
    non_rel_so_far = 0
    for r, val in enumerate(ranking):
        if val == 0:
            non_rel_so_far += 1
        else:
            if non_rel_so_far > 0:
                r_sum += 1.0 - min(non_rel_so_far, pref_top_R_nonrel_num) / min(num_non_relevant, pref_top_R_nonrel_num)
            else:
                r_sum += 1.0

    return r_sum / num_rel
    """
    pass



def read_query_groups(groups_filename):
    input_file = open(groups_filename, 'r', encoding="utf-8")
    all_lines = input_file.readlines()
    input_file.close()
    
    groups = {}
    for line in all_lines:
        parts = line.strip().split(",")
        
        if len(parts) == 2:
            group_name, query_id = parts[1], parts[0]

            if not group_name in groups:
                groups[group_name] = []

            groups[group_name].append(query_id)
    
    return groups

def DCG(values, max_k):
    result = 0.0
    if len(values) > 0:
        result = values[0]

        for k in range(1, min(max_k, len(values))):
            result += values[k] / math.log(k + 1, 2)

    return result

def show_nDCG_at_topk(results_relevance, ideal_results, top_k, query_groups, show_detail):
    query_offsets = sorted([(int(query_id.split("-")[-1]), query_id) for query_id in results_relevance])

    group_index = {}
    group_avg_nDCG = {}
    if query_groups is not None:
        for group_name in query_groups:
            group_avg_nDCG[group_name] = 0.0

            for query_id in query_groups[group_name]:
                group_index[query_id] = group_name

    avg_nDCG = 0.0
    detail_string = ""
    for offset, query_id in query_offsets:
        current_values = []
        ideal_values = []
        for rank in range(top_k):
            if rank + 1 in results_relevance[query_id]:
                if results_relevance[query_id][rank + 1] is not None:
                    current_values.append(results_relevance[query_id][rank + 1])
                else:
                    # not evaluated ...
                    current_values.append(0.0)
            else:
                # missing rank, could be after end of results list
                current_values.append(0.0)


            if rank + 1 in ideal_results[query_id]:
                if ideal_results[query_id][rank + 1] is not None:
                    ideal_values.append(ideal_results[query_id][rank + 1])
                else:
                    # not evaluated ...
                    ideal_values.append(0.0)
            else:
                # missing rank, could be after end of results list
                ideal_values.append(0.0)

        rank_DCG = DCG(current_values, top_k)
        ideal_DCG = DCG(ideal_values, top_k)

        if ideal_DCG > 0.0:
            nDCG = rank_DCG / ideal_DCG
        else:
            nDCG = 1.0

        avg_nDCG += nDCG
        if query_groups is not None:
            group_avg_nDCG[group_index[str(offset)]] += nDCG

        if show_detail:
            str_values = ["{0:.1f}".format(value) for value in current_values]
            detail_string += str(offset) + "\t({0:.5f})\t".format(nDCG) + "\t".join(str_values) + "\n"

    base_str = "nDCG@ {0:d}:\t{1:.4f}".format(top_k, float(avg_nDCG) / len(query_offsets))

    if query_groups is not None:
        group_str = ""
        for group_name in sorted(query_groups.keys()):
            nDCG_at_k = group_avg_nDCG[group_name] / float(len(query_groups[group_name]))
            group_str += "\t{0:.4f}".format(nDCG_at_k)
    else:
        group_str = ""

    print(base_str + group_str)

    if show_detail:
        print(detail_string)

def show_table_headers(metric_name, query_groups):
    if query_groups is not None:
        group_str = "\t".join([group_name for group_name in sorted(query_groups.keys())])
    else:
        group_str = ""

    print("\n\n" + metric_name + "\tAll\t" + group_str)

def main():
    if len(sys.argv) < 7:
        print("Usage:")
        print("\tpython eval_metrics_from_TREC_format.py relevance results sort top_k min_rel show_detail [groups]")
        print("")
        print("Where")
        print("")
        print("\trelevance:\tFile with non-aggregated relevance assessments")
        print("\tresults:\tResults to evaluate in TREC file format")
        print("\tsort:\t\tIf positive, ties will be broken by document name")
        print("\ttop_k:\t\tTop-K results to consider for metrics")
        print("\tmin_rel:\tMinimum relevance value for relevant documents")
        print("\tshow_detail:\tShow per query evaluation results")
        print("\tgroups:\t\tOptional. File with query groups")
        return

    # general parameters
    SHOW_GROUPS = False
    SHOW_DOCS_EVAL_PER_QUERY = False
    SHOW_IDEAL_P_AT_K = False
    SHOW_BEST_P_AT_K = False
    SHOW_P_AT_K = False
    SHOW_NDCG_AT_K = True

    relevance_filename = sys.argv[1]
    results_filename = sys.argv[2]

    try:
        sort_results = int(sys.argv[3]) > 0
    except:
        print("Invalid value for sort")
        return

    try:
        top_k = int(sys.argv[4])
        if top_k < 1:
            print("Invalid value for top_k")
            return
    except:
        print("Invalid value for top_k")
        return

    try:
        min_rel = float(sys.argv[5])
    except:
        print("Invalid value for min relevance")
        return

    try:
        show_detail = int(sys.argv[6]) > 0
    except:
        print("Invalid value for show_detail")
        return

    if len(sys.argv) >= 8:
        query_groups = read_query_groups(sys.argv[7])
        if SHOW_GROUPS:
            print(query_groups)
    else:
        query_groups = None

    # load and show relevance assessment file
    raw_relevance, lines_splitted = load_file(relevance_filename, " |\t")
    relevance_groups = group_relevance(raw_relevance)

    if SHOW_DOCS_EVAL_PER_QUERY:
        show_relevance_group_stats(relevance_groups)

    doc_relevance = compute_doc_relevance(relevance_groups)
    
    # load results file
    raw_results, lines_splitted = load_file(results_filename, " |\t")

    results_groups = group_results(raw_results, sort_results)

    results_relevance = match_relevance(results_groups, doc_relevance)
    best_relevance = sort_by_relevance(results_groups, results_relevance)

    ideal_results = ideal_relevance(doc_relevance)

    if SHOW_IDEAL_P_AT_K:
        show_table_headers("Ideal P@K", query_groups)
        for current_k in range(1, top_k  + 1):
            not_rated = show_precision_at_topk(ideal_results, current_k, min_rel, query_groups, show_detail and current_k == top_k)
        print("Documents not judged: " + str(not_rated))

    if SHOW_BEST_P_AT_K:
        show_table_headers("Best P@K", query_groups)
        for current_k in range(1, top_k + 1):
            not_rated = show_precision_at_topk(best_relevance, current_k, min_rel, query_groups, show_detail and current_k == top_k)
        print("Documents not judged: " + str(not_rated))

    if SHOW_P_AT_K:
        show_table_headers("P@K", query_groups)
        for current_k in range(1, top_k + 1):
            not_rated = show_precision_at_topk(results_relevance, current_k, min_rel, query_groups, show_detail and current_k == top_k)
        print("Documents not judged: " + str(not_rated))

    # print("\n\nRaw bpref @ K Values")
    # show_bpref_topk(results_relevance, ideal_results, top_k, min_rel, query_groups, show_detail)

    # print("\n\nBest bpref @ K Values")
    # show_bpref_topk(best_relevance, ideal_results, top_k, min_rel, query_groups, show_detail)
    if SHOW_NDCG_AT_K:
        show_table_headers("nDCG@K", query_groups)
        for current_k in range(1, top_k + 1):
            show_nDCG_at_topk(results_relevance, ideal_results, current_k, query_groups, show_detail and current_k == top_k)

    print("Finished")

if __name__ == "__main__":
    if sys.stdout.encoding != 'utf8':
      sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf8':
      sys.stderr = codecs.getwriter('utf8')(sys.stderr.buffer, 'strict')
      
    main()
