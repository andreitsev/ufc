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


if __name__ == '__main__':

    today = str(datetime.now().date())
    logging.info(f'today: {today}\n')

    logging.basicConfig(
		filename=f'/home/aiandrejcev/ufc/logs/save_to_minio/{str(today)}.log',
		format='%(asctime)s %(levelname)s %(message)s',
		datefmt="%Y-%m-%d %H:%M:%S",
		level=logging.INFO,
	)


    args = parse_cli()

    ############################### Loading all fights info from minio ####################################
    logging.info('\n'+ '='*60 + 'Loading all fights info from minio' + '='*60 + '\n')
    all_fights_list = None
    tmp_data_local_path = str(today) + str(int(random.random()*1e6))
    minio_client = initialize_minio_client(
        ipaddr=minio_container_ipaddr(),
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        port_number=9000
    )

    logging.info('load_json_from_minio')
    all_fights_list = load_json_from_minio(
        minio_client=minio_client,
        bucket_name=args.minio_bucket_name,
        object_name=args.minio_object_name,
    )
    print(f"len(all_fights_list): {len(all_fights_list):,}")
    logging.info(f"len(all_fights_list): {len(all_fights_list):,}")

    ############################### Getting parsed events set ####################################
    logging.info('\n'+ '='*60 + 'Getting parsed events set' + '='*60 + '\n')
    events_set = set([fight_info['event_uri'] for fight_info in all_fights_list])
    
    ############################### Parsing fights not in events_set ####################################
    logging.info('\n'+ '='*60 + "Parsing fights that aren't parsed yet" + '='*60 + '\n')
    all_fights_list_added = parse_all_fights(
        save_path=None,
        parsed_events_set=events_set,
    )
    if all_fights_list is None:
        all_fights_list = all_fights_list_added
    else:
        all_fights_list.extend(all_fights_list_added)
    print(f"len(all_fights_list): {len(all_fights_list):,}")
    logging.info(f"len(all_fights_list): {len(all_fights_list):,}")

    ############################### Saving to minio ####################################
    logging.info("Saving all_fights_list to minio...")
    save_json_to_minio(
        obj=all_fights_list,
        minio_client=minio_client,
        bucket_name=args.minio_bucket_name,
        object_name=args.minio_object_name,
    )
    logging.info("Done!")

