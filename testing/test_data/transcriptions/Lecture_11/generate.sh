
latexml  --preload=amsmath --preload=amsfonts --preload=aahomework.sty --preload=enumitem.sty  --preload=shortlst.sty --includestyles -dest=Lecture_11.xml  Lecture_11.tex 2> errors.txt

latexmlpost -dest=Lecture_11.html Lecture_11.xml
