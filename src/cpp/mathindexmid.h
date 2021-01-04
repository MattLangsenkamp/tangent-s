// (C) Copyright 2014 Andrew R. J. Kane <arkane@uwaterloo.ca>, All Rights Reserved.
//               2017 Kenny Davila <kxd7282@rit.edu> extensions for Operator Trees
//
//     Released for academic purposes only, All Other Rights Reserved.
//     This software is provided "as is" with no warranties, and the authors are not liable for any damages from its use.
//

// project: tangent-v3

// mathindexmid - classes and methods to implement some basic functionality of mathindex

#include <vector>
#include "mathindexbase.h"

#define DEBUGCOUNTALLPOST false
#define DEBUGVERIFYPARSING false

#define USE_COMMUTATIVE_PAIRS true

//== Expression to Tuple Expansion ========================================================

unsigned windowvalue = 4;
bool operatorTrees = false;

string runl (string s)
{
	int l = s.size ();
	if (l < 6)
	{
		return s;
	}
	ostringstream ss;
	for (int i = 0;;)
	{
		int e = s.find_first_not_of (s[i], i);
		ss << ((e < 0 ? l : e) - i) << s[i];
		i = e;
		if (e < 0)
		{
			return ss.str ();
		}
	}
}

#define ENMAXCH 6
class TupleCB
{
public:virtual void tuple (string frte, string tote, string rel, string loc) =
		0;
};
class TupleEmptyCB:public TupleCB
{
public:virtual void tuple (string frte, string tote, string rel,
		string loc)
{
}};
class TupleOutCB:public TupleCB
{
public:virtual void tuple (string frte, string tote, string rel, string loc)
{
	cout << "T\t" << frte << "\t" << tote << "\t" << rel << "\t" << loc << endl;
}
};

class ExprNode
{
public:
	char rel_type;
	string term_tag;
	//int chSize;
	//ExprNode *ch[ENMAXCH];	// type, term, children (Note: children are owned)
	std::vector<ExprNode*> children;

	ExprNode(char type = '-', string term = ""){
		rel_type = type;
		term_tag = term;

		/*
     chSize = 0;
     for (int i = 0; i < ENMAXCH; i++){
	    ch[i] = NULL;
    }
		 */
	}

	virtual ~ExprNode()
	{
		for (unsigned int i = 0; i < children.size(); i++){
			delete children[i];
		}

	}


	bool heightGT (int h)
	{
		if (h <= 0 && children.size() > 0){
			return true;
		}

		for (unsigned int i = 0; i < children.size(); i++){
			if (children[i]->heightGT(h - 1)){
				return true;
			}
		}

		return false;
	}

	bool has_child(char c)
	{
		//return children.find(c) != children.end();
		for (unsigned int i = 0; i < children.size(); i++){
			if (children[i]->rel_type == c){
				return true;
			}
		}

		return false;
	}

	void add(ExprNode * c)
	{
		if (c == NULL)
			return;

		if (has_child(c->rel_type)){
			cerr << "WARNING: Repeated child adding <" << c->rel_type << ">, " << (*c) << " to " << (*this) << endl;
			return;
		}

		//children[c->rel_type] = c;
		children.push_back(c);

		/*
    if (chSize >= ENMAXCH){
	    cerr << "WARNING: too many children adding " << (*c) << " to " << (*this) << endl;
	    return;
    }

    children[chSize++] = c;
		 */
	}				// takes ownership

    /*
        This functions generates all tuples at different window sizes for a fixed root.
    */
	void tuples (TupleCB & cb, int w, bool eob, string loc, ExprNode * from, string rel, bool commutative)
	{
	    //Relative location between "From" node and "this".
	    if (USE_COMMUTATIVE_PAIRS && commutative){
	        // Ignore relationship, assume first element (for commutative paths)
	        rel += '0';
	    } else {
	        // True tree relationship
		    rel += rel_type;
		}

		//Add pair between "From" and "this"
		if (rel_type != 'w' || term_tag != "E!")
		{
			cb.tuple(from->term_tag, term_tag, rel, runl(loc));
		}

		w--;
		if (w <= 0)
			return;

		for (unsigned int i = 0; i < children.size(); i++){
		    bool child_commutative = operatorTrees && term_tag.compare(0, 2, "U!") == 0;
		    children[i]->tuples(cb, w, eob, loc, from, rel, child_commutative);
		}

	}

