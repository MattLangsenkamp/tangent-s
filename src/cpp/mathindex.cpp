// (C) Copyright 2014 Andrew R. J. Kane <arkane@uwaterloo.ca>, All Rights Reserved.
//               2017 Kenny Davila <kxd7282@rit.edu> extensions for Operator Trees
//
//     Released for academic purposes only, All Other Rights Reserved.
//     This software is provided "as is" with no warranties, and the authors are not liable for any damages from its use.
//

// project: tangent-v3

// mathindex - a search system for tuples (from,to,relationship) generated from math expressions.

#define MATCHVARS true

#define EOBnone 10
#define EOBsmall 20
#define EOBall 30

#ifndef ENDOFBASELINE
#define ENDOFBASELINE EOBsmall
#endif

#define DISTVERT false

bool VERBOSE = false;

#include "mathindexmid.h"

#define EXACTMATCH false
#define EXPANDEXPR true

#define DEBUGOUTPUTDOCS false
#define DEBUGOUTPUTEXPRS false

#define PACIFYRATE INT_MAX
//#define PACIFYRATE 10000

//== Globals ========================================================

StringDictionary dictDocIDs;
StringDictionary dictExpressions;
StringDictionary dictTerms;
StringDictionary dictRelationships;

bool semanticMode;

intlist exprTC;			// tuple counts for expressions
Lexicon lexTokenTuples;
SubObjectMap subExprDoc;

string getvalue (StringDictionary & d, int v)
{
	if (v >= 0)
	{
		return d.get (v);
	}
	else if (v == varID)
	{
		return "?";
	}
	else
	{
		return "null";
	}
}

void dumptuple (ostream & out, const tokentuple & t)
{
	out << "{" << getvalue (dictTerms, t.from) << "," << getvalue (dictTerms, t.to) << "," << getvalue (dictRelationships, t.rel) << "}";
}

#if DISTVERT
string
convertRelationshipToDistVert (string & to, string & rel)
{
	int v = 0;
	for (int i = 0; i < rel.length (); i++)
	{
		int x = rel[i];
		if (x == 'a' || x == 'c')
		{
			v++;
		}
		else if (x == 'b' || x == 'd')
		{
			v--;
		}
		else if (x == 'n' || x == 'w' || x == 'e')
		{
		}
		else
		{
			cerr << "ERROR: Unknown relationship " << rel[i] << endl;
			throw;
		}
	}
	ostringstream ss;
	ss << rel.length () << "." << v;
	string dv = (to == "0!" ? "0.0" : ss.str ());
	// debugging
	//cerr<<"rel="<<rel<<"\t"<<dv<<endl;
	return dv;
}
#endif

//== Verify Index Consistency ========================================================

void
verifyIndex ()
{
	WARN (dictExpressions.size () != exprTC.size (), "expression counts inconsistent", dictExpressions.size () << " " << exprTC.size ())	// expression sizes are consistent
		  llong ttc = lexTokenTuples.ttc;
	llong pc = lexTokenTuples.allPostingSizes ();
	WARN (pc != ttc, "internal postings count error in ttc", pc << " " << ttc);	// count of postings
	llong es = 0;
	for (int i = 0; i < exprTC.size (); i++)
	{
		es += exprTC.get (i);
	} llong pcs = lexTokenTuples.allPostingCounts ();
	WARN (pcs != es, "internal postings count error in exprTC", pcs << " " << es);	// exprTC sizes and size of counts within postings
}

//== Statistics Output ========================================================

void
outputStats (ostream & out)
{
	out << endl;
	out << "I\tdictDocIDs\t" << dictDocIDs.size () << endl;
	out << "I\tdictExpressions\t" << dictExpressions.size () << endl;
	out << "I\tdictTerms\t" << dictTerms.size () << endl;
	out << "I\tdictRelationships\t" << dictRelationships.size () << endl;
	out << "I\tlexTokenTuples\t" << lexTokenTuples.
			size () << "\t" << lexTokenTuples.ttc << "\t" << lexTokenTuples.
			sizevar () << "\t" << lexTokenTuples.vttc << endl;
	out << "I\tsubExprDoc\t" << subExprDoc.ec << endl;
	verifyIndex ();
}

