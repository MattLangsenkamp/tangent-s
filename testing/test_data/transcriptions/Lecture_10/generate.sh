
latexml  --preload=amsmath --preload=amsfonts --preload=aahomework.sty --preload=enumitem.sty  --preload=shortlst.sty --includestyles -dest=Lecture_10.xml  Lecture_10.tex 2> errors.txt

latexmlpost -dest=Lecture_10.html Lecture_10.xml
