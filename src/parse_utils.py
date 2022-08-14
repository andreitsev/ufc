import os
import sys
from tqdm import tqdm
from typing import List, Tuple, Dict, Set, Any, Optional, Callable
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


def get_events_list(
		main_page_url: str="http://www.ufcstats.com/statistics/events/completed?page=all",
		verbose: bool=False,
) -> (List[Dict[str, str]], bool):

	"""
	Parses main ufs stats page "http://www.ufcstats.com/statistics/events/completed?page=all" and returns
	fights as list
	:param main_page_url: "http://www.ufcstats.com/statistics/events/completed?page=all"
	:param verbose: whether to print error logs, during parsing
	:return: List of fights and status_ok - bool variable, which is True, when all the dictionaries have
		the same amount of keys
	"""

	page = requests.get(main_page_url)
	soup = BeautifulSoup(page.content, 'lxml')
	table_rows = soup.find_all("tr", {"class": "b-statistics__table-row"})
	resulting_list = []
	status_ok = True
	n_prev_dict_keys = None
	for i, elem in enumerate(table_rows):
		if i < 2:
			continue

		curr_dict = {}

		try:
			event_href = str(
				[val.split("href=")[1] for val in str(elem).split("\n") if 'href' in val.lower()][0]
				.replace('>', "").replace('"', "")
			)
			curr_dict['event_url'] = event_href
		except Exception as e:
			if verbose:
				color_print(f"Не удалось достать ссылку на бой! (i={i})", color='red')
				print(e, end='\n\n')
		try:
			even_name = elem.findAll("a", {"class": "b-link b-link_style_black"})[0].text.strip()
			curr_dict['event_name'] = even_name
		except Exception as e:
			if verbose:
				color_print(f"Не удалось достать название мероприятия! (i={i})", color='red')
				print(e, end='\n\n')
		try:
			even_date = elem.findAll("span", {"class": "b-statistics__date"})[0].text.strip()
			curr_dict['date'] = even_date
		except Exception as e:
			if verbose:
				color_print(f"Не удалось достать дату мероприятия! (i={i})", color='red')
				print(e, end='\n\n')
		try:
			even_location = (
				elem
				.findAll(
					"td", {"class": "b-statistics__table-col b-statistics__table-col_style_big-top-padding"}
				)[0]
				.text.strip()
			)
			curr_dict['location'] = even_location
		except Exception as e:
			if verbose:
				color_print(f"Не удалось достать место проведения мероприятия! (i={i})", color='red')
				print(e, end='\n\n')

		if n_prev_dict_keys is None:
			n_prev_dict_keys = len(curr_dict.keys())
		if n_prev_dict_keys != len(curr_dict.keys()):
			status_ok = False
			if verbose:
				color_print(f"Some dicts have different number of keys! (i={i})", color='yellow')

		resulting_list.append(curr_dict)
	return resulting_list, status_ok


def get_fights_info(fights_urls: List[str]) -> Dict[str, List[Dict[Any, Any]]]:

	"""
	Parses detailed info about events

	Args:
		:param fights_urls: List of fights urls
			example:
				[
					"http://www.ufcstats.com/event-details/319c15b8aac5bfde",
					"http://www.ufcstats.com/event-details/31da66df48c0c1a0",
					...
				]
	:return:
		events_stats_dict: Dict with keys - fights_urls, values - dict with fight info
	"""

	events_stats_dict = {}
	for event_url in tqdm(fights_urls):
		one_event = requests.get(event_url)
		one_event = BeautifulSoup(one_event.content, 'lxml')

		fights_in_1_event = (
			one_event
			.find_all(
				"tr", {
					"class": "b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click"
				}
			)
		)

		stat_cols_names = (
			one_event.find_all('thead', {'class': "b-fight-details__table-head"})[0]
			.find_all('th', {'class': "b-fight-details__table-col"})
		)
		item_number2stat_mapping = {
			i: stat.text.strip().lower().replace('/', '_').replace(' ', '_') for i, stat in enumerate(stat_cols_names)
		}

		one_event_stats_list = []
		for i, one_fight in enumerate(fights_in_1_event):
			one_fights_stats = one_fight.find_all('td', {"class": "b-fight-details__table-col"})

			curr_fight_stats_dict = {}
			for j, stat in enumerate(one_fights_stats):
				stat = stat.find_all('p', {'class': 'b-fight-details__table-text'})
				if len(stat) == 1:
					curr_fight_stats_dict[item_number2stat_mapping[j]] = stat[0].text.strip()
				elif len(stat) == 2:
					curr_fight_stats_dict[item_number2stat_mapping[j]] = []
					for val in stat:
						curr_fight_stats_dict[item_number2stat_mapping[j]].append(val.text.strip())
				else:
					raise ValueError("it's not expected to be more than 2 values!")

			one_event_stats_list.append(curr_fight_stats_dict)
		events_stats_dict[event_url] = one_event_stats_list
	return events_stats_dict