//== reorder expression IDs by tuple count size (small to large) ========================================================

static int
eidorderodsort (const void *A, const void *B)
{
	return ((eidorder *) A)->od - ((eidorder *) B)->od;
}

static int
eidordertcsort (const void *A, const void *B)
{
	return ((eidorder *) A)->tc - ((eidorder *) B)->tc;
}

static int
eidorderfrsort (const void *A, const void *B)
{
	return ((eidorder *) A)->fr - ((eidorder *) B)->fr;
}

void
reorder (ostream & out)
{
	int s = exprTC.size ();
	eidorder *e = new eidorder[s];
	// order by tuple count
	for (int i = 0; i < s; i++)
	{
		e[i].fr = i;
		e[i].to = -1;
		e[i].tc = exprTC[i];
	}
	qsort (e, s, sizeof (eidorder), eidordertcsort);
	int q1 = e[(int) (0.25 * (s - 1))].tc;
	int q2 = e[(int) (0.5 * (s - 1))].tc;
	out << "I\tquartiles\t" << q1 << "," << q2 << endl;
	// tuple count distribution information
	int breaks = 20;
	out << "I\tdistexpr\t" << 1;
	for (int i = 1; i <= breaks; i++)
	{
		out << "," << i * (s - 1) / breaks + 1;
	} out << endl;
	out << "I\tdisttc\t" << e[0].tc;
	for (int i = 1; i <= breaks; i++)
	{
		out << "," << e[i * (s - 1) / breaks].tc;
	} out << endl;
	// calculate new order (q1-1:q2, q1:1, q2+1:inf)
	for (int i = 0; i < s; i++)
	{
		int x = e[i].tc;
		if (x > q1 && x <= q2)
		{
			x -= q1;
		}
		else if (x <= q1)
		{
			x = q2 + 1 - x;
		}
		e[i].od = x;
	}
	qsort (e, s, sizeof (eidorder), eidorderodsort);
	for (int i = 0; i < s; i++)
	{
		e[i].to = i;
	}
	qsort (e, s, sizeof (eidorder), eidorderfrsort);
	// debugging
	//cerr<<"("; for (int i=0;i<s;i++) {cerr<<e[i]<<" ";} cerr<<")";
	// do the reordering
	dictExpressions.reorder (e);
	for (int i = 0; i < s; i++)
	{
		exprTC[e[i].to] = e[i].tc;
	}
	lexTokenTuples.reorder (e);
	subExprDoc.reorder (e);
	// cleanup
	delete[]e;
	e = NULL;
}

//== serialize index to/from file ========================================================

// negative numbers inticate development versions, positive indicate stable versions

#define INDEXFILEFORMAT -1

void
outputIndex (ostream & out, const char *filename)
{
	outputStats (out);
	out << endl;
	reorder (out);
	out << endl;
	// debugging
	//cerr<<"writing to "<<filename<<endl;
	llong start = nanoTime ();
	WF f (filename);
	f.i (INDEXFILEFORMAT);
	dictDocIDs.w (f);
	dictExpressions.w (f);
	dictTerms.w (f);
	dictRelationships.w (f);
	exprTC.w (f);
	lexTokenTuples.w (f);
	subExprDoc.w (f);
	out << "I\twrite\t" << (nanoTime () - start) / 1000000 << endl;
	verifyIndex ();
}

void
inputIndex (ostream & out, const char *filename)
{
	// debugging
	//cerr<<"reading from "<<filename<<endl;
	llong start = nanoTime ();
	if (dictDocIDs.size () > 0)
	{
		cerr <<
				"ERROR: cannot input from index file after adding data in memory." <<
				endl;
		throw;
	}
	RF f (filename);
	int v = f.i ();
	if (v != INDEXFILEFORMAT)
	{
		cerr << "ERROR: invalid format " << v << " for " << filename << endl;
		throw;
	}
	dictDocIDs.r (f);
	dictExpressions.r (f);
	dictTerms.r (f);
	dictRelationships.r (f);
	exprTC.r (f);
	lexTokenTuples.r (f);
	subExprDoc.r (f);
	out << "I\tread\t" << (nanoTime () - start) / 1000000 << endl;
	verifyIndex ();
}

