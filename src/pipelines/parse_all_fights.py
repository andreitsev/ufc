import os
import sys
import json
from tqdm import tqdm
import time
from datetime import datetime
from argparse import ArgumentParser
from typing import List, Tuple, Dict, Set, Any, Optional, Callable, Union
if 'PYTHONPATH' in os.environ:
	PROJECT_PATH = os.environ["PYTHONPATH"]
	#os.chdir(PROJECT_PATH)
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

from src.processing import eventslist2df
from src.parse_utils import get_events_list, get_one_fight_stats


def parse_cli():

	parser = ArgumentParser()
	parser.add_argument(
		"--save_path",
		help='Where to save parsed fights',
		type=str,
		default=None
	)

	args = parser.parse_args()
	return args

def parse_all_fights(save_path: str=None) -> List[Dict[str], Any]:

	"""
	Parses all fights and returns list of dicts with fights statistics
	:param save_path: Path where to save resulting list as a .json file
	:return: list of dicts with fights statistics
	"""

	fights_list, status_ok = get_events_list()
	print("status_ok:", status_ok)
	fights_df = eventslist2df(fights_list)

	all_fights_list = []
	for event_uri, event_date, event_location, event_name in tqdm(
			fights_df[['event_url', 'date', 'location', 'event_name']].itertuples(index=False),
			total=len(fights_df)
	):
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
		json.dump(all_fights_list, open(save_path, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)

	return all_fights_list


if __name__ == '__main__':

	today = str(datetime.now().date())
	print(f'today: {today}')

	args = parse_cli()
	save_path = args.save_path
	if str(save_path).lower() == 'none':
		save_path = None

	print('\nParsing all fights...')
	st = time.perf_counter()
	save_path = args
	_ = parse_all_fights(save_path=save_path)
	end = time.perf_counter()
	color_print(f'all fights parsed for {(end - st) // 60} minutes {round((end - st) % 60)} seconds', color='green')