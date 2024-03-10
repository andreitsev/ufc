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

import requests
from bs4 import BeautifulSoup
from minio import Minio
from minio.api import Minio as MinioClient

from prefect import task, flow

from src.processing import eventslist2df
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

	args = parser.parse_args()
	return args

@flow(
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

@flow(
	name='parse_all_fights',
	retries=3,
	retry_delay_seconds=10,
	log_prints=True
)
def parse_all_fights(
		save_path: str=None,
		parsed_events_set: Optional[Set[str]]=None,
	) -> List[Dict[str, Any]]:

	"""
	Parses all fights and returns list of dicts with fights statistics
	:param save_path: Path where to save resulting list as a .json file
	:param parsed_events_set: If current parsed event is already in events_set - don't process it
	:return: list of dicts with fights statistics
	"""

	fights_list, status_ok = get_events_list()
	print("status_ok:", status_ok)
	fights_df = eventslist2df(fights_list)

	all_fights_list = []
	for i, (event_uri, event_date, event_location, event_name) in tqdm(
			enumerate(fights_df[['event_url', 'date', 'location', 'event_name']].itertuples(index=False)),
			total=len(fights_df)
	):
		if i == 3:
			break
		
		if parsed_events_set is not None and event_uri in parsed_events_set:
			continue

		one_event = requests.get(event_uri)
		one_event = BeautifulSoup(one_event.content, 'lxml')
		one_event = (
			one_event
			.find_all(
				"tr", {"class": "b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click"}
			)
		)
		for one_fight in one_event:
			fight_uri = [
				row.replace('data-link', '').replace('=', '').replace('"', '')
				for row in str(one_fight).split() if 'data-link' in row
			][0]

			fight_stats_dict = get_one_fight_stats(fight_uri=fight_uri)
			fight_stats_dict['date'] = event_date
			fight_stats_dict['location'] = event_location
			fight_stats_dict['event_name'] = event_name
			fight_stats_dict['event_uri'] = event_uri
			fight_stats_dict['fight_uri'] = fight_uri
			all_fights_list.append(fight_stats_dict)

	if save_path is not None and len(all_fights_list) > 0:
		json.dump(
			all_fights_list, 
			open(save_path, mode='w', encoding='utf-8'), 
			ensure_ascii=False, 
			indent=2
		)

	return all_fights_list

@flow(
	name='main_flow',
	retries=3,
	retry_delay_seconds=10,
	log_prints=True
)
def main_flow(save_path: str) -> None:
	all_fights_list = parse_all_fights(save_path)
	saving_fights_to_minio(
		all_fights_list=all_fights_list,
		bucket_name='ufc-raw-data',
    	object_name='ufc_stats.json',
		minio_client=None,
	)
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
	# _ = parse_all_fights(save_path=save_path)
	main_flow(save_path=args.save_path)
	end = time.perf_counter()
	logging.info(f'all fights parsed for {(end - st) // 60} minutes {round((end - st) % 60)} seconds')