//== Query/Output ========================================================

void
output (ostream & out, qresult & r)
{
	// expand exprID-to-docIDs
	postingslist *docIDxPs = subExprDoc.get (r.ex);
	for (int i = 0; i < docIDxPs->size (); i++)
	{
		int docID = docIDxPs->get (i);
		int firstpos = docIDxPs->getcount (i);
		out << "R\t" << dictDocIDs[docID] << "\t" << firstpos << "\t" <<
				dictExpressions[r.ex] << "\t" << r.sc << endl;
	}
}

bool
iditersizesort (IDIter * x, IDIter * y)
{
	return x->s > y->s;
}

class Query:public TupleCB
{
	map < tokentuple, int >pls;	// {tokentuple,count}, the postingslists are not owned by this class
	vector < tokentuple > var;	// variable token tuples (allow duplicates, since tokentuple does not maintain actual variable name)
	int querytc;			// tuple count
	// Note: must delete IDIter after use.
	IDIter *createIDIterOR (int s, vector < IDIter * >::const_iterator & iter)
	{
		if (s == 1)
		{
			IDIter *r = *iter;
			iter++;
			return r;
		}
		else if (s > 1)
		{
			int f = s / 2;
			return new IDIterOR (createIDIterOR (f, iter),
					createIDIterOR (s - f, iter));
		}
		else
		{
			return new IDIterEmpty ();
		}
	}
	IDIter *createIDIterANY (int s, vector < IDIter * >::const_iterator & iter)
	{
		if (s == 1)
		{
			IDIter *r = *iter;
			iter++;
			return r;
		}
		else if (s > 1)
		{
			int f = s / 2;
			return new IDIterANY (createIDIterANY (f, iter),
					createIDIterANY (s - f, iter));
		}
		else
		{
			return new IDIterEmpty ();
		}
	}				// TODO: handle counts in var interators
	void doAddTuple (const tokentuple & e)
	{
		querytc++;
		map < tokentuple, int >::iterator it = pls.find (e);
		if (it == pls.end ())
		{
			pls[e] = 1;
		}
		else
		{
			it->second++;
		}
	}
	void doAddTupleVar (const tokentuple & e)
	{
		querytc++;
		var.push_back (e);
	}				// repeats kept
	// execute & output
	topkheap topk;		// top-k results
	vector < int >exprSet;
	int exprsk;
	llong posts;
	llong postsk;
	void doOutput (ostream & out)
	{
		vector < qresult > &r = topk.output ();
		for (unsigned i = 0; i < r.size (); i++)
		{
			output (out, r[i]);
		} topk.clear ();
	}
	void doRunExact (ostream & out)
	{
		if (exprID < 0)
			return;
		postingslist *docIDxPs = subExprDoc.get (exprID);
		for (int i = 0; i < docIDxPs->size (); i++)
		{
			topk.add (qresult (exprID, 1));
		} doOutput (out);
	}
	void doRunScored (ostream & out)
	{
		if (pls.size () <= 0 && var.size () <= 0)
			return;
		IDIter *iter = NULL;
		IDIter *iterOR = NULL;
		IDIter *iterADD = NULL;	// may switch top level from OR to ADD
		int varcount = 0;
		{				// create iterators
			map < postingslist *, IDIterPL * >pliters;
			vector < IDIter * >v;
			for (map < tokentuple, int >::const_iterator ci = pls.begin ();
					ci != pls.end (); ci++)
			{
				int s = 0;
				postingslist *pl = lexTokenTuples.get (ci->first);
				if (pl != NULL)
				{
					IDIterPL *t = new IDIterPL (pl, ci->second, postsk);
					pliters[pl] = t;
					v.push_back (t);
					s = t->s;
				}
				if (VERBOSE)
				{
					cerr << "tuple:" << (ci->first) << "=";
					dumptuple (cerr, ci->first);
					cerr << " size=" << s << endl;
				}
			}			// IDIters
			if (VERBOSE)
			{
				cerr << "tuple count:" << v.size () << endl;
			}
			sort (v.begin (), v.end (), iditersizesort);	// sort descending by list size
			vector < IDIter * >::const_iterator ci = v.begin ();
			iterOR = createIDIterOR (v.size (), ci);
			iter = iterOR;		// handle all postings lists combined
			if (MATCHVARS)
			{
				vector < IDIter * >tv;
				for (vector < tokentuple >::const_iterator it = var.begin ();
						it != var.end (); it++)
				{
					varcount++;
					set < postingslist * >s;
					lexTokenTuples.getvar (*it, s);
					v.clear ();
					for (set < postingslist * >::const_iterator ci = s.begin ();
							ci != s.end (); ci++)
					{
						if (pliters.find (*ci) == pliters.end ())
						{
							IDIterPL *t = new IDIterPL (*ci, 1, postsk);
							pliters[*ci] = t;
							v.push_back (t);
						}
						else
						{
							v.push_back (new
									IDIterIND (pliters.find (*ci)->second));
						}
					}		// IDIters
					sort (v.begin (), v.end (), iditersizesort);	// sort descending by list size
					vector < IDIter * >::const_iterator ci = v.begin ();
					IDIter *t = createIDIterANY (v.size (), ci);
					tv.push_back (t);
					if (VERBOSE)
					{
						cerr << "vartuple:" << (*it) << "=";
						dumptuple (cerr, *it);
						cerr << " expand=" << v.size () << " size=" << (t->
								s) << endl;
					}
				}
				if (VERBOSE)
				{
					cerr << "vartuple count:" << tv.size () << endl;
				}
				if (!tv.empty ())
				{
					sort (tv.begin (), tv.end (), iditersizesort);	// sort descending by list size
					vector < IDIter * >::const_iterator ci = tv.begin ();
					IDIter *variter = createIDIterOR (tv.size (), ci);	// make var iterators balanced
					iterOR = new IDIterOR (iter, variter);
					iterADD = new IDIterADD (iter, variter, false);
					iter = iterOR;
				}
			}
		}
		if (VERBOSE)
		{
			cerr << "iter:" << (*iter) << endl;
		}
		posts = iter->us;		// count postings
		int maxexprtc = INT_MAX;
		int minexprtc = 1;
		for (; iter->cv < IDEND;)
		{
			int exprID = iter->cv;
			double cc = iter->cc;
			exprSet.push_back (exprID);	// record unique expressions // TODO: won't work with thresholds
			int exprtc = exprTC[exprID];
			if (exprtc > maxexprtc || exprtc < minexprtc)
			{			// threshold advances along exprTC and calls iter->skip.
				int exprIDOrig = exprID;
				exprsk++;
				int s = exprTC.size ();
				for (;;)
				{
					exprID++;
					if (exprID >= s)
					{
						exprID = IDEND;
						break;
					}
					exprsk++;	// don't recheck first one
					int x = exprTC[exprID];
					if (x <= maxexprtc && x >= minexprtc)
						break;
				}
				if (VERBOSE)
				{
					cerr << "skipping: from=" << exprIDOrig << " to=" << exprID <<
							" s=" << s << endl;
				}
				iter->skip (exprID);
				continue;
			}
			//double P=cc/exprtc; double R=cc/querytc; double F=2*P*R/(P+R); // ranking: precision, recall, f-measure
			double F = 2 * cc / (exprtc + querytc);	// simplified f-measure calculation
			// check
			if (F > 1 || F < 0 || cc > exprtc || cc > querytc)
			{
				// debugging
				//cerr<<dictExpressions.get(exprID)<<endl; iter->printv(cerr,exprID);
				cerr << "WARNING: bad score eID=" << exprID << " F=" << F <<
						" cc=" << cc << " etc=" << exprtc << " qtc=" << querytc << endl;
				iter->skip (iter->cv + 1);
				continue;
			}
			//if (P>1||R>1) { cerr<<"WARNING: bad score eID="<<exprID<<" P="<<P<<" R="<<R<<" cc="<<cc<<" etc="<<exprtc<<" qtc="<<querytc<<endl; continue; }
			//if (exprtc > maxexprtc || exprtc < minexprtc) { if (F>topk.threshold()) { cerr<<"ERROR: threshold failed"<<endl; } } // check threshold
			if (topk.add (qresult (exprID, F)))
			{
				double t = topk.threshold ();
				if (t > 0)
				{
					double x = (2 / t - 1);
					maxexprtc = floor (querytc * x);
					minexprtc = ceil ((double) querytc / x);	// threshold for large and small expressions
					if (VERBOSE)
					{
						cerr << "thresholds:min=" << minexprtc << ",max=" <<
								maxexprtc << endl;
					}
				}
				if (iterADD != NULL && iter != iterADD
						&& t >= ((double) 2 * varcount) / (varcount + querytc))
				{
					iterADD->cv = iter->cv;
					iter = iterADD;	// threshold non-var only
					if (VERBOSE)
					{
						cerr << "iterADD:exprID=" << exprID << endl;
					}
				}
			}
			iter->skip (iter->cv + 1);
		}
		doOutput (out);
		// cleanup
		if (iterOR != NULL)
		{
			delete iterOR;
			iterOR = NULL;
		}
		if (iterADD != NULL)
		{
			delete iterADD;
			iterADD = NULL;
		}
		iter = NULL;
	}
public:
	bool active;
	llong st;
	string queryID;
	string expr;
	int exprID;			// for exact match
	void reset ()
	{
		active = false;
		st = 0;
		pls.clear ();
		var.clear ();
		querytc = 0;
		queryID = expr = "";
		exprID = -1;
		topk.clear ();
		posts = 0;
		postsk = 0;
		exprSet.clear ();
		exprsk = 0;
	}
	Query ()
	{
		reset ();
	}
	void settopk (int v)
	{
		topk.settopk (v);
	}
	void start (string id)
	{
		queryID = id;
		active = true;
		st = nanoTime ();
	}
	void expression (string ex, string pos)
	{
		if (!active)
			return;
		WARNR (queryID.length () <= 0, "No queryID", ex << " " << pos);
		expr = ex;
		exprID = dictExpressions.find (expr);
		// ignore position for query
		if (EXPANDEXPR)
			parseExpr (*this, ex);	// expand expression
	}
	virtual void tuple (string frS, string toS, string rlS, string loc)
	{
		if (!active)
			return;
		if (VERBOSE)
		{
			cerr << "tuple:" << frS << " " << toS << " " << rlS << " " << loc <<
					endl;
		}
		WARNR (expr.length () <= 0, "No expression",
				frS << " " << toS << " " << rlS << " " << loc);
		WARNR (rlS.find ('?') == 0,
				"Query tuple with relationship variable not supported",
				frS << " " << toS << " " << rlS << " " << loc);
		WARNR (frS.find ('?') == 0
				&& toS.find ('?') == 0,
				"Query tuple with from and to as variables not supported",
				frS << " " << toS << " " << rlS << " " << loc);
#if DISTVERT
		rlS = convertRelationshipToDistVert (toS, rlS);
#endif
		int fr = dictTerms.find (frS);
		int to = dictTerms.find (toS);
		int rl = dictRelationships.find (rlS);
		if (frS.find ('?') == 0)
		{
			if (MATCHVARS)
			{
				doAddTupleVar (tokentuple (varID, to, rl));
			}
			else
			{
				WARNR (true, "Query variable ignored",
						frS << " " << toS << " " << rlS << " " << loc);
			}
		}
		else if (toS.find ('?') == 0)
		{
			if (MATCHVARS)
			{
				doAddTupleVar (tokentuple (fr, varID, rl));
			}
			else
			{
				WARNR (true, "Query variable ignored",
						frS << " " << toS << " " << rlS << " " << loc);
			}
		}
		else
		{
			doAddTuple (tokentuple (fr, to, rl));
		}
		// TODO: handle location
	}
	Query & run (ostream & out)
	{
		if (!active || queryID.size () <= 0)
			return *this;		// TODO: warn here if no queryID?
		out << endl << "Q\t" << queryID << endl;
		out << "E\t" << expr << endl;	// TODO: output position
		if (EXACTMATCH)
		{
			doRunExact (out);
		}
		else
		{
			doRunScored (out);
		}
		out << "I\tqt\t" << (double) (nanoTime () - st) / 1000000 << endl;

		// report additional information.
		out << "I\tpost\t" << posts << endl;
		out << "I\tpostsk\t" << postsk << endl;
		out << "I\texpr\t" << exprSet.size () << endl;
		out << "I\texprsk\t" << exprsk << endl;
		// RZ - expand expressions to unique documents - TODO: probably slow and has a large set
		set < int >docSet;
		for (vector < int >::iterator exprIt = exprSet.begin ();
				exprIt != exprSet.end (); exprIt++)
		{
			postingslist *docIDxPs = subExprDoc.get (*exprIt);
			for (int i = 0; i < docIDxPs->size (); i++)
			{
				docSet.insert (docIDxPs->get (i));
			}
		}
		out << "I\tdoc\t" << docSet.size () << endl;
		WARN (posts < (int) exprSet.size (), "too few postings counted",
				"posts=" << posts << " exprs=" << exprSet.size ());

		return *this;
	}
};

