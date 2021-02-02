# Table of Contents
1. [Setup and installation](#setup-and-installation)
   1. [Python](#python)
   2. [c++](#cpp)
   3. [LaTeXMl](#LaTeXML)
2. [Data and configuration](#data-and-configuration)
   1. [cntl file](#cntl-file)
   2. [Raw data](#raw-data)
      1. [ARQMath](#ARQMath)
      2. [NTCIR](#ntcir)
   3. [Tsv Files](#tsv-files)
      1. [Db Index](#index)
      2. [Results](#query)
      3. [1st Results](#1st-results)
      4. [Re-Ranked results](#re-ranked-results)
3. [All in one bash script](#all-in-one-bash-script)
4. [Running parts individually](#running-parts-individually)
   1. [Indexing](#indexing)
      1. [Generating Indices](#generating-indices)
      2. [Precomputed Indices](#using-precomputed-indices)
   2. [Querying](#querying)
   3. [Finding top K results](#Finding-top-K-results)
   4. [Re-ranking](#re-ranking)
   5. [Combining](#combining)
   
5. [Evaluation](#Evaluation)
   1. [Task 1](#Task-1)
   2. [Task 2](#task-2)
6. [Debugging](#debugging)
7. [Community Contributions](#community-contributions)


## Setup and Installation
Tested on linux
### Python
#### Conda
(optional) install anaconda distribution https://www.anaconda.com/products/individual
```zsh
$ conda create -n tangent-s python=3.6.9
$ conda activate tangent-s
$ cd /path/to/tangent-s 
$ pip install -r requirements.txt
$ export PYTHONPATH=$PYTHONPATH:/full/path/to/tangent-s/
```
To avoid having to reset the pythonpath every time a new 
terminal is opened run `conda develop $(pwd)` from the tangent-s directory


####Standalone Python
```zsh
$ cd /path/to/tangent-s 
$ pip install -r requirements.txt
$ export PYTHONPATH=$PYTHONPATH:/full/path/to/tangent-s/
```  
Add the export line to the .bash_profile file to avoid having
to export it every time a console is opened.  

### cpp
Build c++ indexing tool
```zsh
$ cd /path/to/tangent-s/
$ cd src/cpp/
$ make install
```
Take not that a mathindex.exe appears in the ``bin/`` directory
### LaTeXML
install LaTeXML conversion tool  
using debian based linux
```shell
sudo apt-get install latexml
```
other instructions can be found here https://dlmf.nist.gov/LaTeXML/get.html
## Data and Configuration
### cntl file
an example cntl file is shown below. explanations for each field can be found below that.
```shell
cntl	arqopt.cntl
window	4
queries	../testing/test_queries/opt_task1_mod.xml
doc_list	../cntl/testlist.txt
database	dbarqmathopt-new
chunk_size	200
tree_model	operator
file_skips	[0]
index_fileids	{3530}
query_fileids	{23618}
```
explanations: 

`cntl` the name of the control file  
`window` The window that is applied during 
the spectral graph search process. To get 
more info about this parameter reference the tangent-s papers  
`queries` relative or absolute path to the xml file 
containing the queries that should be run against the indexes. 
An example dictating the format is show below. Whether the mathml 
within the query is in presentation or content format matters 
when running the queries. 
<details>
<summary>example-queries.xml</summary>

```
<xml version="1.0">
<topics>
    <topic>
        <num>B.16</num>
        <query>
          <formula id="q_92"><math alttext="\int_{0}^{1}\frac{\ln(1+x)\ln(1-x)}{1+x}\,dx" display="block">   <apply>     <apply>       <csymbol cd="ambiguous">superscript</csymbol>       <apply>         <csymbol cd="ambiguous">subscript</csymbol>         <int/>         <cn type="integer">0</cn>       </apply>       <cn type="integer">1</cn>     </apply>     <apply>       <times/>       <apply>         <divide/>         <apply>           <times/>           <apply>             <ln/>             <apply>               <plus/>               <cn type="integer">1</cn>               <ci>𝑥</ci>             </apply>           </apply>           <apply>             <ln/>             <apply>               <minus/>               <cn type="integer">1</cn>               <ci>𝑥</ci>             </apply>           </apply>         </apply>         <apply>           <plus/>           <cn type="integer">1</cn>           <ci>𝑥</ci>         </apply>       </apply>       <apply>         <ci>d</ci>         <ci>𝑥</ci>       </apply>     </apply>   </apply> </math> </formula>
        </query>
    </topic>
    <topic>
    <num>B.35</num>
    <query>
      <formula id="q_290"><math alttext="\int e^{x^{2}}dx" display="block">   <apply>     <int/>     <apply>       <times/>       <apply>         <csymbol cd="ambiguous">superscript</csymbol>         <ci>𝑒</ci>         <apply>           <csymbol cd="ambiguous">superscript</csymbol>           <ci>𝑥</ci>           <cn type="integer">2</cn>         </apply>       </apply>       <apply>         <ci>d</ci>         <ci>𝑥</ci>       </apply>     </apply>   </apply> </math> </formula>
    </query>
    </topic>
    <topic>
    <num>B.46</num>
    <query>
      <formula id="q_370"><math alttext="\int x^{k}f(x)dx=0" display="block">   <apply>     <eq/>     <apply>       <int/>       <apply>         <times/>         <apply>           <csymbol cd="ambiguous">superscript</csymbol>           <ci>𝑥</ci>           <ci>𝑘</ci>         </apply>         <ci>𝑓</ci>         <ci>𝑥</ci>         <apply>           <ci>d</ci>           <ci>𝑥</ci>         </apply>       </apply>     </apply>     <cn type="integer">0</cn>   </apply> </math> </formula>
    </query>
  </topic>
 <topic>
    <num>B.82</num>
    <query>
      <formula id="q_807"><math alttext="A=\displaystyle\int_{0}^{2\pi}{g(x)\cdot\cos(x)\mathrm{d}x}" display="block">   <apply>     <eq/>     <ci>𝐴</ci>     <apply>       <apply>         <csymbol cd="ambiguous">superscript</csymbol>         <apply>           <csymbol cd="ambiguous">subscript</csymbol>           <int/>           <cn type="integer">0</cn>         </apply>         <apply>           <times/>           <cn type="integer">2</cn>           <ci>𝜋</ci>         </apply>       </apply>       <apply>         <times/>         <apply>           <ci>⋅</ci>           <apply>             <times/>             <ci>𝑔</ci>             <ci>𝑥</ci>           </apply>           <apply>             <cos/>             <ci>𝑥</ci>           </apply>         </apply>         <apply>           <ci>d</ci>           <ci>𝑥</ci>         </apply>       </apply>     </apply>   </apply> </math> </formula>
    </query>
  </topic>
</topics>
</xml>
```
</details>

`doc_list` this is a file containing the paths to the files 
that should be used during the indexing process. Paths can 
be relative or absolute.   
<details>
<summary>example-doclist.txt</summary>

```
/absolute/path/Documents/dprl/raw-data2/1/8829866.mml
/absolute/path/Documents/dprl/raw-data2/1/8799433.mml
/absolute/path/Documents/dprl/raw-data2/1/8872063.mml
/absolute/path/Documents/dprl/raw-data2/1/8844161.mml
/absolute/path/Documents/dprl/raw-data2/1/8864077.mml
```
</details>

`database` name to be prepended to query and index files generated in db-index/  
`chunk_size` During the indexing size multiple processes are kicked off
to speed up computation, the chunk size options dictates how many files are 
processed by a python process at a given time. Systems with less RAM can lower
this value if problems occur.  
`tree_model` operator or layout   
`file_skips` Data cached for the sake of computational speedup. This field will be automatically populated when indexing    
`index_fileids` This field represents the ids of the index files stored in `db-index`.  This field will be automatically populated when indexing    
`query_fileids` This field represents the ids of the query files stored in `db-index`.  This field will be automatically populated when building queries    


### Raw Data
In general the data can 
exist as an arbitrary number of html, xml, or mathml files.
These files then must be properly enumerated by the doclist which
is referenced in the cntl file.
#### ARQMath
Originally the ARQMath dataset exists as a series of html files with embedded latex. These 
files are then cleaned and parsed to generated TSV files in which the latex has been extracted 
and converted to MathML for both slt and opt representations. those files can be found here: https://drive.google.com/drive/folders/18bHlAWkhIJkLeS9CHvBQQ-BLSn4rrlvE.
these tsv files can then be transformed into individual 
files containing just the mathml using the script below. 
Change parameters within main function of script as necessary.
This script may take multiple hours to run and will generate files that can 
take up a significant amount of hard drive space (>100GB). 
If one does not have the space to do this, they can just use the precomputed indices discussed [here](#using-precomputed-indices).
```shell
cd  /path/to/tangent-s/src/python/converters/
python3 arqmath_convertor.py
```
#### NTCIR
NTCIR datasets are html files containing MathMl. They can be run through the 
pipeline by enumerating the documents into a doclist with `src/python/utility/dir2doclist`
### Tsv-Files
#### Index
An example index file (generated by index.py) is found below 
followed by explanations for each row
<details>
<summary>db-index/[db-name]_i_*.tsv</summary>

```
W	4
O	1

D	1000
E	[U!times,0[T!\\mathbb],1[O!SUB,0[V!𝐹],1[V!𝑝]]]	[0]

D	1001
E	[O!notin,0[V!𝑖],1[V!𝑚]]	[0]

D	1002
E	[V!𝑣]	[0]

D	1003
E	[O!leq,0[V!𝐺],1[U!times,0[T!\\mathfrak],1[O!SUB,0[V!𝑆],1[V!𝐺]]]]	[0]

D	1005
E	[U!eq,0[O!SUP,0[O!SUP,0[O!SUB,0[V!𝐴],1[O!minus,0[V!𝑞],1[N!1]]],1[V!𝑒]],1[V!𝑦]],1[U!union,0[U!intersect,0[O!SUB,0[O!SUP,0[V!𝐴],1[V!𝑒]],1[V!𝑞]],1[V!𝑇]],1[O!minus,0[O!SUB,0[O!SUP,0[V!𝐴],1[O!minus,0[V!𝑒],1[N!1]]],1[V!𝑞]],1[V!𝑇]]]]	[0]
```

</details>

`W` the window size  
`O` wherer or not is is an operator tree or slt

`D` DocId  
`E` [the expression] [the position it appears in]
#### Query
An example query file (generated by query.py) is found below 
followed by explanations for each row
the name is 
<details>
<summary>example db-index/[database]_q_*.tsv</summary>

```
K	1000
W	4
O	0

Q	A.1
E	[V!f[M!()1x1[=[O!divide,o[V!x[+[V!x[+[V!c]]]],a[N!2]],u[V!x[+[N!2[V!x[+[V!c]]]]],a[N!2]]]],w[V!x]]]	[0]

Q	A.2
E	[V!f[M!()1x1[=[V!f[M!()1x1,w[V!x[+[N!1]]]]]],w[V!x]],a[′]]	[0]

Q	A.3
E	[O!root,w[N!5]]	[0]

...
```
</details>

`K` Indicates that the top K results will be found for each query  
`W` the window size  
`O` todo

`Q` query id  
`E` formula

#### 1st Results

These are the initial K top results found for each query using the 
c++ built mathindex tool.

<details>
<summary>example results/[cntl]_results.tsv</summary>

```
I	it	77728.3
I	it	49447.7
I	it	68733
I	it	67039.8
I	it	65412.9
I	it	46666.1
I	it	47961.3
I	it	47491
I	it	80854.5
I	it	55637.2

Q	B.1
E	[U!eq,0[U!times,0[V!𝑓],1[V!𝑥]],1[O!divide,0[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[V!𝑥],2[V!𝑐]],1[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]],2[V!𝑐]]]]
R	15658584	0	[O!form-seq,0[U!eq,0[U!times,0[V!𝑓],1[V!𝑥]],1[O!divide,0[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[V!𝑥],2[V!𝑐]],1[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]],2[V!𝑐]]]],1[O!in,0[V!𝑥],1[U!times,0[T!\\mathbb],1[V!𝑅]]]]	0.8125
R	11639119	0	[U!eq,0[U!times,0[V!𝑔],1[U!times,0[V!𝑓],1[V!𝑥]]],1[O!divide,0[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[V!𝑥],2[N!1]],1[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]],2[N!1]]]]	0.8
R	11657033	0	[U!eq,0[U!times,0[V!𝑔],1[U!times,0[V!𝑓],1[V!𝑥]]],1[O!divide,0[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[V!𝑥],2[N!1]],1[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]],2[N!1]]]]	0.8
R	23659576	0	[U!eq,0[U!times,0[V!𝑓],1[V!𝑥]],1[O!divide,0[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]]],1[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]],2[N!2]]]]	0.788991
R	18854663	0	[U!eq,0[U!times,0[V!𝑓],1[V!𝑥]],1[O!divide,0[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[V!𝑎],1[V!𝑥]],2[V!𝑏]],1[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]],2[N!3]]]]	0.767857
R	3726843	0	[U!eq,0[U!times,0[V!𝑓],1[V!𝑥]],1[O!divide,0[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[V!𝑎],1[V!𝑥]],2[V!𝑏]],1[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]],2[N!3]]]]	0.767857
...
```

</details>

`I` indexing time  

`Q` query id  
`E` the Formula  
`R` a tuple defined as such (DocId, Score, Formula, retrieval time)


#### Re-Ranked Results
<details>
<summary>example results/[cntl]_results.tsv</summary>

```
Q	B.1
E	[U!eq,0[U!times,0[V!𝑓],1[V!𝑥]],1[O!divide,0[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[V!𝑥],2[V!𝑐]],1[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]],2[V!𝑐]]]]
R	15658584	0	[O!form-seq,0[U!eq,0[U!times,0[V!𝑓],1[V!𝑥]],1[O!divide,0[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[V!𝑥],2[V!𝑐]],1[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]],2[V!𝑐]]]],1[O!in,0[V!𝑥],1[U!times,0[T!\\mathbb],1[V!𝑅]]]]	[1.0,0.76,1.0]
R	23659576	0	[U!eq,0[U!times,0[V!𝑓],1[V!𝑥]],1[O!divide,0[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]]],1[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]],2[N!2]]]]	[0.8376963350785339,0.8,0.8421052631578947]
R	11535509	0	[U!eq,0[U!times,0[V!𝑓],1[V!𝑥]],1[O!divide,0[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!14],1[V!𝑥]],2[N!9]],1[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]],2[N!3]]]]	[0.8376963350785339,0.7619047619047619,0.8421052631578947]
R	18854663	0	[U!eq,0[U!times,0[V!𝑓],1[V!𝑥]],1[O!divide,0[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[V!𝑎],1[V!𝑥]],2[V!𝑏]],1[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]],2[N!3]]]]	[0.8376963350785339,0.7619047619047619,0.8421052631578947]
R	3726843	0	[U!eq,0[U!times,0[V!𝑓],1[V!𝑥]],1[O!divide,0[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[V!𝑎],1[V!𝑥]],2[V!𝑏]],1[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]],2[N!3]]]]	[0.8376963350785339,0.7619047619047619,0.8421052631578947]
R	20014085	0	[U!eq,0[U!times,0[V!𝑓],1[V!𝑥]],1[O!divide,0[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[V!𝑎],1[V!𝑥]],2[V!𝑏]],1[U!plus,0[O!SUP,0[V!𝑥],1[N!2]],1[U!times,0[N!2],1[V!𝑥]],2[N!3]]]]	[0.8376963350785339,0.7619047619047619,0.8421052631578947]
...
```

</details>

`Q` query id  
`E` the Formula  
`R` a tuple defined as such (DocId, Score, Formula, [post count , expr count , doc count])
## All in One Bash Script
It is recommended to read the rest of the documentation, even if one chooses to use 
the all-in-one script.
Within the tangent-s/bin directory there will be a set of bash scripts
which can be run to perform certain parts of the pipeline. 
To run everything with one command simply configure the cntl files
as needed and run `./arqmath-all` 

## Running Parts Individually
If relative paths are used in the control 
file, be mindful of where these commands are run.
In these examples commands are being run from the `bin` directory
### Indexing
#### Generating Indices  
If this is just a test it is recommended not to use the full ARQMath dataset
to achieve this run `head -20000 /path/to/full/doclist/ > new-doclist-small.txt` and use this
new doclist in the cntl file.  
run `python3 ../src/python/index_query/index.py example.cntl`  
this will generate a file in `/db-index` called `<database>_i_<number>.tsv` depending 
on the database name specified in the .cntl file. the format of this file
is discussed in [index](#index)
#### Using Precomputed Indices
A zip file called precomputed indices is located https://drive.google.com/drive/folders/1Qbrl7OpoMUpvJ-TJ65tNz3FRjVIV6CX4. 
Overwrite the existing db-index directory with the contents of the one contained 
in precomputed-indices. copy the control files and doc_list files into the cntl directory.
### Querying
run `python3 ../src/python/index_query/query.py example.cntl`  
this will generate a file in `/db-index` called `<database>_q_<number>.tsv` depending 
on the database name specified in the .cntl file. the format of this file
is discussed in [query](#query)
### Finding Top K Results
pipe the output of the indexes and queries to the math 
index tool and save that output to a results tsv  
``cat mathdata.tsv mathqueries.tsv | ./bin/mathindex.exe [-v] > mathresults.tsv``  
In the case in which the index and query files 
have just been generated in the db-index directory the command
would look as such  
`` cat ../db-index/[database]* | ./mathindex.exe > ../results/[cntl]-results.tsv``

### Re-Ranking

to rerank results run  
`python3 ../src/python/ranking/rerank_results.py ../cntl/control-file.cntl ../results/result-file-from-previous-step.tsv 12 ../results/reranked-result-file-to-be-generated.tsv`  
To rerank and generate a folder container html files giving insight to the re-rankings run  
`python3 ../src/python/ranking/rerank_results.py ../cntl/control-file.cntl ../results/result-file-from-previous-step.tsv 12 ../results/reranked-result-file-to-be-generated.tsv -h ../html`

### Combining
Combining results can be done with the following command. It is normally done to combine results from opt and slt representations.   


`python3 ../src/python/ranking/combine_rankings.py ../results/arq-slt-opt-results.tsv  __COMBINE_CACHE -r ../cntl/slt-cntl ../results/reranked-slt-result -r ../cntl/opt-cntl ../results/reranked-opt-result`
### Debugging
The index.py portion of the pipeline using multi-process programming. 
This can cause IDE debuggers to lose track of the process you would like to monitor. 
index_matt.py is a modified version of index.py that will run with only one process,
and will allow for proper debugging. This script will be orders of magnitude slower than
the original index.py and should not be run in production settings.
### Community Contributions
There are other datasets that can be applied to tangent-s. If you 
come across one you want to use, but have to do some cleaning in order for the dataset to
conform to the tangent-s inputs please consider documenting the cleaning script, adding it
to `src/python/converters/` and making a pull request.
