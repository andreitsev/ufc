from tqdm import tqdm
from collections import deque
from typing import List, Tuple, Dict, Set, Any, Optional, Callable, Union
import pandas as pd

from sqlalchemy.engine.base import Engine

from src.db_utils import get_pg_engine


def eventslist2df(events_list: List[Dict[str, str]]) -> pd.DataFrame:

    """
    Processes result of get_events_list() function from parse_utils and returns a pandas DataFrame

    :param events_list: output of get_events_list() function
    :return:
        list of dicts transformed to pandas dataframe
    """

    transformed_dict = {}
    for subdict in events_list:
        for k, v in subdict.items():
            if k not in transformed_dict:
                transformed_dict[k] = []
            transformed_dict[k].append(v)
    return pd.DataFrame(transformed_dict)


def bfs_dict(
    one_fight_dict: Dict[Any, Any],
    union_filed_identifier: str='__',
) -> Dict[str, Union[str, int, float]]:
    """In a nutshell, turns embedded dict into 1 level dict which then turns into pandas Dataframe as follows:
            {                                                           
                key1_lvl1: {                                               
                    key1_lvl2: [val1, val2, ...],                         
                    key2_lvl2: 'plain_value',     
                    key3_lvl2: {
                        key1_lvl3: 'val'
                    }                                   
                }
            }

            into

            {
                key1_lvl1__key1_lvl2_1: val1,
                key1_lvl1__key1_lvl2_2: val2,
                key1_lvl1__key1_lvl2_3: ...,
                key1_lvl1__key2_lvl2: 'plain_value',
                key1_lvl1__key3_lvl2__key1_lvl3: 'val',
            }

    Args:
        all_fights_list

    Returns:
        pd.DataFrame: _description_
    """
    
    def process_key(stat: str) -> str:
        """Prettifies key"""
        stat = (
            stat
            .lower()
            .strip()
            .replace(":", "")
            .replace(' ', '')
            .replace('%', '_perc')
            .replace('sig.str.', 'sig_str')
            .replace('sig.str', 'sig_str')
            .replace('totalstr.', 'totalstr')
            .replace('sub.att', 'sub_att')
            .replace('rev.', 'rev')
        )
        return stat

    resulting_dict = {}
    queue = deque([(k, v) for (k, v) in one_fight_dict.items()])
    processed_first_winloose_fighter = False
    while queue:
        k, v = queue.popleft()
        k = process_key(stat=k)
        
        # if key starts with 'winloose' then next comes the fighter name
        # which we want to change into 'fighter<1/2>'
        if k.startswith('winloose_'):
            if not processed_first_winloose_fighter:
                k = 'winloose_fighter1'
                processed_first_winloose_fighter = True
            else:
                k = 'winloose_fighter2'

        if isinstance(v, list):
            for i, elem in enumerate(v, start=1):
                resulting_dict[f"{k}{union_filed_identifier}{i}"] = elem
        elif isinstance(v, dict):
            for sub_k, sub_v in v.items():
                queue.append((f"{k}{union_filed_identifier}{sub_k}", sub_v))
        else:
            resulting_dict[k] = v
    return resulting_dict
            
def minio_data_to_pandas(
    all_fights_list: List[Dict[Any, Any]],
    union_filed_identifier: str='__',
    verbose: bool=True
) -> pd.DataFrame:
    """Applies bfs_dict to all fights dicts in all_fights_list list

    Args:
        all_fights_list: list of all fights' info
        union_filed_identifier: which separator to use to unite field in dict
        verbose: whether to show a progress with tqdm
    Returns:
        pd.DataFrame: 
    """
    
    res_list = []
    for i, one_fight in tqdm(enumerate(all_fights_list)) if verbose else all_fights_list:
        try:
            curr_dict = bfs_dict(one_fight_dict=one_fight, union_filed_identifier=union_filed_identifier)
            res_list.append(curr_dict)
        except Exception as e:
            if verbose:
                print('Problem with transforming {i}`th fight')
                print(e, end='\n')
    return pd.DataFrame(res_list)


def minio_data_to_postgres(
        all_fights_list: List[Any],
        schema: str='raw_data',
        table_name: str='all_fights_info',
        engine: Optional[Engine]=None,
    ) -> None:

    from sqlalchemy.schema import CreateSchema

    if engine is None:
        engine = get_pg_engine()

    if not engine.dialect.has_schema(engine, schema):
        engine.execute(CreateSchema(schema))

    res_df = minio_data_to_pandas(all_fights_list=all_fights_list)
    res_df.to_sql(
        name=table_name,
        con=engine,
        schema=schema,
        if_exists='replace',
        index=False
    )
    return 
