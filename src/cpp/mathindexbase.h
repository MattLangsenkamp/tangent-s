// (C) Copyright 2014 Andrew R. J. Kane <arkane@uwaterloo.ca>, All Rights Reserved.
//               2017 Kenny Davila <kxd7282@rit.edu> extensions for Operator Trees
//
//     Released for academic purposes only, All Other Rights Reserved.
//     This software is provided "as is" with no warranties, and the authors are not liable for any damages from its use.
//

// project: tangent-v3

// mathindexbase - base classes and methods to support mathindex

#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <list>
#include <vector>
#include <iterator>
#include <algorithm>
#include <iostream>
#include <map>
#include <set>
#include <string.h>
#include <sstream>
#include <fstream>
#include <limits.h>
#include <sys/time.h>

using namespace std;

//== utils ========================================================

#define llong long long int

static llong
nanoTime ()
{
	timeval t;
	gettimeofday (&t, NULL);
	return (llong) t.tv_sec * 1000000000 + (llong) t.tv_usec * 1000;
}

//== reorder expression IDs ========================================================

class eidorder
{
public:
	int fr, to, tc, od;
	friend ostream & operator<< (ostream & out, const eidorder & t)
	{
		out << "{" << t.fr << "," << t.to << "," << t.tc << "," << t.od << "}";
		return out;
	}
};

//== serialize index to/from file ========================================================

class WF
{
	FILE *f;
public:
	WF (const char *filename)
{
		f = fopen (filename, "w");
}
	WF (WF &)
	{
		cerr << "ERROR: should pass by reference WF" << endl;
		throw;
	}
	virtual ~ WF ()
	{
		fclose (f);
		f = NULL;
	}
	void i (int v)
	{
		fwrite (&v, sizeof (int), 1, f);
	}
	void ia (int *v, int size)
	{
		fwrite (v, size * sizeof (int), 1, f);
	}
	void ll (llong v)
	{
		fwrite (&v, sizeof (llong), 1, f);
	}
	void s (string v)
	{
		int size = v.size ();
		i (size);
		fwrite (v.c_str (), sizeof (char) * size, 1, f);
	}
};

inline void
fread_full (void *ptr, size_t size, size_t count, FILE * stream)
{
	size_t rsize = fread (ptr, size, count, stream);
	if (rsize != count)
	{
		cerr << "file read error count=" << count << " rsize=" << rsize << endl;
		perror ("perror");
		throw;
	}
}

class RF
{
	FILE *f;
	char *b;
	int bSize;
public:
	RF (const char *filename)
{
		f = fopen (filename, "r");
		bSize = 1 << 20;
		b = new char[bSize];
}
	RF (RF &)
	{
		cerr << "ERROR: should pass by reference RF" << endl;
		throw;
	}
	virtual ~ RF ()
	{				/* TODO: verify read entire index */
		fclose (f);
		f = NULL;
		delete[]b;
		b = NULL;
		bSize = 0;
	}
	int i ()
	{
		int v;
		fread_full (&v, sizeof (int), 1, f);
		return v;
	}
	void ia (int *v, int size)
	{
		fread_full (v, sizeof (int), size, f);
	}
	llong ll ()
	{
		llong v;
		fread_full (&v, sizeof (llong), 1, f);
		return v;
	}
	string s ()
	{
		int size = i ();
		if (size + 1 >= bSize)
		{
			cerr << "ERROR:string too big" << endl;
			throw;
		}
		fread_full (b, sizeof (char), size, f);
		b[size] = 0;
		return string (b);
	}
};

//== Base Classes ========================================================

#define WARN(b,s,x) if (b) { cerr<<"WARNING: " s " "<<x<<endl; }
#define WARNR(b,s,x) if (b) { cerr<<"WARNING: " s " "<<x<<endl; return; }

class tokentuple
{
public:
	int from, to, rel;		// from, to, relationship
	tokentuple (RF & f)
	{
		r (f);
	}
	tokentuple (int f, int t, int r)
	{
		from = f;
		to = t;
		rel = r;
	}
	bool isValid ()
	{
		return (from >= 0 && to >= 0 && rel >= 0);
	}
	bool operator== (const tokentuple & t) const
		  {
		return (from == t.from && to == t.to && rel == t.rel);
		  }
	bool operator!= (const tokentuple & t) const
		  {
		return !(*this == t);
		  }
	bool operator< (const tokentuple & t) const
	{
		if (from < t.from || (from == t.from && (to < t.to || (to == t.to && rel < t.rel))))
			return true;
		else
			return false;
	}
	friend ostream & operator<< (ostream & out, const tokentuple & t)
	{
		out << "{" << t.from << "," << t.to << "," << t.rel << "}";
		return out;
	}
	void w (WF & f)
	{
		f.i (from);
		f.i (to);
		f.i (rel);
	}
	void r (RF & f)
	{
		from = f.i ();
		to = f.i ();
		rel = f.i ();
	}
};

