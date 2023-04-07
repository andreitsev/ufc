import os
from os.path import join as p_join
from dotenv import load_dotenv
load_dotenv()
import logging
from typing import List, Dict, Any, Optional
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
from minio.api import Minio as MinioClient

if 'PYTHONPATH' in os.environ:
    PROJECT_PATH = os.environ["PYTHONPATH"]
    sys.path.insert(0, PROJECT_PATH)
else:
    PROJECT_PATH = '..'

from src.pipelines.parse_all_fights import parse_all_fights
from src.minio_utils import (
    initialize_minio_client, 
    load_json_from_minio, 
    minio_container_ipaddr,
    save_json_to_minio
)

from prefect import task, flow
from prefect.task_runners import SequentialTaskRunner


MINIO_ACCESS_KEY = os.environ['MINIO_ACCESS_KEY']
MINIO_SECRET_KEY = os.environ['MINIO_SECRET_KEY']


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

# @task(retries=3)
# def get_initialized_minio_client() -> MinioClient:
#     minio_client = initialize_minio_client(
#         ipaddr=minio_container_ipaddr(),
#         access_key=MINIO_ACCESS_KEY,
#         secret_key=MINIO_SECRET_KEY,
#         port_number=9000
#     )
#     return minio_client

@task(retries=3)
def load_parsed_fights_from_minio(
    bucket_name: str, 
    object_name: str,
    minio_client: Optional[MinioClient]=None,
) -> List[Dict[Any, Any]]:
    all_fights_list = None
    if minio_client is None:
        minio_client = initialize_minio_client(
            ipaddr=minio_container_ipaddr(),
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            port_number=9000
        )

    all_fights_list = load_json_from_minio(
        minio_client=minio_client,
        bucket_name=bucket_name,
        object_name=object_name,
    )
    return all_fights_list

@task(retries=3)
def parsing_fights_not_in_events(
    events_set: Optional[set]=None,
    all_fights_list: Optional[List[Dict[Any, Any]]]=None,
) -> List[Dict[Any, Any]]:
    all_fights_list_added = parse_all_fights(
        save_path=None,
        parsed_events_set=events_set,
    )
    if all_fights_list is None:
        all_fights_list = all_fights_list_added
    else:
        all_fights_list.extend(all_fights_list_added)
    return all_fights_list

@task(retries=3)
def saving_fights_to_minio(
    all_fights_list: List[Dict[Any, Any]],
    bucket_name: str,
    object_name: str,
    minio_client: Optional[MinioClient]=None,
) -> None:
    
    if minio_client is None:
        minio_client = initialize_minio_client(
            ipaddr=minio_container_ipaddr(),
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            port_number=9000
        )

    save_json_to_minio(
        obj=all_fights_list,
        minio_client=minio_client,
        bucket_name=bucket_name,
        object_name=object_name,
    )
    return

@flow(retries=3, 
      retry_delay_seconds=600, 
      timeout_seconds=7200,
      log_prints=True,
      task_runner=SequentialTaskRunner())
def load_data_to_minio(
    bucket_name: str,
    object_name: str,
    minio_client: Optional[object]=None,
):
    # minio_client = get_initialized_minio_client()
    all_fights_list = load_parsed_fights_from_minio(
                            bucket_name=bucket_name, 
                            object_name=object_name,
                            minio_client=minio_client
                        )
    events_set = set([fight_info['event_uri'] for fight_info in all_fights_list])
    all_fights_list_added = parsing_fights_not_in_events(
                                events_set=events_set,
                                all_fights_list=all_fights_list
                            )
    saving_fights_to_minio(
        all_fights_list=all_fights_list_added,
        bucket_name=bucket_name,
        object_name=object_name,
        minio_client=minio_client
    )
    

if __name__ == '__main__':

    today = str(datetime.now().date())
    args = parse_cli()

    minio_client = initialize_minio_client(
            ipaddr=minio_container_ipaddr(),
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            port_number=9000
        )

    load_data_to_minio(
        bucket_name=args.minio_bucket_name,
        object_name=args.minio_object_name,
        minio_client=minio_client
    )

