import itertools

import numpy as np
import pandas as pd

def make_features(
    df: pd.DataFrame,
    name_col: str='names',
    date_col: str='date_processed',
) -> pd.DataFrame:
    
    for col in [name_col, date_col]:
        assert col in df.columns, f'{col} should be in df! But {df.columns} are the only columns in df!' 

    for col in ['winloose', 'method']:
        assert col in df.columns, f'{col} should be in df!'

    tmp = df.copy(deep=True)
    tmp = (
        df
        .sort_values(by=[name_col, date_col], ascending=False)
        .reset_index(drop=True)
    )
    tmp['n_fights_so_far'] = (
        tmp
        .assign(winloose_int = lambda x: x['winloose'].map({'W': 1}).fillna(0))
        .groupby([name_col])
        ['winloose_int']
        .transform(lambda x: x.sort_index(ascending=False).expanding().count().shift(1))
    )
    for winloose_status in ['W', 'L']:
        win_or_lose = 'wins' if winloose_status == 'W' else 'lost' if winloose_status == 'L' else ''
        tmp[f'n_{win_or_lose}_so_far'] = (
            tmp
            .assign(winloose_int = lambda x: x['winloose'].map({winloose_status: 1}).fillna(0))
            .groupby([name_col])
            ['winloose_int']
            .transform(lambda x: x.sort_index(ascending=False).expanding().sum().shift(1))
        )
        if 'n_fights_so_far' in tmp.columns:
            tmp[f'pers_{win_or_lose}_so_far'] = tmp[f'n_{win_or_lose}_so_far'] / tmp['n_fights_so_far']

    for winloose_status, method in itertools.product(['W', 'L'], tmp['method'].unique()):
        win_or_lose = 'wins' if winloose_status == 'W' else 'lost' if winloose_status == 'L' else ''
        method_ = (
            method
            .lower()
            .replace('-', '_')
            .replace(' ', '_')
            .replace('/', '_')
            .replace('__', '_')
            .replace("'s", "")
        )
        feature_name = f'n_{method_}_{win_or_lose}_so_far'.replace('__', '_')
        tmp[feature_name] = (
            tmp
            .assign(
                winloose_and_method = lambda x: 
                x['winloose'].map({winloose_status: 1}).fillna(0)
                * x['method'].map({method: 1}).fillna(0)
            )
            .groupby([name_col])
            ['winloose_and_method']
            .transform(
                lambda x: x.sort_index(ascending=False).expanding().sum().shift(1)
            )
        )
        if 'n_fights_so_far' in tmp.columns:
            tmp[feature_name.replace('n_', 'pers_')] = tmp[feature_name] / tmp['n_fights_so_far']
    
    for winloose_status in ['W', "L"]:
        win_or_lose = 'wins' if winloose_status == 'W' else 'lost' if winloose_status == 'L' else ''
        tmp[f'n_any_type_decision_{win_or_lose}_so_far'] = (
            tmp
            .assign(
                winloose_and_method = lambda x: 
                x['winloose'].map({winloose_status: 1}).fillna(0)
                * x['method'].apply(lambda x: 'decision' in str(x).lower()).fillna(0)
            )
            .groupby([name_col])
            ['winloose_and_method']
            .transform(
                lambda x: x.sort_index(ascending=False).expanding().sum().shift(1)
            )
        )
        if 'n_fights_so_far' in tmp.columns:
            tmp[f'pers_any_type_decision_{win_or_lose}_so_far'] = tmp[f'n_any_type_decision_{win_or_lose}_so_far'] / tmp['n_fights_so_far']

    tmp['winloose_last_fight'] = (
        tmp
        .groupby([name_col])
        ['winloose']
        .transform(
            lambda x: x.sort_index(ascending=False).shift(1)
        )
    )
    tmp['days_since_last_fight'] = (
        tmp
        .groupby([name_col])
        [date_col]
        .transform(
            lambda x:
            (x.sort_index(ascending=False) - x.sort_index(ascending=False).shift(1)).dt.days
        )
    )
    if 'days_since_last_fight' in tmp.columns:
        for stat, stat_func in [
                ('min', np.min),
                ('avg', np.mean),
                ('std', np.std),
                ('max', np.max)
            ]:
            tmp[f'{stat}_days_between_fights'] = (
                tmp
                .groupby([name_col])
                ['days_since_last_fight']
                .transform(
                    lambda x: stat_func(x)
                )
            )
    return tmp
