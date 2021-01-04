
__author__ = 'KMDC'

import time

from .alignment_matching import AlignmentMatching
from .matching_helper import MatchingHelper
from .scoring_helper import ScoringHelper
from .matching_result import MatchingResult

class Reranker:
    def __init__(self, matching, scoring, is_operator):
        self.matching = matching
        self.scoring = scoring
        self.operator = is_operator

        self.query = None


    def set_query(self, current_query):
        self.query = current_query

    def score_match(self, query_tree, result_tree, constraints_tree):
        match = self.matching.match(query_tree, result_tree, constraints_tree, self.scoring)

        return match

    def rerank_query_results(self):
        # Note the sorted function has been added to ensure a more deterministic behavior when re-ranking expressions
        # Since now each candidate for each query on the same file will always be considered in the same order.
        for res_idx, exp_result in enumerate(sorted(self.query.results.keys())):
            result = self.query.results[exp_result]
            print("Reranking query: " + self.query.name + ", Result " + str(res_idx), end="\r", flush=True)

            start_time = time.time()
            if self.matching is None:
                # bypass mode, keep original score, no matching is performed
                matched_c = {}
                scores = result.original_score
            else:
                # apply matching + scoring
                match = self.matching.match(self.query.tree, result.tree, self.query.constraints, self.scoring)
                assert isinstance(match, MatchingResult)

                matched_c = match.locs_c_exact
                assert isinstance(matched_c, dict)
                scores = match.scores

                result.set_unified_elements(match.locs_c_unified)
                result.set_wildcard_matches(match.locs_c_wildcard)

                if match.matches_unified is not None:
                    result.set_all_unified(match.matches_unified)
            end_time = time.time()

            result.set_matched_elements(matched_c)
            result.new_scores = scores
            result.reranking_time = end_time - start_time

        # re-rank based on new score(s)
        self.query.sort_results()
        self.query.sort_documents()


    @staticmethod
    def CreateFromMetricID(metric_id, is_operator, metric_params):

        if metric_id == 0:
            # same as core engine, based on f-measure of matched pairs..
            matching = MatchingHelper.CreatePairsMatching(metric_params["window"], metric_params["eob"], False, False)
            scores = [ScoringHelper.DiceCoeff_EW_Pairs]

        elif metric_id == 1:
            matching = MatchingHelper.CreateAlignmentMatching(False, MatchingHelper.WildcardsSingle, True)

            matching.alignment_opt_comb = AlignmentMatching.OPTComb_same_op
            matching.alignment_opt_strict = AlignmentMatching.OPTStrict_exact

            scores = [ScoringHelper.DiceCoeff_EW_Nodes]

        elif metric_id == 2:
            matching = MatchingHelper.CreatePairsMatching(metric_params["window"], metric_params["eob"], False, True)
            scores = [ScoringHelper.DiceCoeff_EW_Pairs]

        elif metric_id == 3:
            matching = MatchingHelper.CreatePairsMatching(metric_params["window"], metric_params["eob"], True, True)
            scores = [ScoringHelper.DiceCoeff_EWU_Pairs, ScoringHelper.DiceCoeff_EW_Pairs]

        elif metric_id == 4:
            matching = MatchingHelper.CreateAlignmentMatching(True, MatchingHelper.WildcardsSingle, True)

            matching.alignment_opt_comb = AlignmentMatching.OPTComb_same_op
            matching.alignment_opt_strict = AlignmentMatching.OPTStrict_exact

            scores = [ScoringHelper.MSS, ScoringHelper.NegCount_EWU_c_unmatched_nodes,
                      ScoringHelper.Count_EW_q_matched_nodes]

        elif metric_id == 5:
            # TODO: fix matching system that accepts multiple compatible alignments ...
            matching = MatchingHelper.CreateAlignmentMatching(True, MatchingHelper.WildcardsSingle, False)

            matching.alignment_opt_comb = AlignmentMatching.OPTComb_same_op
            matching.alignment_opt_strict = AlignmentMatching.OPTStrict_exact

            scores = [ScoringHelper.MSS, ScoringHelper.NegCount_EWU_c_unmatched_nodes,
                      ScoringHelper.Count_EW_q_matched_nodes]

        elif metric_id == 6:
            matching = MatchingHelper.CreateAlignmentMatching(True, MatchingHelper.WildcardsSubtreeApprox, True)

            matching.alignment_opt_comb = AlignmentMatching.OPTComb_same_op
            matching.alignment_opt_strict = AlignmentMatching.OPTStrict_exact

            scores = [ScoringHelper.DiceCoeff_MSS_EW_Recall, ScoringHelper.NegCount_EWU_c_unmatched_nodes,
                      ScoringHelper.NegCount_W_c_matched_nodes, ScoringHelper.Pos_Left_Baseline1,
                      ScoringHelper.Pos_Left_Baseline2, ScoringHelper.Pos_Left_Baseline3,
                      ScoringHelper.NegSTDev_W_c_matched_nodes]

        elif metric_id == 7:
            matching = MatchingHelper.CreateAlignmentMatching(False, MatchingHelper.WildcardsSubtreeApprox, True)
            matching.alignment_opt_comb = AlignmentMatching.OPTComb_same_op
            matching.alignment_opt_strict = AlignmentMatching.OPTStrict_exact

            scores = [ScoringHelper.DiceCoeff_EW_aligned_pairs_w1]

        elif metric_id == 8:
            matching = MatchingHelper.CreateAlignmentMatching(True, MatchingHelper.WildcardsSubtreeApprox, True)
            matching.alignment_opt_comb = AlignmentMatching.OPTComb_same_op
            matching.alignment_opt_strict = AlignmentMatching.OPTStrict_exact

            scores = [ScoringHelper.DiceCoeff_EWU_aligned_pairs_w1]

        elif metric_id == 9:
            matching = MatchingHelper.CreateAlignmentMatching(False, MatchingHelper.WildcardsSubtreeApprox, True)
            matching.alignment_opt_comb = AlignmentMatching.OPTComb_same_op
            matching.alignment_opt_strict = AlignmentMatching.OPTStrict_exact

            scores = [ScoringHelper.DiceCoeff_EW_aligned_pairs_w0,
                      ScoringHelper.NegCount_W_c_matched_nodes, ScoringHelper.NegSTDev_W_c_matched_nodes,
                      ScoringHelper.Pos_Left_Baseline1, ScoringHelper.Pos_Left_Baseline2]

        elif metric_id == 10:
            matching = MatchingHelper.CreateAlignmentMatching(True, MatchingHelper.WildcardsSubtreeApprox, True)
            matching.alignment_opt_comb = AlignmentMatching.OPTComb_same_op
            matching.alignment_opt_strict = AlignmentMatching.OPTStrict_exact

            scores = [ScoringHelper.DiceCoeff_EWU_aligned_pairs_w0,
                      ScoringHelper.NegCount_W_c_matched_nodes, ScoringHelper.NegSTDev_W_c_matched_nodes,
                      ScoringHelper.Pos_Left_Baseline1, ScoringHelper.Pos_Left_Baseline2]

        elif metric_id == 11:
            matching = MatchingHelper.CreateAlignmentMatching(True, MatchingHelper.WildcardsSubtreeApprox, True)
            matching.alignment_opt_comb = AlignmentMatching.OPTComb_same_op
            matching.alignment_opt_strict = AlignmentMatching.OPTStrict_exact

            scores = [ScoringHelper.MSS, ScoringHelper.NegCount_EWU_c_unmatched_nodes,
                      ScoringHelper.Count_EW_q_matched_nodes]

        elif metric_id == 12:
            # note this version allows "holes" for consistency between SLTs and OPT matching.
            # children of a node can be matched in OPTs even if the parent is not matched, but MSS should rank these
            # candidates lower than those with perfect matching
            matching = MatchingHelper.CreateAlignmentMatching(True, MatchingHelper.WildcardsSubtreeApprox, True,
                                                              AlignmentMatching.OPTComb_greedy_same_op,
                                                              AlignmentMatching.OPTStrict_any)

            scores = [ScoringHelper.MSS, ScoringHelper.Precision_EWU_matched_nodes, ScoringHelper.Recall_EW_matched_nodes]

        else:
            # bypass mode
            matching = None
            scores = []

        scoring = ScoringHelper(scores)

        return Reranker(matching, scoring, is_operator)
