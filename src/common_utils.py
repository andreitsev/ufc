import itertools
from datetime import datetime

import pandas as pd

import docker
from docker.models.containers import Container as DockerContainer



def get_container_ipaddr(container: DockerContainer) -> str:
    """Returns the ipaddr of docker container"""
    container_attrs = container.attrs['NetworkSettings']['Networks']
    random_container_key = list(container_attrs.keys())[0]
    ipaddr = container_attrs[random_container_key]['IPAddress']
    return str(ipaddr)


def prepare_date(date_col: pd.Series) -> pd.Series:
    """convert 'date' column of dataframe from raw_data.all_fights_info to datetime format"""

    month2digit_mapping = {
        'January': 1,
        'February': 2,
        'March': 3,
        'April': 4,
        'May': 5,
        'June': 6,
        'July': 7,
        'August': 8,
        'September': 9,
        'October': 10,
        'November': 11,
        'December': 12
    }

    assert date_col.loc[0].split(' ')[0] in month2digit_mapping, \
        "date_col elements should start from months' names!"

    res = (
        date_col
        .apply(lambda x: f"{month2digit_mapping[x.split(' ')[0]]}-{x.split(' ')[1].replace(',', '')}-{x.split(' ')[-1]}")
        .apply(lambda x: datetime.strptime(x, "%m-%d-%Y"))
    )
    return res



def clip_categories(
    series: pd.Series, 
    leave_top_n_categories: int=100, 
    other_category_name: str='other_category'
) -> pd.Series:
    """Clips pd.Series if it has more than leave_top_n_categories unique values with other_category_name 
        value to least common unique values

    Args:
        series (pd.Series): series that should be clipped
        leave_top_n_categories (int, optional): How many categories to leave
        other_category_name (str, optional): With what value to clip least common categories

    Returns:
        pd.Series: clipped series object
    """
    
    vals_dict = series.value_counts().to_dict()
    leave_these_values = sorted(vals_dict.items(), key=lambda x: x[1], reverse=True)[:leave_top_n_categories]
    leave_these_values = set([category_name for category_name, cnt in leave_these_values])
    mapping_dict = {**{k: other_category_name for k in vals_dict}, **{k: k for k in leave_these_values}}
    return  series.map(mapping_dict)
    
    
def choose_fighter_stats(raw_fights_df: pd.DataFrame, fighter_name: str) -> pd.DataFrame:
    """Returns dataframe with fights stats for <fighter_name> fighter. 
    This will be a subset of raw_fights_df dataframe (which necessary should have
    names__1 and names__2 columns!)

    Args:
        raw_fights_df (pd.DataFrame): dataframe from which to make slice to make output
        fighter_name (str): fighter name to make slice by

    Returns:
        one_fighter_stats_df: resulting dataframe with fights of a particular fighter
    """
    
    assert 'names__1' in raw_fights_df.columns, 'names__1 column should be in raw_fights_df!'
    assert 'names__2' in raw_fights_df.columns, 'names__2 column should be in raw_fights_df!'

    one_fighter_stats_df = (
        raw_fights_df.loc[
            (raw_fights_df['names__1'] == fighter_name) 
            | (raw_fights_df['names__2'] == fighter_name)
        ]
        .reset_index(drop=True)
    )

    # it's more convenient to always present chosen fighter in the first column
    # but it's not always the case for raw_fights_df dataset, so we need to swap stats cols
    
    # making sure, that we only have pairs of columns or single columns (like 
    # submission method, date, referee, etc.)
    cols_dict = {}
    for col in one_fighter_stats_df.columns:
        if col[-1].isdigit():
            col_name, fighter_1_or_2 = col[:-1], int(col[-1])
        else:
            col_name, fighter_1_or_2 = col, None
        if col_name not in cols_dict:
            cols_dict[col_name] = []
        cols_dict[col_name].append(fighter_1_or_2)

    columns_for_swapping = []
    for col, values in cols_dict.items():
        assert len(values) <= 2, f'len(values) should be <= 2, but got {len(values)} for {col}'
        if len(values) == 2:
            assert set(values) == set([1, 2]), \
                f'set(values) should be set([1, 2]), but got {set(values)} for {col}'
            columns_for_swapping.append(col)
        elif len(values) == 1:
             assert values[0] is None, \
                f'values[0] should be None, but got {values[0]} for {col}'

    # determining rows to swap columns
    # those rows, where <fighter_name> fighter is not in names__1 column:
    rows_to_swap = [
        row[0] for row in one_fighter_stats_df[['names__1']].itertuples(index=True) 
        if row[1] != fighter_name
    ]

    # here we're swapping columns:
    for col in columns_for_swapping:
        first = one_fighter_stats_df[f'{col}1'].tolist()
        second = one_fighter_stats_df[f'{col}2'].tolist()
        for idx in rows_to_swap:
            first[idx], second[idx] = second[idx], first[idx]
        one_fighter_stats_df[f'{col}1'] = first
        one_fighter_stats_df[f'{col}2'] = second

    return one_fighter_stats_df

def get_ego_graph(
    raw_fights_df: pd.DataFrame, 
    fighter_name: str
) -> pd.DataFrame:
    """Returns ego-subgraph of a given fighter

    Args:
        raw_fights_df (pd.DataFrame): dataframe from which to make slice to make output
        fighter_name (str): fighter name to make slice by
    Returns:
        pd.DataFrame: pd.DataFrame for ego subgraph
    """
    
    res_df = (
        raw_fights_df.loc[
            (raw_fights_df['names__1'] == fighter_name) |
            (raw_fights_df['names__2'] == fighter_name)
        ]
        .reset_index(drop=True)
    )
    hop1_fighters = set(
        res_df['names__1'].tolist()
        + res_df['names__2'].tolist()
    )
    for fighter in hop1_fighters:
        other_fighter_df = (
            raw_fights_df.loc[
                (raw_fights_df['names__1'] == fighter) |
                (raw_fights_df['names__2'] == fighter)
            ]
            .reset_index(drop=True)
        )
        res_df = pd.concat([
            res_df,
            other_fighter_df
        ], axis=0)
    res_df = res_df.drop_duplicates().reset_index(drop=True)
    return res_df