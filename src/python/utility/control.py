import csv
import pathlib
import os

__author__ = 'FWTompa'

"""
Control manages control files for indexing and searching in Tangent
"""


class Control:
    def __init__(self,cntl=None):
        self.params = {}
        csv.field_size_limit(999999999) # NTCIR cntl file has 17853644 characters (limit is now approx 50 times bigger) 
        if not cntl:
            cntl = os.path\
                .join(str(pathlib.Path(__file__).parent.parent.parent.parent.absolute()), "cntl/tangent-s.cntl")
        if not os.path.exists(cntl):
            raise Exception(cntl+" does not exist.")
        self.store("cntl",cntl)
        with open(cntl, mode='r', encoding='utf-8', newline='') as file:
            reader = csv.reader(file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
            for (parm,value) in reader:
                self.store(parm,value) # set all the control parameters

    def read(self, param, num=False, default=None):
        val = self.params.get(param.strip(), default)
        if val and num:
            try:
                val = int(val)
            except ValueError:
                print("Parameter %s not numeric; value given is %s; using %s" % (param, val, default))
                val = default
        return val if val else default

    def store(self, param, val):
        self.params[param.strip()] = val.strip()

    def dump(self):
        cntl = self.params["cntl"]
        with open(cntl, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE, escapechar="\\")
            for pair in self.params.items():
                writer.writerow(pair)

