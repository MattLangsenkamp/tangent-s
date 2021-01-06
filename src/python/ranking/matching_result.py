from src.python.math.math_symbol import MathSymbol


class MatchingResult:
    def __init__(self):
        # most common attributes ...
        self.scores = None

        self.query_size = None
        self.query_root = None

        self.candidate_size = None
        self.candidate_root = None

        # unification results ....
        self.var_q_unified = None       # Dict from q tag to c tag
        self.var_c_unified = None       # Dict from c tag to q tag
        self.qvar_unified = None        # List of accepted WildcardAlignment

        # alignment-based matches (should be lists of alignments)...
        self.matches_unified = None
        self.matches_exact = None
        self.matches_wildcard_q = None
        self.matches_wildcard_subtrees = None

        # temporary values for alignment-based matching. Should be lists of alignments
        self.unifiable_vars = None
        self.unifiable_qvars = None
        self.unifiable_const = None
        # count (int). For alignments.
        self.total_unmatched_q = 0

        # matches based on pairs
        self.pairs_total_q = None
        self.pairs_total_c = None
        self.pairs_matched_q = None
        self.pairs_matched_c = None
        self.pairs_u_matched_q = None
        self.pairs_u_matched_c = None

        # for common highlighting, patch to matches
        self.locs_q_exact = {}
        self.locs_c_exact = {}
        self.locs_q_unified = {}
        self.locs_c_unified = {}
        self.locs_q_wildcard = {}
        self.locs_c_wildcard = {}

    def set_locations(self, locs_c_exact, locs_c_unified, locs_c_wildcard,
                      locs_q_exact=None, locs_q_unified=None, locs_q_wildcard=None):
        if locs_q_exact is None:
            locs_q_exact = {}
        if locs_q_unified is None:
            locs_q_unified = {}
        if locs_q_wildcard is None:
            locs_q_wildcard = {}

        assert isinstance(locs_c_exact, dict)
        assert isinstance(locs_c_unified, dict)
        assert isinstance(locs_c_wildcard, dict)
        assert isinstance(locs_q_exact, dict)
        assert isinstance(locs_q_unified, dict)
        assert isinstance(locs_q_wildcard, dict)

        self.locs_c_exact = locs_c_exact
        self.locs_c_unified = locs_c_unified
        self.locs_c_wildcard = locs_c_wildcard
        self.locs_q_exact = locs_q_exact
        self.locs_q_unified = locs_q_unified
        self.locs_q_wildcard = locs_q_wildcard

    def update_alignments_locations(self):
        self.locs_q_exact = {}
        self.locs_c_exact = {}

        self.locs_q_unified = {}
        self.locs_c_unified = {}

        self.locs_q_wildcard = {}
        self.locs_c_wildcard = {}

        # now, to highlight the matches ...
        for match in self.matches_exact:
            loc = MathSymbol.get_child_path(match.q_location, "")
            self.locs_q_exact[loc] = match.q_element

            loc = MathSymbol.get_child_path(match.c_location, "")
            self.locs_c_exact[loc] = match.c_element

        for match in self.matches_wildcard_q:
            loc = MathSymbol.get_child_path(match.q_location, "")
            self.locs_q_wildcard[loc] = match.q_variable

        for match in self.matches_wildcard_subtrees:
            loc = MathSymbol.get_child_path(match.c_location, "")
            self.locs_c_wildcard[loc] = match.c_element

        for match in self.matches_unified:
            loc = MathSymbol.get_child_path(match.q_location, "")
            self.locs_q_unified[loc] = match.q_element

            loc = MathSymbol.get_child_path(match.c_location, "")
            self.locs_c_unified[loc] = match.c_element

    def set_unification_info(self, var_q_unified, var_c_unified, qvar_unified):
        self.var_q_unified = var_q_unified
        self.var_c_unified = var_c_unified
        self.qvar_unified = qvar_unified

    def query_nodes_matched(self, exact, unified, wildcards):
        q_nodes_matched = []
        if exact:
            q_nodes_matched += self.matches_exact
        if unified:
            q_nodes_matched += self.matches_unified
        if wildcards:
            q_nodes_matched += self.matches_wildcard_q

        return q_nodes_matched

    def candidate_nodes_matched(self, exact, unified, wildcards):
        c_nodes_matched = []
        if exact:
            c_nodes_matched += self.matches_exact
        if unified:
            c_nodes_matched += self.matches_unified
        if wildcards:
            c_nodes_matched += self.matches_wildcard_subtrees

        return c_nodes_matched

    def max_potential_query_matches(self):
        total_potential = len(self.matches_exact)
        total_potential += len(self.unifiable_qvars)
        total_potential += len(self.unifiable_vars)
        total_potential += len(self.unifiable_const)

        return total_potential

    def total_query_nodes_edges_matched(self, exact, unified, wildcards):
        q_nodes_matched = self.query_nodes_matched(exact, unified, wildcards)
        q_matches = len(q_nodes_matched)

        # compute query matched edges
        q_locations = [match.q_location for match in q_nodes_matched]
        q_matched_edges = MatchingResult.matched_edges_from_locations(q_locations)

        return q_matches, q_matched_edges

    def total_candidates_nodes_edges_matched(self, exact, unified, wildcards):
        c_nodes_matched = self.candidate_nodes_matched(exact, unified, wildcards)
        c_matches = len(c_nodes_matched)

        # compute query matched edges
        c_locations = [match.q_location for match in c_nodes_matched]
        c_matched_edges = MatchingResult.matched_edges_from_locations(c_locations)

        return c_matches, c_matched_edges

    def add_alignment(self, other):
        assert isinstance(other, MatchingResult)

        self.matches_exact += other.matches_exact
        self.unifiable_qvars += other.unifiable_qvars
        self.unifiable_vars += other.unifiable_vars
        self.unifiable_const += other.unifiable_const
        self.total_unmatched_q += other.total_unmatched_q

    @staticmethod
    def FromPairs(matched_pairs_query, total_pairs_q, matched_pairs_candidate, total_pairs_c,
                  matched_u_pairs_query=None, matched_u_pairs_candidate=None):
        result = MatchingResult()

        result.pairs_total_q = int(total_pairs_q)
        result.pairs_total_c = int(total_pairs_c)
        result.pairs_matched_q = matched_pairs_query
        result.pairs_matched_c = matched_pairs_candidate

        if matched_u_pairs_query is None:
            result.pairs_u_matched_q = result.pairs_matched_q
        else:
            result.pairs_u_matched_q = matched_u_pairs_query

        if matched_u_pairs_candidate is None:
            result.pairs_u_matched_c = result.pairs_matched_c
        else:
            result.pairs_u_matched_c = matched_u_pairs_candidate

        return result

    @staticmethod
    def FromTreeAlignment(matched_e, unifiable_qvars, unifiable_vars, unifiable_const, total_unmatched_q):
        result = MatchingResult()

        result.matches_exact = matched_e
        result.unifiable_qvars = unifiable_qvars
        result.unifiable_vars = unifiable_vars
        result.unifiable_const = unifiable_const
        result.total_unmatched_q = total_unmatched_q

        return result

    @staticmethod
    def FromEmptyAlignment(q_root, q_size, c_root, c_size):
        result = MatchingResult()

        result.matches_exact = []
        result.unifiable_qvars = []
        result.unifiable_vars = []
        result.unifiable_const = []

        result.matches_unified = []
        result.matches_wildcard_q = []
        result.matches_wildcard_subtrees = []
        result.total_unmatched_q = 0

        result.query_size = q_size
        result.query_root = q_root
        result.candidate_size = c_size
        result.candidate_root = c_root

        return  result

    @staticmethod
    def matched_edges_from_locations(locations):
        return MatchingResult.matched_triplets_from_locations(locations, 1)

    @staticmethod
    def matched_triplets_from_locations(locations, max_window):
        if len(locations) > 0:
            min_len = None
            max_len = None
            full_locations = {}
            for loc in locations:
                current_len = len(loc)

                if min_len is None or current_len < min_len:
                    min_len = current_len
                if max_len is None or current_len > max_len:
                    max_len = current_len

                if current_len in full_locations:
                    full_locations[current_len].append(loc)
                else:
                    full_locations[current_len] = [loc]

            total_triplets = 0
            # count from children to ancestors
            current_len = max_len
            while current_len > min_len:
                # check ...
                if current_len in full_locations:

                    start_len = min_len if max_window == 0 else max(current_len - max_window, min_len)

                    for ancestor_len in range(start_len, current_len):
                        # only do test if ancestor appear at this length
                        if ancestor_len in full_locations:
                            # for each element at current depth, check if ancestor is in the list
                            for loc in full_locations[current_len]:
                                prefix = loc[:ancestor_len]

                                if prefix in full_locations[ancestor_len]:
                                    total_triplets += 1

                current_len -= 1

            return total_triplets
        else:
            return 0
