
from .matching_result import MatchingResult
from .scoring_helper import ScoringHelper

from TangentS.math.math_symbol import MathSymbol

# ==================================================
#  Helper class with pair-based matching functions
# ==================================================

class PairsMatching:
    @staticmethod
    def unique_ancestors(pairs_list):
        # count unique elements
        elements = {}
        for ancestor, descendant, rel_location, abs_location in pairs_list:
            if ancestor not in elements:
                elements[ancestor] = {}

            if abs_location not in elements[ancestor]:
                elements[ancestor][abs_location] = 1
            else:
                elements[ancestor][abs_location] += 1

        unique = {}
        for tag in elements:
            unique[tag] = len(elements[tag])

        return unique

    @staticmethod
    def pairs_per_ancestor(pairs):
        per_element = {}
        for ancestor, descendant, relation, location in pairs:
            if ancestor not in per_element:
                per_element[ancestor] = []

            per_element[ancestor].append((ancestor, descendant, relation, location))

        return per_element

    @staticmethod
    def generate_unification_pairs(tag_pairs):
        # This function assumes that all pairs in the input have a common ancestor ...
        unification_pairs = []

        for ancestor, descendant, relation, location in tag_pairs:
            if descendant == ancestor:
                u_descendant = "<U>"
            elif MathSymbol.tag_is_variable(descendant):
                u_descendant = "<V>"
            else:
                u_descendant = descendant

            unification_pairs.append(("<U>", u_descendant, relation, location))

        return unification_pairs

    @staticmethod
    def compute_matches(pairs_a, pairs_b):
        pairs_a_hashed = {}

        # create a temporary index of pairs from list a...
        for current_pair in pairs_a:
            ancestor, descendant, relation, location = current_pair

            pair_id = "[" + ancestor + "][" + descendant + "][" + relation + "]"

            if pair_id in pairs_a_hashed:
                pairs_a_hashed[pair_id].append(current_pair)
            else:
                pairs_a_hashed[pair_id] = [current_pair]

        # count matches from b
        actual_matches = []
        for pair_b in pairs_b:
            ancestor, descendant, relation, location = pair_b
            pair_id = "[" + ancestor + "][" + descendant + "][" + relation + "]"

            if pair_id in pairs_a_hashed:
                # get next matching pair
                pair_a = pairs_a_hashed[pair_id][0]
                del pairs_a_hashed[pair_id][0]

                if len(pairs_a_hashed[pair_id]) == 0:
                    del pairs_a_hashed[pair_id]

                actual_matches.append((pair_a, pair_b))

        return actual_matches

    @staticmethod
    def unify_variables(pairs, variables):
        new_pairs = []

        for ancestor, descendent, relation, location in pairs:
            # check if variable...
            if ancestor in variables:
                if variables[ancestor] is not None:
                    ancestor = "U!" + str(variables[ancestor])
            else:
                # check if constant
                if ancestor[0:2] == "N!":
                    # single value for all constants
                    ancestor = "N!U"

            if descendent in variables:
                if variables[descendent] is not None:
                    descendent = "U!" + str(variables[descendent])
            else:
                # check if constant
                if descendent[0:2] == "N!":
                    # single value for all constants
                    descendent = "N!U"

            new_pairs.append((ancestor, descendent, relation, location))

        return new_pairs

    @staticmethod
    def greedy_unification(pairs_query, pairs_candidate):
        # TODO: the greedy unification here doesn't work as intended. it only considers alignments between variables
        #       that appear as ancestors. This is never the case for operator trees.

        # Find the unique elements and their counts on each expression
        e_query = PairsMatching.unique_ancestors(pairs_query)
        e_candidate = PairsMatching.unique_ancestors(pairs_candidate)

        # separate pairs....
        pairs_element_query = PairsMatching.pairs_per_ancestor(pairs_query)
        pairs_element_candidate = PairsMatching.pairs_per_ancestor(pairs_candidate)

        # identify ancestor variables...
        v_query = {}
        v_candidate = {}

        # ... on query...
        unification_pairs_query = {}
        unification_pairs_candidate = {}
        for tag in e_query:
            if MathSymbol.tag_is_variable(tag):
                v_query[tag] = None
                unification_pairs_query[tag] = PairsMatching.generate_unification_pairs(pairs_element_query[tag])

        # ... on candidate ...
        for tag in e_candidate:
            if MathSymbol.tag_is_variable(tag):
                v_candidate[tag] = None
                unification_pairs_candidate[tag] = PairsMatching.generate_unification_pairs(pairs_element_candidate[tag])

        # Evaluate all possible unifications ...
        unifications = []
        unification_weights = []
        for query_var in v_query:
            for candidate_var in v_candidate:
                # test unification between query_var and candidate_var
                matches = PairsMatching.compute_matches(unification_pairs_query[query_var],
                                                        unification_pairs_candidate[candidate_var])

                matches_q, matches_c = [[pairs_matched[i] for pairs_matched in matches] for i in range(2)]
                matching_results = MatchingResult.FromPairs(matches_q, len(unification_pairs_query[query_var]),
                                                            matches_c, len(unification_pairs_candidate[candidate_var]))

                fmeasure = ScoringHelper.get_pairs_fmeasure(matching_results)
                extra_score = 1.0 if query_var == candidate_var else 0.0

                weight = ((fmeasure, extra_score), query_var, candidate_var)
                unification_weights.append(weight)

        # greedily accept unifications with the most matching pairs ...
        unification_weights = sorted(unification_weights, reverse=True)
        for scores, query_var, candidate_var in unification_weights:
            fmeasure, equal = scores
            if fmeasure > 0.0:
                # check if variables have not been unified yet...
                if v_query[query_var] is None and v_candidate[candidate_var] is None:
                    # Accept unification...
                    u_idx = len(unifications)
                    unifications.append((query_var, candidate_var))
                    v_query[query_var] = u_idx
                    v_candidate[candidate_var] = u_idx

        # print(unifications)
        unified_pairs_query = PairsMatching.unify_variables(pairs_query, v_query)
        unified_pairs_candidate = PairsMatching.unify_variables(pairs_candidate, v_candidate)

        return unified_pairs_query, unified_pairs_candidate

    @staticmethod
    def find_common_elements(elements_a, elements_b):
        common = {}
        for element in elements_a:
            if element in elements_b:
                common[element] = min(elements_a[element], elements_b[element])

        return common

    @staticmethod
    def find_pairs_with_ancestor(pairs, symbol):
        sub_pairs = []
        for ancestor, descendant, relation, location in pairs:
            if ancestor == symbol:
                sub_pairs.append((ancestor, descendant, relation, location))

        return sub_pairs

    @staticmethod
    def pairs_per_instance(pairs):
        per_instance = {}

        for ancestor, descendant, relation, location in pairs:
            if location not in per_instance:
                per_instance[location] = []

            per_instance[location].append((ancestor, descendant, relation, location))

        return per_instance

    @staticmethod
    def total_from_count_per_unique(count_per_unique):
        total_count = 0
        for tag in count_per_unique:
            total_count += count_per_unique[tag]

        return total_count

    @staticmethod
    def restrict_candidate_pairs(e_query, e_candidate, pairs_query, pairs_candidate):
        # Compute counts of shared elements
        overlap = PairsMatching.find_common_elements(e_query, e_candidate)

        # separate pairs....
        pairs_element_query = PairsMatching.pairs_per_ancestor(pairs_query)
        pairs_element_candidate = PairsMatching.pairs_per_ancestor(pairs_candidate)

        # Get a subset of pairs from the candidate which comes
        # from a limited number of overlapping unique elements
        final_pairs_candidate = []

        for ancestor in overlap:
            count = overlap[ancestor]

            # Get all pairs for the current symbol from candidate
            sub_candidate_pairs = pairs_element_candidate[ancestor]

            if count < e_candidate[ancestor]:
                # Get all pairs for that symbol from query
                sub_query_pairs = pairs_element_query[ancestor]

                # Organize candidate pairs by instance....
                sub_pairs_per_instance = PairsMatching.pairs_per_instance(sub_candidate_pairs)

                # score unique instances
                scored_list = []
                for location in sub_pairs_per_instance:
                    matches = PairsMatching.compute_matches(sub_query_pairs, sub_pairs_per_instance[location])
                    score = len(matches)
                    scored_list.append((score, location))

                # prefer unique instances with most matching pairs between query and candidate
                sorted_list = sorted(scored_list, reverse=True)

                # only add the top-count matches from the candidate
                # (will not allow more instances of the same element from the candidate than there are on the query)
                for score, location in sorted_list[:count]:
                    # add pairs...
                    final_pairs_candidate += sub_pairs_per_instance[location]
            else:
                # Add all pairs....
                final_pairs_candidate += sub_candidate_pairs

        return final_pairs_candidate

    @staticmethod
    def matches_locations(matches):
        locs_a = {}
        locs_b = {}
        for pair_a, pair_b in matches:
            # from a ...
            ancestor, descendant, relation, location = pair_a

            if location not in locs_a:
                locs_a[location] = ancestor
            child_location = MathSymbol.get_child_path(location, relation)
            if child_location not in locs_a:
                locs_a[child_location] = descendant

            # from b ...
            ancestor, descendant, relation, location = pair_b
            if location not in locs_b:
                locs_b[location] = ancestor
            child_location = MathSymbol.get_child_path(location, relation)
            if child_location not in locs_b:
                locs_b[child_location] = descendant

        return locs_a, locs_b

    @staticmethod
    def match(pairs_q, pairs_c, unification, count_constraint):
        size_pairs_q = len(pairs_q)
        size_pairs_c = len(pairs_c)

        # Find the unique elements and their counts on each expression
        unique_q = PairsMatching.unique_ancestors(pairs_q)
        unique_c = PairsMatching.unique_ancestors(pairs_c)

        # total elements in the original trees ....
        size_q = PairsMatching.total_from_count_per_unique(unique_q)
        size_c = PairsMatching.total_from_count_per_unique(unique_c)

        if unification:
            # apply greedy unification
            u_pairs_q, u_pairs_c = PairsMatching.greedy_unification(pairs_q, pairs_c)
        else:
            u_pairs_q, u_pairs_c = None, None

        if count_constraint:
            # apply to original pairs ...
            pairs_c = PairsMatching.restrict_candidate_pairs(unique_q, unique_c, pairs_q, pairs_c)

            if unification:
                # apply to unified pairs too
                u_unique_q = PairsMatching.unique_ancestors(u_pairs_q)
                u_unique_c = PairsMatching.unique_ancestors(u_pairs_c)

                u_pairs_c = PairsMatching.restrict_candidate_pairs(u_unique_q, u_unique_c, u_pairs_q, u_pairs_c)

        # compute exact and wildcard matches
        exact_matches = PairsMatching.compute_matches(pairs_q, pairs_c)
        e_matches_q, e_matches_c = [[pairs_matched[i] for pairs_matched in exact_matches] for i in range(2)]

        locs_exact_q, locs_exact_c = PairsMatching.matches_locations(exact_matches)

        locs_unif_c = {}
        locs_unif_q = {}
        if unification:
            # compute pairs matches after unification
            unified_matches = PairsMatching.compute_matches(u_pairs_q, u_pairs_c)
            u_matches_q, u_matches_c = [[pairs_matched[i] for pairs_matched in exact_matches] for i in range(2)]
            locs_EWU_q, locs_EWU_c = PairsMatching.matches_locations(unified_matches)

            # find new locations matched after unification ...
            # (for candidate)
            for location in locs_EWU_c:
                if location not in locs_exact_c:
                    locs_unif_c[location] = 1

            # (for query)
            for location in locs_EWU_q:
                if location not in locs_exact_q:
                    locs_unif_q[location] = 1
        else:
            u_matches_q, u_matches_c = None, None

        # prepare detailed matching results ...
        result = MatchingResult.FromPairs(e_matches_q, size_pairs_q, e_matches_c, size_pairs_c, u_matches_q, u_matches_c)
        result.set_locations(locs_exact_c, locs_unif_c, {}, locs_exact_q, locs_unif_q, {})
        result.query_size = size_q
        result.candidate_size = size_c

        return result
