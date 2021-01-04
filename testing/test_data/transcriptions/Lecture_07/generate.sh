
latexml  --preload=amsmath --preload=amsfonts --preload=aahomework.sty --preload=enumitem.sty  --preload=shortlst.sty --includestyles -dest=Lecture_07.xml  Lecture_07.tex 2> errors.txt

latexmlpost -dest=Lecture_07.html Lecture_07.xml
