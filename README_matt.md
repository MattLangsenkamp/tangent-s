# Table of Contents
1. [setup and installation](#setup-and-installation)
   1. [python](#python)
   2. [c++](#c++)
2. [data and configuration](#data-and-configuration)
3. [indexing](#indexing)
4. [querying](#querying)


## setup and installation
tested on linux
### python
(optional) install anaconda distribution https://www.anaconda.com/products/individual
```zsh
$ conda create -n tangent-s python=3.6.9
$ conda activate tangent-s
$ export PYTHONPATH=$PYTHONPATH:/path/to/tangent-s/src/
$ cd /path/to/tangent-s 
$ pip install -r requirements.txt
```

standalone python
```zsh
$ cd /path/to/tangent-s 
$ pip install -r requirements.txt
```

### c++
Build c++ indexing tool
```zsh
$ cd /path/to/tangent-s/
$ cd src/cpp/
$ make
```
Take not that a mathindex.exe appears in the ``src/cpp/`` directory
## data and configuration
## indexing
## querying
## testing
## example