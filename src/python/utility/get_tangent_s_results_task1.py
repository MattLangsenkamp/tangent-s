import pandas as pd
import numpy as np
import argparse
import os


def load_and_clean_results_df(file_name: str, run_name: str, latex: pd.DataFrame, task: str) -> pd.DataFrame:
    """
    returns a df with a schema matching arqmath evaluation specification for Task 1
    :param task: task 1 or 2
    :param latex: Dataframe containing latex representation along with post metadata
    :param run_name: string to be used as Run_Number identifier
    :param file_name: path to tsv file to load
    :return: populated dataframe with columns [topic
    """
    df = pd.read_csv(file_name, sep='\t', names=["Query_Id", "Post_Id", "Score", "Rank", "Run_Number"])
    # setting run number passed on command line input
    df.Run_Number = run_name
    # convert Post_Id to int as expected
    # df.loc[:, ['Post_Id']] = df['Post_Id'].apply(lambda x: int(x.strip('.mml')))
    ''' 
    Before indexing, the latex from original posts 
    are extracted to TSVs containing the latex, opts and slt formats
    https://drive.google.com/drive/folders/18bHlAWkhIJkLeS9CHvBQQ-BLSn4rrlvE
    each line in these files are then turned into individual files, 
    named based on the position in tsv corpus. The post ids generated by
    tangent-s only correspond to a line in the tsv representation corpus,
    which has the actual post id info
    '''
    representation_ids = df['Post_Id']-1
    df.loc[:, ['Post_Id']] = latex.loc[representation_ids, :]['post_id'].values
    # reorder columns
    if task == '1':
        df = df[["Query_Id", "Post_Id", "Rank", "Score", "Run_Number"]]
    elif task == '2':
        df['Formula_Id'] = latex.loc[representation_ids, :]['visual_id'].values
        df = df[["Query_Id", "Formula_Id", "Post_Id", "Rank", "Score", "Run_Number"]]
    return df


def load_latex_df(latex_dir: str) -> pd.DataFrame:
    dfs = []
    for filename in sorted(os.listdir(latex_dir), key=lambda x: float(x.strip('.tsv'))):
        filename_with_dir = os.path.join(latex_dir, filename)
        df = pd.read_csv(filename_with_dir, sep='\t')
        dfs.append(df)
    cumulative_df = pd.concat(dfs, ignore_index=True)
    return cumulative_df


def generate_rankings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Populates the rank column and returns a new DF
    :param df: DataFrame with Columns ["Query_Id", "Post_Id", "Rank", "Score", "Run_Number"]]
    :return: DataFrame with Columns ["Query_Id", "Post_Id", "Rank", "Score", "Run_Number"]] and Rank populated
    """
    df_with_ranks = pd.DataFrame()
    # iterate over 'A.1', 'A.2', 'A.3'... in that order
    topics = df["Query_Id"].unique()  # np.sort()
    for topic in topics:
        print("Generating ranks for query: ", topic)
        # sort based on score break ties with post_id
        certain_query = df[df["Query_Id"] == topic].sort_values(["Score", "Post_Id"], ascending=False).reset_index()
        # get top 1000 unique posts:
        '''post_ids = []
        rows_to_remove = []
        ind = 0
        while (len(post_ids) < 1000) and (len(post_ids) < len(certain_query)):
            row = certain_query.ix[ind]
            ind += 1
            if row['Post_Id'] in post_ids:
                rows_to_remove.append(row.name)
            else:
                post_ids.append(row['Post_Id'])

        certain_query = certain_query.drop(rows_to_remove)'''
        # get only the top 1000
        certain_query = certain_query[:1000]
        certain_query["Rank"] = np.arange(1, len(certain_query)+1)
        df_with_ranks = pd.concat([df_with_ranks, certain_query])
    return df_with_ranks


def export_to_tsv(df: pd.DataFrame, output_file: str) -> None:
    df.to_csv(output_file, sep="\t", header=False, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--results-file', help='path to the combined results')
    parser.add_argument('-n', '--run-name', help='name of the current run')
    parser.add_argument('-l', '--latex-representation', help='path to latex representation')
    parser.add_argument('-o', '--output-file', help='name of the file with newly added ranked column')
    parser.add_argument('-t', '--task', help='task 1 or 2 are the only acceptable values')
    args = parser.parse_args()

    latex_df = load_latex_df(args.latex_representation)
    results_df = load_and_clean_results_df(args.results_file, args.run_name, latex_df, args.task)

    ranked_df = generate_rankings(results_df)
    export_to_tsv(ranked_df, args.output_file)
