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

from src.python.utility.control import Control
from src.python.math.math_document import MathDocument
from src.python.math.math_extractor import MathExtractor


class MathMLCache:
    def __init__(self, control_filename, presentation_only=True):
        self.control_filename = control_filename
        self.presentation_only = presentation_only
        self.cached_locations = {}
        self.cached_expressions = {}

    def get(self, doc_id, location, expression, force_update=False):
        if not doc_id in self.cached_locations:
            self.cached_locations[doc_id] = {}

        if location in self.cached_locations[doc_id] and not force_update:
            return self.cached_locations[doc_id][location]
        else:
            #first time the expression is seen, check....

            if expression in self.cached_expressions and not force_update:
                #expression has been retrieved before but at different location...
                prev_doc_id, prev_location = self.cached_expressions[expression]

                return self.cached_locations[prev_doc_id][prev_location]
            else:

                control = Control(self.control_filename) # control file name (after indexing)
                document_finder = MathDocument(control)

                mathml = document_finder.find_mathml(doc_id, location)
                if self.presentation_only:
                    mathml = MathExtractor.isolate_pmml(mathml)

                if isinstance(mathml, bytes):
                    mathml = mathml.decode('UTF-8')

                # save on cache...
                self.cached_locations[doc_id][location] = mathml
                self.cached_expressions[expression] = (doc_id, location)

                return mathml

class CompoundMathMLCache:
    def __init__(self):
        # indexing is [control filename, doc_id, location]
        self.cache = {}

    def get(self, control_filename, doc_id, location):
        if not control_filename in self.cache:
            # add new cache ...
            self.cache[control_filename] = {}

        if not doc_id in self.cache[control_filename]:
            self.cache[control_filename][doc_id] = {}

        if not location in self.cache[control_filename][doc_id]:
            control = Control(control_filename)  # control file name (after indexing)
            document_finder = MathDocument(control)

            mathml = document_finder.find_mathml(doc_id, location)
            if isinstance(mathml, bytes):
                mathml = mathml.decode('UTF-8')

            # save on cache...
            self.cache[control_filename][doc_id][location] = mathml

            return mathml
        else:
            return self.cache[control_filename][doc_id][location]