//== Document/Input ========================================================

class Doc:public TupleCB
{
	std::map < tokentuple, int >ttm;	// {tokentuple,count}
	void doFinishExpr ()
	{
		for (std::map < tokentuple, int >::const_iterator it = ttm.begin ();
				it != ttm.end (); it++)
		{
			lexTokenTuples.add (it->first, it->second, exprID);
		}
		ttm.clear ();
	}
public:
	llong st;			// process creation time
	bool active;
	int docID;
	int exprID;
	bool isNewExpr;
	void reset ()
	{
		active = false;
		docID = -1;
		exprID = -1;
		isNewExpr = false;
		ttm.clear ();
	}
	Doc ()
	{
		reset ();
		st = nanoTime ();
	}
	void timest ()
	{
		st = nanoTime ();
	}
	Doc & time (ostream & out)
	{
		if (active)
		{
			out << "I\tit\t" << (double) (nanoTime () - st) / 1000000 << endl;
		}
		return *this;
	}
	void start (string id)
	{
		int t = dictDocIDs.add (id);
		WARNR (t != dictDocIDs.size () - 1, "Repeated docID", id);
		docID = t;
		active = true;
	}
	void expression (string ex, string pos)
	{
		if (!active)
			return;
		doFinishExpr ();
		WARNR (docID < 0, "No docID", ex << " " << pos);
		int exprCount = dictExpressions.size ();
		exprID = dictExpressions.add (ex);
		isNewExpr = (exprID == exprCount);
		if (isNewExpr)
		{
			exprTC.add (0);
			if (exprTC.size () != exprID + 1)
			{
				cerr << "ERROR: bad exprTC " << exprTC.
						size () << " exprID=" << exprID << endl;
				throw;
			}
		}
		// handle multiple positions
		vector < int >poslist;
		for (;;)
		{
			poslist.
			push_back (stoi (pos.substr (pos.find_first_of ("0123456789"))));
			int x = pos.find (',');
			if (x == string::npos)
				break;
			pos = pos.substr (x + 1);
		}
		subExprDoc.add (exprID, docID, poslist);
		// debugging: output expression expansion
		//TupleOutCB cb; parseExpr(cb, ex);
		if (EXPANDEXPR)
			parseExpr (*this, ex);	// expand expression
	}
	virtual void tuple (string fr, string to, string rel, string loc)
	{
		if (!active)
			return;
		WARNR (exprID < 0, "No expression",
				fr << " " << to << " " << rel << " " << loc);
		if (!isNewExpr)
			return;
		exprTC[exprID]++;
		WARNR (fr.find ('?') == 0 || to.find ('?') == 0
				|| rel.find ('?') == 0, "Document tuple is a variable",
				fr << " " << to << " " << rel << " " << loc);
#if DISTVERT
		rel = convertRelationshipToDistVert (to, rel);
#endif
		tokentuple e (dictTerms.add (fr), dictTerms.add (to),
				dictRelationships.add (rel));
		std::map < tokentuple, int >::iterator it = ttm.find (e);
		if (it != ttm.end ())
		{
			it->second++;
		}
		else
		{
			ttm[e] = 1;
		}
		// TODO: handle location
	}
	Doc & finish ()
	{
		if (active)
			doFinishExpr ();
		return *this;
	}
};