class qresult
{
public:
	int ex;
	double sc;			// exprID, score
	qresult (int e, double s)
	{
		ex = e;
		sc = s;
	}
	bool operator< (const qresult & t) const
	{
		if (sc < t.sc || (sc == t.sc && ex > t.ex))
			return true;
		else
			return false;
	}				// consistent ordering
	friend ostream & operator<< (ostream & out, const qresult & t)
	{
		out << "{" << t.ex << "," << t.sc << "}";
		return out;
	}
};

class intlist
{
protected:
	int lSize;
	int allocSize;
	int *l;
	void grow ()
	{
		int gs = min (1 << 20, allocSize);	// max 1m integer growth
		l = (int *) realloc (l, (allocSize + gs) * sizeof (int));
		memset (l + allocSize, 0, gs * sizeof (int));
		allocSize += gs;
	}
public:
	intlist ()
{
		lSize = 0;
		allocSize = 4;
		l = (int *) realloc (NULL, allocSize * sizeof (int));
}				// initial size 4 integers
	virtual ~ intlist ()
	{
		if (l != NULL)
		{
			free (l);
		}
	}
	void add (int value)
	{
		if (lSize >= allocSize)
			grow ();
		l[lSize++] = value;
	}
	int size ()
	{
		return lSize;
	}
	int get (int i)
	{
		return (*this)[i];
	}
	int &operator[] (int i)
	{
		if (i < 0 || i >= lSize)
		{
			cerr << "INTERNAL ERROR: access to list out of range " << i << endl;
			throw;
		}
		return l[i];
	}
	friend ostream & operator<< (ostream & out, const intlist & t)
	{
		out << "(";
		for (int i = 0; i < t.lSize; i++)
		{
			out << t.l[i] << " ";
		} out << ")";
		return out;
	}
	void w (WF & f)
	{
		f.i (lSize);
		f.ia (l, lSize);
	}
	void r (RF & f)
	{
		allocSize = lSize = f.i ();
		l = (int *) realloc (l, (allocSize) * sizeof (int));
		f.ia (l, lSize);
	}
};

static int
twointsort (const void *A, const void *B)
{
	return ((int *) A)[0] - ((int *) B)[0];
}

class postingslist:protected intlist
{				// list of {id,count}
public:
	void add (int v, int count)
	{
		intlist::add(v);
		intlist::add(count);
	}
	int size ()
	{
		return intlist::size () / 2;
	}
	int get (int i)
	{
		return l[2 * i];
	}
	int getcount (int i)
	{
		return l[2 * i + 1];
	}
	friend ostream & operator<< (ostream & out, const postingslist & t)
	{
		out << (intlist &) t;
		return out;
	}
	void reorder (eidorder * e)
	{
		for (int i = 0; i < lSize; i += 2)
		{
			l[i] = e[l[i]].to;
		} qsort (l, size (), 2 * sizeof (int), twointsort);
	}
	void w (WF & f)
	{
		intlist::w (f);
	}
	void r (RF & f)
	{
		intlist::r (f);
	}
};

//== Dictionary/Lexicon/SubObjectMap ========================================================

// TODO: canonical form of strings to save memory?

int noValue = -2;		// must be different from varID below
int varID = -1;			// variable special id (must not equal noValue from failed dictionary lookup)

// Dictionary: maps T-to-int and array int-to-T
template < class T > class Dictionary
{
protected:
	std::map < T, int > dict;	// T-to-int
	vector < T > rev;		// int-to-T
public:
	int last ()
	{
		return dict.size() - 1;
	}
	int add (const T & s)
	{
		typename std::map < T, int >::const_iterator it = dict.find(s);
		if (it != dict.end ())
			return it->second;	// value exists

		int id = dict.size();

		dict[s] = id;
		rev.push_back (s);

		return id;			// new value
	}
	int find (const T & s)
	{
		typename std::map < T, int >::const_iterator it = dict.find (s);
		if (it != dict.end ())
			return it->second;
		else
			return noValue;
	}
	int size ()
	{
		return dict.size ();
	}
	const T & get (int i)
	{
		if (i < 0 || i >= (int) dict.size ())
		{
			cerr << "INTERNAL ERROR: access to dictionary out of range " << i <<
					endl;
			throw;
		}
		return rev[i];
	}
	const T & operator[] (int i)
	{
		return get (i);
	}
	friend ostream & operator<< (ostream & out, const Dictionary & t)
	{
		out << "[";
		for (unsigned i = 0; i < t.rev.size (); i++)
		{
			out << "(" << i << "=" << t.rev[i] << ")";
		} out << "]";
		return out;
	}
};

