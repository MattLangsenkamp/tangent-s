This Readme is supplemental to the main readme. If things are unclear consider reading the main readme first

# Table of Contents
1. [Download Files and Installation](#Download-Files-and-Installation)
   1. [Indices](#indices)
   2. [Control and Doclist Files](#control-and-doclist-files)
   4. [Trec Eval Tool](#trec-eval-tool)
   5. []
2. [Run It]($run it)
3. [Evaluation](#evaluation)

## Download Files and Installation
### Indices 
Download the zip file here.  
https://drive.google.com/drive/folders/1Qbrl7OpoMUpvJ-TJ65tNz3FRjVIV6CX4  
After extracting the files move all index files to the `tangent-s/db-index` folder  
![Indices](imgs/indices.png)
### Control and Doclist Files
Move the doclist files and control files to the `tangent-s/cntl` folder 
![Files](imgs/cntl.png)
### Trec Eval Tool
Download trec eval tool shown here, outside the tangent-s directory.  
https://github.com/usnistgov/trec_eval  
Navigate the directory it is downloaded in and edit the Makefile so that the first
line BIN variable points to the `tangent-s/evaluation/data/` folder as such  
![bin](imgs/bin.png)  
Run `make install` and ensure a `trec_eval` executable populated in the `tangent-s/evaluation/data/` folder  
![trec](imgs/trec.png)  