    /*
        This function tranverses the tree, and call the tuple generation process for each node as the root
    */
	void tuples (TupleCB & cb, int w, bool eob, string loc)
	{
	    //Absolute location for current element
		loc += rel_type;

		// Generate the tuples for different window sizes at the current root ...
		for (unsigned int i = 0; i < children.size(); i++)
		{
		    bool child_commutative = operatorTrees && term_tag.compare(0, 2, "U!") == 0;
			children[i]->tuples(cb, w, eob, loc, this, "", child_commutative);
		}

        // Check if the end-of-base line tuple should be added for this node ...
		if (eob && !(has_child('n') || has_child('0')) && term_tag != "E!")
		{
			//Add the End-of-baseline tuple
			if (operatorTrees){
			    cb.tuple(term_tag, "0!", "0", runl(loc));
			} else {
			    cb.tuple(term_tag, "0!", "n", runl(loc));
			}

		}

		// Move to each child as a the new root and generate the corresponding tuples recursively...
		for (unsigned int i = 0; i < children.size(); i++)
		{
			children[i]->tuples (cb, w, eob, (rel_type == '-' ? "" : loc));
		}
	}

	void prec (ostream & out) const
	{
		/*
		for (int i = 0; i < chSize; i++)
		{
			out << (*children[i]);
		}
		*/
		//map<char, ExprNode*>::iterator

		/*
		//Special case next, print first!
		if (const_cast<ExprNode*>(this)->has_child('n')){
			out << *(const_cast<ExprNode*>(this)->children['n']);
		}

		for (auto it = children.cbegin(); it != children.cend(); it++){
			if (it->second->rel_type != 'n'){
				out << (*it->second);
			}
		}*/
		for (unsigned int i = 0; i < children.size(); i++)
		{
			out << (*children[i]);
		}
	}				// recursive print of children

	friend ostream & operator<< (ostream & out, const ExprNode & t)
	{
		if ((t.rel_type != '-') && (operatorTrees || t.rel_type != 'n'))
		{
			out << "," << t.rel_type;
		}

		out << "[" << t.term_tag;
		t.prec(out);
		out << "]";

		return out;
	}
};

#define PEWARN(b,w) if (b) { ostringstream ss; ss<<"WARNING: " w " "<<s<<" at i="<<i; error=ss.str(); return; }

static void
parseExprRec(string s, int &i, ExprNode * parent, string & error, char type='n')
{
	if (i >= (int)s.size())
		return;			// end of recursion

	bool first = (i == 0);
	PEWARN (s[i] != '[', "bad expression (0)");

	i++;
	// first element - relation specified by input type
	int end = s.find_first_of("[,]", i);

	PEWARN (end < 0 || end >= (int)s.size(), "bad expression reading past end");	// next control character
	char cc = s[end];

	PEWARN (end <= i, "bad expression (1)");	// must have value

	ExprNode *n = (first ? parent : new ExprNode());

	//Gets and assigns the node tag ...
	n->term_tag = s.substr(i, end - i);

	if (!first)
	{
		n->rel_type = type;
		parent->add(n);
		parent = n;
	}

	switch (cc)
	{
	case '[':
	       i = end;
	       parseExprRec(s, i, parent, error);
	       break;
	case ',':
		i = end + 1;
		break;
	case ']':
		i = end + 1;
		return;
	default:
		PEWARN (true, "bad expression (2)");
	}
	// remaining elements
	for (;;)
	{
		// value position indicates type is specified or not
		end = s.find_first_of("[,]", i);
		PEWARN (end < 0 || end >= (int) s.size (), "bad expression reading past end");	// next control character

		char cc = s[end];
		switch (cc)
		{
		case '[':
			PEWARN (end != i + 1, "bad expression (3)");
			type = s[i];
			i = end;
			parseExprRec(s, i, parent, error, type);
			break;		// other relation (single character type) followed by [...]
		case ',':
			PEWARN (end != i, "bad expression (4)");
			i++;
			break;		// must not have a value
		case ']':
			PEWARN (end != i, "bad expression (5)");
			i++;
			return;		// must not have a value
		default:
			PEWARN (true, "bad expression (6)");
		}
	}
}

