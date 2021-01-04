__author__ = 'KMDC'

import xml
import io
from TangentS.math.symbol_tree import SymbolTree
from TangentS.math.layout_symbol import LayoutSymbol
from TangentS.math.math_extractor import MathExtractor

class Result:
    def __init__(self, query, expression, original_ranking, original_score, mathml=None, operator=False):
        self.query = query
        self.original_ranking = original_ranking
        self.original_score = original_score
        self.mathml = mathml
        self.reranking_time = 0.0
        self.new_scores = [0.0]

        if not operator:
            if mathml is not None:
                # parse from mathml (additional information extracted)
                self.tree = MathExtractor.convert_and_link_mathml(mathml)
                self.expression = self.tree.tostring()

                #out_file = open("probando.txt", 'w', encoding='utf-8')
                #out_file.write(self.tree.tostring())
                #out_file.close()
            else:
                # parse from SLT string (no mathml information available)
                self.tree = SymbolTree.parse_from_slt(expression)
                self.expression = expression
        else:
            # parse from OPT string
            self.tree = SymbolTree.parse_from_opt(expression)

            if mathml is not None:
                # assign the root to the mathml ...
                elem_content = io.StringIO(mathml)  # treat the string as if a file
                root = xml.etree.ElementTree.parse(elem_content).getroot()
                self.tree.xml_root = root

            self.expression = expression

        if self.tree.tostring() != expression:
            print("Bad conversion for result for query " + query.name + ": " + expression + " -> " + self.tree.tostring())
            exit(1)

        self.locations = []
        self.matched_elements = {}
        self.unified_elements = {}
        self.wildcard_matches = {}
        self.all_unified = []
        self.times_rendered = 0

    def get_variable_character_set(self):
        return Result.get_variable_character_set_rec(self.tree.root)

    @staticmethod
    def get_variable_character_set_rec(root):
        result = set()

        if root.tag[0:2] == "V!":
            for val in root.tag[2:]:
                result.add(val)

        if root.next is not None:
            result = result.union(Result.get_variable_character_set_rec(root.next))

        if root.above is not None:
            result = result.union(Result.get_variable_character_set_rec(root.above))
        if root.below is not None:
            result = result.union(Result.get_variable_character_set_rec(root.below))
        if root.over is not None:
            result = result.union(Result.get_variable_character_set_rec(root.over))
        if root.under is not None:
            result = result.union(Result.get_variable_character_set_rec(root.under))

        if root.within is not None:
            result = result.union(Result.get_variable_character_set_rec(root.within))

        if root.pre_above is not None:
            result = result.union(Result.get_variable_character_set_rec(root.pre_above))
        if root.pre_below is not None:
            result = result.union(Result.get_variable_character_set_rec(root.pre_below))

        if root.element is not None:
            result = result.union(Result.get_variable_character_set_rec(root.element))


        return result

    def set_matched_elements(self, matched_elements):
        self.matched_elements = matched_elements

    def set_unified_elements(self, unified_elements):
        self.unified_elements = unified_elements

    def set_wildcard_matches(self, wildcard_matches):
        self.wildcard_matches = wildcard_matches

    def set_all_unified(self, all_unified):
        self.all_unified = all_unified

    def __modify_xml_ids(self, root):

        if "id" in root.attrib:
            if self.times_rendered == 0:
                root.attrib["id"] += "_0"
            else:
                base_id = root.attrib["id"][:-(len(str(self.times_rendered - 1)) + 1)]
                root.attrib["id"] = base_id + "_" + str(self.times_rendered)

        for child in root:
            self.__modify_xml_ids(child)

    def get_highlighted_mathml(self):

        if self.mathml is not None and self.tree.xml_root is not None:

            if self.times_rendered == 0:
                # compute highlighted mathml only once ...
                self.tree.root.mark_matches("", self.matched_elements, self.unified_elements, self.wildcard_matches)

            # modify ids to avoid Math Jax error on expressions rendered multiple times
            self.__modify_xml_ids(self.tree.xml_root)

            marked_mathml = xml.etree.ElementTree.tostring(self.tree.xml_root)
            if isinstance(marked_mathml, bytes):
                marked_mathml = marked_mathml.decode('UTF-8')

            self.highlighted_mathml = marked_mathml

            # count how many times the expression has been rendered...
            self.times_rendered += 1

            return self.highlighted_mathml
        else:
            return None
