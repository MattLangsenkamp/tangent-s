__author__ = 'KMDC'

from TangentS.math.layout_symbol import LayoutSymbol
from TangentS.math.semantic_symbol import SemanticSymbol

class WildcardAlignment:
    def __init__(self, q_variable, q_location, c_tree, c_location):
        self.q_variable = q_variable
        self.q_location = q_location

        self.c_tree = c_tree
        self.c_location = c_location
        self.c_size =  c_tree.get_size()

        self.score = 0.0



    def __eq__(self, other):
        if isinstance(other, WildcardAlignment):
            return (self.q_location == other.q_location and
                    self.c_location == other.c_location)
        else:
            return False


    def same_substitution(self, other):
        if isinstance(other, WildcardAlignment):
            local_slt = self.c_tree.tostring()
            other_slt = other.c_tree.tostring()

            return local_slt == other_slt
        else:
            return None

    def __repr__(self):
        return ("<(" + str(self.q_variable.tag) + ", " + self.q_location + ")-(" +
                self.c_tree.tostring() + ", " + self.c_location + ")>")
