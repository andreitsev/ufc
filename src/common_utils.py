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