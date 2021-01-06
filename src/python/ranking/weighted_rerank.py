# weighted_rerank.py
#
# modification of regression_reranking.py for first ARQMath task.
import sys
import numpy as np
import matplotlib.pyplot as plt
from sklearn import linear_model
from src.python.experiment_tools.qrels_to_tsv import *
from src.python.ranking.regression_reranking import load_topic_groups, separate_training_data


def load_combined_input(input_filename, choose_fields):
    input_file = open(input_filename, "r")
    input_lines = input_file.readlines()
    input_file.close()

    query_results = {}
    for line in input_lines:
        parts = line.split("\t")

        if len(parts) < 3:
            # ignore ...
            continue

        query_name = parts[0].strip()
        formula_id = parts[1].strip()
        scores = [float(part) for part in parts[2:]]

        if not query_name in query_results:
            query_results[query_name] = {}

        if formula_id in query_results[query_name]:
            raise Exception("Formula appears more than once: " + query_name + ", " + formula_id)

        if choose_fields is None:
            # Add all fields
            query_results[query_name][formula_id] = scores
        else:
            query_results[query_name][formula_id] = []
            for field in choose_fields:
                query_results[query_name][formula_id].append(scores[field])


    return query_results


def var_to_relevance_levels_boxplot(x_values, rel_values, graph_dir, var_name):
    #paired = sorted(zip(rel_values, x_values))

    min_rel = int(min(rel_values))
    max_rel = int(max(rel_values))

    # separate values per level of relevance
    list_per_level = [[] for value in range(max_rel - min_rel + 1)]
    for rel, x in zip(rel_values, x_values):
        list_per_level[int(rel) - min_rel].append(x)

    axis_labels = [str(i) for i in range(min_rel, max_rel + 1)]
    plt.figure()
    ret = plt.boxplot(list_per_level,labels=axis_labels, vert=False)
    plt.xlabel(var_name)
    plt.ylabel("Relevance")
    plt.title("Relevance vs " + var_name)
    plt.savefig(graph_dir + "/relevance_vs_" + var_name + ".png")

