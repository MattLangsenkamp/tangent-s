__author__ = 'KMDC'

class DocumentRankInfo:
    def __init__(self, doc_id):
        self.doc_id = doc_id
        self.top_formula_score = None
        self.total_score = 0.0
        self.expressions = []

    def add_formula_scores(self, expression, location, scores):
        self.expressions.append((location, expression))

        if self.top_formula_score is None or self.top_formula_score < scores:
            self.top_formula_score = scores

        # add sum of first score as second sort criterion
        self.total_score += scores[0]


    def __repr__(self):
        return "Doc(id=" + str(self.doc_id) + \
               ", top=" + str(["{0:.4f}".format(score) for score in self.top_formula_score]) + \
               ", sum=" + str("{0:.4f}".format(self.total_score)) + ")"

    def get_score_string(self, separator):
        all_scores = ["{0:.4f}".format(score) for score in self.top_formula_score] + \
                     ["{0:.4f}".format(self.total_score)]

        return separator.join(all_scores)

