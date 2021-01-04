__author__ = 'KMDC'

class Alignment:
    def __init__(self, q_element, q_location, c_element, c_location, constraint=None):
        self.q_element = q_element
        self.q_location = q_location

        self.c_element = c_element
        self.c_location = c_location

        self.score = 0.0

        self.constraint = constraint

    def __eq__(self, other):
        if isinstance(other, Alignment):
            return (self.q_location == other.q_location and
                    self.c_location == other.c_location)
        else:
            return False

    def __repr__(self):
        return ("<(" + str(self.q_element.tag) + ", " + self.q_location + ")-(" +
                str(self.c_element.tag) + ", " + self.c_location + ")>")