static void parseExpr(TupleCB & cb, string s)
{
	int i = 0;
	ExprNode root;
	string error = "";

	parseExprRec (s, i, &root, error);	// parse
	if (error != "")
		cerr << error << " got " << root << endl;
	else{
		ostringstream ss;
		ss << root;
		if (s != ss.str())
			cerr << "WARNING: parse cannot reproduce input " << s << " -> " << ss.str() << endl;
	}
	// debugging
	//if (!root.heightGT(1)) cerr<<s<<"\t"<<root.heightGT(1)<<endl;
	root.tuples(cb, windowvalue, ENDOFBASELINE == EOBall || (ENDOFBASELINE == EOBsmall && !root.heightGT (1)), "");	// expand
	if (DEBUGVERIFYPARSING)
	{
		stringstream ss;
		ss << root;
		if (s != ss.str())
		{
			cerr << "WARNING: '" << s << "' != '" << ss.str () << "'" << endl;
		}
	}
}

//== Query/Output ========================================================

// TODO: can we remove all these virtual function calls?  maybe an array of IDIterPL pointers and keep them in sorted order...

#define IDEND INT_MAX

class IDIter
{
public:
	int cv, cc;
	llong s, us;			// value, count, size, unique size (no IND double counting)
	IDIter ()
	{
		cv = -1;
		cc = -1;
		s = us = 0;
	}
	virtual ~ IDIter ()
	{
	};
	virtual void skip (int v) = 0;	// jump to >= v
	virtual void print (ostream & out) const = 0;
	virtual void printv (ostream & out, int v) const
	{
		if (cv == v)
		{
			print (out);
		}
	}
	friend ostream & operator<< (ostream & out, const IDIter & t)
	{
		t.print (out);
		return out;
	}
};

class IDIterEmpty:public IDIter
{
public:
	IDIterEmpty ()
{
		cv = IDEND;
		cc = 0;
}
	virtual void skip (int v)
	{
	};				// jump to >= v
	virtual void print (ostream & out) const
	{
		out << "{empty}";
	}
};

class IDIterPL:public IDIter
{
	postingslist *pl;		// not owned by this object
	llong & postsk;
	int ci;			// index
	int qcount;			// query count
	inline void getCurrent ()
	{
		cv = pl->get (ci);
		cc = min (qcount, pl->getcount (ci));
		rem = pl->getcount (ci) - cc;
	}
	inline void next ()
	{
		ci++;
		if (ci >= s)
		{
			cv = IDEND;
			ci = s - 1;
		}
		else
		{
			getCurrent ();
		}
	}
public:
	int rem;			// remaining postings
	IDIterPL (postingslist * pl, int count, llong & p):postsk (p)
	{
		this->pl = pl;
		s = us = pl->size ();
		ci = -1;
		qcount = count;
		rem = -1;
		next ();
		if (DEBUGCOUNTALLPOST)
			postsk++;
	}				// start at first element
	virtual ~ IDIterPL ()
	{
		if (ci != s - 1)
		{
			cerr << "INTERNAL ERROR: not at end of postingslist" << endl;
			throw;
		}
	}
	virtual void skip (int v)
	{
		int ciOrig = ci;
		if (cv < v)
		{
			next ();
		}
		if (cv >= v)
		{
			if (DEBUGCOUNTALLPOST)
				postsk += ci - ciOrig;
			return;
		}				// could be v - 1...
		if (v >= IDEND)
		{
			cv = IDEND;
			ci = s - 1;
			postsk += ci - ciOrig;
			return;
		}
		// doubling search
		int jump = 1;
		while (ci + jump < s && pl->get (ci + jump) < v)
		{
			jump *= 2;
		}
		if (jump > 1)
		{
			jump /= 2;
			ci += jump;
			// binary search in range
			while (jump > 1)
			{
				jump /= 2;
				int split = ci + jump;
				if (split < s && pl->get (split) < v)
				{
					ci = split;
				}
			}
		}
		next ();
		postsk += ci - ciOrig;
	}				// jump to >= v
	virtual void print (ostream & out) const
	{
		out << "{" << cv << "," << cc << "}";
	}
};