def get_fighters_info(fighters_stats_url: str=None) -> (List[Dict[str, Any]], bool):

	"""
	Parses fighters stats page

	Args:
		:param fighters_stats_url: 'http://www.ufcstats.com/statistics/fighters?char=a&page=all'
	Returns:
		overall_fighters_list: List of dicts with fighters info (weight, height, etc.)
		status_ok: whether columns_names are the same across different fighters stats pages (
			'http://www.ufcstats.com/statistics/fighters?char=a&page=all',
			'http://www.ufcstats.com/statistics/fighters?char=b&page=all', etc.
		)
	"""

	alphabet = 'abcdefghijklmnopqrstuvwxyz'
	prev_columns_names_set = None
	status_ok = True
	overall_fighters_list = []
	objects_set = set()
	for letter in tqdm(alphabet):
		if fighters_stats_url is None:
			fighters_stats_url = f'http://www.ufcstats.com/statistics/fighters?char={letter}&page=all'
		else:
			fighters_stats_url = fighters_stats_url.replace("char=a", f"char={letter}")

		fighters_page_for_one_letter = requests.get(fighters_stats_url)
		fighters_page_for_one_letter = BeautifulSoup(fighters_page_for_one_letter.content, 'lxml')

		columns_names = (
			fighters_page_for_one_letter
			.find_all('thead', {'class': "b-statistics__table-caption"})[0]
			.find_all('th', {'class': "b-statistics__table-col"})
		)
		columns_names_dict = {i: col.text.strip() for i, col in enumerate(columns_names)}
		if prev_columns_names_set is None:
			prev_columns_names_set = set(columns_names_dict.keys())
		if len(prev_columns_names_set.symmetric_difference(set(columns_names_dict.keys()))) > 0:
			status_ok = False
			warning_message = f"Set of columns is not the same! prev columns: {prev_columns_names_set}"
			warning_message += f', current: {set(columns_names_dict.keys())}'
			color_print(warning_message, color='red')

		fighters_rows = (
			fighters_page_for_one_letter
			.find_all('tbody')[0]
			.find_all('tr', {'class': "b-statistics__table-row"})
		)

		fighters_info_list = []
		for row in fighters_rows:
			row_statistics = row.find_all('td', {'class': "b-statistics__table-col"})
			curr_fighter_stats_dict = {}
			for i, statistic in enumerate(row_statistics):
				curr_fighter_stats_dict[columns_names_dict[i]] = statistic.text.strip()

			if len(curr_fighter_stats_dict) > 0:
				# this plug is needed, because for some reason there are dubplicates of
				# fighters during parsing
				object_str = ''.join([f"{k}~~{v}" for k, v in curr_fighter_stats_dict.items()])
				if object_str not in objects_set:
					objects_set.add(object_str)
					fighters_info_list.append(curr_fighter_stats_dict)

		overall_fighters_list.extend(fighters_info_list)
	return overall_fighters_list, status_ok



