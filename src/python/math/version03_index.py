import sys
import os
import csv
import socket
import time
from pathlib import Path
from src.python.text import text_engine_client as tec
from src.python.ranking.query import Query
from src.python.utility.text_query import TQuery
from src.python.utility.comp_query import CompQuery
from .math_document import MathDocument

MAX_UNCOMMITED = 1000
max_results = 1000
max_size_pairs=10000

__author__ = 'FWTompa'

# acts as math engine client for integrated processing
#   (and calls text engine client as needed)
# or writes files for offline processing


class Version03Index:
    def __init__(self, cntl, ranker=None, window=None, process_id=""):
        self.cntl = cntl
        self.ranker = ranker
        self.db = cntl.read("database")
        self.runmode = cntl.read("runmode")  # if 'now', processing queries immediately
        self.process_id = process_id
        self.window = window
        self.semantic_trees = cntl.read("tree_model", num=False, default="layout").lower() == "operator"
        # check for directory
        self.db_index_directory = os.path.join(Path(__file__).parent.parent.parent.parent, "db-index")
        if not os.path.exists(self.db_index_directory):
            os.makedirs(self.db_index_directory)

    def openDB(self, fileid, topk):
        """
        Start a file for collecting query tuples to pass to search engine

        param fileid: process id used to distinguish files
        type  fileid: string
        param topk: (maximum) number of matches to return
        type  topk: int
        """
        if self.runmode == "now":
            w = self.window if self.window else 0
            try:
                url = self.cntl.read("mathURL")
                port = self.cntl.read("mathPort",num=True)+w
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((url,port))
                self.rfile = self.socket.makefile(mode='r', encoding="utf-8", newline='')
                self.reader = csv.reader(self.rfile, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
                self.wfile = self.socket.makefile(mode='w', encoding='utf-8', newline='')
                self.writer = csv.writer(self.wfile, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
                writer = self.writer
                print("created reader and write for math engine")
                filename = self.cntl.read("resultFile")
                file_path = os.path.join(self.db_index_directory, filename)
                self.out_file = open(file_path, "w", encoding='UTF-8') # initialize result file
            except Exception as err:
                reason = str(err)
                print("Failed to open socket or result file: "+reason, file=sys.stderr)
                exit(1)
            self.topk = topk # save the value for text engine and for output
        else:
            filename = "%s_q_%s.tsv" % (self.db, fileid)
            file_path = os.path.join(self.db_index_directory, filename)
            file = open(file_path, mode='w', encoding='utf-8', newline='')
            writer = csv.writer(file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
        #writer.writerow(["K",10*topk])
        writer.writerow(["K", topk])
        writer.writerow(["W", self.window if self.window else 0])
        writer.writerow(["O", "1" if self.semantic_trees else "0"])

    def closeDB(self, fileid, mode="q"):
        """
        Terminate a file for collecting query tuples to pass to search engine

        param fileid: process id used to distinguish files
        type  fileid: string
        param mode: "q" for querying or "i" for indexing
        type  topk: string
        """
        if (mode == "q" and self.runmode == "now"):
            self.writer.writerow(["X"])
            self.rfile.close()
            self.wfile.close()
            self.socket.close()
            self.out_file.close()
        else:
            filename = "%s_%s_%s.tsv" % (self.db, mode, fileid)
            file_path = os.path.join(self.db_index_directory, filename)
            with open(file_path, mode='a', encoding='utf-8', newline='') as file:
                writer = csv.writer(file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
                writer.writerow([])
                writer.writerow(["X"])

    def add(self, expression_objects):
        """
        Add expression to index by writing into tsv file

        :param expression_objects: collection of tuples for indexing
        :type  expression_objects: list(pair(SymbolTree,list(tuples)))
        :return full fileid used to save data
        :rtype  string

        W       size
        D	docID
        E	expression	positions
        ...
        E	expression	positions
        ...
        D	docID
        ...
        X

        (but X written by CloseDB)

        N.B. tuples generated from expressions within C++ module
        """
        fileid = os.getpid()
        filename = "%s_i_%s.tsv" % (self.db, fileid)
        file_path = os.path.join(self.db_index_directory, filename)
        new = not os.path.exists(file_path) # starting a new file
        with open(file_path, mode='a', encoding='utf-8', newline='') as file:
            writer = csv.writer(file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
            if new:
                writer.writerow(["W",self.window if self.window else 0])
                writer.writerow(["O", "1" if self.semantic_trees else "0"])

            docid = None
            for tree in expression_objects:
                if tree is not None:
                    if not docid == tree.document:
                        docid = tree.document
                        writer.writerow([])
                        writer.writerow(["D",docid])
                    expr = tree.tostring()
                    if expr != "":
                        writer.writerow(["E",expr,tree.position])
                    # tuples for pairs will be generated from expressions by C++ module
##                    pairs = tree.get_pairs(self.window)
##                    for pair in pairs: 
##                        lp, rp, rel, loc = pair.split('\t')
##                        writer.writerow(["T",lp,rp,rel,loc])
        return(fileid)

    def search(self, fileid, query_id, trees, keywords, topk):
        """
        prepare query tuples for all trees in the query

        :param fileid: process id used to distinguish files
        :type  fileid: string
        :param query_id: query identifier
        :type  query_id: string
        :param trees: collection of trees included in query
        :type  trees: list(SymbolTree)
        :param keywords: collection of terms included in query
        :type  keywords: list(string)

        Q	queryID
        E	expression	positions
        E	expression positions
        ...
        P	keyword
        P	keyword
        ...

        N.B. tuples generated from expressions within C++ module
        """

        if (self.runmode == "now"):
            writer = self.writer
            file = self.wfile
            #writer.writerow(["K",10*topk])
            writer.writerow(["K",topk])
            writer.writerow(["W",self.window if self.window else 0])
        else:
            filename = "%s_q_%s.tsv" % (self.db, fileid)
            file_path = os.path.join(self.db_index_directory, filename)
            file = open(file_path, mode='a', encoding='utf-8', newline='')
            writer = csv.writer(file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
            writer.writerow([])
        writer.writerow(["Q",query_id])
        exprs = []
        for tree in trees:
            # get query formulae
            print("search for " + tree.tostring())
            expr = tree.tostring()
            if expr != "":
                exprs.append(expr)
                writer.writerow(["E",expr,tree.position])
            # tuples for pairs will be generated from expressions by C++ module
##                pairs = tree.get_pairs(self.window)
##                for pair in pairs: 
##                    lp, rp, rel, loc = pair.split('\t')
##                    writer.writerow(["T",lp,rp,rel,loc])
        if self.runmode == "now":
            print("send query to math engine")
            start_time = time.time()

            file.flush()
            
            # get the results from the core engine immediately
            mresult = self.get(fileid)
            query = mresult[query_id]
            
            # now use TEC_client
            current_tquery = TQuery(query_id)
            query.set_keywords(current_tquery)
            for kw in keywords:
                current_tquery.add_keyword(kw)
            try:
                (tscores,tpositions) = tec.get(self.cntl,keywords,self.topk)
            except Exception as err:
                reason = str(err)
                print("Failed to connect to text engine: "+reason, file=sys.stderr)
                tscores = {}
            for (doc_id,line) in tscores.items():
                # line = (title,  raw score,  normalized score)
                doc_name = line[0]
                score = (float(line[1]),float(line[2]))
                current_tquery.add_result(doc_id, doc_name, score, tpositions.get(doc_id,{"<math":[]}))

            mscore = self.cntl.read("mScore",default="MSS")
            mweight = self.cntl.read("mWeight",num=True,default=50)
            mdynamic = self.cntl.read("mDynamicWeight",default=0,num=True)
            msize_norm = self.cntl.read("mSizeNormalization",default=0,num=True)
            mtext_only = self.cntl.read("mTextOnly", default=0, num=True)
            query.combine_math_text(mscore,mweight, mdynamic, msize_norm, mtext_only) # Compute document scores, combining (rescored) math and text

            end_time = time.time()
            elapsed_time = (end_time - start_time) * 1000
            query.output_query(self.out_file,self.cntl,self.topk, elapsed_time)
        else:
            for term in keywords:
                # get query keywords
                if term != "":
                    writer.writerow(["P",term])

    def get(self, fileid):
        """
        ingest result tuples for topk responses to queries

        :param fileid: process id used to distinguish files
        :type  fileid: string
        :return: query responses
        :rtype:  dict mapping query_name -> CompQuery()

        Q	queryID
        E       search-expr
        R	docID   position	expression	score
        R	docID   position	expression	score
        ...
        Q	queryID
        ...
        X

        """

        if (self.runmode == "now"):
            reader = self.reader
        else:
            filename = "%s_r_%s.tsv" % (self.db, fileid)
            file_path = os.path.join(self.db_index_directory, filename)
            file = open(file_path, mode='r', encoding='utf-8', newline='')
            reader = csv.reader(file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
        print("Reading from math engine")
        doc_list = MathDocument(self.cntl)
        all_queries = {}
        for line in reader:
            if line:
                if line[0] == "Q":
                    current_name = line[1]
                    try:
                        current_query = all_queries[current_name]
                    except:
                        current_query = CompQuery(current_name)
                        all_queries[current_name] = current_query
                    current_expr = None
                elif line[0] == "E":
                    if current_name is None:
                        print("Invalid expression: Q tuple with query name expected first: " + str(line), flush=True)
                    else:
                        query_expression = line[1]
                        current_expr = Query(current_name,query_expression)
                        current_query.add_expr(current_expr)
                elif line[0] == "C":
                    print("Constraint ignored: " + line)

                elif line[0] == "I":
                    if current_name is None or current_expr is None:
                        print("Invalid information: Q tuple with query name and E tuple with expression expected first: " + str(line))
                    elif line[1] == "qt":
                        current_expr.initRetrievalTime = float( line[2] )
                    elif line[1] == "post":
                        current_expr.postings = int( line[2] )
                    elif line[1] == "expr":
                        current_expr.matchedFormulae = int( line[2] )
                    elif line[1] == "doc":
                        current_expr.matchedDocs = int( line[2] )

                elif line[0] == "R":
                    if current_name is None or current_expr is None:
                        print("Invalid result item: Q tuple with query name and E tuple with expression expected first: " + str(line))
                    else:
                        doc_id = int(line[1])
                        doc_name = doc_list.find_doc_file(doc_id)
                        if not doc_name:
                            doc_name = "NotADoc"
                        location = int(line[2])
                        expression = line[3]
                        score = float(line[4])
                        current_expr.add_result(doc_id, doc_name, location, expression, score)

                elif line[0] == "X":
                    break
                else:
                    print("Ignoring invalid tuple: " + str(line))
        print("Read " + str(len(all_queries)) + " queries")
        return all_queries
