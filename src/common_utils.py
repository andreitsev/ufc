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
    