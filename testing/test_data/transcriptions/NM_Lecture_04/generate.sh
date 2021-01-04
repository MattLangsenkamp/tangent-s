
latexml  --preload=amsmath --preload=amsfonts --preload=aahomework.sty --preload=enumitem.sty  --preload=shortlst.sty --includestyles -dest=NM_Lecture_04.xml  NM_Lecture_04.tex 2> errors.txt

latexmlpost -dest=NM_Lecture_04.html NM_Lecture_04.xml
