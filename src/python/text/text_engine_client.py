import sys
import os
import ast

import urllib
import requests
from TangentS.utility.control import Control
from TangentS.text.TextResult import TextResult


__author__ = 'FWTompa'

import requests


def get(cntl,keywords,topk):
    """
    :param cntl: control file handle
    :type  cntl: Control
    :param keywords: search terms
    :type  keywords: list(string)
    :param topk: number of final results to retrieve
    :type  topk: int
    :result: text result info
    :rtype:  list(pair(docid,score))
    """
    print("Text Query: "+str(keywords))

    if keywords:
        # http://saskatoon.cs.rit.edu:8984/solr/ntcir/mathtvrh?defType=dismax&fl=title,score&rows=100&q=%22euclid%22
        url = cntl.read("textURL")
        port = str(cntl.read("textPort",num=True))
        path = cntl.read("textPath")
        url = urllib.parse.urlunsplit(("http",url+":"+port,path,"",""))
        query = ""
        for kw in keywords:
            query = query + '"' + kw + '" '

        # Using title as id, since ids are not consistent between search engines
        
        #urlparms = {"defType":"dismax", "fl":"id,score", "rows":"1000", "q":query.strip()}  # "wt":"python" ????
        #urlparms = {"defType":"dismax", "fl":"id,title,score", "rows":str(100*topk), "q":query.strip()}  # "wt":"python" ????
        urlparms = {"defType":"dismax", "fl":"id,title,score", "rows":str(10*topk), "q":query.strip()}  # "wt":"python" ????
        #print("opening: "+url+ "with "+str(urlparms))
        print("Querying " + url, flush=True)
        r = requests.get(url,params=urlparms)
        print("Text query completed", flush=True)
    ##    print("    -> "+r.url)
        response = TextResult(keywords,r.json())
    ##    print("Returned: "+str(response.scores)+" at "+str(response.positions))
        return(response.scores,response.positions)
    else:
        return(({},{}))