class StringDictionary:public Dictionary < string >
{
public:
	void reorder (eidorder * e)
	{
		for (std::map < string, int >::iterator it = dict.begin ();
				it != dict.end (); it++)
		{
			it->second = e[it->second].to;
		}
		for (std::map < string, int >::iterator it = dict.begin ();
				it != dict.end (); it++)
		{
			rev[it->second] = it->first;
		}
	}
	void w (WF & f)
	{
		int size = rev.size ();
		f.i (size);
		for (int i = 0; i < size; i++)
		{
			f.s (rev[i]);
		}}
	void r (RF & f)
	{
		int size = f.i ();
		for (int i = 0; i < size; i++)
		{
			add (f.s ());
		}}
};

class TTDictionary:public Dictionary < tokentuple >
{
public:
	void w (WF & f)
	{
		int size = rev.size ();
		f.i (size);
		for (int i = 0; i < size; i++)
		{
			rev[i].w (f);
		}}
	void r (RF & f)
	{
		int size = f.i ();
		for (int i = 0; i < size; i++)
		{
			tokentuple t (f);
			add (t);
		}}
};

// vector of intlist* or postingslist*
template < class T > class VectorL
{
	vector < T * >ls;
public:
	virtual ~ VectorL ()
	{
		for (unsigned i = 0; i < ls.size (); i++)
		{
			delete ls[i];
		}}
	T *get (int i)
	{
		if (i >= 0)
			return ls[i];
		else
			return NULL;
	}
	T *start (int i)
	{				// get or start new T
		if (i >= (int) ls.size ())
			ls.push_back (new T ());	// add if new
		T *l = ls[i];
		if (l == NULL)
		{
			cerr << "ERROR: internal problem with VectorL i=" << i << endl;
			throw;
		}				// check
		return l;
	}
	friend ostream & operator<< (ostream & out, const VectorL < T > &t)
	{
		out << "[";
		for (unsigned i = 0; i < t.ls.size (); i++)
		{
			out << "(" << i << "=" << t.ls[i] << ")";
		} out << "]";
		return out;
	}
	void reordervalues (eidorder * e)
	{
		typename vector < T * >::const_iterator ci;
		for (ci = ls.begin (); ci != ls.end (); ci++)
		{
			(*ci)->reorder (e);
		}
	}
	void reorderlists (eidorder * e)
	{
		vector < T * >t (ls);
		for (unsigned i = 0; i < t.size (); i++)
		{
			ls[e[i].to] = t[i];
		}}
	void w (WF & f)
	{
		int size = ls.size ();
		f.i (size);
		for (int i = 0; i < size; i++)
		{
			ls[i]->w (f);
		}}
	void r (RF & f)
	{
		int size = f.i ();
		for (int i = 0; i < size; i++)
		{
			T *t = new T ();
			t->r (f);
			ls.push_back (t);
		}}
};

class VectorPL:public VectorL < postingslist >
{
};
class VectorIL:public VectorL < intlist >
{
};

// Lexicon: maps tokentuple-to-int and int-to-postinglist* (of exprIDs) and tokentuplevar-to-postingslist* (of tokentupleIDs)
class Lexicon
{
	TTDictionary dict;
	VectorPL pls;
	TTDictionary dictvar;
	VectorPL plsvar;
public:
	llong ttc;			// tokentuple count (unique tuples within each expression)
	llong vttc;			// var tokentuple expansion count
	Lexicon ()
	{
		ttc = 0;
	}
	llong allPostingSizes ()
	{
		llong c = 0;
		for (int i = 0; i < dict.size (); i++)
		{
			c += pls.get (i)->size ();
		} return c;
	}
	llong allPostingCounts ()
	{
		llong c = 0;
		for (int i = 0; i < dict.size (); i++)
		{
			postingslist *pl = pls.get (i);
			for (int k = 0; k < pl->size (); k++)
			{
				c += pl->getcount (k);
			}} return c;
	}
	postingslist *get (const tokentuple & e)
	{
		return pls.get (dict.find (e));
	}
	void getvar (const tokentuple & e, set < postingslist * >&v)
	{
		postingslist *pl = plsvar.get (dictvar.find (e));
		if (pl == NULL)
			return;
		// debugging
		//cerr<<"expand "<<e<<" to "; for (int i=0; i<pl->size(); i++) { cerr<<dict.get(pl->get(i))<<" "; } cerr<<endl;
		for (int i = 0; i < pl->size (); i++)
		{
			v.insert (pls.get (pl->get (i)));
		}
	}
	int size ()
	{
		return dict.size ();
	}
	int sizevar ()
	{
		return dictvar.size ();
	}
	void add (const tokentuple & e, int count, int exprID)
	{
		int ttID = dict.add (e);
		postingslist *pl = pls.start (ttID);
		postingslist *npl = get (e);
		if (pl != npl)
		{
			cerr << "ERROR: Lexicon.add did not add " << e << " pl=" << pl <<
					" npl=" << npl << endl;
			throw;
		}				// check
		pl->add (exprID, count);
		ttc++;
		// variable tokentuples
		if (MATCHVARS && ttID == dict.last ())
		{
			// TODO: add counts
			// TODO: could have multiple postings for same ttID?
			vttc += 2;
			plsvar.start (dictvar.add (tokentuple (e.from, varID, e.rel)))->
					add (ttID, 1);
			plsvar.start (dictvar.add (tokentuple (varID, e.to, e.rel)))->
					add (ttID, 1);
		}
	}
	friend ostream & operator<< (ostream & out, const Lexicon & t)
	{
		out << "[dict=" << t.dict << " pls=" << t.pls << "]";
		return out;
	}
	void reorder (eidorder * e)
	{
		pls.reordervalues (e);
	}
	void w (WF & f)
	{
		f.ll (ttc);
		f.ll (vttc);
		dict.w (f);
		pls.w (f);
		dictvar.w (f);
		plsvar.w (f);
	}
	void r (RF & f)
	{
		ttc = f.ll ();
		vttc = f.ll ();
		dict.r (f);
		pls.r (f);
		dictvar.r (f);
		plsvar.r (f);
	}
};