//== Input/Output Control ========================================================

#define TVSIZE(l,h) if (tv.size()<l||tv.size()>h) { cerr<<"WARNING: Invalid line "<<line<<endl; continue; }
#define TVWARN(b,s) if (b) { cerr<<"WARNING: " s " in line "<<line<<endl; continue; }

int pacify = 0;
void
inputDQ (istream & in, ostream & out)
{
	Doc doc;
	Query query;
	for (;;)
	{
		string line;
		getline (in, line);
		if (in.eof ())
			break;
		if (false)
		{
			cout << line << endl;
		}
		if (line.length () <= 0)
			continue;		// line
			vector < string > tv;
			split (line, "\t", tv);	// cmd  v1  v2  v3
			// add to dictionaries
			TVWARN (tv[0].length () != 1, "Invalid length of command");
			switch (tv[0][0])
			{
			case 'W':
				TVSIZE (2, 2);
				TVWARN (stoi (tv[1]) < 0, "Invalid window value");
				windowvalue = stoi (tv[1]);
				if (windowvalue == 0)
					windowvalue = INT_MAX;
				doc.timest();
				break;
			case 'O':
				TVSIZE (2, 2);
				TVWARN (stoi (tv[1]) < 0, "Invalid operator flag value");
				operatorTrees = stoi(tv[1]) > 0;
				break;
			case 'D':
				TVSIZE (2, 2);
				query.run (out).reset ();
				doc.finish ().reset ();
				doc.start (tv[1]);
				if ((++pacify) % PACIFYRATE == 0)
				{
					cerr << tv[1] << endl;
				}
				break;		// new document
			case 'K':
				TVSIZE (2, 2);
				TVWARN (stoi (tv[1]) <= 0, "Invalid top-k value");
				query.run (out).reset ();
				doc.finish ().reset ();
				query.settopk (stoi (tv[1]));
				break;
			case 'Q':
				TVSIZE (2, 2);
				query.run (out).reset ();
				doc.finish ().reset ();
				query.start (tv[1]);
				break;		// new query
			case 'E':
				TVSIZE (3, 3);
				if (query.expr.length () > 0)
				{
					string t = query.queryID;
					query.run (out).reset ();
					query.start (t);
				}			// run previous expression
				doc.expression (tv[1], tv[2]);
				query.expression (tv[1], tv[2]);
				if (!doc.active && !query.active)
				{
					TVWARN (true, "Unknown Document/Query");
				}
				break;
			case 'T':
				TVSIZE (5, 5);
				doc.tuple (tv[1], tv[2], tv[3], tv[4]);
				query.tuple (tv[1], tv[2], tv[3], tv[4]);
				if (!doc.active && !query.active)
				{
					TVWARN (true, "Unknown Document/Query");
				}
				break;
			case 'S':
				TVSIZE (1, 1);
				outputStats (out);
				break;
			case 'X':
				TVSIZE (1, 1);
				query.run (out).reset ();
				doc.finish ().time (out).reset ();
				break;
			case 'R':
				TVWARN (true, "Invalid command");	// placeholder for result output
			case 'I':
				TVWARN (true, "Invalid command");	// placeholder for statistics information output
			default:
				TVWARN (true, "Invalid command");
			}
	}
	query.run (out).reset ();
	doc.finish ().reset ();
	out << "X" << endl;		// if no X command at end, need to execute final query
	if (DEBUGOUTPUTDOCS)
	{
		for (int i = 0; i < dictDocIDs.size (); i++)
		{
			cout << "D\t" << dictDocIDs.get (i) << endl;
		}}				// one for each document
	if (DEBUGOUTPUTEXPRS)
	{
		for (int i = 0; i < dictExpressions.size (); i++)
		{
			int count = subExprDoc.get (i)->size ();
			for (int k = 0; k < count; k++)
			{
				cout << "E\t" << dictExpressions.get (i) << endl;
			}}}				// one line for each expression posting
}

