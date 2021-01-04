import codecs
import sys
from sys import argv

from TangentS.utility.control import Control
from TangentS.math.math_document import MathDocument

__author__ = 'FWTompa'

if __name__ == '__main__':

    if sys.stdout.encoding != 'utf8':
      sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf8':
      sys.stderr = codecs.getwriter('utf8')(sys.stderr.buffer, 'strict')

    if len(argv) != 4 or argv[1] == "help":
        print("Use: python get_math.py <cntl> <doc#> <expr#>")
        print("        where (doc# < 0) => use queryfile")
        sys.exit()

    cntl = Control(argv[1]) # control file name (after indexing)
    d = MathDocument(cntl)
    docno = int(argv[2])
    exprno = int(argv[3])
    print("doc "+argv[2]+": "+d.find_doc_file(docno)) #print document file name
    print(d.find_mathml(docno,exprno))  # doc_num and pos_num
