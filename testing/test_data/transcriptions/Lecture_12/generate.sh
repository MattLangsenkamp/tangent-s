
latexml  --preload=amsmath --preload=amsfonts --preload=aahomework.sty --preload=enumitem.sty  --preload=shortlst.sty --includestyles -dest=Lecture_12.xml  Lecture_12.tex 2> errors.txt

latexmlpost -dest=Lecture_12.html Lecture_12.xml