//== SOCKET ACCESS ========================================================

#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

void
socketerror (const char *msg)
{
	perror (msg);
	exit (1);
}

void
socketInput (int portno)
{
	int sockfd, newsockfd;
	unsigned int clilen;
	const int bufferSize = 1 << 10;
	char buffer[bufferSize];
	struct sockaddr_in serv_addr, cli_addr;
	int n;
	// bind
	sockfd = socket (AF_INET, SOCK_STREAM, 0);
	if (sockfd < 0)
		socketerror ("ERROR opening socket");
	bzero ((char *) &serv_addr, sizeof (serv_addr));
	serv_addr.sin_family = AF_INET;
	serv_addr.sin_addr.s_addr = INADDR_ANY;
	serv_addr.sin_port = htons (portno);
	if (::bind (sockfd, (struct sockaddr *) &serv_addr, sizeof (serv_addr)) < 0)
		socketerror ("ERROR on binding");
	cerr << "listening" << endl;
	for (;;)
	{
		// listen
		listen (sockfd, 5);
		// accept
		clilen = sizeof (cli_addr);
		newsockfd =::accept (sockfd, (struct sockaddr *) &cli_addr, &clilen);
		if (newsockfd < 0)
			socketerror ("ERROR on accept");
		for (;;)
		{
			// read
			bzero (buffer, bufferSize);
			n =::recv (newsockfd, buffer, bufferSize - 1, 0);
			if (n < 0)
				socketerror ("ERROR reading from socket");
			if (strncmp ("quit", buffer, 4) == 0
					|| strncmp ("exit", buffer, 4) == 0)
				break;
			//printf("Here is the message: '%s'\n",buffer);
			// execute
			stringstream in (buffer);
			stringstream out;
			inputDQ (in, out);
			// write
			string s = out.str ();
			n =::send (newsockfd, s.c_str (), s.length (), 0);
			if (n < 0)
				socketerror ("ERROR writing to socket");
		}
		// cleanup
		::close (newsockfd);
	}
}

