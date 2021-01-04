## Tangent-S Math Formula Search Engine##

*Released August 2017*

*Authors:*

**Kenny Davila and Richard Zanibbi**,
Rochester Institute of Technology, USA

**Andrew Kane and Frank Tompa**,
University of Waterloo, Canada

-----

Tangent S is an application designed for indexing and retrieval of math formulas from large collections of documents or web pages. A complete description of our system may be found in our paper:

[Tangent-S SIGIR 2017](http://dl.acm.org/citation.cfm?id=3080748)

Further details can be found at: 

[Tangent-3 SIGIR 2016](http://dl.acm.org/citation.cfm?id=2911512)


##License##
	LICENSE: Source code, data and results are being released under a Non-Commercial Creative Commons License (see the LICENSE file). 


**Please cite the paper above if you use the source code or data in this repository, and indicate any changes made when code or data are re-released.**




##Package Overview##

This package contains the tools, code and debug data used for the version of our paper submitted to SIGIR 2017. The code package contains the following directory:

+ **tangent** <br /> 
  Source code for Tangent system along with additional tools for experiments and debug data


##Package Contents##



###Directory: tangent###

Contains all source code and test data required to run Tangent-S. The main directory has a set of python and C++ files used by Tangent. The pre-processing tools, re-ranking algorithm and experiment tools are all implemented in Python 3. The core-engine component has been implemented in C++. 

	NOTE: For detailed information about the source code and the tools, please see:
		tangent/readme.txt:  Basic instructions to compile and execute Tangent.
		tangent/experiment_tools/README_experiment_tools.txt: Describes tools for experiments.
  
The repository also contains the following sub-directories:

+ **experiment_tools** <br />
  A set of python scripts that can be used to obtain the different metrics for evaluation of our system. 

+ **TangentS** <br />
  This is the root module that contains the main sub-modules of our search engine. 

+ **TangentS/math** <br />
  This module contains all the basic Python classes used by our system for pre-processing of data and data representation (Symbol Layout Trees). 

+  **TangentS/ranking** <br /> A module which defines a set of classes and functions required for re-ranking of results using different similarity metrics including Maximum Subtree Similarity (MSS).  It also contains the set of classes used for generation of HTML search results.

+  **TangentS/utility** <br />
   Additional miscellaneous classes required by the Tangent system. 



+  **testing** <br />
   This directory contains some examples of the data and queries that can be accepted by our system. It contains the following files and sub-directories: 

  	+ **test_data:** A small Dataset containing files in different formats accepted by our system.
  	
    + **semantic_test_data:** A small Dataset containing files in different formats accepted by our system. Used for debugging of Operator Trees.
    
 	 + **test_queries:** Includes some examples of queries defined in the XML format supported by our system. Note that this folder includes the file NTCIR11-Math-queries.xml which defines the 100 queries used for the NTCIR-11 Wikipedia Task.
 	 
  	+ **testlist.txt:** This file has a listing of all the files contained in the test_data sub-directory, one file per line. This is the format used by our system to define a Dataset.  

  	+ **semantic_testlist.txt:** This file has a listing of all the files contained in the semantic_test_data sub-directory, one file per line. This is the format used by our system to define a Dataset.  

