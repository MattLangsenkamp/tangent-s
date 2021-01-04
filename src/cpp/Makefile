COMPILERFLAGS = -Wall -O3 -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64 -std=c++0x 
# COMPILERFLAGS = -Wall -g -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64 -std=c++0x -DDEBUG


COMPILER = c++ $(COMPILERFLAGS)                 # the default compiler to use for C++ programs as u++

default:   all		# Default

all: mathindex.exe

install: mathindex.exe
	mv mathindex*.exe ../../bin
## Executables

mathindex.exe: mathindexbase.h mathindexmid.h mathindex.cpp
	$(COMPILER) -D ENDOFBASELINE=EOBsmall mathindex.cpp -o mathindex.exe
	$(COMPILER) -D ENDOFBASELINE=EOBall   mathindex.cpp -o mathindex_eob.exe
	$(COMPILER) -D ENDOFBASELINE=EOBnone  mathindex.cpp -o mathindex_no_eob.exe

## Documentation
docs: 
	$(MAKE) -C doc 

## Clean
clean:
	rm -rf *.o *.exe *.dSYM
	rm -rf */__pycache__
	
