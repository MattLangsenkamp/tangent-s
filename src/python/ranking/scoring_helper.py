
import statistics

from .matching_result import MatchingResult

class ScoringHelper:
    # Types of matches
    # E = Exact matches
    # W = Wildcard matches
    # U = Unified Matches

    DiceCoeff_EW_Pairs = 0              # Core Engine basic metric, affected by matching configuration
    DiceCoeff_EWU_Pairs = 1             # Core Engine basic metric, added unification

    DiceCoeff_EW_Nodes = 2              # Dice coeff. of EW matching nodes (Recall and Precision)
    DiceCoeff_EWU_Nodes = 3             # Dice coeff. of EWU matching nodes (Recall and Precision)

    MSS = 4                             # Dice Coeff. of Unif. Node Recall and Edge Recall (query-based)
    DiceCoeff_EW_aligned_pairs_w1 = 5   # Modified DiceCoeff_EW_Pairs for alignment-based matching (+1 Edge fix, window =1, no EOB)
    DiceCoeff_EWU_aligned_pairs_w1 = 6  # Modified DiceCoeff_EWU_Pairs for alignment-based matching (+2 Edge fix, window =1, no EOB)
    DiceCoeff_EW_aligned_pairs_w0 = 7   # Modified DiceCoeff_EW_Pairs for alignment-based matching (+1 Edge fix, window =0, no EOB)
    DiceCoeff_EWU_aligned_pairs_w0 = 8  # Modified DiceCoeff_EWU_Pairs for alignment-based matching (+2 Edge fix, window =0, no EOB)
    DiceCoeff_MSS_EW_Recall = 9         # Dice coefficient of MSS and EW recall

    NegCount_EW_q_unmatched_nodes = 11   # Tie-breaker: Negative of query nodes not mached by EW
    NegCount_EWU_q_unmatched_nodes = 12  # Tie-breaker: Negative of query nodes not mached by EWU
    NegCount_EW_c_unmatched_nodes = 13   # Tie-breaker: Negative of candidate nodes not mached by EW
    NegCount_EWU_c_unmatched_nodes = 14  # Tie-breaker: Negative of candidate nodes not mached by EWU
    NegCount_W_c_matched_nodes = 15      # Tie-breaker: Negative of candidate nodes matched by Wildcards
    NegSTDev_W_c_matched_nodes = 16      # Tie-breaker: Negative of Standard Deviation of wildcard matches size

    Count_EW_q_matched_nodes = 20       # Tie-breaker: query nodes matched by EW
    Count_EWU_q_matched_nodes = 21      # Tie-breaker: query nodes matched by EWU
    Count_EW_c_matched_nodes = 22       # Tie-breaker: candidate nodes matched by EW
    Count_EWU_c_matched_nodes = 23      # Tie-breaker: candidate nodes matched by EWU

    Recall_EW_matched_nodes = 30        # Recall of Exact and wildcard matches
    Precision_EWU_matched_nodes = 35    # Precision of Exact, Wildcard and Unified matches

    Pos_Left_Baseline1 = 41             # Position in Main baseline of first matching node (SLT only)
    Pos_Left_Baseline2 = 42             # Position in Child baseline of first matching node (SLT only)
    Pos_Left_Baseline3 = 43             # Position in Child of Child baseline of first matching node (SLT only)
    Pos_Left_Baseline4 = 44             # Position in Child of Child of Child baseline of first matching node (SLT only)

    def __init__(self, active_scores):
        self.active_scores = active_scores

    def score_pairs(self, matching):
        assert isinstance(matching, MatchingResult)

        scores = []
        for score in self.active_scores:
            if score == ScoringHelper.DiceCoeff_EW_Pairs:
                scores.append(ScoringHelper.get_pairs_fmeasure(matching))

            if score == ScoringHelper.DiceCoeff_EWU_Pairs:
                scores.append(ScoringHelper.get_unified_pairs_fmeasure(matching))

        matching.scores = scores

        return scores

    def score_alignment(self, matching):
        assert isinstance(matching, MatchingResult)

        scores = []
        leftmost_scores = None
        for score in self.active_scores:
            if score == ScoringHelper.DiceCoeff_EW_Nodes:
                scores.append(ScoringHelper.get_node_fmeasure(matching))

            if score == ScoringHelper.DiceCoeff_EWU_Nodes:
                scores.append(ScoringHelper.get_unified_node_fmeasure(matching))

            if score == ScoringHelper.MSS:
                scores.append(ScoringHelper.get_MSS(matching))

            if score == ScoringHelper.NegCount_EW_q_unmatched_nodes:
                scores.append(ScoringHelper.get_negative_count_query_unmatched(matching, True, False, True))

            if score == ScoringHelper.NegCount_EWU_q_unmatched_nodes:
                scores.append(ScoringHelper.get_negative_count_query_unmatched(matching, True, True, True))

            if score == ScoringHelper.NegCount_EW_c_unmatched_nodes:
                scores.append(ScoringHelper.get_negative_count_candidate_unmatched(matching, True, False, True))

            if score == ScoringHelper.NegCount_EWU_c_unmatched_nodes:
                scores.append(ScoringHelper.get_negative_count_candidate_unmatched(matching, True, True, True))

            if score == ScoringHelper.NegCount_W_c_matched_nodes:
                scores.append(ScoringHelper.get_negative_count_candidate_wildcard_matches(matching))

            if score == ScoringHelper.Count_EW_q_matched_nodes:
                scores.append(ScoringHelper.get_count_query_matched(matching, True, False, True))

            if score == ScoringHelper.Count_EWU_q_matched_nodes:
                scores.append(ScoringHelper.get_count_query_matched(matching, True, True, True))

            if score == ScoringHelper.Count_EW_c_matched_nodes:
                scores.append(ScoringHelper.get_count_candidate_matched(matching, True, False, True))

            if score == ScoringHelper.Count_EWU_c_matched_nodes:
                scores.append(ScoringHelper.get_count_candidate_matched(matching, True, True, True))

            if score == ScoringHelper.Precision_EWU_matched_nodes:
                scores.append(ScoringHelper.get_nodes_precision(matching, True, True, True))

            if score == ScoringHelper.Recall_EW_matched_nodes:
                scores.append(ScoringHelper.get_nodes_recall(matching, True, False, True))

            if score == ScoringHelper.DiceCoeff_MSS_EW_Recall:
                scores.append(ScoringHelper.get_DiceCoeff_MSS_EW_recall(matching))

            if (score == ScoringHelper.Pos_Left_Baseline1 or score == ScoringHelper.Pos_Left_Baseline2 or
                score == ScoringHelper.Pos_Left_Baseline3 or score == ScoringHelper.Pos_Left_Baseline4):

                if leftmost_scores is None:
                    # compute only once ....
                    leftmost_scores = ScoringHelper.get_leftmost_match_scores(matching, 4)

                # add the requested left-most score ...
                if score == ScoringHelper.Pos_Left_Baseline1:
                    scores.append(leftmost_scores[0])
                elif score == ScoringHelper.Pos_Left_Baseline2:
                    scores.append(leftmost_scores[1])
                elif score == ScoringHelper.Pos_Left_Baseline3:
                    scores.append(leftmost_scores[2])
                elif score == ScoringHelper.Pos_Left_Baseline4:
                    scores.append(leftmost_scores[3])

            if score == ScoringHelper.NegSTDev_W_c_matched_nodes:
                scores.append(ScoringHelper.get_negative_wildcard_match_size_stdev(matching))

            if score == ScoringHelper.DiceCoeff_EW_aligned_pairs_w1:
                scores.append(ScoringHelper.get_DiceCoeff_EW_aligned_pairs(matching, 1))

            if score == ScoringHelper.DiceCoeff_EWU_aligned_pairs_w1:
                scores.append(ScoringHelper.get_DiceCoeff_EWU_aligned_pairs(matching, 1))

            if score == ScoringHelper.DiceCoeff_EW_aligned_pairs_w0:
                scores.append(ScoringHelper.get_DiceCoeff_EW_aligned_pairs(matching, 0))

            if score == ScoringHelper.DiceCoeff_EWU_aligned_pairs_w0:
                scores.append(ScoringHelper.get_DiceCoeff_EWU_aligned_pairs(matching, 0))

        matching.scores = scores

        return scores

    @staticmethod
    def get_pairs_fmeasure(matched):
        assert isinstance(matched, MatchingResult)

        # validate ....
        if (len(matched.pairs_matched_q) == 0 or len(matched.pairs_matched_c) == 0  or
            matched.pairs_total_q == 0 or matched.pairs_total_c == 0):
            return 0.0

        recall = len(matched.pairs_matched_q) / float(matched.pairs_total_q)
        precision = len(matched.pairs_matched_c) / float(matched.pairs_total_c)

        fmeasure = (2.0 * recall * precision) / (recall + precision)

        return fmeasure

    @staticmethod
    def get_unified_pairs_fmeasure(matched):
        assert isinstance(matched, MatchingResult)

        # validate ....
        if (len(matched.pairs_u_matched_q) == 0 or len(matched.pairs_u_matched_c) == 0 or
                    matched.pairs_total_q == 0 or matched.pairs_total_c == 0):
            return 0.0

        recall = len(matched.pairs_u_matched_q) / float(matched.pairs_total_q)
        precision = len(matched.pairs_u_matched_c) / float(matched.pairs_total_c)

        fmeasure = (2.0 * recall * precision) / (recall + precision)

        return fmeasure

    @staticmethod
    def get_node_fmeasure(matched):
        assert isinstance(matched, MatchingResult)

        total_matches_q = len(matched.matches_exact) + len(matched.matches_wildcard_q)
        total_matches_c = len(matched.matches_exact) + len(matched.matches_wildcard_subtrees)

        if total_matches_q == 0  or total_matches_c == 0 or matched.query_size == 0 or matched.candidate_size == 0:
            return 0.0

        recall = total_matches_q / float(matched.query_size)
        precision = total_matches_c / float(matched.candidate_size)

        fmeasure = (2.0 * recall * precision) / (recall + precision)

        return fmeasure

    @staticmethod
    def get_unified_node_fmeasure(matched):
        assert isinstance(matched, MatchingResult)

        matches_common = len(matched.matches_exact) + len(matched.matches_unified)
        total_matches_q = matches_common + len(matched.matches_wildcard_q)
        total_matches_c = matches_common + len(matched.matches_wildcard_subtrees)

        if total_matches_q == 0 or total_matches_c == 0 or matched.query_size == 0 or matched.candidate_size == 0:
            return 0.0

        recall = total_matches_q / float(matched.query_size)
        precision = total_matches_c / float(matched.candidate_size)

        fmeasure = (2.0 * recall * precision) / (recall + precision)

        return fmeasure

    @staticmethod
    def get_MSS(matched):
        assert isinstance(matched, MatchingResult)

        q_unified_matches, q_matched_edges = matched.total_query_nodes_edges_matched(True, True, True)

        u_sym_rec = q_unified_matches / float(matched.query_size)

        if matched.query_size > 1:
            if q_matched_edges > 0:
                u_edge_rec = q_matched_edges / float(matched.query_size - 1)
            else:
                # avoid making f-measure 0 if nodes were matched but no edges were matches
                # assume that less than one edge was matched but not zero
                u_edge_rec = 0.5 / float(matched.query_size - 1)
        else:
            # no edges to match ...
            u_edge_rec = 1.0

        if u_sym_rec + u_edge_rec > 0:
            combined_fmeasure = (2.0 * u_sym_rec * u_edge_rec) / (u_sym_rec + u_edge_rec)
        else:
            combined_fmeasure = 0.0

        return combined_fmeasure

    @staticmethod
    def get_DiceCoeff_MSS_EW_recall(matched):
        assert isinstance(matched, MatchingResult)

        mss = ScoringHelper.get_MSS(matched)
        q_ew_recall = len(matched.query_nodes_matched(True, False, True)) / float(matched.query_size)

        # combined dice coeff. of MSS and EW recall
        if mss + q_ew_recall > 0:
            score = (2.0 * mss * q_ew_recall) / (mss + q_ew_recall)
        else:
            score = 0.0

        return score

    @staticmethod
    def get_count_query_matched(matched, exact, unified, wildcard):
        assert isinstance(matched, MatchingResult)

        total_matched_q = len(matched.query_nodes_matched(exact, unified, wildcard))

        return total_matched_q

    @staticmethod
    def get_nodes_recall(matched, exact, unified, wildcard):
        assert isinstance(matched, MatchingResult)

        total_matched_q = len(matched.query_nodes_matched(exact, unified, wildcard))

        recall = total_matched_q / matched.query_size

        assert 0.0 <= recall <= 1.0

        return recall

    @staticmethod
    def get_count_candidate_matched(matched, exact, unified, wildcard):
        assert isinstance(matched, MatchingResult)

        total_matched_c = len(matched.candidate_nodes_matched(exact, unified, wildcard))

        return total_matched_c

    @staticmethod
    def get_nodes_precision(matched, exact, unified, wildcard):
        assert isinstance(matched, MatchingResult)

        total_matched_c = len(matched.candidate_nodes_matched(exact, unified, wildcard))

        precision = total_matched_c / matched.candidate_size

        assert  0.0 <= precision <= 1.0

        return precision

    @staticmethod
    def get_negative_count_query_unmatched(matched, exact, unified, wildcard):
        assert isinstance(matched, MatchingResult)

        total_matched_q = len(matched.query_nodes_matched(exact, unified, wildcard))

        return -(matched.query_size - total_matched_q)

    @staticmethod
    def get_negative_count_candidate_unmatched(matched, exact, unified, wildcard):
        assert isinstance(matched, MatchingResult)

        total_matched_c = len(matched.candidate_nodes_matched(exact, unified, wildcard))

        return -(matched.candidate_size - total_matched_c)

    @staticmethod
    def get_negative_count_candidate_wildcard_matches(matched):
        assert isinstance(matched, MatchingResult)

        return -len(matched.matches_wildcard_subtrees)

    @staticmethod
    def get_leftmost_match_scores(matched, max_depth):
        assert isinstance(matched, MatchingResult)

        # compute left-most match...
        min_depth_val = None

        all_matches = [(0, matched.matches_exact), (1, matched.matches_wildcard_subtrees), (2, matched.matches_unified)]
        n_types = len(all_matches)
        for c_type, alignments in all_matches:
            for match in alignments:
                match_score = ScoringHelper.match_leftmost_scores(match.c_location, max_depth, n_types, c_type)

                if min_depth_val is None or min_depth_val < match_score:
                    min_depth_val = match_score

        return min_depth_val

    @staticmethod
    def match_leftmost_scores(location, max_depth, n_types, c_type):
        match_score = [0] * max_depth

        current_depth = 0
        loc_pos = 0
        baseline_pos = 0
        while loc_pos < len(location) and current_depth < max_depth:
            if location[loc_pos] == "n":
                baseline_pos += 1
            else:
                # change of baseline, write current, reset next
                match_score[current_depth] = -(baseline_pos * (n_types + 1) + c_type)

                baseline_pos = 0
                current_depth += 1

            loc_pos += 1

        if current_depth < max_depth:
            # write current score ...
            match_score[current_depth] = -(baseline_pos * (n_types + 1) + c_type)

        return match_score

    @staticmethod
    def get_negative_wildcard_match_size_stdev(matched):
        assert isinstance(matched, MatchingResult)

        # count wildcard instances and how many matches per wildcard
        count_per_location = {}

        for match in matched.matches_wildcard_subtrees:
            if not match.q_location in count_per_location:
                count_per_location[match.q_location] = 1
            else:
                count_per_location[match.q_location] += 1

        if len(count_per_location) < 2:
            return 0
        else:
            return -statistics.stdev(count_per_location.values())

    @staticmethod
    def get_DiceCoeff_EW_aligned_pairs(matched, window):
        assert isinstance(matched, MatchingResult)

        # q_triplets = len(matched.query_root.get_pairs('', window, False))
        # c_triplets = len(matched.candidate_root.get_pairs('', window, False))
        q_triplets = matched.query_root.count_pairs(window)
        c_triplets = matched.candidate_root.count_pairs(window)

        # ew_matches = exact + wildcard
        q_ew_matches = matched.matches_exact + matched.matches_wildcard_q
        q_ew_locations = [match.q_location for match in q_ew_matches]
        q_ew_triplets = MatchingResult.matched_triplets_from_locations(q_ew_locations, window)

        c_ew_matches = matched.matches_exact + matched.matches_wildcard_subtrees
        c_ew_locations = [match.c_location for match in c_ew_matches]
        c_ew_triplets = MatchingResult.matched_triplets_from_locations(c_ew_locations, window)

        # Giving one extra triplet for free
        ew_edge_recall = (q_ew_triplets + 1.0) / float(q_triplets + 1.0)
        ew_edge_precision = (c_ew_triplets + 1.0) / float(c_triplets + 1.0)

        return (2.0 * ew_edge_recall * ew_edge_precision) / (ew_edge_recall + ew_edge_precision)

    @staticmethod
    def get_DiceCoeff_EWU_aligned_pairs(matched, window):
        assert isinstance(matched, MatchingResult)

        # q_triplets = len(matched.query_root.get_pairs('', window, False))
        # c_triplets = len(matched.candidate_root.get_pairs('', window, False))
        q_triplets = matched.query_root.count_pairs(window)
        c_triplets = matched.candidate_root.count_pairs(window)

        # ew_matches = exact + wildcard
        q_ew_matches = matched.matches_exact + matched.matches_wildcard_q
        q_ew_locations = [match.q_location for match in q_ew_matches]
        q_ew_triplets = MatchingResult.matched_triplets_from_locations(q_ew_locations, window)

        q_u_matches = matched.matches_exact + matched.matches_wildcard_q + matched.matches_unified
        q_u_locations = [match.q_location for match in q_u_matches]
        q_u_triplets = MatchingResult.matched_triplets_from_locations(q_u_locations, window)

        c_ew_matches = matched.matches_exact + matched.matches_wildcard_subtrees
        c_ew_locations = [match.c_location for match in c_ew_matches]
        c_ew_triplets = MatchingResult.matched_triplets_from_locations(c_ew_locations, window)

        c_u_matches = matched.matches_exact + matched.matches_wildcard_subtrees + matched.matches_unified
        c_u_locations = [match.c_location for match in c_u_matches]
        c_u_triplets = MatchingResult.matched_triplets_from_locations(c_u_locations, window)

        # Giving two extra triplets for free (1 for exact + wildcards, 1 for unified)
        ewu_edge_recall = (q_ew_triplets + q_u_triplets + 2.0) / float(2 * (q_triplets + 1))
        ewu_edge_precision = (c_ew_triplets + c_u_triplets + 2.0) / float(2 * (c_triplets + 1))

        score = (2.0 * ewu_edge_recall * ewu_edge_precision) / (ewu_edge_recall + ewu_edge_precision)

        return score