def main():
    if len(sys.argv) < 6:
        print("Usage")
        print("    python3 regression_reranking.py combined_input weight_file")
        print("                                    output_graphs run_name max_k") 
        print("")
        print("\tcombined_input:\tPath to combined results from different rankings")
        print("\toutput_graphs:\tPath to directory where visualizations will be saved")
        print("\trun_name:\tName for output run")
        print("\tmax_k:\tMax results to output per query. If negative, it will output all")
        print("\tfields:\tOptionally, use a subset of the provided fields")
        print("\t\t\t Must be a set of pairs: field_id field_name")
        return

    # input parameters
    combined_input_filename = sys.argv[1]
    weight_file = sys.argv[2]
    graph_dir = sys.argv[3]
    run_name = sys.argv[4]

    try:
        max_k = int(sys.argv[5])
    except:
        print("Invalid value for parameter max_k")
        return

    # HACK: disable these 'fields'
    chosen_fields = None
    field_names = None

    # load input data
    # .... combined results ...
    comb_results = load_combined_input(combined_input_filename, chosen_fields)
    # .... judgments ...
    qrels = load_aggregated_qrels(judged_qrels_agg_filename)
    # .... topic groups ...
    topic_groups = load_topic_groups(topics_groups_filename)

    # Separate training/testing data for regression using judged documents only ...
    folds_data, folds_labels, count_nonjudged = separate_training_data(comb_results, qrels, topic_groups)

    all_data = []
    all_labels = []
    for fold_idx in range(len(topic_groups)):
        all_data += folds_data[fold_idx]
        all_labels += folds_labels[fold_idx]

    n_features = len(folds_data[0][0])
    print("Total Features: {0:d}".format(n_features))
    print("")

    # RZ: disabling 
    # Do cross-validation
    #print("\tTrain\tTest\tTrain\tTest\t")
    #print("Fold\tSize\tSize\tMSE\tMSE\t" + "\t".join(["W" + str(idx) for idx in range(n_features + 1)]))
    #row_str = "{0:s}\t{1:d}\t{2:d}\t{3:.4f}\t{4:.4f}"

    crossvalidated_predictions = []
    all_train_sizes = []
    all_test_sizes = []
    all_train_mse = []
    all_test_mse = []
    all_coefficients = []
    all_interceptors = []

    final_results = {}
    for fold_idx, topic_group in enumerate(topic_groups):
        # ... Prepare training/testing data ...
        training_data = []
        training_labels = []
        testing_data = []
        testing_labels = []
        for other_idx in range(len(topic_groups)):
            if other_idx == fold_idx:
                # testing data ...
                testing_data += folds_data[other_idx]
                testing_labels += folds_labels[other_idx]
            else:
                # training data ...
                training_data += folds_data[other_idx]
                training_labels += folds_labels[other_idx]

        # ... convert to numpy arrays
        training_data = np.array(training_data)
        training_labels = np.array(training_labels)
        testing_data = np.array(testing_data)
        testing_labels = np.array(testing_labels)

        # ... Train regressor ...
        regressor = linear_model.LinearRegression()
        #regressor = linear_model.Lasso(alpha=0.01)

        # Train the model using the training sets
        regressor.fit(training_data, training_labels)

        # ... Test regressor ...
        testing_pred = regressor.predict(testing_data)
        crossvalidated_predictions += testing_pred.tolist()

        train_mse = np.mean((regressor.predict(training_data) - training_labels) ** 2)
        test_mse = np.mean((testing_pred - testing_labels) ** 2)

        # values for averages ....
        all_train_sizes.append(training_data.shape[0])
        all_test_sizes.append(testing_data.shape[0])
        all_train_mse.append(train_mse)
        all_test_mse.append(test_mse)
        all_interceptors.append(regressor.intercept_)
        all_coefficients.append(regressor.coef_)

        left_part = row_str.format(str(fold_idx + 1), training_data.shape[0], testing_data.shape[0], train_mse, test_mse)
        mid_part = "\t{0:.4f}\t".format(regressor.intercept_)
        right_part = "\t".join(["{0:.4f}".format(regressor.coef_[idx]) for idx in range(n_features)])
        print(left_part + mid_part + right_part)

        # ....Generate results for cross-validation test queries using the trained regressor
        # ....by generating the combined similarity score for all results
        for query_id in topic_group:
            final_results[query_id] = []

            for formula_id in comb_results[query_id]:
                score = regressor.predict(np.array([comb_results[query_id][formula_id]]))
                final_results[query_id].append((score[0], formula_id))

            final_results[query_id] = sorted(final_results[query_id], reverse=True)

    all_coefficients = np.array(all_coefficients)
    all_train_sizes = np.array(all_train_sizes)
    all_test_sizes = np.array(all_test_sizes)
    all_train_mse = np.array(all_train_mse)
    all_test_mse = np.array(all_test_mse)

    left_part = row_str.format("AVG", int(all_train_sizes.mean()), int(all_test_sizes.mean()),
                               all_train_mse.mean(), all_test_mse.mean())
    mid_part = "\t{0:.4f}\t".format(np.array(all_interceptors).mean())


    right_part = "\t".join(["{0:.4f}".format(all_coefficients[:, idx].mean()) for idx in range(n_features)])
    print("=" * 80)
    print(left_part + mid_part + right_part)

    left_part = row_str.format("STDev", int(all_train_sizes.std()), int(all_test_sizes.std()),
                               all_train_mse.std(), all_test_mse.std())

    mid_part = "\t{0:.4f}\t".format(np.array(all_interceptors).std())

    right_part = "\t".join(["{0:.4f}".format(all_coefficients[:, idx].std()) for idx in range(n_features)])
    print(left_part + mid_part + right_part)

    # show labels vs predictions ...
    all_data = np.array(all_data)
    all_labels = np.array(all_labels)

    crossvalidated_predictions = np.array(crossvalidated_predictions)

    var_to_relevance_levels_boxplot(crossvalidated_predictions, all_labels, graph_dir, run_name + " Predicted Relevance")
    if chosen_fields is not None:
        for idx in range(len(chosen_fields)):
            var_to_relevance_levels_boxplot(all_data[:, idx], all_labels, graph_dir, field_names[idx])


    # Generate the final results file
    lines = []
    for query_id in sorted(final_results.keys(), key=lambda  x: int(x.split("-")[-1])):
        if max_k < 0:
            top_k = len(final_results[query_id])
        else:
            top_k = min(len(final_results[query_id]), max_k)

        next_rank = 1
        seen_docs_top_scores = {}
        for score, formula_id in final_results[query_id]:
            doc_id = ":".join(formula_id.split(":")[:-1])

            # check if only the best should be kept, and if the document has been seen before and
            # if the score is lower than the current top score.
            # currently keeps all tied formulas
            if best_only and doc_id in seen_docs_top_scores and score < seen_docs_top_scores[doc_id]:
                # ignore this result...
                continue

            if not doc_id in seen_docs_top_scores:
                # mark first score found for document (best score)
                seen_docs_top_scores[doc_id] = score

            output_line = "\t".join([query_id, "1", formula_id, str(next_rank), str(score), run_name, "\n"])
            lines.append(output_line)

            next_rank += 1
            if next_rank > top_k:
                break


        """
        # query_id  unused doc_name:formula_id rank score run_name
        top_results = final_results[query_id][:top_k]
        for rank_idx, (score, formula_id) in enumerate(top_results):
            output_line = "\t".join([query_id, "1", formula_id, str(rank_idx + 1), str(score), run_name, "\n"])
            lines.append(output_line)
        """

    out_file = open(output_filename, "w")
    out_file.writelines(lines)
    out_file.close()

    print("Finished!")

if __name__ == '__main__':
    main()
