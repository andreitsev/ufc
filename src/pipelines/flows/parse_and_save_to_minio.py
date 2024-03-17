import os
import sys
import logging
import json
from dotenv import load_dotenv
from tqdm import tqdm
import time
from datetime import datetime
import argparse
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

from minio import Minio
from minio.api import Minio as MinioClient

from prefect import task, flow
from prefect.task_runners import SequentialTaskRunner


from src.processing import eventslist2df
from src.pipelines.parse_all_fights import parse_all_fights
from src.parse_utils import get_events_list, get_one_fight_stats
from src.minio_utils import (
    initialize_minio_client, 
    load_json_from_minio, 
    minio_container_ipaddr,
    save_json_to_minio
)

load_dotenv()
MINIO_ACCESS_KEY = os.environ['MINIO_ACCESS_KEY']
MINIO_SECRET_KEY = os.environ['MINIO_SECRET_KEY']


def parse_cli():

	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--save_path",
		help='Where to save parsed fights',
		type=str,
		default=None
	)
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
	parser.add_argument('--verbose', dest='verbose', default=False, action='store_true')
	args = parser.parse_args()
	return args

def get_initialized_minio_client(verbose: bool=False) -> MinioClient:
	if verbose:
		print("initialize_minio_client...")
	minio_client = initialize_minio_client(
        ipaddr=minio_container_ipaddr(),
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        port_number=9000
    )
	return minio_client

@task(
	name='load_parsed_fights_from_minio',
	retries=3,
	retry_delay_seconds=10,
	log_prints=True,
)
def load_parsed_fights_from_minio(
    bucket_name: str, 
    object_name: str,
    minio_client: Optional[MinioClient]=None,
	verbose: bool=False
) -> List[Dict[Any, Any]]:
	all_fights_list = None
	if minio_client is None:
		minio_client = get_initialized_minio_client(verbose=verbose)
	
	if verbose: 
		print("load_json_from_minio...")
	all_fights_list = load_json_from_minio(
        minio_client=minio_client,
        bucket_name=bucket_name,
        object_name=object_name,
    )
	return all_fights_list


@task(
	name='parsing_fights_not_in_events',
	retries=3,
	retry_delay_seconds=10,
	log_prints=True
)
def parsing_fights_not_in_events(
	save_path: Optional[str]=None,
    events_set: Optional[set]=None,
    all_fights_list: Optional[List[Dict[Any, Any]]]=None,
	verbose: bool=False,
) -> List[Dict[Any, Any]]:
	if verbose:
		print('parse_all_fights...')
	all_fights_list_added = parse_all_fights(
        save_path=save_path,
        parsed_events_set=events_set,
		# parse_only_n_fights=4,
    )
	if all_fights_list is None:
		all_fights_list = all_fights_list_added
	else:
		all_fights_list.extend(all_fights_list_added)
	return all_fights_list

@task(
	name='saving_fights_to_minio',
	retries=3,
	retry_delay_seconds=10,
	log_prints=True
)
def saving_fights_to_minio(
    all_fights_list: List[Dict[Any, Any]],
    bucket_name: str,
    object_name: str,
    minio_client: Optional[MinioClient]=None,
	verbose: bool=False,
) -> None:
	
	if minio_client is None:
		minio_client = get_initialized_minio_client(verbose=verbose)

	if verbose:
		print("save_json_to_minio...")
	save_json_to_minio(
        obj=all_fights_list,
        minio_client=minio_client,
        bucket_name=bucket_name,
        object_name=object_name,
    )
	return

@flow(
	name='main_flow',
	retries=3,
	retry_delay_seconds=10,
	log_prints=True,
	task_runner=SequentialTaskRunner()
)
def main_flow(
	save_path: str,
	minio_bucket_name: str,
	minio_object_name: str,
	verbose: bool=False,
) -> None:
	if verbose:
		print("get_initialized_minio_client...")
	minio_client = get_initialized_minio_client(verbose=verbose)
	if verbose:
		print("load_parsed_fights_from_minio...")
	parsed_events_from_minio = load_parsed_fights_from_minio(
		bucket_name=minio_bucket_name, 
		object_name=minio_object_name,
		minio_client=minio_client,
		verbose=verbose
	)
	events_set = set([fight_info['event_uri'] for fight_info in parsed_events_from_minio])
	if verbose:
		print("parsing_fights_not_in_events...")
	all_fights_list = parsing_fights_not_in_events(
		save_path=save_path,
		events_set=events_set,
    	all_fights_list=parsed_events_from_minio,
		verbose=verbose
	)
	if verbose:
		print("saving_fights_to_minio...")
	saving_fights_to_minio(
		all_fights_list=all_fights_list,
		bucket_name=minio_bucket_name,
    	object_name=minio_object_name,
		minio_client=minio_client,
		verbose=verbose
	)
	if verbose:
		print("OK!")
	return


if __name__ == '__main__':

	today = str(datetime.now().date())
	print(f'today: {today}')

	logging.basicConfig(
		filename=f'/home/aiandrejcev/ufc/logs/parse_all_fights/{str(today)}.log',
		format='%(asctime)s %(levelname)s %(message)s',
		datefmt="%Y-%m-%d %H:%M:%S",
		level=logging.INFO,
	)

	logging.info('Parsing arguments...')
	try:
		args = parse_cli()
		save_path = args.save_path
		if str(save_path).lower() == 'none':
			save_path = None
		logging.info('done')
	except Exception as e:
		save_path = None
		color_print("can't parse cli!", color='red')
		print(e, end='\n\n')


	logging.info('Parsing all fights...')
	st = time.perf_counter()
	main_flow(
		save_path=args.save_path,
		minio_bucket_name=args.minio_bucket_name,
		minio_object_name=args.minio_object_name,
		verbose=args.verbose,
	)
	end = time.perf_counter()
	logging.info(f'all fights parsed for {(end - st) // 60} minutes {round((end - st) % 60)} seconds')