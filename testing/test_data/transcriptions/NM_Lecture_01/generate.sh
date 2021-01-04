
latexml  --preload=amsmath --preload=amsfonts --preload=aahomework.sty --preload=enumitem.sty  --preload=shortlst.sty --includestyles -dest=NM_Lecture_01.xml  NM_Lecture_01.tex 2> errors.txt

latexmlpost -dest=NM_Lecture_01.html NM_Lecture_01.xml
