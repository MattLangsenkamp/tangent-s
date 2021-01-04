
from .scoring_helper import ScoringHelper
from .alignment_matching import AlignmentMatching
from .pairs_matching import PairsMatching
from .matching_result import MatchingResult
from TangentS.math.symbol_tree import SymbolTree
from TangentS.math.math_symbol import MathSymbol

class MatchingHelper:
    MatchingPairs = 1
    MatchingAlignment = 2

    WildcardsSingle = 1
    WildcardsSubtreeApprox = 2

    SmallEOB_Depth = 1

    def __init__(self, unification, wildcard_mode):
        self.mode = MatchingHelper.MatchingAlignment

        # general matching parameters
        self.unification = unification
        self.wildcard_mode = wildcard_mode

        # parameters for each particular mode ...
        # (pairs)
        self.pairs_window = 1
        self.pairs_count_constraint = False
        self.pairs_eob = 0

        # (alignments)
        self.alignment_best_only = True
        # by default, the most unrestricted and slow matching configuration ...
        self.alignment_opt_comb = AlignmentMatching.OPTComb_none
        self.alignment_opt_strict = AlignmentMatching.OPTStrict_any

        # (optimizations)
        self.last_query_tree = None
        self.last_query_pairs = None
        self.last_query_eob = None

    @staticmethod
    def CreatePairsMatching(window, eob, unify, constrain_count):

        helper = MatchingHelper(unify, MatchingHelper.WildcardsSingle)
        helper.mode = MatchingHelper.MatchingPairs

        helper.pairs_window = window
        helper.pairs_eob = eob
        helper.pairs_count_constraint = constrain_count

        return helper

    @staticmethod
    def CreateAlignmentMatching(unify, wildcard_mode, best_only, alignment_opt_comb=None, alignment_opt_strict=None):

        helper = MatchingHelper(unify, wildcard_mode)
        helper.mode = MatchingHelper.MatchingAlignment

        helper.alignment_best_only = best_only

        if alignment_opt_comb is not None:
            helper.alignment_opt_comb = alignment_opt_comb
        if alignment_opt_strict is not None:
            helper.alignment_opt_strict = alignment_opt_strict


        return helper

    def match(self, tree_query, tree_candidate, tree_constraints, scoring_helper):
        assert isinstance(tree_query, SymbolTree)
        assert isinstance(tree_candidate, SymbolTree)
        assert isinstance(tree_constraints, SymbolTree)

        if self.mode == MatchingHelper.MatchingPairs:
            # Match and score pairs ...
            result = self.match_pairs(tree_query, tree_candidate, tree_constraints, scoring_helper)
        elif self.mode == MatchingHelper.MatchingAlignment:
            # Match and score alignments
            result = self.match_alignments(tree_query, tree_candidate, tree_constraints, scoring_helper)
        else:
            # empty match by default
            result = MatchingResult()

        # update last query tree seen
        self.last_query_tree = tree_query

        return result

    def match_pairs(self, tree_query, tree_candidate, tree_constraints, scoring_helper):
        # TODO: constraints are currently ignored in this procedure ...

        if tree_query ==self.last_query_tree:
            # use cached pairs from last match ...
            pairs_query = self.last_query_pairs
            eob = self.last_query_eob
        else:
            # update query pairs
            if self.pairs_eob == 2:
                eob = tree_query.tree_depth() <= MatchingHelper.SmallEOB_Depth
            else:
                eob = self.pairs_eob == 1

            pairs_query = tree_query.root.get_pairs("", self.pairs_window, eob, False)
            self.last_query_pairs = pairs_query
            self.last_query_eob = eob

        pairs_candidate = tree_candidate.root.get_pairs("", self.pairs_window, eob, False)

        if len(pairs_query) == 0 or len(pairs_candidate) == 0:
            # Empty match ....
            match = MatchingResult.FromPairs([], len(pairs_query), [], len(pairs_candidate))
        else:
            # compute pair match ...
            match = PairsMatching.match(pairs_query, pairs_candidate, self.unification, self.pairs_count_constraint)

        # now, score the match ....
        scoring_helper.score_pairs(match)

        # return all info ...
        return match


    def match_alignments(self, tree_query, tree_candidate, tree_constraints, scoring_helper):
        wildcard_subtree = self.wildcard_mode == MatchingHelper.WildcardsSubtreeApprox

        # use helper class to do compute and score the match ...
        if not tree_query.is_semantic():
            match = AlignmentMatching.match_SLT(tree_query, tree_candidate, tree_constraints, self.unification,
                                                wildcard_subtree, self.alignment_best_only, scoring_helper)
        else:
            match = AlignmentMatching.match_OPT(tree_query, tree_candidate, tree_constraints, self.unification,
                                                wildcard_subtree, self.alignment_opt_comb, self.alignment_opt_strict,
                                                scoring_helper)

        return match
