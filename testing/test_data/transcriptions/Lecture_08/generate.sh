
latexml  --preload=amsmath --preload=amsfonts --preload=aahomework.sty --preload=enumitem.sty  --preload=shortlst.sty --includestyles -dest=Lecture_08.xml  Lecture_08.tex 2> errors.txt

latexmlpost -dest=Lecture_08.html Lecture_08.xml
