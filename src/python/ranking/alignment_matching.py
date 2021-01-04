
import itertools

from .alignment import Alignment
from .matching_result import MatchingResult
from .scoring_helper import ScoringHelper
from .wildcard_alignment import WildcardAlignment

from TangentS.math.math_symbol import MathSymbol
from TangentS.math.layout_symbol import LayoutSymbol
from TangentS.math.semantic_symbol import SemanticSymbol

# =========================================================
#  Helper class with alignment-based matching functions
# =========================================================

class AlignmentMatching:
    OPTComb_none = 0            # Match without considering combinations (original order)
    OPTComb_same_op = 1         # All combinations for aligned operators
    OPTComb_greedy_same_op = 2  # All combinations for aligned operators in greedy order

    OPTStrict_any = 0           # Match children of all branches without requiring to match internal nodes
    OPTStrict_subtype = 1       # Internal nodes must be patched at least to the subtype
    OPTStrict_exact = 2         # Internal nodes must be matched exactly

    @staticmethod
    def match_SLT(tree_query, tree_candidate, tree_constraints, unify, wildcard_subtreess, best_only, scoring):
        assert isinstance(scoring, ScoringHelper)

        align_info = AlignmentMatching.get_possible_alignments(tree_query, tree_candidate, tree_constraints, unify)
        all_alignments, q_size, c_size, restricted_vars = align_info

        # evaluate alignments ....
        p_alignments = list(all_alignments)
        #print("")

        #print("Total Alignments: " + str(len(p_alignments)))
        #print("Query size: " + str(q_size))
        #print("Candidate size: " + str(c_size))

        scored_alignments = []

        # Now, compute a score for each possible sub alignment
        for alignment in all_alignments:
            if alignment in p_alignments:
                match_info = AlignmentMatching.test_SLT_alignment(alignment, p_alignments, tree_query.root,
                                                                  tree_candidate.root, restricted_vars, q_size, c_size,
                                                                  unify, wildcard_subtreess)

                scores = scoring.score_alignment(match_info)

                scored_alignments.append((scores, alignment, match_info))

        scored_alignments = sorted(scored_alignments, reverse=True, key=lambda x: x[0])

        #print("Actual alignment roots tested: " + str(len(scored_alignments)))

        # select final matches ....
        if len(scored_alignments) > 0:
            if best_only:
                # use match with highest score only ...
                result_match = scored_alignments[0][2]

            else:
                # combine compatible alignments into a single, bigger match
                result_match = AlignmentMatching.greedy_combine_aligments(scored_alignments, scoring)
        else:
            # create empty match ...
            result_match = MatchingResult.FromEmptyAlignment(tree_query.root, q_size, tree_candidate.root, c_size)
            scoring.score_alignment(result_match)

        # produce highlighting information
        result_match.update_alignments_locations()

        # return match results ...
        return result_match

    @staticmethod
    def match_OPT(tree_query, tree_candidate, tree_constraints, unify, wildcard_subtreess, comb_mode, strict_mode,
                  scoring):

        assert isinstance(scoring, ScoringHelper)

        align_info = AlignmentMatching.get_possible_alignments(tree_query, tree_candidate, tree_constraints, unify)
        all_alignments, q_size, c_size, restricted_vars = align_info

        # evaluate alignments ....
        p_alignments = list(all_alignments)

        # print(tree_query.tostring())
        # print(tree_candidate.tostring(), flush=True)
        # for alignment in all_alignments:
        #     print(alignment)

        scored_alignments = []

        # Now, compute a score for each possible sub alignment
        for alignment in all_alignments:
            if alignment in p_alignments:
                match_info = AlignmentMatching.test_OPT_alignment(alignment, p_alignments, tree_query.root,
                                                                  tree_candidate.root, restricted_vars, q_size, c_size,
                                                                  unify, wildcard_subtreess, comb_mode, strict_mode)

                scores = scoring.score_alignment(match_info)

                scored_alignments.append((scores, alignment, match_info))

        scored_alignments = sorted(scored_alignments, reverse=True, key=lambda x: x[0])

        # select final matches ....
        if len(scored_alignments) > 0:
            # use match with highest score only ...
            result_match = scored_alignments[0][2]
        else:
            # create empty match ...
            result_match = MatchingResult.FromEmptyAlignment(tree_query.root, q_size, tree_candidate.root, c_size)
            scoring.score_alignment(result_match)

        # produce highlighting information
        result_match.update_alignments_locations()

        # return match results ...
        return result_match

    @staticmethod
    def list_SLT_elements(tree_root, path):
        current_elements = [(tree_root, path)]

        for label, child in tree_root.active_children():
            current_elements += AlignmentMatching.list_SLT_elements(child, path + label)

        return current_elements

    @staticmethod
    def list_OPT_elements(tree_root, path):
        current_elements = [(tree_root, path)]

        if tree_root.children is not None:
            for child_idx, child in enumerate(tree_root.children):
                label = SemanticSymbol.idx_rel_type(child_idx)

                current_elements += AlignmentMatching.list_OPT_elements(child, path + label)

        return current_elements

    @staticmethod
    def list_tree_elements(tree):
        if tree.root.is_semantic():
            return AlignmentMatching.list_OPT_elements(tree.root, '')
        else:
            return AlignmentMatching.list_SLT_elements(tree.root, '')

    @staticmethod
    def greedy_unification(unifiable_alignments):
        # ideal unification method (optimization -> pair matching, Hungarian method) might be too heavy.
        # use a faster sub-optimal greedy unification instead

        # the unified tags
        q_unified = {}
        c_unified = {}

        # ... first, identify the possible unifications and count their frequency
        q_vars = {}
        for u_alignment in unifiable_alignments:
            # ... count frequency of matches between query and candidate vars
            if u_alignment.q_element.tag not in q_vars:
                q_vars[u_alignment.q_element.tag] = {}
                q_unified[u_alignment.q_element.tag] = None

            if u_alignment.c_element.tag not in q_vars[u_alignment.q_element.tag]:
                q_vars[u_alignment.q_element.tag][u_alignment.c_element.tag] = 1
            else:
                q_vars[u_alignment.q_element.tag][u_alignment.c_element.tag] += 1

            # ... identify the candidate vars
            if u_alignment.c_element.tag not in c_unified:
                c_unified[u_alignment.c_element.tag] = None

        # ... sort possible unification by frequency
        sorted_vars = []
        for q_tag in q_vars:
            for c_tag in q_vars[q_tag]:
                extra_score = 1 if q_tag == c_tag else 0
                sorted_vars.append(((q_vars[q_tag][c_tag], extra_score), q_tag, c_tag))
        sorted_vars = sorted(sorted_vars, reverse=True)

        # ... unify variables preferring most frequent first  ...
        for scores, q_tag, c_tag in sorted_vars:
            if q_unified[q_tag] is None and c_unified[c_tag] is None:
                # accept unification...
                # also, ensure 1 to 1 relation...
                q_unified[q_tag] = c_tag
                c_unified[c_tag] = q_tag

        return q_unified, c_unified

    @staticmethod
    def greedy_subtree_unification(instances_by_var):
        # This function will check that the same query variables are always assigned to the same subtree
        # If that is not the case, keep the largest subtree for now and reject inconsistent assignments
        valid_by_var = {}
        valid_assignments = []
        invalid_assignments = []
        for name in instances_by_var:
            valid_by_var[name] = 0
            instances = instances_by_var[name]
            if len(instances) >= 2:
                # more than one assignment, find the largest one ...
                longest_idx = 0
                for idx in range(1, len(instances)):
                    if instances[idx].c_size > instances[longest_idx].c_size:
                        longest_idx = idx

                largest_tree_string = instances[longest_idx].c_tree.tostring()
                for alignment in instances:
                    if alignment.c_tree.tostring() == largest_tree_string:
                        valid_assignments.append(alignment)
                        valid_by_var[name] += 1
                    else:
                        invalid_assignments.append(alignment)
            else:
                # only one instance, always valid ...
                valid_assignments.append(instances[0])
                valid_by_var[name] += 1

        return valid_assignments, invalid_assignments, valid_by_var

    @staticmethod
    def get_wildcard_instances_by_var(unifiable_qvars):
        instances_by_var = {}
        for alignment in unifiable_qvars:
            assert isinstance(alignment, WildcardAlignment)

            name = alignment.q_variable.tag
            if name not in instances_by_var:
                instances_by_var[name] = []

            instances_by_var[name].append(alignment)

        return instances_by_var

    @staticmethod
    def wildcard_expansion_SLT(root_1, root_2, root_c, unify):

        children_tests = []
        subtree_root = LayoutSymbol(root_2.tag)

        if root_2.next is not None:
            # check if it can be expanded ....
            hor_expandable = root_1.wildcard_hor_expandable()

            if root_1.next is not None:
                if hor_expandable:
                    # search for next tag (horizontal expansion)
                    # start wildcard match
                    subtree_root.next = LayoutSymbol.Copy(root_2.next)

                    # search for exact match first  ...
                    tempo = subtree_root
                    comma_rel = 'n'
                    exact_found = False
                    while tempo.next is not None:
                        if tempo.next.tag == root_1.next.tag:
                            # matching element found
                            children_tests.append((root_1.next, tempo.next, root_c.next, 'n', comma_rel))

                            # detach next from subtree ...
                            tempo.next = None

                            # search complete
                            exact_found = True
                            break

                        # continue search
                        tempo = tempo.next
                        comma_rel += 'n'

                    # if not exact is found ...
                    unifiable_found = False
                    if not exact_found and unify:

                        # search for unifiable match...
                        tempo = subtree_root
                        comma_rel = 'n'
                        while tempo.next is not None:
                            if root_c.next.tag.check_unifiable(root_1.next, tempo.next):
                                # matching element found
                                children_tests.append((root_1.next, tempo.next, root_c.next, 'n', comma_rel))

                                # detach next from subtree ...
                                tempo.next = None

                                # search complete
                                unifiable_found = True
                                break

                            # continue search
                            tempo = tempo.next
                            comma_rel += 'n'
                else:
                    # cannot be expanded ...
                    # next will be matched as a normal child
                    children_tests.append((root_1.next, root_2.next, root_c.next, 'n', 'n'))
            else:
                # next will be matched by the wildcard (if it can be expanded)
                if hor_expandable:
                    subtree_root.next = LayoutSymbol.Copy(root_2.next)

        if root_2.above is not None:
            if root_1.above is not None:
                # will be matched as a normal child
                children_tests.append((root_1.above, root_2.above, root_c.above, 'a', 'a'))
            else:
                # will be matched by the wildcard
                subtree_root.above = LayoutSymbol.Copy(root_2.above)

        if root_2.below is not None:
            if root_1.below is not None:
                # will be matched as a normal child
                children_tests.append((root_1.below, root_2.below, root_c.below, 'b', 'b'))
            else:
                # will be matched by the wildcard
                subtree_root.below = LayoutSymbol.Copy(root_2.below)

        if root_2.over is not None:
            if root_1.over is not None:
                # will be matched as a normal child
                children_tests.append((root_1.over, root_2.over, root_c.over, 'o', 'o'))
            else:
                # will be matched by the wildcard
                subtree_root.over = LayoutSymbol.Copy(root_2.over)

        if root_2.under is not None:
            if root_1.under is not None:
                # will be matched as a normal child
                children_tests.append((root_1.under, root_2.under, root_c.under, 'u', 'u'))
            else:
                # will be matched by the wildcard
                subtree_root.under = LayoutSymbol.Copy(root_2.under)

        if root_2.pre_above is not None:
            if root_1.pre_above is not None:
                # will be matched as a normal child
                children_tests.append((root_1.pre_above, root_2.pre_above, root_c.pre_above, 'c', 'c'))
            else:
                # will be matched by the wildcard
                subtree_root.pre_above = LayoutSymbol.Copy(root_2.pre_above)

        if root_2.pre_below is not None:
            if root_1.pre_below is not None:
                # will be matched as a normal child
                children_tests.append((root_1.pre_below, root_2.pre_below, root_c.pre_below, 'd', 'd'))
            else:
                # will be matched by the wildcard
                subtree_root.pre_below = LayoutSymbol.Copy(root_2.pre_below)

        # inherit the within edge (if any)
        subtree_root.within = LayoutSymbol.Copy(root_2.within)

        return children_tests, subtree_root

    @staticmethod
    def wildcard_expansion_OPT(root_1, root_2, root_c, unify):
        # basically, expand wildcard to the entire subtree at root_2
        # here, we expect wildcards to be leaves and not to have children ...
        if not root_1.is_leaf():
            raise Exception("OPT Alignment Error: Unexpected Wildcard as Internal Node")

        subtree_root = SemanticSymbol.Copy(root_2)

        return subtree_root

    @staticmethod
    def root_wildcard_left_expansion_SLT(candidate_root, wildcard_alignment):
        additions = []

        while len(wildcard_alignment.c_location) >= 1 and wildcard_alignment.c_location[-1] == "n":
            # get root ...
            root_path = wildcard_alignment.c_location[:-1]
            parent_root = candidate_root.get_node_from_location(root_path)

            # create copy
            subtree_root = LayoutSymbol(parent_root.tag)

            # set next element (previous root)
            subtree_root.next = wildcard_alignment.c_tree

            # add children (except "next" that is already covered and "element" that is a new baseline)
            if parent_root.above is not None:
                subtree_root.above = LayoutSymbol.Copy(parent_root.above)
            if parent_root.below is not None:
                subtree_root.below = LayoutSymbol.Copy(parent_root.below)

            if parent_root.pre_above is not None:
                subtree_root.pre_above = LayoutSymbol.Copy(parent_root.pre_above)
            if parent_root.pre_below is not None:
                subtree_root.pre_below = LayoutSymbol.Copy(parent_root.pre_below)

            if parent_root.over is not None:
                subtree_root.over = LayoutSymbol.Copy(parent_root.over)
            if parent_root.under is not None:
                subtree_root.under = LayoutSymbol.Copy(parent_root.under)

            if parent_root.within is not None:
                subtree_root.within = LayoutSymbol.Copy(parent_root.within)

            # move to previous element
            wildcard_alignment.c_location = wildcard_alignment.c_location[:-1]
            wildcard_alignment.c_tree = subtree_root

    @staticmethod
    def align_tree_roots(root_1, path_1, root_2, path_2, root_c, restricted_vars, unify, wildcard_subtrees):
        matched = []
        unifiable_qvars = []
        unifiable_vars = []
        unifiable_const = []
        children_tests = []
        total_unmatched = 0

        r1_is_var = root_1.is_variable()
        r2_is_var = root_2.is_variable()

        r1_is_wmat = root_1.is_wildcard_matrix()

        current_alignment = Alignment(root_1, path_1, root_2, path_2)

        # check current alignment ...
        if root_1.tag[0] == "?":
            if wildcard_subtrees:
                # in this metric, query variables can be aligned to any subtree with restrictions

                if isinstance(root_1, LayoutSymbol):
                    # for SLT....
                    # horizontal expansion is restricted only to leaf wildcards ...
                    sub_tests, subtree_root = AlignmentMatching.wildcard_expansion_SLT(root_1, root_2, root_c, unify)
                    children_tests += sub_tests
                else:
                    # for OPT ...
                    subtree_root = AlignmentMatching.wildcard_expansion_OPT(root_1, root_2, root_c, unify)

                subtree_alignment = WildcardAlignment(root_1, path_1, subtree_root, path_2)
                unifiable_qvars.append(subtree_alignment)


            else:
                # only 1-to-1 matches for wildcards ...
                # it's a query variable, it could be align with almost anything ...
                if root_c.tag.check_unifiable(root_1, root_2):
                    # create a 1x1 Wildcard Alignment
                    if isinstance(root_1, LayoutSymbol):
                        # SLT
                        subtree_alignment = WildcardAlignment(root_1, path_1, LayoutSymbol(root_2.tag), path_2)
                    else:
                        # OPT
                        subtree_alignment = WildcardAlignment(root_1, path_1, SemanticSymbol(root_2.tag), path_2)

                    unifiable_qvars.append(subtree_alignment)
                else:
                    total_unmatched += 1

        elif r1_is_var and r2_is_var:
            # check if constraints var ....
            if (not unify) or (root_1.tag in restricted_vars) or (root_2.tag in restricted_vars):
                # can only be matched exactly
                if root_1.tag == root_2.tag:
                    matched.append(current_alignment)
                else:
                    total_unmatched += 1
            else:
                # all other variables could be unifiable (even when exact matches)
                # check for any further restriction 
                if root_c.tag.check_unifiable(root_1, root_2):
                    unifiable_vars.append(current_alignment)
                else:
                    total_unmatched += 1

        elif r1_is_wmat and root_2.tag[0:2] == "M!":
            # consider exact match
            matched.append(current_alignment)

        elif root_1.tag == root_2.tag:
            # exact match
            matched.append(current_alignment)
        else:
            # check if unifiable
            if unify and root_c.tag.check_unifiable(root_1, root_2):
                # constraints allowed unification ...
                unifiable_const.append(current_alignment)
            else:
                # completely unmatched...
                total_unmatched += 1

        root_alignment = MatchingResult.FromTreeAlignment(matched, unifiable_qvars, unifiable_vars, unifiable_const,
                                                          total_unmatched)

        return root_alignment, children_tests


    @staticmethod
    def align_SLT_trees(root_1, path_1, root_2, path_2, root_c, restricted_vars, unify, wildcard_subtrees):

        # Align the roots ....
        root_result, children_tests = AlignmentMatching.align_tree_roots(root_1, path_1, root_2, path_2, root_c,
                                                                         restricted_vars, unify, wildcard_subtrees)

        r1_is_wmat = root_1.is_wildcard_matrix()


        # if the root is not a wildcard
        if not wildcard_subtrees or root_1.tag[0] != "?":
            # children to be tested for alignment.... (only if not query variable or no wildcard expansion)
            if root_1.next is not None and root_2.next is not None:
                children_tests.append((root_1.next, root_2.next, root_c.next, 'n', 'n'))
            if root_1.above is not None and root_2.above is not None:
                children_tests.append((root_1.above, root_2.above, root_c.above, 'a', 'a'))
            if root_1.below is not None and root_2.below is not None:
                children_tests.append((root_1.below, root_2.below, root_c.below, 'b', 'b'))
            if root_1.over is not None and root_2.over is not None:
                children_tests.append((root_1.over, root_2.over, root_c.over, 'o', 'o'))
            if root_1.under is not None and root_2.under is not None:
                children_tests.append((root_1.under, root_2.under, root_c.under, 'u', 'u'))
            if root_1.pre_above is not None and root_2.pre_above is not None:
                children_tests.append((root_1.pre_above, root_2.pre_above, root_c.pre_above, 'c', 'c'))
            if root_1.pre_below is not None and root_2.pre_below is not None:
                children_tests.append((root_1.pre_below, root_2.pre_below, root_c.pre_below, 'd', 'd'))

        if root_1.tag[0:2] == "M!" and root_2.tag[0:2] == "M!":

            if r1_is_wmat:
                if wildcard_subtrees:
                    # wildcard matches everything on the matrix or group...
                    subtree_root = LayoutSymbol.Copy(root_2.within)

                    subtree_alignment = WildcardAlignment(root_1.within, path_1 + "w", subtree_root, path_2 + "w")

                    root_result.unifiable_qvars.append(subtree_alignment)
                else:
                    # wildcard only matches single elements
                    if root_1.within is not None and root_2.within is not None:
                        children_tests.append((root_1.within, root_2.within, root_c.within, 'w', 'w'))
            else:
                # standard match of matrix elements
                m_rows_1, m_cols_1 = LayoutSymbol.get_matrix_size(root_1.tag)
                m_rows_2, m_cols_2 = LayoutSymbol.get_matrix_size(root_2.tag)

                children_1 = root_1.get_element_children()
                children_2 = root_2.get_element_children()
                children_c = root_c.get_element_children()

                if (m_rows_1 == 1 or m_cols_1 == 1) and (m_rows_2 == 1 or m_cols_2 == 1):
                    # both are one-dimensional, compare as a list...
                    child_path = "w"
                    for child_idx in range(min(len(children_1), len(children_2))):
                        children_tests.append((children_1[child_idx], children_2[child_idx], children_c[child_idx],
                                               child_path, child_path))
                        child_path += "e"
                else:
                    # at least one is a matrix, compare as matrices
                    matrix_error = False
                    for child_row in range(min(m_rows_1, m_rows_2)):
                        for child_col in range(min(m_cols_1, m_cols_2)):
                            child_idx_1 = child_row * m_cols_1 + child_col
                            child_idx_2 = child_row * m_cols_2 + child_col

                            if child_idx_1 >= len(children_1) or child_idx_2 >= len(children_2):
                                # bad formed matrix found!
                                warning = "Warning: Bad matrix found, Expected={0:d} x {1:d}, actual elements = {2:d}"
                                if child_idx_1 >= len(children_1):
                                    print(warning.format(m_rows_1, m_cols_1, len(children_1)))
                                if child_idx_2 >= len(children_2):
                                    print(warning.format(m_rows_2, m_cols_2, len(children_2)))

                                matrix_error = True
                                break

                            child_1 = children_1[child_idx_1]
                            child_c = children_c[child_idx_1]
                            child_2 = children_2[child_idx_2]

                            child_path_1 = "w" + "e" * child_idx_1
                            child_path_2 = "w" + "e" * child_idx_2

                            children_tests.append((child_1, child_2, child_c, child_path_1, child_path_2))

                        if matrix_error:
                            break
        else:
            # other elements different from M! that might contain elements within
            # note that wildcards cannot have a within link
            if root_1.within is not None and root_2.within is not None:
                children_tests.append((root_1.within, root_2.within, root_c.within, 'w', 'w'))

        # for all children tests ....
        for child_1, child_2, constrain, relation1, relation2 in children_tests:
            # evaluate alignment ....
            child_res = AlignmentMatching.align_SLT_trees(child_1, path_1 + relation1, child_2, path_2 + relation2,
                                                          constrain, restricted_vars, unify, wildcard_subtrees)
            # merge .....
            root_result.add_alignment(child_res)

        return root_result

    @staticmethod
    def OPT_same_order_children_tests(children_1, children_2, children_c):
        order_tests = []

        # Simply add all pairs in their sequential order
        for child_idx in range(min(len(children_1), len(children_2))):
            label = SemanticSymbol.idx_rel_type(child_idx)

            child_1 = children_1[child_idx]
            child_2 = children_2[child_idx]
            child_c = children_c[child_idx]

            order_tests.append((child_1, child_2, child_c, label, label))

        return order_tests

    @staticmethod
    def OPT_children_permutations(children_1, children_2, children_c):
        # get permutations for the longest list of children (indices)
        if len(children_1) < len(children_2):
            comb_len = len(children_1)
            permutations = itertools.permutations(range(len(children_2)), len(children_1))
        else:
            comb_len = len(children_2)
            permutations = itertools.permutations(range(len(children_1)), len(children_2))

        # create a list for each permutation ...
        final_permutations = []
        for perm in permutations:
            # get the final pairings of children indices ...
            if len(children_1) < len(children_2):
                zipped = zip(range(len(children_1)), perm)
            else:
                zipped = zip(perm, range(len(children_2)))

            # use the paired indices to create the list of all possible alignments between children ....
            children_tests = []
            for child_idx_1, child_idx_2 in zipped:
                label_1 = SemanticSymbol.idx_rel_type(child_idx_1)
                label_2 = SemanticSymbol.idx_rel_type(child_idx_2)

                child_1 = children_1[child_idx_1]
                child_2 = children_2[child_idx_2]
                child_c = children_c[child_idx_1]

                children_tests.append((child_1, child_2, child_c, label_1, label_2))

            final_permutations.append(children_tests)

        return final_permutations

    @staticmethod
    def OPT_greedy_permutation(children_1, path_1, children_2, path_2, children_c, restricted_vars, unify,
                               wildcard_subtrees, comb_mode, strict_mode, pair_cache):

        # test alignments for individual pairs ....
        comb_scores = []
        for child_idx_1 in range(len(children_1)):
            label_1 = SemanticSymbol.idx_rel_type(child_idx_1)
            child_1 = children_1[child_idx_1]
            child_c = children_c[child_idx_1]

            pair_cache[label_1] = {}

            for child_idx_2 in range(len(children_2)):
                label_2 = SemanticSymbol.idx_rel_type(child_idx_2)
                child_2 = children_2[child_idx_2]

                res = AlignmentMatching.align_OPT_trees(child_1, path_1 + label_1, child_2, path_2 + label_2,
                                                        child_c, restricted_vars, unify, wildcard_subtrees,
                                                        comb_mode, strict_mode)

                pair_cache[label_1][label_2] = res

                comb_scores.append((res.max_potential_query_matches(), len(res.matches_exact), -child_idx_1, -child_idx_2))

        # sort by descending score....
        # indices are negative, so they will be sorted by ascending order once applied absolute value
        comb_scores = sorted(comb_scores, reverse=True)

        children_tests = []
        choosen_children_1 = {}
        choosen_children_2 = {}

        max_tests = min(len(children_1), len(children_2))
        non_trivial = False
        for score_1, score_2, neg_idx_1, neg_idx_2 in comb_scores:
            if neg_idx_1 in choosen_children_1 or neg_idx_2 in choosen_children_2:
                # one of the children has been already chosen ...
                continue

            # add test ...
            label_1 = SemanticSymbol.idx_rel_type(-neg_idx_1)
            label_2 = SemanticSymbol.idx_rel_type(-neg_idx_2)

            child_1 = children_1[-neg_idx_1]
            child_2 = children_2[-neg_idx_2]
            child_c = children_c[-neg_idx_1]

            children_tests.append((child_1, child_2, child_c, label_1, label_2))
            choosen_children_1[neg_idx_1] = True
            choosen_children_2[neg_idx_2] = True

            if neg_idx_1 != neg_idx_2:
                non_trivial = True

            if len(children_tests) == max_tests:
                # found pairing for all children that could be paired ...
                break

        """
        if non_trivial and len(children_tests) > 5:
            print([child.tag for child in children_1])
            print([child.tag for child in children_2])
            print(comb_scores)

            print(children_tests)
        """

        return children_tests


    @staticmethod
    def align_OPT_trees(root_1, path_1, root_2, path_2, root_c, restricted_vars, unify, wildcard_subtrees, comb_mode,
                        strict_mode):

        # For  OPTs, we do not expect candidate alignments to be tested from the root ....
        # These are considered at this point only for wildcard horizontal expansion in SLT. ...
        root_result, _ = AlignmentMatching.align_tree_roots(root_1, path_1, root_2, path_2, root_c, restricted_vars,
                                                            unify, wildcard_subtrees)

        r1_is_wmat = root_1.is_wildcard_matrix()

        children_tests = []
        pair_cache = {}

        if root_1.tag[0:2] == "M!" and root_2.tag[0:2] == "M!":
            # matrix and groups, special cases...
            if root_1.tag[0:3] == root_2.tag[0:3]:
                # only if the group is of the same type ....
                if r1_is_wmat:
                    # handle wildcard matrices matches as special case ....
                    raise Exception("Wildcard Matrix not yet supported")

                # other matches will not be considered
                elif root_1.tag[2] in ["D", "V", "S", "L", "R"]:
                    # match children linearly in order ....
                    order_tests = AlignmentMatching.OPT_same_order_children_tests(root_1.children, root_2.children,
                                                                                  root_c.children)

                    children_tests.append(order_tests)

                elif root_1.tag[2] in ["M"]:
                    # squared matrix, match by row/colum position ...
                    order_tests = []

                    for row_idx in range(min(len(root_1.children), len(root_2.children))):
                        row_label = SemanticSymbol.idx_rel_type(row_idx)

                        row_1 = root_1.children[row_idx]
                        row_2 = root_2.children[row_idx]
                        row_c = root_c.children[row_idx]

                        # add the M!R! node to the list of exact matches ....
                        row_alignment = Alignment(row_1, path_1 + row_label, row_2, path_2 + row_label)
                        root_result.matches_exact.append(row_alignment)

                        for col_idx in range(min(len(row_1.children), len(row_2.children))):
                            col_label = SemanticSymbol.idx_rel_type(col_idx)
                            label = row_label + col_label

                            child_1 = row_1.children[col_idx]
                            child_2 = row_2.children[col_idx]
                            child_c = row_c.children[col_idx]

                            order_tests.append((child_1, child_2, child_c, label, label))

                    children_tests.append(order_tests)
                else:
                    raise Exception("Unexpected matrix/group tag " + root_1.tag)

        else:
            # everything else, children will be matched according to Strict Mode and Combination Mode
            if (not root_1.is_leaf()) and (not root_2.is_leaf()):
                # for Strict Mode = Exact, we can do the matching only if roots are identical
                # For Strict Mode = Subtype, we proceed if the subtype of the tags is identical
                # For Strict Mode = Any, we proceeed to match children even if the tags are completely different
                if ((root_1.tag == root_2.tag) or
                    (strict_mode == AlignmentMatching.OPTStrict_subtype and root_1.tag[0:3] == root_2.tag[0:3]) or
                    (strict_mode == AlignmentMatching.OPTStrict_any)):

                    # has to be same operator and it has to be an Unordered operator to test combinations ...
                    combinable_op = (root_1.tag == root_2.tag) and root_1.tag[0] == "U"

                    # do the matching according to the selected mode
                    if (not combinable_op) or comb_mode == AlignmentMatching.OPTComb_none:
                        # do not test any combinations, simply try to match elements in their original order
                        order_tests = AlignmentMatching.OPT_same_order_children_tests(root_1.children, root_2.children,
                                                                                      root_c.children)
                        children_tests.append(order_tests)

                    else:
                        if comb_mode == AlignmentMatching.OPTComb_same_op:
                            # Try all combinations .... (Exponential)
                            # print(str((root_1.tag, path_1, root_2.tag, path_2)), flush=True)
                            children_tests += AlignmentMatching.OPT_children_permutations(root_1.children,
                                                                                          root_2.children,
                                                                                          root_c.children)
                        elif comb_mode == AlignmentMatching.OPTComb_greedy_same_op:
                            # Try the expected best combination only (N^2)

                            greedy_comb = AlignmentMatching.OPT_greedy_permutation(root_1.children, path_1,
                                                                                   root_2.children, path_2,
                                                                                   root_c.children, restricted_vars,
                                                                                   unify, wildcard_subtrees, comb_mode,
                                                                                   strict_mode, pair_cache)
                            children_tests.append(greedy_comb)
                        else:
                            # unknown mode ....
                            raise Exception("OPT Combination mode {0} unknown".format(comb_mode))

        comb_results = []       # [(n_matches, combined_result), .... ] - Keep sorted
        for idx, children_tests in enumerate(children_tests):
            # evaluate current permutation of children alignments ...
            order_result = MatchingResult.FromEmptyAlignment(None, None, None, None)
            for child_1, child_2, constrain, relation1, relation2 in children_tests:
                if relation1 in pair_cache and relation2 in pair_cache[relation1]:
                    # use result in cache ...
                    res = pair_cache[relation1][relation2]
                else:
                    # first time seen, compute alignment ....
                    res = AlignmentMatching.align_OPT_trees(child_1, path_1 + relation1, child_2, path_2 + relation2,
                                                            constrain, restricted_vars, unify, wildcard_subtrees,
                                                            comb_mode, strict_mode)
                    # add to pair cache ...
                    if not relation1 in pair_cache:
                        pair_cache[relation1] = {}

                    pair_cache[relation1][relation2] = res

                # combine alignment results ....
                order_result.add_alignment(res)

            # compute score for combination
            score = (order_result.max_potential_query_matches(), len(order_result.matches_exact))

            comb_results.append((idx, score, order_result))

        # greedily choose the combination (order of children matching)
        # that has the maximum number of potential matches
        comb_results = sorted(comb_results, key=lambda result: result[1], reverse=True)

        if len(comb_results) > 0:
            # Select the top match ....
            idx, score, best_result = comb_results[0]

            """
            if idx > 0 and len(comb_results) > 10:
                print(str((root_1.tag, path_1, root_2.tag, path_2)), flush=True)
                print(comb_results, flush=True)
                x = 5 / 0
            """

            # Add best combination to current alignment ...
            root_result.add_alignment(best_result)

        return root_result

    @staticmethod
    def alignment_unification(tree_results, qvar_instances, unify_vars):
        # Common processing of variable and wildcard unification for both SLT and OPT

        tree_results.matches_unified = []

        # check if normal variables have to be unified
        if unify_vars:

            # greedy unification of normal variables
            q_unified, c_unified = AlignmentMatching.greedy_unification(tree_results.unifiable_vars)

            # ... apply unified variables to compute total matches ...
            for u_alignment in tree_results.unifiable_vars:
                # check ...
                if q_unified[u_alignment.q_element.tag] == u_alignment.c_element.tag:
                    if u_alignment.q_element.tag == u_alignment.c_element.tag:
                        # same variable, count as standard match...
                        tree_results.matches_exact.append(u_alignment)
                    else:
                        tree_results.matches_unified.append(u_alignment)

            # unified constants
            for u_alignment in tree_results.unifiable_const:
                tree_results.matches_unified.append(u_alignment)
        else:
            # no unification performed ...
            q_unified, c_unified = {}, {}

        # greedy unification of query variables with subtrees ...
        # here, the 1-to-1 or 1-to-many (subtree) matching restriction has been applied in the previous step
        # and we can simply run these tests to check for wildcard constrains
        unified_subtrees_children = []
        if len(tree_results.unifiable_qvars) > 0:
            # (accept or reject query variable matches based on size)
            unified_qvars, unmatched_qvars, wc_by_name = AlignmentMatching.greedy_subtree_unification(qvar_instances)

            # add all elements from matched subtrees to list of unified elements
            for wilcard_uni in unified_qvars:
                # get all elements in the subtree
                if isinstance(wilcard_uni.q_variable, LayoutSymbol):
                    subtree_nodes = AlignmentMatching.list_SLT_elements(wilcard_uni.c_tree, wilcard_uni.c_location)
                elif isinstance(wilcard_uni.q_variable, SemanticSymbol):
                    subtree_nodes = AlignmentMatching.list_OPT_elements(wilcard_uni.c_tree, wilcard_uni.c_location)
                else:
                    raise Exception("Unexpected type <" + str(type(wilcard_uni.q_variable)) + "> for query root")

                # add each matched element in the subtree to the unified list
                for c_node, c_path in subtree_nodes:
                    u_alignment = Alignment(wilcard_uni.q_variable, wilcard_uni.q_location, c_node, c_path)

                    unified_subtrees_children.append(u_alignment)

        else:
            # no wildcards ....
            unified_qvars, unmatched_qvars, wc_by_name = [], [], {}

        tree_results.matches_wildcard_q = unified_qvars
        tree_results.matches_wildcard_subtrees = unified_subtrees_children
        tree_results.set_unification_info(q_unified, c_unified, unified_qvars)

    @staticmethod
    def remove_matched_alignments(p_alignments, alignment, tree_results):
        # remove the alignments tested from pending alignments....
        # ... remove matches from list of pending alignments...
        for m_alignment in tree_results.matches_exact:
            if m_alignment in p_alignments:
                p_alignments.remove(m_alignment)

        # also, remove unified from list of pending alignments...
        for u_alignment in tree_results.matches_unified:
            if u_alignment in p_alignments:
                p_alignments.remove(u_alignment)

        # remove roots of unified trees...
        for w_alignment in tree_results.matches_wildcard_q:
            # convert from WildcardAlignment to regular Alignment
            u_alignment = Alignment(w_alignment.q_variable, w_alignment.q_location,
                                    w_alignment.c_tree, w_alignment.c_location)

            if u_alignment in p_alignments:
                p_alignments.remove(u_alignment)

        # check case where root was a variable and was not unified ...
        if alignment in p_alignments:
            # root was not unified or matched. Remove from pending alignments anyway ...
            p_alignments.remove(alignment)


    @staticmethod
    def test_SLT_alignment(alignment, p_alignments, query_root, candidate_root, restricted_vars,
                           size_query, candidate_size, unify, wildcard_subtrees):

        # compute best structural alignment subtree
        tree_results = AlignmentMatching.align_SLT_trees(alignment.q_element, alignment.q_location, alignment.c_element,
                                                         alignment.c_location, alignment.constraint, restricted_vars,
                                                         unify, wildcard_subtrees)

        instances_by_var = AlignmentMatching.get_wildcard_instances_by_var(tree_results.unifiable_qvars)

        # if alignment begins with wildcard .... try left expansion ...
        if wildcard_subtrees and alignment.q_element.tag[0] == "?":
            wc_is_unique = len(instances_by_var[alignment.q_element.tag]) == 1

            hor_expandable = alignment.q_element.wildcard_hor_expandable()

            if len(alignment.c_location) > 0 and alignment.c_location[-1] == "n" and wc_is_unique and hor_expandable:
                wildcard_alignment = instances_by_var[alignment.q_element.tag][0]

                # expand match to the left ...
                AlignmentMatching.root_wildcard_left_expansion_SLT(candidate_root, wildcard_alignment)

        # run greedy unification for Vars and QVars (wildcards)
        AlignmentMatching.alignment_unification(tree_results, instances_by_var, unify)

        # remove all matched alignments already tested from list of pending alignments
        AlignmentMatching.remove_matched_alignments(p_alignments, alignment, tree_results)

        # Record general information about trees being aligned ...
        tree_results.query_size = size_query
        tree_results.query_root = query_root
        tree_results.candidate_size = candidate_size
        tree_results.candidate_root = candidate_root

        return tree_results

    @staticmethod
    def test_OPT_alignment(alignment, p_alignments, query_root, candidate_root, restricted_vars,
                           size_query, candidate_size, unify, wildcard_subtrees, comb_mode, strict_mode):

        # compute best structural alignment subtree
        tree_results = AlignmentMatching.align_OPT_trees(alignment.q_element, alignment.q_location, alignment.c_element,
                                                         alignment.c_location, alignment.constraint, restricted_vars,
                                                         unify, wildcard_subtrees, comb_mode, strict_mode)

        instances_by_var = AlignmentMatching.get_wildcard_instances_by_var(tree_results.unifiable_qvars)

        # no further wildcard expansion is performed in OPT

        # run greedy unification for Vars and QVars (wildcards)
        AlignmentMatching.alignment_unification(tree_results, instances_by_var, unify)

        # remove all matched alignments already tested from list of pending alignments
        AlignmentMatching.remove_matched_alignments(p_alignments, alignment, tree_results)

        # Record general information about trees being aligned ...
        tree_results.query_size = size_query
        tree_results.query_root = query_root
        tree_results.candidate_size = candidate_size
        tree_results.candidate_root = candidate_root

        return tree_results

    @staticmethod
    def get_possible_alignments(tree_query, tree_candidate, tree_constraints, unify):
        all_alignments = []

        # 1) first, list all nodes from the trees
        all_nodes_query = AlignmentMatching.list_tree_elements(tree_query)
        all_nodes_candidate = AlignmentMatching.list_tree_elements(tree_candidate)
        all_nodes_constraints = AlignmentMatching.list_tree_elements(tree_constraints)

        # 2) second, check all possible alignments and restricted vars
        restricted_vars = []
        for idx, q_node in enumerate(all_nodes_query):
            elem_q, loc_q = q_node
            const_info, const_loc = all_nodes_constraints[idx]

            # verify ...
            if loc_q != const_loc:
                raise Exception("Invalid constraint tree used")

            # check if variable and restricted
            if not const_info.tag.unifiable and elem_q.tag[0:2] == "V!":
                # variable not unifiable
                if not elem_q.tag in restricted_vars:
                    restricted_vars.append(elem_q.tag)

            for elem_c, loc_c in all_nodes_candidate:
                add_alignment = False
                if unify:
                    # exact, wildcard and unified matches ...
                    add_alignment = const_info.tag.check_unifiable(elem_q, elem_c)
                else:
                    # only exact and wildcard matches ...
                    add_alignment = (elem_q.tag == elem_c.tag) or (elem_q.is_wildcard())

                if add_alignment:
                    alignment = Alignment(elem_q, loc_q, elem_c, loc_c, const_info)
                    all_alignments.append(alignment)

        # Now, compute a score for each possible sub alignment
        query_size = len(all_nodes_query)
        candidate_size = len(all_nodes_candidate)

        return all_alignments, query_size, candidate_size, restricted_vars


    @staticmethod
    def greedy_combine_aligments(scored_alignments, scoring):
        raise Exception("Greedy combination of multiple alignments not implemented")
