from typing import List, Tuple, Dict, Set, Any, Optional, Callable
import pandas as pd


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