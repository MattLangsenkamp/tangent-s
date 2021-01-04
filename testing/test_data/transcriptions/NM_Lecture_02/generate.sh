
latexml  --preload=amsmath --preload=amsfonts --preload=aahomework.sty --preload=enumitem.sty  --preload=shortlst.sty --includestyles -dest=NM_Lecture_02.xml  NM_Lecture_02.tex 2> errors.txt

latexmlpost -dest=NM_Lecture_02.html NM_Lecture_02.xml
