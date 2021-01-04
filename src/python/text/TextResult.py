
__author__ = 'Nidhin,FWTompa'
from TangentS.text.porter import stem


class TextResult:
    def __init__(self, keywords, struct):
        # keywords: list of string
        self.QTime = struct['responseHeader']['QTime']
        self.numResults = struct['response']['numFound']
        self.maxScore = struct['response']['maxScore']
        self.scores = self.parseDocumentInfo(struct['response']['docs'])
        self.all = struct
        self.positions = self.parsePositionInfo(struct['termVectors'],keywords)


    def parseDocumentInfo(self, doc_list):
##        print("Scores: "+str(doc_list))
        scores = {}
        for d in doc_list:

            # Using title as id, since ids are not consistent between search engines
    
            #scores.append((d["id"],d["score"],d["score"]/self.maxScore))
            scores[d["id"]] = (d["title"][0],d["score"],d["score"]/self.maxScore)
        return scores

    def parsePositionInfo(self, termVectorsJson, query_terms):
        terms = []  # get stemmed versions of search terms
        for kw in query_terms:
            term = kw.lower().split()
            terms.extend(list(map(stem,term)))
            
        doc_id_pos_mapping = {}
        for t in termVectorsJson:
            if isinstance(t, list):
                id = t[1]  #document identifier
                token_pos_mapping = {"<math":[]}
                doc_id_pos_mapping[id] = token_pos_mapping
                positions = t[3]
                for i in range(0, len(positions), 2):
                    token = positions[i]
##                    if token in self.query: # or "<math" in token:  #if token in query or math
                    if token in terms:
                        token_positions = list(map(int, positions[i + 1][1][1::2]))  #odd indices have position
                        token_pos_mapping[token] = token_positions
                    if token.startswith("<math"):
                        token_positions = list(map(int, positions[i + 1][1][1::2]))  #odd indices have position
                        token_pos_mapping["<math"].extend(token_positions)
                    token_pos_mapping["<math"].sort()
                      
        return doc_id_pos_mapping
