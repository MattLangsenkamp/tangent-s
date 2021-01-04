00_README_ARQMATH
July 11, 2020 (minor update, Dec. 22, 2020)

Notes from running Tangent-s with the ARQMath Topics

R. Zanibbi

CHANGES:

- RZ: added scripts for easier use of tools and later reference (beginning with 'arqmath-')
- query.py :
	- RZ: Changed default top-k hits ('K' in db-index/ query file) to 1000
	- Note that this is top-1000 unique formulas, not number of hits.
- combine_rankings.py:
	- RZ: Modifed input to read '.' as well as '-' as separators in topic names.
- Tangent-S/ranking/query.py
	- RZ: Also modifed to read in '.' as separators in topic names.
- Tangent-S/math/math_document.py
	- RZ: Added methods to lookup ARQMath ids directly from doc_ids in results,
	  for use in producing final results.
- added new arqmath_search_combine.py to combine *reranked* SLT and OPT results
  directly. This includes linear weigthing of Tangent-s score vector values
  (similar to SIGIR 2017 paper).

NOTES:
- In stage 1 (tuple retrieval), Tangent-s retrieves the top-1000 UNIQUE formulas. These
  are then expanded into separate entries for different appearances of the formulas in
  different documents, producing a result list much longer than 1000 formulas, potentially.

- LaTeXML wraps '?' in LaTeX strings in <mi> (identifier) tags for Presentation MathML (SLT),
  and <ci> tags for Content MathML (OPT). So they should be treated as concrete symbols in
  search. This is important, because there are no wildcards in the task, and wildcard matching
  would likely slow queries down, and hurt the quality of results. *Unfortunately, not 
  completely certain how tokens such as '?' and '??' are handled, but they do not have the
  standard '?*<integer>*' format used to name wildcard variables in the system.

- Indexing (9:41am June 11, 2020) for ARQMath formula collection.
	- At time of this writing, many more OPT failures.
	- 25,399,524 SLT formulas indexed 
	- 24,284,810 OPT formulas indexed 
	- Confirmed these counts via 'grep' and 'wc': SLT "E" formula entry
	  line count matches the 'expression instance' count in the log file
	  produced during indexing. Obtained OPT count similarly (due to number of error
	  messages, did not log OPT indexing).

- Need to check how '?' is handled at index time vs. query time - ARQMath formulas contain
  a lot of trailing '?' because of questions, and we don't want them treated as wildcards.

- Weights for combining SLT/OPT include a bias weight (W0). Kenny provided
  outputs from his cross-validation experiments with NTCIR-12 data; we have
  used the average weight values acrross folds in our  reranking (ideally
  combining SLT + OPT, or just SLT).