// SubObjectMap: array exprID-to-postingslist (of docIDs, firstposition)
class SubObjectMap
{
	VectorPL pls;
public:
	llong ec;			// expression count
	postingslist *get (int exprID)
	{
		return pls.get (exprID);
	}
	void add (unsigned exprID, int docID, vector < int >&pos)
	{
		// TODO: handle multiple of same docID?
		// TODO: verify docID order?
		ec++;
		postingslist *pl = pls.start (exprID);
		for (int i = 0; i < pos.size (); i++)
		{
			pl->add (docID, pos[i]);	// use pos as count
		}
	}
	friend ostream & operator<< (ostream & out, const SubObjectMap & t)
	{
		out << t.pls;
		return out;
	}
	void reorder (eidorder * e)
	{
		pls.reorderlists (e);
	}
	void w (WF & f)
	{
		f.ll (ec);
		pls.w (f);
	}
	void r (RF & f)
	{
		ec = f.ll ();
		pls.r (f);
	}
};

//== top-k heap of results ========================================================

bool
comptopk (const qresult & a, const qresult & b)
{
	return b < a;
}				// comparison function

class topkheap
{
	bool active;
	unsigned topksize;
	vector < qresult > h;
public:
	topkheap ()
{
		active = true;
		topksize = 3;
}

	bool add (qresult r)
	{
		if (!active)
		{
			cerr << "INTERNAL ERROR: adding to heap when not active " << r <<
					endl;
			throw;
		}
		bool nmin = false;		// new minimum score
		if (h.size () < topksize)
		{
			h.push_back (r);
			push_heap (h.begin (), h.end (), comptopk);
			if (h.size () >= topksize)
			{
				nmin = (threshold () > 0);
			}
		}

		else if (comptopk (r, h.front ()))
		{
			double t = threshold ();
			std::pop_heap (h.begin (), h.end (), comptopk);
			h.pop_back ();
			h.push_back (r);
			std::push_heap (h.begin (), h.end (), comptopk);
			nmin = (threshold () > t);
		}
		// debugging
		//cerr<<"added "<<r<<"\theap "<<h.size()<<" "; for (int i=0;i<h.size();i++) { cerr<<h[i]<<" "; } cerr<<endl;
		return nmin;
	}

	vector < qresult > &output ()
		  {
		active = false;		/* don't allow adds while not a heap */
		sort_heap (h.begin (), h.end (), comptopk);
		return h;
		  }

	void clear ()
	{
		h.clear ();
		active = true;
	}

	void settopk (int v)
	{
		clear ();
		topksize = v;
	}

	double threshold ()
	{
		return (h.size () < topksize ? 0 : h.front ().sc);
	}

	friend ostream & operator<< (ostream & out, const topkheap & t)
	{
		out << "[";
		for (unsigned i = 0; i < t.h.size (); i++)
		{
			out << "(" << i << "=" << t.h[i] << ")";
		} out << "]";
		return out;
	}
};

//== Input/Output Control ========================================================

ifstream *
ifstreamOpen (char *filename)
{
	ifstream *in = new ifstream (filename, ifstream::in);
	if (!in->is_open ())
	{
		cerr << "ERROR: unable to open file " << filename << endl;
		exit (1);
	}

	return in;
}

static void
split (const string & line, string delim, vector < string > &result)
{
	for (int s = 0;;)
	{
		int e = line.find (delim, s);
		result.push_back (e >= 0 ? line.substr (s, e - s) : line.substr (s));
		if (e >= 0)
			s = e + 1;
		else
			break;
	}
}
