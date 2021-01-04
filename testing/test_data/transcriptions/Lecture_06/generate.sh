
latexml  --preload=amsmath --preload=amsfonts --preload=aahomework.sty --preload=enumitem.sty  --preload=shortlst.sty --includestyles -dest=Lecture_06.xml  Lecture_06.tex 2> errors.txt

latexmlpost -dest=Lecture_06.html Lecture_06.xml