//== MAINLINE ========================================================

void usage ()
{
	cerr <<
			"Usage: cat mathdata.tsv mathqueries.tsv | ./mathindex.exe [-v] > mathresults.tsv"
			<< endl;
	cerr << "  OR" << endl;
	cerr << "       cat mathdata.tsv | ./mathindex.exe -o mathdata.idx" << endl;
	cerr <<
			"       cat mathqueries.tsv | ./mathindex.exe -i mathdata.idx [-v] > mathresults.tsv"
			<< endl;
	cerr << "  OR" << endl;
	cerr << "       ./mathindex.exe -i mathdata.idx -p 41414" << endl;
	exit (1);
}

int main (int argc, char **argv)
{
	if (ENDOFBASELINE != EOBnone && ENDOFBASELINE != EOBsmall
			&& ENDOFBASELINE != EOBall)
	{
		cerr << "ERROR: ENDOFBASELINE defined incorrectly (" << ENDOFBASELINE <<
				")" << endl;
		throw;
	}
	char *infile = NULL;
	char *outfile = NULL;
	int base = 1;
	int socket = -1;
	while (argc - base > 0)
	{
		if (argc - base >= 1 && strcmp (argv[base], "-v") == 0)
		{
			VERBOSE = true;
			base++;
			continue;
		}
		if (argc - base >= 2 && strcmp (argv[base], "-i") == 0)
		{
			infile = argv[base + 1];
			base += 2;
			continue;
		}
		if (argc - base >= 2 && strcmp (argv[base], "-o") == 0)
		{
			outfile = argv[base + 1];
			base += 2;
			continue;
		}
		if (argc - base >= 2 && strcmp (argv[base], "-p") == 0)
		{
			socket = atoi (argv[base + 1]);
			base += 2;
			continue;
		}
		if (argc - base != 0)
			usage ();
	}
	istream & inDQ = cin;		// data or queries together
	ostream & outresults = cout;
	if (infile != NULL)
		inputIndex (outresults, infile);	// read in index
	if (socket >= 0)
	{
		socketInput (socket);
	}
	else
	{
		inputDQ (inDQ, outresults);
	}
	if (outfile != NULL)
		outputIndex (outresults, outfile);	// write out index
}
