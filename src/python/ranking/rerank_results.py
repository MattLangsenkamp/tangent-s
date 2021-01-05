"""
    Tangent
   Copyright (c) 2013, 2015, 2017 David Stalnaker, Richard Zanibbi, Nidhin Pattaniyil,
                  Andrew Kane, Frank Tompa, Kenny Davila Castellanos

    This file is part of Tangent.

    Tanget is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Tangent is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Tangent.  If not, see <http://www.gnu.org/licenses/>.

    Contact:
        - Richard Zanibbi: rlaz@cs.rit.edu
"""
__author__ = 'KDavila'

import os
import sys
import time
import codecs
import pickle
import csv

from src.python.utility.control import Control
from src.python.math.math_document import MathDocument

from src.python.ranking.query import Query
from src.python.ranking.mathml_cache import MathMLCache

from src.python.ranking.reranker import Reranker

def optional_parameters(args):
    values = {}

    pos = 0
    while pos < len(args):
        if args[pos][0] == "-":
            arg_name = args[pos][1:]
            if pos + 1 < len(args):
                values[arg_name] = args[pos + 1]
            else:
                print("incomplete parameter " + arg_name)
            pos += 2
        else:
            print("Unexpected value: " + args[pos])
            pos += 1

    return values

def main():
    if len(sys.argv) < 5:
        print("Usage")
        print("\tpython3 rerank_results.py control input_results metric output_results")
        print("")
        print("Where:")
        print("\tcontrol:\tPath to tangent control file")
        print("\tinput_results:\tPath to file with results to re-rank")
        print("\tmetric:\t\tSimilarity metric to use")
        print("\toutput_results:\tPath to file where re-ranked results will be stored")
        print("")
        print("Optional:")
        print("\t-w\twindow\t\tWindow for pair generation (default is read from control file)")
        print("\t-e\teob pairs\tAdd end of baseline pairs (default is 2 - small EOB)")
        print("\t-h\thtml_prefix\tPrefix for HTML output (requires dot)")
        print("\t-c\tcondition\tCurrent test condition")
        print("\t-s\tstats\t\tFile to store stats")
        print("\t-t\ttimes\t\tFile to accumulate time stats")
        print("\t-k\tmax_results\tK number of results to rerank as maximum")
        print("\t-S\tslowest\t\tPrint the K slowest to compute candidates")
        return

    control_filename = sys.argv[1]
    input_filename = sys.argv[2]

    try:
        metric = int(sys.argv[3])
        if metric < -1 or metric > 12:
            print("Invalid similarity metric function")
            return
    except:
        print("Invalid similarity metric function")
        return

    #Reranker

    output_filename = sys.argv[4]

    optional_params = optional_parameters(sys.argv[5:])

    #load control file
    control = Control(control_filename) # control file name (after indexing)
    is_OPT = control.read("tree_model", num=False, default="layout").lower() == "operator"
    math_doc = MathDocument(control)

    # also, the mathml cache ...
    mathml_cache_file = control_filename + ".retrieval_2.cache"
    if not os.path.exists(mathml_cache_file):
        mathml_cache = MathMLCache(control_filename)
    else:
        cache_file = open(mathml_cache_file, "rb")
        mathml_cache = pickle.load(cache_file)
        cache_file.close()

    if "w" in optional_params:
        try:
            window = int(optional_params["w"])
            if window < 0:
                print("Invalid window")
                return
        except:
            print("Invalid value for window")
            return
    else:
        window = int(control.read("window"))

    if "e" in optional_params:
        try:
            eob = int(optional_params["e"])
            if eob < 0 or eob > 2:
                print("Invalid EOB")
                return
        except:
            print("Invalid value for eob")
            return
    else:
        eob = 2

    if "h" in optional_params:
        html_prefix = optional_params["h"]
        if not os.path.isdir(html_prefix):
            os.makedirs(html_prefix)

    else:
        html_prefix = None

    if "c" in optional_params:
        condition = optional_params["c"]
        print("testing condition: " + condition)
    else:
        condition = "undefined"

    if "s" in optional_params:
        stats_file = optional_params["s"]
    else:
        stats_file = None

    if "S" in optional_params:
        try:
            slowest_k = int(optional_params["S"])
        except:
            print("Invalid parameter value for slowest K")
            return
    else:
        slowest_k = 0

    if "k" in optional_params:
        try:
            max_k = int(optional_params["k"])
        except:
            print("Invalid max_results parameter")
            return
    else:
        max_k = 0

    if "t" in optional_params:
        times_file = optional_params["t"]
    else:
        times_file = None

    all_queries = Query.LoadQueryResultsFromTSV(input_filename, math_doc, mathml_cache, html_prefix, max_k, is_OPT)

    # save any changes made to the MathML cache ...
    cache_file = open(mathml_cache_file, "wb")
    pickle.dump(mathml_cache, cache_file, pickle.HIGHEST_PROTOCOL)
    cache_file.close()

    # now, re-rank...
    print("Results loaded, reranking ...", flush=True)

    # compute similarity first...
    reranker = Reranker.CreateFromMetricID(metric, is_OPT, {"window": window, "eob": eob})


    for q_idx, query in enumerate(all_queries):
        print("Evaluating: " + query.name + " - " + query.expression)
        reranker.set_query(query)

        query_start_time = time.time() * 1000 # RZ: ms
        reranker.rerank_query_results()
        query_end_time = time.time() * 1000 # RZ: ms

        query.elapsed_time = query_end_time - query_start_time 
        print(query.name)
        print(query.elapsed_time)
    # end_time = time.time()
    # elapsed = end_time - start_time

    #now, store the re-ranked results...
    out_file = open(output_filename, 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(out_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
    for query in all_queries:
        csv_writer.writerow([])
        query.output_query(csv_writer)
        query.output_sorted_results(csv_writer)

        if html_prefix is not None:
            print("Saving " + query.name + " to HTML file.....", flush=True)
            query.save_html(html_prefix + "/" + query.name)
    out_file.close()

    #if stats file is requested ...
    if stats_file is not None:
        out_file = open(stats_file, "w")
        out_file.write(Query.stats_header("\t"))
        for query in all_queries:
            query.output_stats(out_file,"\t", condition)
        out_file.close()

    # if times file is requested ...
    if times_file is not  None:
        sorted_queries = sorted([(query.name.strip(), query) for query in all_queries])

        if os.path.exists(times_file):
            out_file = open(times_file, "a")
        else:
            out_file = open(times_file, "w")
            header = "condition," + ",".join([name for (name, query) in sorted_queries])
            out_file.write(header + "\n")

        line = condition

        for name, query in sorted_queries:
            line += "," + str(query.elapsed_time)

        out_file.write(line + "\n")

        out_file.close()

    if slowest_k > 0:
        # find the slowest K ...
        all_times = []
        for query in all_queries:
            for exp in query.results:
                all_times.append((query.results[exp].reranking_time, query.name, exp))

        all_times = sorted(all_times, reverse=True)

        print("Expressions that required the most time to re-rank")
        print("")
        for time_query, query_id, exp in all_times[:slowest_k]:
            print(query_id + " - Time: " + str(time_query) + " s")
            print(exp)
            print("")

    # print("Elapsed Time Ranking: " + str(elapsed) + " s", flush=True)

    print("Finished successfully")
    

if __name__ == '__main__':
    if sys.stdout.encoding != 'utf8':
      sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf8':
      sys.stderr = codecs.getwriter('utf8')(sys.stderr.buffer, 'strict')

    main()
