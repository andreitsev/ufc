import os
from os.path import join as p_join
from dotenv import load_dotenv
load_dotenv()
import logging
from datetime import datetime
from pathlib import Path
import sys
import json
import random
from tqdm import tqdm
import argparse

import numpy as np
import pandas as pd

from minio import Minio

from typing import List, Tuple, Dict, Set, Any, Optional, Callable, Union
if 'PYTHONPATH' in os.environ:
    PROJECT_PATH = os.environ["PYTHONPATH"]
    sys.path.insert(0, PROJECT_PATH)
else:
    PROJECT_PATH = '..'

try:
    from fabulous import color as fb_color
    color_print = lambda x, color='green': print(getattr(fb_color, color)(x)) if 'fb_color' in globals() else print(x)
except Exception as e:
    color_print = lambda x, color='green': print(x)


from src.processing import eventslist2df
from src.pipelines.parse_all_fights import parse_all_fights

def parse_cli():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--minio_bucket_name",
        help='Bucket name where to save parsed fights to minio',
        type=str,
        default='ufc-raw-data'
    )
    parser.add_argument(
        "--minio_object_name",
        help='Name of the object on Minio',
        type=str,
        default='ufc_stats.json'
    )

    args = parser.parse_args()
    return args


if __name__ == '__main__':

    today = str(datetime.now().date())
    print(f'today: {today}')

    MINIO_ACCESS_KEY = os.environ['MINIO_ACCESS_KEY']
    MINIO_SECRET_KEY = os.environ['MINIO_SECRET_KEY']

    args = parse_cli()

    ############################### Loading all fights info from minio ####################################
    all_fights_list = None
    tmp_data_local_path = str(today) + str(int(random.random()*1e6))
    try:
        minio_client = Minio(
            endpoint="172.17.0.2:9000",
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False,
        )

        minio_client.fget_object(
            bucket_name=args.minio_bucket_name,
            object_name=args.object_name,
            file_path=tmp_data_local_path,
        )

        all_fights_list = json.load(open(tmp_data_local_path, mode='r', encoding='utf-8'))
        os.remove(tmp_data_local_path)
    except Exception as e:
        color_print("Can't load all_fights_list!", color='red')
        print(e, end='\n'*2)

    ############################## get events, that are already parsed ##############################
    try:    
        events_set = set([fight_info['event_uri'] for fight_info in all_fights_list])
    except Exception as e:
        events_set = None
        print(e, end='\n'*2)


    ############################## parse rest events ##############################
    all_fights_list_added = parse_all_fights(
        save_path=None,
        parsed_events_set=events_set,
    )
    if all_fights_list is None:
        all_fights_list = all_fights_list_added
    else:
        all_fights_list.extend(all_fights_list_added)

    json.dump(
        all_fights_list, 
        open(tmp_data_local_path, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2
    )

    #################################### Putting data to minio ################################################
    all_fights_list = json.load(open(tmp_data_local_path, mode='r', encoding='utf-8'))

    # creating Minio client
    minio_client = Minio(
        endpoint="172.17.0.2:9000",
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )

    minio_client.fput_object(
        bucket_name=args.minio_bucket_name,
        object_name=args.object_name,
        file_path=tmp_data_local_path,
    )
    os.remove(tmp_data_local_path)
