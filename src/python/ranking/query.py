from subprocess import call

__author__ = 'KMDC'

import os
import io
import xml
import csv
import pickle
import re # RZ - ARQMath

from src.python.math.symbol_tree import SymbolTree
from src.python.math.layout_symbol import LayoutSymbol
from src.python.math.semantic_symbol import SemanticSymbol
from src.python.math.math_extractor import MathExtractor
from src.python.math.mathml import MathML
from src.python.ranking.alignment import Alignment
from src.python.ranking.result import Result
from src.python.ranking.document_rank_info import DocumentRankInfo
from src.python.ranking.constraint_info import ConstraintInfo

class Query:
    HTML_ResultColumns = 3

    def __init__(self, name, expression, mathml=None, initRetrievalTime='undefined', max_results=0, operator=False):
        self.name = name

        self.mathml = mathml
        self.results = {}
        self.documents = {}

        self.operator = operator

        if operator:
            self.tree = SymbolTree.parse_from_opt(expression)
            self.expression = expression
        else:
            if mathml is not None:
                # parse from mathml (additional information extracted)
                self.tree = MathExtractor.convert_and_link_mathml(mathml)
                self.expression = self.tree.tostring()
            else:
                # parse from SLT string (no mathml information available)
                self.tree = SymbolTree.parse_from_slt(expression)
                self.expression = expression

        self.constraints = Query.create_default_constraints(self.tree)

        self.sorted_results = None
        self.sorted_result_index = None
        self.sorted_abs_ranks = None
        self.sorted_documents = None
        self.sorted_document_index = None
        self.elapsed_time = 0.0

        # RZ: add tuple-based retrieval time and other measures.
        self.initRetrievalTime = initRetrievalTime
        self.postings = None
        self.matchedFormulae = None
        self.matchedDocs = None

        # Re-rank at most K results
        self.max_results = max_results

        # cache ...
        self.html_queryblock = {}

    @staticmethod
    def create_default_constraints(query_tree, default_value="U"):
        # duplicate structure ...
        root = Query.duplicate_structure(query_tree.root, default_value)
        # now create constraint nodes ....
        Query.convert_to_constraint_tree(root)

        # create and return symbol tree
        return SymbolTree(root)

    @staticmethod
    def duplicate_structure(current_root, default_tag):
        if isinstance(current_root, LayoutSymbol):
            duplicated_node = LayoutSymbol(default_tag)

            if current_root.next is not None:
                child = Query.duplicate_structure(current_root.next, default_tag)
                duplicated_node.next = child

            if current_root.above is not None:
                child = Query.duplicate_structure(current_root.above, default_tag)
                duplicated_node.above = child

            if current_root.below is not None:
                child = Query.duplicate_structure(current_root.below, default_tag)
                duplicated_node.below = child

            if current_root.over is not None:
                child = Query.duplicate_structure(current_root.over, default_tag)
                duplicated_node.over = child

            if current_root.under is not None:
                child = Query.duplicate_structure(current_root.under, default_tag)
                duplicated_node.under = child

            if current_root.pre_above is not None:
                child = Query.duplicate_structure(current_root.pre_above, default_tag)
                duplicated_node.pre_above = child

            if current_root.pre_below is not None:
                child = Query.duplicate_structure(current_root.pre_below, default_tag)
                duplicated_node.pre_below = child

            if current_root.within is not None:
                child = Query.duplicate_structure(current_root.within, default_tag)
                duplicated_node.within = child

            if current_root.element is not None:
                child = Query.duplicate_structure(current_root.element, default_tag)
                duplicated_node.element = child
        elif isinstance(current_root, SemanticSymbol):
            duplicated_node = SemanticSymbol(default_tag)

            if current_root.children is not None:
                duplicated_node.children = []
                for child in current_root.children:
                    dup_child = Query.duplicate_structure(child, default_tag)
                    dup_child.parent = duplicated_node
                    duplicated_node.children.append(dup_child)
        else:
            duplicated_node = None

        return duplicated_node

    @staticmethod
    def convert_to_constraint_tree(current_root):
        # replace "text" constraint with structure used for restrictions ...
        current_root.tag = ConstraintInfo.create_from_string(current_root.tag)

        if isinstance(current_root, LayoutSymbol):
            if current_root.next is not None:
                Query.convert_to_constraint_tree(current_root.next)

            if current_root.above is not None:
                Query.convert_to_constraint_tree(current_root.above)

            if current_root.below is not None:
                Query.convert_to_constraint_tree(current_root.below)

            if current_root.over is not None:
                Query.convert_to_constraint_tree(current_root.over)

            if current_root.under is not None:
                Query.convert_to_constraint_tree(current_root.under)

            if current_root.pre_above is not None:
                Query.convert_to_constraint_tree(current_root.pre_above)

            if current_root.pre_below is not None:
                Query.convert_to_constraint_tree(current_root.pre_below)

            if current_root.within is not None:
                Query.convert_to_constraint_tree(current_root.within)

            if current_root.element is not None:
                Query.convert_to_constraint_tree(current_root.element)

        elif isinstance(current_root, SemanticSymbol):
            if current_root.children is not None:
                for child in current_root.children:
                    Query.convert_to_constraint_tree(child)


    @staticmethod
    def tree_size(current_root):

        count = 1
        if isinstance(current_root, LayoutSymbol):
            if current_root.next is not None:
                count += Query.tree_size(current_root.next)

            if current_root.above is not None:
                count += Query.tree_size(current_root.above)

            if current_root.below is not None:
                count += Query.tree_size(current_root.below)

            if current_root.over is not None:
                count += Query.tree_size(current_root.over)

            if current_root.under is not None:
                count += Query.tree_size(current_root.under)

            if current_root.pre_above is not None:
                count += Query.tree_size(current_root.pre_above)

            if current_root.pre_below is not None:
                count += Query.tree_size(current_root.pre_below)

            if current_root.within is not None:
                count += Query.tree_size(current_root.within)

            if current_root.element is not None:
                count += Query.tree_size(current_root.element)

        elif isinstance(current_root, SemanticSymbol):
            for child in current_root.children:
                count += Query.tree_size(child)

        return count


    def set_constraints(self, tree_string, semantic):
        # create the tree with the original text labels
        if semantic:
            tree_constraints = SymbolTree.parse_from_opt(tree_string)
        else:
            tree_constraints = SymbolTree.parse_from_slt(tree_string)

        # convert the text labels to constraints
        Query.convert_to_constraint_tree(tree_constraints.root)

        if not Query.equal_subtree_structure(self.tree.root, tree_constraints.root):
            print("Warning: Invalid constraint tree specified for " + self.name)
        else:
            self.constraints = tree_constraints

    def add_result(self, doc_id, doc_name, location, expression, score, mathml=None):
        # first, verify if the expression is new...
        if expression not in self.results:
            # new, create....
            if 0 < self.max_results <= len(self.results):
                # stop adding results
                return

            ranking = len(self.results) + 1     # assume results are added in original ranking order
            self.results[expression] = Result(self, expression, ranking, score, mathml, self.operator)

        # add location..
        self.results[expression].locations.append((doc_id, location))

        # add document ...
        if doc_id not in self.documents:
            self.documents[doc_id] = doc_name

    def equal_matched_elements(self, expression1, expression2):
        matched_1 = self.results[expression1].matched_elements
        matched_2 = self.results[expression2].matched_elements

        if len(matched_1) != len(matched_2):
            return False
        else:
            s1 = set(matched_1.keys())
            s2 = set(matched_2.keys())

            return s1 == s2

    def equal_unified_elements(self, expression1, expression2):
        unified_1 = self.results[expression1].unified_elements
        unified_2 = self.results[expression2].unified_elements

        if len(unified_1) != len(unified_2):
            return False
        else:
            s1 = set(unified_1.keys())
            s2 = set(unified_2.keys())

            return s1 == s2

    def equal_wildcard_matches(self, expression1, expression2):
        wildcard_matches_1 = self.results[expression1].wildcard_matches
        wildcard_matches_2 = self.results[expression2].wildcard_matches

        if len(wildcard_matches_1) != len(wildcard_matches_2):
            return False
        else:
            s1 = set(wildcard_matches_1.keys())
            s2 = set(wildcard_matches_2.keys())

            return s1 == s2

    @staticmethod
    def equal_subtree_structure(root1, root2):
        if isinstance(root1, LayoutSymbol) and isinstance(root2, LayoutSymbol):
            # a
            if (root1.above is not None) and (root2.above is not None):
                if not Query.equal_subtree_structure(root1.above, root2.above):
                    return False
            elif not (root1.above is None and root2.above is None):
                return False
            # b
            if (root1.below is not None) and (root2.below is not None):
                if not Query.equal_subtree_structure(root1.below, root2.below):
                    return False
            elif not (root1.below is None and root2.below is None):
                return False
            # o
            if (root1.over is not None) and (root2.over is not None):
                if not Query.equal_subtree_structure(root1.over, root2.over):
                    return False
            elif not (root1.over is None and root2.over is None):
                return False
            # u
            if (root1.under is not None) and (root2.under is not None):
                if not Query.equal_subtree_structure(root1.under, root2.under):
                    return False
            elif not (root1.under is None and root2.under is None):
                return False
            # c
            if (root1.pre_above is not None) and (root2.pre_above is not None):
                if not Query.equal_subtree_structure(root1.pre_above, root2.pre_above):
                    return False
            elif not (root1.pre_above is None and root2.pre_above is None):
                return False
            # d
            if (root1.pre_below is not None) and (root2.pre_below is not None):
                if not Query.equal_subtree_structure(root1.pre_below, root2.pre_below):
                    return False
            elif not (root1.pre_below is None and root2.pre_below is None):
                return False
            # n
            if (root1.next is not None) and (root2.next is not None):
                if not Query.equal_subtree_structure(root1.next, root2.next):
                    return False
            elif not (root1.next is None and root2.next is None):
                return False
            # w
            if (root1.within is not None) and (root2.within is not None):
                if not Query.equal_subtree_structure(root1.within, root2.within):
                    return False
            elif not (root1.within is None and root2.within is None):
                return False
            # e
            if (root1.element is not None) and (root2.element is not None):
                if not Query.equal_subtree_structure(root1.element, root2.element):
                    return False
            elif not (root1.element is None and root2.element is None):
                return False

            # leaf or same sub-structure found ...
            return True
        elif isinstance(root1, SemanticSymbol) and isinstance(root2, SemanticSymbol):
            # check if both roots have children ...
            if root1.children is not None and root2.children is not None:
                # both have children ...
                if len(root1.children) != len(root2.children):
                    # different number of children ...
                    return False
                else:
                    # same number of children, check for each pair recursively
                    for child1, child2 in zip(root1.children, root2.children):
                        if not Query.equal_subtree_structure(child1, child2):
                            return False

                    # all children substructures are equal ...
                    return True
            else:
                # one or the two don't have, if only one has then structure is not similar....
                return root1.children is None and root2.children is None
        else:
            return False


    def equal_structure(self, expression1, expression2):
        tree1 = self.results[expression1].tree.root
        tree2 = self.results[expression2].tree.root

        return Query.equal_subtree_structure(tree1, tree2)

    def sort_documents(self):
        if len(self.results) > 0:
            current_documents = {}

            # sum scores for all existing formulas over all documents
            for expression in self.results:
                result = self.results[expression]

                for doc_id, location in result.locations:
                    # add document if first time seen
                    if not doc_id in current_documents:
                        current_documents[doc_id] = DocumentRankInfo(doc_id)

                    # add score of current result to current document
                    current_documents[doc_id].add_formula_scores(expression, location, result.new_scores)

            all_docs = [((current_documents[doc_id].top_formula_score, current_documents[doc_id].total_score),
                         current_documents[doc_id]) for doc_id in current_documents]

            all_docs = sorted(all_docs, key=lambda x: x[0], reverse=True)

            self.sorted_documents = [doc for scores, doc in all_docs]

            self.sorted_document_index = {}
            for idx, doc in enumerate(self.sorted_documents):
                self.sorted_document_index[doc.doc_id] = idx


    def character_set_distance(self, char_set_1, char_set_2):
        total_dist = 0

        for c2 in char_set_2:
            min_dist = None

            for c1 in char_set_1:
                dist = abs(ord(c2) - ord(c1))

                if min_dist is None or dist < min_dist:
                    min_dist = dist

            total_dist += min_dist

        #print(str((char_set_1, char_set_2, total_dist)))

        return total_dist

    def alignment_distance(self, alignments):
        total_distance = 0

        for alignment in alignments:
            assert isinstance(alignment, Alignment)

            if (alignment.q_element.tag[0:2] == "V!" and alignment.c_element.tag[0:2] == "V!"):
                char_q_set = set()
                for char_q in alignment.q_element.tag[2:]:
                    char_q_set.add(char_q)

                char_c_set = set()
                for char_c in alignment.c_element.tag[2:]:
                    char_c_set.add(char_c)

                total_distance += self.character_set_distance(char_q_set, char_c_set)

        return total_distance


    def sort_results(self):
        groups_with_multi_subgroups = 0
        count_subgroups = 0
        if len(self.results) > 0:
            # different number of score might be in use...
            n_scores = len(self.results[next(iter(self.results))].new_scores)
            score_function = lambda x: [x[i] for i in range(n_scores)]

            #query_char_set = Result.get_variable_character_set_rec(self.tree.root)

            # now, sort them ...
            result_list = [self.results[expression].new_scores + [expression] for expression in self.results]
            sorted_list = [x[-1] for x in sorted(result_list, key=score_function, reverse=True)]

            # first group by unique scores...
            last_group_scores = None
            sorted_groups = []
            for expression in sorted_list:
                if last_group_scores is None or last_group_scores != self.results[expression].new_scores:
                    # create new group
                    sorted_groups.append([])
                    last_group_scores = self.results[expression].new_scores

                sorted_groups[-1].append(expression)

            # now, create sub groups based on same structure matched....
            for group_idx in range(len(sorted_groups)):
                group_list = sorted_groups[group_idx]

                # find subgroups with the same matching substructure ...
                sub_group_list = []

                # ... for the remaining elements ...
                for expression in group_list:
                    # ... compare againts every group ...
                    found = False
                    for group in sub_group_list:
                        group_expression = group[0]

                        # ... compare match structure and match location...
                        if (self.equal_structure(expression, group_expression) and
                            self.equal_matched_elements(expression, group_expression) and
                            self.equal_unified_elements(expression, group_expression) and
                            self.equal_wildcard_matches(expression, group_expression)):

                            group.append(expression)
                            found = True
                            break

                    if not found:
                        sub_group_list.append([expression])

                if len(sub_group_list) > 1:
                    groups_with_multi_subgroups += 1
                count_subgroups += len(sub_group_list)

                # ... now, sort elements within each subgroup
                sorted_subgroups = []
                for subgroup in sub_group_list:
                    sorted_subgroup = []

                    for expression in subgroup:
                        #exp_char_set = self.results[expression].get_variable_character_set()
                        #dist = self.character_set_distance(query_char_set, exp_char_set)

                        dist = self.alignment_distance(self.results[expression].all_unified)

                        sorted_subgroup.append([dist, expression])

                    sorted_subgroup = sorted(sorted_subgroup)

                    sorted_subgroups.append([x[-1] for x in sorted_subgroup])

                # finally, replace...
                sorted_groups[group_idx] = sorted_subgroups

            #print(self.name + "\t" + str(count_subgroups) + "\t" + str(groups_with_multi_subgroups))
            #print("Multi sub groups: " + str(groups_with_multi_subgroups))
            #print("Total sub groups: " + str(count_subgroups))

            # self.sorted_results = [x[-1] for x in sorted(result_list, key=score_function, reverse=True)]
            self.sorted_results = sorted_groups

            # keep an inverted index from expressions to their sub groups indices after sorting
            self.sorted_result_index = {}
            self.sorted_abs_ranks = {}
            sub_group_idx = 0
            previous_count = 0

            for group in self.sorted_results:
                current_count = 0
                for subgroup in group:
                    sub_group_idx += 1
                    current_count += len(subgroup)

                    # for expression in self.sorted_results:
                    for expression in subgroup:
                        self.sorted_result_index[expression] = sub_group_idx
                        self.sorted_abs_ranks[expression] = previous_count

                previous_count += current_count

        else:
            # empty results ...
            self.sorted_results = []



    def get_query_stats(self):
        total_matches = 0
        total_formulae = 0

        for group in self.sorted_results:
            total_matches += len(group)
            for subgroup in group:
                total_formulae += len(subgroup)

                for expression in subgroup:
                    result = self.results[expression]

        total_documents = len(self.documents)

        return total_matches, total_formulae, total_documents


    def output_query(self, csv_writer):
        csv_writer.writerow(["Q", self.name])
        csv_writer.writerow(["E", self.expression])

    def output_sorted_results(self, csv_writer):
        if self.sorted_results is None:
            print("Results must be sorted first")
            return

        for group in self.sorted_results:
            for subgroup in group:

                # for expression in self.sorted_results:
                for expression in subgroup:
                    result = self.results[expression]
                    for doc_id, location in result.locations:
                        score_str = "[" + ",".join([str(score) for score in result.new_scores]) + "]"

                        csv_writer.writerow(["R", str(doc_id), str(location), result.expression, score_str])

    def output_stats(self, out_file, separator, test_condition):
        if self.sorted_results is None:
            print("Results must be sorted first")
            return

        q_size = Query.tree_size(self.tree.root)

        structure_idx = 0
        for g_idx, group in enumerate(self.sorted_results):
            for subgroup in group:
                structure_idx += 1

                for expression in subgroup:
                    result = self.results[expression]

                    c_size = Query.tree_size(result.tree.root)

                    values = [self.name, test_condition, str(result.original_ranking), str(result.original_score),
                              str(g_idx + 1), str(structure_idx), str(result.new_scores[0]), str(result.new_scores[1]),
                              str(result.new_scores[2]), str(q_size), str(c_size), result.expression]
                    line = separator.join(values)
                    out_file.write(line + "\n")

    @staticmethod
    def stats_header(separator):
        header = separator.join(["query", "condition", "o_rank", "o_score", "n_rank", "n_str",
                                 "n_score_1", "n_score_2", "n_score_3", "q_size", "c_size", "slt"])
        return header + "\n"


    def save_png(self, output_name, tree, highlight_nodes=None, unified_nodes=None, wildcard_nodes=None, generic=False):
        # first, save to temporal dot file
        tree.save_as_dot("temporal_rerank_graph.gv", highlight_nodes, unified_nodes, wildcard_nodes, generic)

        # now, execute dot....
        try:
            code = call(["dot", "-Tpng", "temporal_rerank_graph.gv", "-o", output_name])
        except:
            print("Must install dot in order to use HTML output")
            return False

        return code == 0

    def save_svg(self, output_name, tree, highlight_nodes=None, unified_nodes=None, wildcard_nodes=None, generic=False):
        # first, save to temporal dot file
        tree.save_as_dot("temporal_rerank_graph.gv", highlight_nodes, unified_nodes, wildcard_nodes, generic)

        # now, execute dot....
        try:
            code = call(["dot", "-Tsvg", "temporal_rerank_graph.gv", "-o", output_name])
        except:
            print("Must install dot in order to use HTML output")
            return False

        return code == 0

    def __recursive_find_elements(self, current_root, tag):
        if current_root.tag == tag:
            result = [current_root]
        else:
            result = []

        for element in current_root:
            child_res = self.__recursive_find_elements(element, tag)
            result += child_res

        return result

    def get_html_common_header(self):
        return """
        <!DOCTYPE html>
        <html>
            <head>
                <title>Results for: """ + self.name + """</title>
                <style>
                 .results_list td  { border: 0px solid black; padding: 5px; }
                 .results_list th  { border: 0px solid black; padding: 5px; }

                 .math_formula {
                     background-color: #fff;
                     padding: 10px;
                     border: 1px solid #ddd;
                     font-size: 200%;
                     font-family: Helvetica;
                 }

                 #body {
                    margin: 0;
                    font-family: "Helvetica Neue";
                    font-size: 1em;
                    color: #222;
                    padding: 30px 60px;
                }

                #statsline {
                    font-size: 1.25em;
                }


                #logo {
                    width: 140px;
                    font-family: "Helvetica Neue";
                    font-weight: 250;
                    font-size: 2em;
                    float: left;
                }

                .score {
                    color: #999;
                }

                #queryblock {
                }

                #header {
                    background-color: #eee;
                    padding: 12px 30px;
                    overflow: auto;
                    border-bottom: 1px solid #ccc;
                }

                #searchbutton {
                    padding: 5px;
                    background-color: #efe;
                    border: 2px solid black;
                    height: 2.5em;
                    width: 6.5em;
                    font-size: 125%;
                }

                </style>
                <meta charset=\"UTF-8\">
                <script type=\"text/javascript\"
                   src=\"http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML\">
                </script>
                <script type=\"text/javascript\" >
                    function hide_class(hide, class_name){
                        var nodes = document.getElementsByClassName(class_name);
                        var i;
                        for (i = 0; i < nodes.length; i++){
                            if (hide){
                                nodes[i].style.display = "none";
                            } else {
                                nodes[i].style.display = "";
                            }
                        }

                        if (hide){
                            document.getElementById('id_' + class_name + '_show').style.display = '';
                            document.getElementById('id_' + class_name + '_hide').style.display = 'none';
                        } else {
                            document.getElementById('id_' + class_name + '_show').style.display = 'none';
                            document.getElementById('id_' + class_name + '_hide').style.display = '';
                        }
                    }
                </script>
            </head>
            <body>
                <font face=helvetica>
        """

    def get_html_common_footer(self):
        return """
                </font>
            </body>
        </html>
        """

    def get_html_queryblock(self, prefix):
        if prefix not in self.html_queryblock:
            # create the SVG for the query ...

            image_base_name = "images/" + self.name + "_"

            if self.save_svg(prefix + "/" + image_base_name + "query.svg", self.tree):
                query_image = """
                <object type=\"image/svg+xml\" data=\"""" + image_base_name + """query.svg\">
                    Not Supported
                </object>"""
            else:
                query_image = """
                    <p><Query SLT could not be rendered</p>
                """

            # Prepare MathML
            if self.mathml is not None:
                if isinstance(self.mathml, bytes):
                    self.mathml = self.mathml.decode('UTF-8')

                # remove qvar elements....
                elem_content = io.StringIO(self.mathml)  # treat the string as if a file
                root = xml.etree.ElementTree.parse(elem_content).getroot()
                all_vars = self.__recursive_find_elements(root, MathML.mqvar)
                all_vars += self.__recursive_find_elements(root, MathML.mqvar2)

                if len(all_vars) > 0:
                    for query_var in all_vars:
                        query_var.tag = MathML.mi
                        if "name" in query_var.attrib:
                            query_var.text = query_var.attrib["name"]

                    query_mathml = xml.etree.ElementTree.tostring(root)
                    if isinstance(query_mathml, bytes):
                        query_mathml = query_mathml.decode('UTF-8')
                else:
                    query_mathml = self.mathml
            else:
                query_mathml = ""

            self.html_queryblock[prefix] = """
            <!-- Query -->
            <div id="queryblock" align="left">
                <table>
                    <tr><td>
                        <div class="tree_svg" style="display: none;">""" + query_image + """</div>
                    </td></tr>
                    <tr><td>
                        <div class=\"math_formula\">""" + query_mathml + """</div>
                    </td></tr>
                </table>
            </div>
            """

        return self.html_queryblock[prefix]

    def get_html_logo(self, prefix, include_show_buttons):
        result = """
        <div id="header">
            <table><tr>
                <td>
                    <!-- Logo and buttons -->
                    <div>
                        <div id="logo">tangent<br>

                            <table align="left" ><tr>
                                <td>
        """

        if include_show_buttons:
            result += """
            <input type="button" id="id_tree_svg_show" value="Graphs" onclick="hide_class(false, 'tree_svg');">
            <input type="button" id="id_tree_svg_hide" value="Graphs" style="background:yellow; display: none;"
                onclick="hide_class(true, 'tree_svg');">
            """
        else:
            result += "<br />"

        result += """
                                </td>
                            </tr></table>
                        </div>
                    </div>
                <td>""" + self.get_html_queryblock(prefix) + """</td>
                <td width="99%" align="right">
                    <!-- Search Button -->
                    <button id="searchbutton" type="button">Search</button>
                </td>
            </tr></table>
        </div>
        """

        return result

    def get_html_stats(self):
        # compute statistics ....
        total_matches, total_formulae, total_locations = self.get_query_stats()

        if self.initRetrievalTime != "undefined":
            stat_str = "{0:.3f}".format(self.initRetrievalTime) + " ms, "
            stat_str += "Re-ranking " + "{0:.3f}".format(self.elapsed_time) + " ms<br>"
            stat_str += "&nbsp;&nbsp;&nbsp;&nbsp;Found " + str(self.postings) + " tuple postings, "
            stat_str +=  str(self.matchedFormulae) + " formulae, " + str(self.matchedDocs) + " documents"
        else:
            stat_str = "? ms, Re-ranking ? ms, &nbsp;&nbsp;&nbsp;&nbsp;Found ? tuple postings, ? formulae, ? documents"

        result = """
        <!-- STATISTICS -->
        <div id="statsline">
            Returned """ + str(total_matches) + """ matches
            (""" + str(total_formulae) + """ formulae, """ + str(total_locations) + """ docs)
            <br>&nbsp;&nbsp;&nbsp;&nbsp;Lookup """ + stat_str + """
            <br>
            <table cellpadding="5">
                <tr>
                    <td>
                        <A href=\"""" + self.name + """_main.html\" style="text-decoration:none">
                            [ formulas ]
                        </a>
                    </td>
                    <td>
                        <A href=\"""" + self.name + """_docs.html\" style="text-decoration:none">
                            [ documents ]
                        </a>
                    </td>
                    <td>
                        <A href=\"""" + self.name + """_formulas.html\" style="text-decoration:none">
                            [ documents-by-formula ]
                        </a>
                    </td>
                </tr>
            </table>
            <br>
        </div>
        """

        return result

    def save_html_groups(self, prefix):
        if self.sorted_results is None:
            print("Results must be sorted first")
            return False

        base_name = prefix + "/" + self.name
        out_filename = base_name + "_main.html"
        image_base_name = "images/" + self.name + "_"

        header = self.get_html_common_header()
        header += self.get_html_logo(prefix, True)

        content = "<div id=\"body\">"
        content += self.get_html_stats()

        content += "<table class=\"results_list\" align=\"left\" cellpadding=\"0\" cellspacing=\"0\" border=\"0\" >\n"

        g_idx = 0
        exp_idx = 0
        for group in self.sorted_results:
            for subgroup in group:
                g_idx += 1

                # output header row
                content += "<tr>"

                # scores...
                # ... add an anchor to current group
                scores_str = "<br />".join(["{0:.4f}".format(x) for x in self.results[subgroup[0]].new_scores])
                content += """<td rowspan=\"2\" style=\"vertical-align: text-top;\" >
                                <a name=\"group_""" + str(g_idx) + """\"></a>
                                <div class="score">""" + scores_str + """</div>
                               </td>
                            """

                # SVG tree
                content += "<td>"
                result_name = image_base_name + str(g_idx) + ".svg"
                first_result = self.results[subgroup[0]]

                if self.save_svg(prefix + "/" + result_name, first_result.tree, first_result.matched_elements,
                                 first_result.unified_elements, first_result.wildcard_matches, True):
                    content += "<object class=\"tree_svg\" style=\"display: none;\" type=\"image/svg+xml\" " \
                               "data=\"" + result_name + "\">Not Supported</object>"

                content += "</td>"
                content += "</tr>\n"

                # now expressions in single cell (on their own tables)
                content += "<tr><td>"


                content += "<table>"
                for sg_idx, expression in enumerate(subgroup):
                    exp_idx += 1

                    result = self.results[expression]

                    if sg_idx % Query.HTML_ResultColumns == 0:
                        content += "<tr>"

                    #content += "<td>" + str(sg_idx + 1) + "</td>"
                    content += "<td></td>"
                    content += "<td>"
                    marked_mathml = result.get_highlighted_mathml()
                    if marked_mathml is not None:
                        content += "<a href=\"" + self.name + "_formulas.html#formula_" + str(exp_idx) + "\"  >"
                        content += "    <div class=\"math_formula\">" + marked_mathml + "</div>"
                        content += "</a>"
                    else:
                        content += "<br />"
                    content += "</td>\n"

                    if (sg_idx + 1) % Query.HTML_ResultColumns == 0:
                        content += "</tr>\n"

                # create the empty cell for the empty spaces in the grid of results...
                reminder = len(subgroup) % Query.HTML_ResultColumns
                if reminder > 0:
                    content += "<td colspan=\"" + str((Query.HTML_ResultColumns - reminder) * 2) + "\"><br /></td>"
                    content += "</tr>\n"

                content += "</table>"
                content += "</td></tr>"


        content += "</table>\n"

        content += "</div>\n"

        footer = self.get_html_common_footer()

        out_file = open(out_filename, "wb")
        final_content = bytes(header + content + footer, "UTF-8")
        out_file.write(final_content)
        out_file.close()

        return True


    def save_html_docs(self, prefix):
        if self.sorted_documents is None:
            print("Documents must be sorted first")
            return False

        base_name = prefix + "/" + self.name
        out_filename = base_name + "_docs.html"
        # image_base_name = "images/" + self.name + "_"

        header = self.get_html_common_header()
        header += self.get_html_logo(prefix, False)

        content = "<div id=\"body\">"
        content += self.get_html_stats()

        content += "<table class=\"results_list\" align=\"left\" cellpadding=\"0\" cellspacing=\"0\" border=\"0\" >\n"
        for idx, document in enumerate(self.sorted_documents):

            doc_link = self.documents[document.doc_id]
            doc_params = ""
            for loc, expr in document.expressions:
                doc_params += "&exp=" + str(loc)
                #doc_params += "&int=" + str(self.results[expr].new_scores[0])
                doc_params += "&int=" + str(1.0 - (self.sorted_abs_ranks[expr] / float(len(self.results))))

            content += "<tr>"
            content += "<td rowspan=\"2\" style=\"vertical-align: text-top;\">Doc " + str(idx + 1) + "</td>"

            scores_str = document.get_score_string("<br />")
            content += """<td rowspan=\"2\" style=\"vertical-align: text-top;\" >
                            <div class="score">""" + scores_str + """</div>
                           </td>
                        """
            content += "<td><a href=\"../highlighter.html?doc=" + doc_link + doc_params + "\">" + doc_link + "</a></td>"
            content += "</tr>"

            content += "<tr>"
            content += "<td>"
            content += "<table>"

            sorted_locs = sorted([(self.sorted_result_index[expr], expr) for loc, expr in document.expressions])

            for sg_idx, exp_info in enumerate(sorted_locs):
                group_idx, expression = exp_info
                result = self.results[expression]

                if sg_idx % Query.HTML_ResultColumns == 0:
                    content += "<tr>"

                content += "<td></td>"
                content += "<td>"
                marked_mathml = result.get_highlighted_mathml()
                if marked_mathml is not None:

                    content += "<a href=\"" + self.name + "_main.html#group_" + str(group_idx) + "\"  >"
                    content += "    <div class=\"math_formula\">" + marked_mathml + "</div>"
                    content += "</a>"
                else:
                    content += "<br />"
                content += "</td>\n"

                if (sg_idx + 1) % Query.HTML_ResultColumns == 0:
                    content += "</tr>\n"

            # create the empty cell for the empty spaces in the grid of results...
            reminder = len(document.expressions) % Query.HTML_ResultColumns
            if reminder > 0:
                content += "<td colspan=\"" + str((Query.HTML_ResultColumns - reminder) * 2) + "\"><br /></td>"
                content += "</tr>\n"

            content += "</table>"
            content += "</td>"
            content += "</tr>"

        content += "</table>\n"

        content += "</div>\n"

        footer = self.get_html_common_footer()

        out_file = open(out_filename, "wb")
        final_content = bytes(header + content + footer, "UTF-8")
        out_file.write(final_content)
        out_file.close()

        return True

    def save_html_formulas(self, prefix):
        if self.sorted_results is None:
            print("Results must be sorted first")
            return False

        if self.sorted_documents is None:
            print("Documents must be sorted first")
            return False

        base_name = prefix + "/" + self.name
        out_filename = base_name + "_formulas.html"
        # image_base_name = "images/" + self.name + "_"

        header = self.get_html_common_header()
        header += self.get_html_logo(prefix, False)

        content = "<div id=\"body\">"
        content += self.get_html_stats()

        content += "<table class=\"results_list\" align=\"left\" cellpadding=\"0\" cellspacing=\"0\" border=\"0\" >\n"
        exp_idx = 0
        for group in self.sorted_results:
            for subgroup in group:
                for sg_idx, expression in enumerate(subgroup):
                    exp_idx += 1

                    group_idx = self.sorted_result_index[expression]

                    result = self.results[expression]

                    # MathML
                    content += "<tr>\n<td>\n"
                    content += "<a name=\"formula_" + str(exp_idx) + "\"></a>"
                    content += "<table><tr><td>\n"
                    marked_mathml = result.get_highlighted_mathml()
                    if marked_mathml is not None:
                        content += "<a href=\"" + self.name + "_main.html#group_" + str(group_idx) + "\"  >"
                        content += "<div class=\"math_formula\">" + marked_mathml + "</div>"
                        content += "</a>"
                    else:
                        content += "<br />"
                    content += "</td></tr></table>\n"
                    content += "</td>\n</tr>\n"

                    # Document lists....
                    content += "<tr>\n<td>\n"

                    content += "<table>"
                    sorted_idxs = sorted([self.sorted_document_index[doc_id] for doc_id, loc in result.locations])
                    for sorted_idx in sorted_idxs:
                        document = self.sorted_documents[sorted_idx]
                        doc_id = document.doc_id
                        doc_link = self.documents[doc_id]

                        doc_params = ""
                        for loc, expr in document.expressions:
                            doc_params += "&exp=" + str(loc)
                            #doc_params += "&int=" + str(self.results[expr].new_scores[0])
                            doc_params += "&int=" + str(1.0 - (self.sorted_abs_ranks[expr] / float(len(self.results))))

                        content += "<tr>"
                        content += "<td>Doc " + str(sorted_idx + 1) + "</td>"
                        scores_str = document.get_score_string(", ")
                        content += """
                                    <td style=\"vertical-align: text-top;\" >
                                        <div class="score">""" + scores_str + """</div>
                                    </td>
                                    """
                        link = "<a href=\"../highlighter.html?doc=" + doc_link + doc_params + "\">" + doc_link + "</a>"
                        content += "<td>" + link + "</td>"
                        content += "</tr>"
                    content += "</table>"

                    content += "</td>\n</tr>\n"

        content += "</table>\n"

        content += "</div>\n"

        footer = self.get_html_common_footer()

        out_file = open(out_filename, "wb")
        final_content = bytes(header + content + footer, "UTF-8")
        out_file.write(final_content)
        out_file.close()

        return True

    def save_html(self, prefix):

        # save the main page with groups ....
        if not self.save_html_groups(prefix):
            return False

        # save the docs page ...
        if not self.save_html_docs(prefix):
            return False

        # save the formulas page ...
        if not self.save_html_formulas(prefix):
            return False

        # all pages saved successfully
        return True

    @staticmethod
    def LoadQueryResultsFromTSV(input_filename, math_doc, mathml_cache, html_prefix, max_k, is_OPT):
        in_file = open(input_filename, 'r', newline='', encoding='utf-8')
        reader = csv.reader(in_file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
        lines = [row for row in reader]
        in_file.close()

        current_query = None
        current_name = None
        tuple_ret_time = 'undefined'
        all_queries = []

        # read all results to re-rank
        for idx, line in enumerate(lines):
            # parts = line.strip().split("\t")
            parts = line

            if len(parts) == 2:
                if parts[0][0] == "Q":
                    current_name = parts[1]
                    current_query = None


                elif parts[0][0] == "E":
                    if current_name is None:
                        print("invalid expression at " + str(idx) + ": query name expected first")
                    else:
                        query_expression = parts[1]

                        # query_offset = len(all_queries)
                        #query_offset = int(current_name.split("-")[-1]) - 1

                        # RZ: modify for ARQMath topic names.
                        query_offset = int(re.split('\.|-',current_name)[-1]) - 1

                        if html_prefix != None:
                            mathml = mathml_cache.get(-1, query_offset, query_expression, True)

                            # create empty directories for this query ...
                            if not os.path.isdir(html_prefix + "/" + current_name):
                                os.makedirs(html_prefix + "/" + current_name)

                            if not os.path.isdir(html_prefix + "/" + current_name + "/images"):
                                os.makedirs(html_prefix + "/" + current_name + "/images")
                        else:
                            mathml = None

                        current_query = Query(current_name, query_expression, mathml, tuple_ret_time, max_k, is_OPT)
                        current_name = None
                        all_queries.append(current_query)

                        print("Query: " + current_query.name + ": " + current_query.expression)
                        # print(mathml)
                        # current_query.tree.save_as_dot("expre_" + str(idx) + ".gv")

                elif parts[0][0] == "C":
                    if current_query is None:
                        print("invalid constraint at " + str(idx) + ": query expression expected first")
                    else:
                        # create a constraint tree
                        current_query.set_constraints(parts[1], is_OPT)

            # RZ: Record tuple-based retrieval time and other metrics.
            if len(parts) == 3 and parts[0][0] == "I" and current_query != None:
                if parts[1] == "qt":
                    current_query.initRetrievalTime = float(parts[2])
                elif parts[1] == "post":
                    current_query.postings = int(parts[2])
                elif parts[1] == "expr":
                    current_query.matchedFormulae = int(parts[2])
                elif parts[1] == "doc":
                    current_query.matchedDocs = int(parts[2])

            if len(parts) == 5:
                if parts[0][0] == "R":
                    doc_id = int(parts[1])
                    location = int(parts[2])
                    doc_name = math_doc.find_doc_file(doc_id)

                    expression = parts[3]
                    if parts[4][0] == "[" and parts[4][-1] == "]":
                        scores = [float(value) for value in parts[4][1:-1].split(",")]
                    else:
                        scores = [float(parts[4])]

                    if html_prefix != None:
                        mathml = mathml_cache.get(doc_id, location, expression)
                    else:
                        mathml = None

                    if current_query is None:
                        print("Error: result listed before a query, line " + str(idx))
                    else:
                        current_query.add_result(doc_id, doc_name, location, expression, scores, mathml)

        return all_queries




