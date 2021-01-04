"""
    Tangent
   Copyright (c) 2013, 2015 David Stalnaker, Richard Zanibbi, Nidhin Pattaniyil,
                  Andrew Kane, Frank Tompa, Kenny Davila Castellanos

    This file is part of Tangent.

    Tanget is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Tangent is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Tangent.  If not, see <http://www.gnu.org/licenses/>.

    Contact:
        - Richard Zanibbi: rlaz@cs.rit.edu
"""
__author__ = 'KDavila'


class ConstraintInfo:
    def __init__(self, unifiable):
        self.unifiable = unifiable
        self.min_value = None
        self.min_strict = False
        self.max_value = None
        self.max_strict = False
        self.restricted_type = None

    def check_unifiable(self, q_node, c_node):
        # if they are equal (or query is wildcard) ...
        if q_node.tag == c_node.tag or q_node.tag[0] == "?":
            return True

        # if they are not equal, they might be unifiable
        if self.unifiable:
            # check ....
            q_has_type = q_node.tag[1:2] == "!"
            c_hast_type = c_node.tag[1:2] == "!"

            # first, check if query var
            if q_node.tag[0] == "?":
                # has a query var, unifiable with everything ...
                if self.restricted_type is None:
                    return True
                else:
                    # has restricted type
                    if c_hast_type:
                        # check same type
                        return self.restricted_type == c_node.tag[0]
                    else:
                        # type not specified for candidate
                        return False

            # handle cases when it is not query var differently ...
            if c_hast_type and q_has_type and (q_node.tag[0] == c_node.tag[0]):
                # same type ...
                if q_node.tag[0] == "N":
                    # check constraints for numbers ...
                    try:
                        tag_value = float(c_node.tag.split("!")[1].strip())
                    except:
                        # the value is invalid numeric constant, restriction cannot be applied,
                        # assume it cannot be unified
                        return False

                    # minimum value ...
                    if self.min_value is not None:
                        if ((self.min_strict and tag_value <= self.min_value) or
                           (not self.min_strict and tag_value < self.min_value)):

                            # value is smaller than lower limit
                            return False

                    # maximum value ...
                    if self.max_value is not None:
                        if ((self.max_strict and tag_value >= self.max_value) or
                           (not self.max_strict and tag_value > self.max_value)):

                            # value is larger than limit
                            return False

                    # can be unified ....
                    return True

                elif q_node.tag[0] == "O" or q_node.tag[0] == "U":
                    # operators cannot be unified ....
                    return False

                elif q_node.tag[0] == "V":
                    # restrictions on unifying variable names ...
                    unifiable = True

                    # 1) Length. To prevent function names to be unified to variables or vice-versa we
                    # assume that names with at least 2 characters are more likely to be function names
                    # and we do not allow them to unify with single character variable names ...

                    if len(q_node.tag) != len(c_node.tag) and (len(q_node.tag) == 3 or len(c_node.tag) == 3):
                        # different lengths, and one of them is only one character long
                        unifiable = False

                    return unifiable

                # Todo: Add here any other type of constraints specific to different node types
                else:
                    # all other types ...
                    return True
            else:
                # different type, cannot be unified
                return False
        else:
            # constrained to be exact match ....
            return False

    @staticmethod
    def create_from_string(constraint_text):
        unifiable = (constraint_text != "E")

        info = ConstraintInfo(unifiable)

        if unifiable:
            parts = constraint_text.split("!")

            if parts[0] == "U":
                for idx in range(1, len(parts)):
                    if parts[idx][0] == ">":
                        if parts[idx][1] == "=":
                            info.min_value = float(parts[idx][2:])
                            info.min_strict = False
                        else:
                            info.min_value = float(parts[idx][1:])
                            info.min_strict = True

                    if parts[idx][0] == "<":
                        if parts[idx][1] == "=":
                            info.max_value = float(parts[idx][2:])
                            info.min_strict = False
                        else:
                            info.max_value = float(parts[idx][1:])
                            info.min_strict = True
            else:
                info.restricted_type = parts[0]

        return info



