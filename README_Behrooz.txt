Task 1
*** Tangent-S to ARQMath conversion:
To convert Tangent-s result to ARQMath result run the following script:
python3 convert_tangents_to_arqmath_task1.py -ldir path/to/latex_files -res tangents_combined -arq result_file
-ldir: directory in which the latex tsv files are located
-res: TangentS retrieval results for task 1 (This is the combined results after re-ranking)
-arq: The arqmath format output file

*** Tangent-S and TF-IDF combination:
To have an unweighted combination of Tangent-S and TF-IDF results, run the following script on the Trec_formatted result files:
python linear_combination.py -tan TangentS_Res.tsv  -te tf_idf_task1_final.tsv  -res combined_tf_idf_tangents
-tan: ARQMath formatted result from Tangent-s
-te: ARQMath formatted result from TF-IDF model
-res: File path to save the result


*** ARQMath to Prim conversion:
To do the evaluation, the arqmath formatted files should be converted to Trec format and them unjudged posts should be removed. 
To do that locate all the arqmath formatted files in a directory, then specify the trec format and prim directory to write the result.
Sample command:
    python get_prim_files_task1.py
    -qre qrel_partial_task1
    -sub "/ARQMath Task 1/All_results/"
    -tre "/ARQMath Task 1/All_Trec/"
    -pri "/ARQMath Task 1/All_Trec_Prim/"

*** Evaluation
To evaluate the results, user "qrel_official_task1" as the qrel file and run the following code:
python3 task1_evaluation.py -eva path/to/trec_eval   -qre path/to/qrel_file   -prim path/to/prim_directory   -res result_file
-eva: Path to trec_eval tool
-qre: Path to qrel file, which is "qrel_official_task1"
-prim: Path to prim directory, where all the prim results are located in
-res: File path to save the results

Task 2
*** Tangent-S to ARQMath conversion:
To convert Tangent-s result to ARQMath formatted result run the following code:
python3 get_tangents_results_task2.py -ldir path/to/latex_files	-res tangents_combined	-arq result_file
-ldir: Directory in which the latex tsv files are located
-res: TangentS retrieval results for task 2 (This is the combined results after re-ranking)
-arq: The arqmath format output file

*** ARQMath to Deduplicated conversion:
In Task 2, only visually-distinct formulae are considered. To convert the ARQMath formatted result to a de-duplicated one, you need the following files:
- visual_id_file: this file shows the formula visual id, slt string, latex string
- formulas_slt_string: this file indicates formula id, post id, slt string
Run the following script to get de-duplicated result:
python3 arqmath_2020_task2_convert_runs.py -ru /path/to/ARQMath_result_files  -re /path/to/result  -v /path/to/visual_if_file -q /path/to/visual_qrel -ld path/to/latex_tsv_files -s path/to/formula_slt_string
-ru: Directory in which the ARQMath formatted results for task 2 are located
-re: Directory to save de-duplicated results
-v: Path to visual_id_file
-q: Path to qrel built on visual ids (qrel_task2_official_2020_visual_id.tsv)
-ld: Directory in which the latex tsv files are located
-s: Path to formula_slt_string

<Note>: This will produce results on test queries. To get results on all the queries use "qrel_task2_2020_visual_id.tsv".

*** Evaluation:
To evaluate results for task 2, run the following script:
python3 task2_get_results.py -eva path/to/trec_eval   -qre path/to/qrel_file   -de path/to/deduplicate_directory   -res result_file
-eva: Path to trec_eval tool
-qre: Path to qrel file, which is "qrel_task2_official_2020_visual_id.tsv"
-de: Path to deduplicated directory, where all the results are located in
-res: File path to save the results