class IDIterIND:public IDIter
{				// indirect iterator pointing to a shared IDIterPL
	IDIterPL *bs;			// not owned, so do not delete
	inline void getCurrent ()
	{
		cv = bs->cv;
		cc = min (1, bs->rem);
		bs->rem -= cc;
	}
public:
	IDIterIND (IDIterPL * base)
{
		bs = base;
		s = bs->s;
		getCurrent ();
}
	virtual void skip (int v)
	{
		if (bs->cv < v)
		{
			bs->skip (v);
		}
		getCurrent ();
	}				// jump to >= v
	virtual void print (ostream & out) const
	{
		out << "{IND," << *bs << "}";
	}
};

class IDIterOR:public IDIter
{
protected:
	string type;
	bool own;
	IDIter *x;
	IDIter *y;
	inline void getCurrent ()
	{
		if (x->cv < y->cv)
		{
			cv = x->cv;
			cc = x->cc;
		}
		else if (x->cv > y->cv)
		{
			cv = y->cv;
			cc = y->cc;
		}
		else
		{
			cv = x->cv;
			cc = (x->cc) + (y->cc);
		}
	}
public:
	IDIterOR (IDIter * x, IDIter * y, bool own = true)
{
		type = "OR";
		this->own = own;
		this->x = x;
		this->y = y;
		getCurrent ();
		s = x->s + y->s;
		us = x->us + y->us;
}
	virtual ~ IDIterOR ()
	{
		if (own && x != NULL)
		{
			delete x;
			x = NULL;
		}
		if (own && y != NULL)
		{
			delete y;
			y = NULL;
		}
	};
	virtual void skip (int v)
	{
		if (x->cv < v)
		{
			x->skip (v);
		}
		if (y->cv < v)
		{
			y->skip (v);
		}
		getCurrent ();
	};				// jump to >= v
	virtual void print (ostream & out) const
	{
		out << "[" << type << (*x) << "," << (*y) << "]";
	}
	virtual void printv (ostream & out, int v) const
	{
		if (cv == v)
		{
			out << "[" << type << "(cc=" << cc << ")";
			x->printv (out, v);
			out << ",";
			y->printv (out, v);
			out << "]";
		}
	}
};

class IDIterADD:public IDIterOR
{
public:			// LHS doesn generate values
	IDIterADD (IDIter * x, IDIter * y, bool own = true):IDIterOR (x, y, own)
{
		type = "ADD";
}
	virtual void skip (int v)
	{
		if (x->cv < v)
		{
			x->skip (v);
		}
		if (y->cv < x->cv)
		{
			y->skip (x->cv);
		}
		getCurrent ();
	};				// jump to >= v
};

// TODO: mechanism not right for this when count > 1
class IDIterANY:public IDIterOR
{				// count always 1
	inline void getCurrent ()
	{
		if (x->cv < y->cv)
		{
			cv = x->cv;
			cc = x->cc;
		}
		else if (x->cv > y->cv)
		{
			cv = y->cv;
			cc = y->cc;
		}
		else
		{
			cv = x->cv;
			cc = max (x->cc, y->cc);
		}
	}
public:
	IDIterANY (IDIter * x, IDIter * y, bool own = true):IDIterOR (x, y, own)
{
		type = "ANY";
		getCurrent ();
}

	virtual void skip (int v)
	{
		if (x->cv < v)
			x->skip (v);

		if (x->cv == v && x->cc == 1 && v < IDEND){
			cv = x->cv;
			cc = x->cc;
			return;
		}				/* don't process right side if already at value */

		if (y->cv < v)
			y->skip (v);

		getCurrent ();
	}				// jump to >= v

	virtual void print (ostream & out) const
	{
		out << "[" << type << "...]";
	}				// don't expand IDIterANY
};
