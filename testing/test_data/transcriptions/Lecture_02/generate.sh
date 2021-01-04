
latexml  --preload=amsmath --preload=amsfonts --preload=aahomework.sty --preload=enumitem.sty  --preload=shortlst.sty --includestyles -dest=Lecture_02.xml  Lecture_02.tex 2> errors.txt

latexmlpost -dest=Lecture_02.html Lecture_02.xml
