
latexml  --preload=amsmath --preload=amsfonts --preload=aahomework.sty --preload=enumitem.sty  --preload=shortlst.sty --includestyles -dest=Lecture_01.xml  Lecture_01.tex 2> errors.txt

latexmlpost -dest=Lecture_01.html Lecture_01.xml
