import os
import sys
from tqdm import tqdm
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


def get_events_info(event_urls: List[str]) -> Dict[str, List[Dict[Any, Any]]]:

	"""
	Parses detailed info about events

	Args:
		:param event_urls: List of fights urls
			example:
				[
					"http://www.ufcstats.com/event-details/319c15b8aac5bfde",
					"http://www.ufcstats.com/event-details/31da66df48c0c1a0",
					...
				]
	:return:
		events_stats_dict: Dict with keys - fights_urls, values - dict with fight info

	Example:

		events = [
			'http://www.ufcstats.com/event-details/4f853e98886283cf',
			'http://www.ufcstats.com/event-details/a23e63184c65f5b8'
		]
		fights_info_dict = get_fights_info(events)
		print(fights_info_dict)

	>>> {'http://www.ufcstats.com/event-details/4f853e98886283cf': [{'fighter': ['Leon '
                                                                         'Edwards',
                                                                         'Kamaru '
                                                                         'Usman'],
																	 'kd': ['1', '0'],
																	 'method': ['KO/TKO',
																				'Kick'],
																	 'round': '5',
																	 'str': ['55',
																			 '83'],
																	 'sub': ['1', '0'],
																	 'td': ['1', '5'],
																	 'time': '4:04',
																	 'w_l': 'win',
																	 'weight_class': 'Welterweight'},
																	{'fighter': ['Paulo '
																				 'Costa',
																				 'Luke '
																				 'Rockhold'],
																	 'kd': ['0', '0'],
																	 'method': ['U-DEC',
																				''],
																	 'round': '3',
																	 'str': ['73',
																			 '51'],
																	 'sub': ['0', '0'],
																	 'td': ['2', '1'],
																	 'time': '5:00',
																	 'w_l': 'win',
																	 'weight_class': 'Middleweight'},
																	{'fighter': ['Merab '
																				 'Dvalishvili',
																				 'Jose '
																				 'Aldo'],
																	 'kd': ['0', '0'],
																	 'method': ['U-DEC',
																				''],
																	 'round': '3',
																	 'str': ['57',
																			 '38'],
																	 'sub': ['0', '0'],
																	 'td': ['0', '0'],
																	 'time': '5:00',
																	 'w_l': 'win',
																	 'weight_class': 'Bantamweight'},
																	{'fighter': ['Lucie '
																				 'Pudilova',
																				 'Wu '
																				 'Yanan'],
																	 'kd': ['0', '0'],
																	 'method': ['KO/TKO',
																				'Elbows'],
																	 'round': '2',
																	 'str': ['39',
																			 '26'],
																	 'sub': ['1', '0'],
																	 'td': ['2', '0'],
																	 'time': '4:04',
																	 'w_l': 'win',
																	 'weight_class': "Women's "
																					 'Bantamweight'},
																	{'fighter': ['Tyson '
																				 'Pedro',
																				 'Harry '
																				 'Hunsucker'],
																	 'kd': ['1', '0'],
																	 'method': ['KO/TKO',
																				'Kick'],
																	 'round': '1',
																	 'str': ['6', '2'],
																	 'sub': ['0', '0'],
																	 'td': ['0', '0'],
																	 'time': '1:05',
																	 'w_l': 'win',
																	 'weight_class': 'Light '
																					 'Heavyweight'},
																	{'fighter': ['Marcin '
																				 'Tybura',
																				 'Alexandr '
																				 'Romanov'],
																	 'kd': ['0', '0'],
																	 'method': ['M-DEC',
																				''],
																	 'round': '3',
																	 'str': ['47',
																			 '40'],
																	 'sub': ['0', '0'],
																	 'td': ['0', '2'],
																	 'time': '5:00',
																	 'w_l': 'win',
																	 'weight_class': 'Heavyweight'},
																	{'fighter': ['Jared '
																				 'Gordon',
																				 'Leonardo '
																				 'Santos'],
																	 'kd': ['0', '0'],
																	 'method': ['U-DEC',
																				''],
																	 'round': '3',
																	 'str': ['116',
																			 '36'],
																	 'sub': ['0', '0'],
																	 'td': ['0', '0'],
																	 'time': '5:00',
																	 'w_l': 'win',
																	 'weight_class': 'Lightweight'},
																	{'fighter': ['Sean '
																				 'Woodson',
																				 'Luis '
																				 'Saldana'],
																	 'kd': ['0', '2'],
																	 'method': ['S-DEC',
																				''],
																	 'round': '3',
																	 'str': ['73',
																			 '91'],
																	 'sub': ['1', '0'],
																	 'td': ['0', '1'],
																	 'time': '5:00',
																	 'w_l': ['draw',
																			 'draw'],
																	 'weight_class': 'Featherweight'},
																	{'fighter': ['Ange '
																				 'Loosa',
																				 'AJ '
																				 'Fletcher'],
																	 'kd': ['0', '0'],
																	 'method': ['U-DEC',
																				''],
																	 'round': '3',
																	 'str': ['129',
																			 '87'],
																	 'sub': ['0', '0'],
																	 'td': ['2', '0'],
																	 'time': '5:00',
																	 'w_l': 'win',
																	 'weight_class': 'Welterweight'},
																	{'fighter': ['Amir '
																				 'Albazi',
																				 'Francisco '
																				 'Figueiredo'],
																	 'kd': ['0', '0'],
																	 'method': ['SUB',
																				'Rear '
																				'Naked '
																				'Choke'],
																	 'round': '1',
																	 'str': ['12',
																			 '11'],
																	 'sub': ['1', '0'],
																	 'td': ['2', '0'],
																	 'time': '4:34',
																	 'w_l': 'win',
																	 'weight_class': 'Flyweight'},
																	{'fighter': ['Aoriqileng',
																				 'Jay '
																				 'Perrin'],
																	 'kd': ['0', '0'],
																	 'method': ['U-DEC',
																				''],
																	 'round': '3',
																	 'str': ['72',
																			 '88'],
																	 'sub': ['0', '0'],
																	 'td': ['0', '3'],
																	 'time': '5:00',
																	 'w_l': 'win',
																	 'weight_class': 'Bantamweight'},
																	{'fighter': ['Victor '
																				 'Altamirano',
																				 'Daniel '
																				 'Da '
																				 'Silva'],
																	 'kd': ['1', '1'],
																	 'method': ['KO/TKO',
																				'Punches'],
																	 'round': '1',
																	 'str': ['58',
																			 '22'],
																	 'sub': ['0', '0'],
																	 'td': ['0', '0'],
																	 'time': '3:39',
																	 'w_l': 'win',
																	 'weight_class': 'Flyweight'}],
		 'http://www.ufcstats.com/event-details/a23e63184c65f5b8': [{'fighter': ['Marlon '
																				 'Vera',
																				 'Dominick '
																				 'Cruz'],
																	 'kd': ['3', '0'],
																	 'method': ['KO/TKO',
																				'Kick'],
																	 'round': '4',
																	 'str': ['61',
																			 '92'],
																	 'sub': ['0', '0'],
																	 'td': ['0', '2'],
																	 'time': '2:17',
																	 'w_l': 'win',
																	 'weight_class': 'Bantamweight'},
																	{'fighter': ['Nate '
																				 'Landwehr',
																				 'David '
																				 'Onama'],
																	 'kd': ['0', '1'],
																	 'method': ['M-DEC',
																				''],
																	 'round': '3',
																	 'str': ['91',
																			 '71'],
																	 'sub': ['2', '0'],
																	 'td': ['3', '1'],
																	 'time': '5:00',
																	 'w_l': 'win',
																	 'weight_class': 'Featherweight'},
																	{'fighter': ['Yazmin '
																				 'Jauregui',
																				 'Iasmin '
																				 'Lucindo'],
																	 'kd': ['0', '0'],
																	 'method': ['U-DEC',
																				''],
																	 'round': '3',
																	 'str': ['86',
																			 '66'],
																	 'sub': ['0', '0'],
																	 'td': ['0', '0'],
																	 'time': '5:00',
																	 'w_l': 'win',
																	 'weight_class': "Women's "
																					 'Strawweight'},
																	{'fighter': ['Azamat '
																				 'Murzakanov',
																				 'Devin '
																				 'Clark'],
																	 'kd': ['1', '0'],
																	 'method': ['KO/TKO',
																				'Punch'],
																	 'round': '3',
																	 'str': ['79',
																			 '14'],
																	 'sub': ['0', '0'],
																	 'td': ['0', '0'],
																	 'time': '1:18',
																	 'w_l': 'win',
																	 'weight_class': 'Light '
																					 'Heavyweight'},
																	{'fighter': ['Priscila '
																				 'Cachoeira',
																				 'Ariane '
																				 'Lipski'],
																	 'kd': ['1', '0'],
																	 'method': ['KO/TKO',
																				'Punches'],
																	 'round': '1',
																	 'str': ['20', '4'],
																	 'sub': ['0', '0'],
																	 'td': ['0', '0'],
																	 'time': '1:05',
																	 'w_l': 'win',
																	 'weight_class': "Women's "
																					 'Bantamweight'},
																	{'fighter': ['Gerald '
																				 'Meerschaert',
																				 'Bruno '
																				 'Silva'],
																	 'kd': ['1', '0'],
																	 'method': ['SUB',
																				'Guillotine '
																				'Choke'],
																	 'round': '3',
																	 'str': ['46',
																			 '29'],
																	 'sub': ['1', '0'],
																	 'td': ['1', '0'],
																	 'time': '1:39',
																	 'w_l': 'win',
																	 'weight_class': 'Middleweight'},
																	{'fighter': ['Angela '
																				 'Hill',
																				 'Loopy '
																				 'Godinez'],
																	 'kd': ['0', '0'],
																	 'method': ['U-DEC',
																				''],
																	 'round': '3',
																	 'str': ['85',
																			 '92'],
																	 'sub': ['0', '0'],
																	 'td': ['1', '1'],
																	 'time': '5:00',
																	 'w_l': 'win',
																	 'weight_class': 'Catch '
																					 'Weight'},
																	{'fighter': ['Martin '
																				 'Buday',
																				 'Lukasz '
																				 'Brzeski'],
																	 'kd': ['0', '0'],
																	 'method': ['S-DEC',
																				''],
																	 'round': '3',
																	 'str': ['66',
																			 '118'],
																	 'sub': ['0', '0'],
																	 'td': ['0', '0'],
																	 'time': '5:00',
																	 'w_l': 'win',
																	 'weight_class': 'Heavyweight'},
																	{'fighter': ['Nina '
																				 'Nunes',
																				 'Cynthia '
																				 'Calvillo'],
																	 'kd': ['0', '0'],
																	 'method': ['S-DEC',
																				''],
																	 'round': '3',
																	 'str': ['39',
																			 '48'],
																	 'sub': ['0', '0'],
																	 'td': ['0', '3'],
																	 'time': '5:00',
																	 'w_l': 'win',
																	 'weight_class': "Women's "
																					 'Flyweight'},
																	{'fighter': ['Gabriel '
																				 'Benitez',
																				 'Charlie '
																				 'Ontiveros'],
																	 'kd': ['0', '0'],
																	 'method': ['KO/TKO',
																				'Punches'],
																	 'round': '1',
																	 'str': ['37',
																			 '22'],
																	 'sub': ['0', '0'],
																	 'td': ['1', '0'],
																	 'time': '3:33',
																	 'w_l': 'win',
																	 'weight_class': 'Lightweight'},
																	{'fighter': ['Tyson '
																				 'Nam',
																				 'Ode '
																				 'Osbourne'],
																	 'kd': ['1', '0'],
																	 'method': ['KO/TKO',
																				'Punch'],
																	 'round': '1',
																	 'str': ['13',
																			 '15'],
																	 'sub': ['0', '0'],
																	 'td': ['0', '0'],
																	 'time': '2:59',
																	 'w_l': 'win',
																	 'weight_class': 'Flyweight'},
																	{'fighter': ['Josh '
																				 'Quinlan',
																				 'Jason '
																				 'Witt'],
																	 'kd': ['1', '0'],
																	 'method': ['KO/TKO',
																				'Punch'],
																	 'round': '1',
																	 'str': ['3', '1'],
																	 'sub': ['0', '0'],
																	 'td': ['0', '1'],
																	 'time': '2:09',
																	 'w_l': 'win',
																	 'weight_class': 'Catch '
																					 'Weight'},
																	{'fighter': ['Youssef '
																				 'Zalal',
																				 "Da'Mon "
																				 'Blackshear'],
																	 'kd': ['0', '0'],
																	 'method': ['M-DEC',
																				''],
																	 'round': '3',
																	 'str': ['63',
																			 '27'],
																	 'sub': ['1', '1'],
																	 'td': ['1', '1'],
																	 'time': '5:00',
																	 'w_l': ['draw',
																			 'draw'],
																	 'weight_class': 'Bantamweight'}]}

	"""

	events_stats_dict = {}
	for event_url in tqdm(event_urls):
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


def get_winloose_status(one_fight_page: Union[BeautifulSoup, str]) -> Dict[str, str]:
	"""
    Returns who of fighters won the fight in form of mapping: {fighter1: status1, fighter2: status2}

    Args:
        one_fight_page: fight uri (ex: 'http://www.ufcstats.com/fight-details/72c3e5eacde4f0e5') or Beautiful soup
    Returns:
        resulting_dict: {fighter1: status1, fighter2: status2}

    Example:
        for fight_uri in [
            'http://www.ufcstats.com/fight-details/72c3e5eacde4f0e5',
            'http://www.ufcstats.com/fight-details/96b62bd56b252bab',
            'http://www.ufcstats.com/fight-details/5a2b86570110191b',
            'http://www.ufcstats.com/fight-details/3aa49ed298e4c34f',
            'http://www.ufcstats.com/fight-details/b810951e39a0af1b',
            'http://www.ufcstats.com/fight-details/cb640b7dcc9db7e8',
            'http://www.ufcstats.com/fight-details/1c0bf66167c91e01',
            'http://www.ufcstats.com/fight-details/2de50e21c8f32761',
            'http://www.ufcstats.com/fight-details/53d0df57a917c6a0',
        ]:
        print(get_winloose_status(one_fight_page=BeautifulSoup(requests.get(fight_uri).content, 'lxml')))

        >>> {'Julianna Pena': 'L', 'Amanda Nunes': 'W'}
        >>> {'Alexandre Pantoja': 'W', 'Alex Perez': 'L'}
        >>> {"Don'Tale Mayes": 'L', 'Hamdy Abdelwahab': 'W'}
        >>> {'Karine Silva': 'W', 'Poliana Botelho': 'L'}
        >>> {'Olivier Aubin-Mercier': 'L', 'Diego Ferreira': 'W'}
        >>> {'Mike Aina': 'NC', 'Billy Evangelista': 'NC'}
        >>> {'Felipe Arantes': 'D', 'Milton Vieira': 'D'}
        >>> {'Hiroyuki Abe': 'D', 'Naoki Matsushita': 'D'}
        >>> {'Jack Shore': 'W', 'Timur Valiev': 'L'}
    """

	if isinstance(one_fight_page, str):
		one_fight = requests.get(one_fight_page)
		one_fight = BeautifulSoup(one_fight.content, 'lxml')
	else:
		one_fight = one_fight_page

	res = (
		one_fight
		.find_all('div', {'class': 'b-fight-details__persons clearfix'})[0]
		.find_all('div', {'class': 'b-fight-details__person'})
	)
	assert len(res) == 2, f'expected to see only 2 person, but got {len(res)}!'

	name1 = (
		res[0]
		.find_all('div', {'class': 'b-fight-details__person-text'})[0]
		.find_all('h3', {'class': 'b-fight-details__person-name'})[0]
		.contents[1]
		.contents[0].strip()
	)
	winloose_status1 = res[0].find_all('i', {'class': "b-fight-details__person-status"})[0].contents[0].strip()

	name2 = (
		res[1]
		.find_all('div', {'class': 'b-fight-details__person-text'})[0]
		.find_all('h3', {'class': 'b-fight-details__person-name'})[0]
		.contents[1]
		.contents[0].strip()
	)
	winloose_status2 = res[1].find_all('i', {'class': "b-fight-details__person-status"})[0].contents[0].strip()

	resulting_dict = {
		name1: winloose_status1,
		name2: winloose_status2
	}
	return resulting_dict


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

def get_one_fight_name(one_fight_page: BeautifulSoup, verbose: bool = False) -> str:
	"""
    Returns fight category/name (ex. UFC Women's Bantamweight Title Bout, BANTAMWEIGHT BOUT, LIGHTWEIGHT BOUT, etc.)

    Example:
        for fight_uri in [
            'http://www.ufcstats.com/fight-details/72c3e5eacde4f0e5',
            'http://www.ufcstats.com/fight-details/96b62bd56b252bab',
            'http://www.ufcstats.com/fight-details/5a2b86570110191b',
            'http://www.ufcstats.com/fight-details/3aa49ed298e4c34f',
            'http://www.ufcstats.com/fight-details/b810951e39a0af1b',
            'http://www.ufcstats.com/fight-details/cb640b7dcc9db7e8',
            'http://www.ufcstats.com/fight-details/1c0bf66167c91e01',
            'http://www.ufcstats.com/fight-details/2de50e21c8f32761',
            'http://www.ufcstats.com/fight-details/53d0df57a917c6a0',
        ]:
            print(get_one_fight_name(one_fight_page=BeautifulSoup(requests.get(fight_uri).content, 'lxml')))

        >>> ufc women's bantamweight title bout
        >>> flyweight bout
        >>> heavyweight bout
        >>> women's flyweight bout
        >>> lightweight bout
        >>> lightweight bout
        >>> featherweight bout
        >>> lightweight bout
        >>> bantamweight bout
    """

	res = (
		one_fight_page
		.find_all('div', {'class': 'b-fight-details__fight'})[0]
		.find_all('i', {'class': 'b-fight-details__fight-title'})[0]
		.contents[-1]
		.strip()
		.lower()
	)
	return res

def get_fighters_names(one_fight_page: BeautifulSoup, verbose: bool = False) -> (str, str):
	"""
    Returns fighters names

    Example:
        for fight_uri in [
            'http://www.ufcstats.com/fight-details/72c3e5eacde4f0e5',
            'http://www.ufcstats.com/fight-details/96b62bd56b252bab',
            'http://www.ufcstats.com/fight-details/5a2b86570110191b',
            'http://www.ufcstats.com/fight-details/3aa49ed298e4c34f',
            'http://www.ufcstats.com/fight-details/b810951e39a0af1b',
            'http://www.ufcstats.com/fight-details/cb640b7dcc9db7e8',
            'http://www.ufcstats.com/fight-details/1c0bf66167c91e01',
            'http://www.ufcstats.com/fight-details/2de50e21c8f32761',
            'http://www.ufcstats.com/fight-details/53d0df57a917c6a0',
        ]:
            print(get_fighters_names(one_fight_page=BeautifulSoup(requests.get(fight_uri).content, 'lxml')))

        >>> ['Julianna Pena', 'Amanda Nunes']
        >>> ['Alexandre Pantoja', 'Alex Perez']
        >>> ["Don'Tale Mayes", 'Hamdy Abdelwahab']
        >>> ['Karine Silva', 'Poliana Botelho']
        >>> ['Olivier Aubin-Mercier', 'Diego Ferreira']
        >>> ['Mike Aina', 'Billy Evangelista']
        >>> ['Felipe Arantes', 'Milton Vieira']
        >>> ['Hiroyuki Abe', 'Naoki Matsushita']
        >>> ['Jack Shore', 'Timur Valiev']

    """
	fighter_names = (
		one_fight_page
		.find_all('h3', {'class': 'b-fight-details__person-name'})
	)
	if len(fighter_names) > 2 and verbose:
		print("There seem to be more than two fighters in this fight!")

	names_list = []
	for fighter in fighter_names:
		name = fighter.find_all('a', {'class': 'b-link b-fight-details__person-link'})
		names_list.append(name[0].contents[0].strip())
	return names_list

def get_one_fight_details(one_fight_page: BeautifulSoup, verbose: bool = False) -> Dict[str, Any]:
	"""
    Returns fight details (number of rounds, referee, method, etc.)

    Example:
        for fight_uri in [
            'http://www.ufcstats.com/fight-details/72c3e5eacde4f0e5',
            'http://www.ufcstats.com/fight-details/96b62bd56b252bab',
            'http://www.ufcstats.com/fight-details/5a2b86570110191b',
            'http://www.ufcstats.com/fight-details/3aa49ed298e4c34f',
            'http://www.ufcstats.com/fight-details/b810951e39a0af1b',
            'http://www.ufcstats.com/fight-details/cb640b7dcc9db7e8',
            'http://www.ufcstats.com/fight-details/1c0bf66167c91e01',
            'http://www.ufcstats.com/fight-details/2de50e21c8f32761',
            'http://www.ufcstats.com/fight-details/53d0df57a917c6a0',
        ]:
            res = get_overall_fight_details(one_fight_page=BeautifulSoup(requests.get(fight_uri).content, 'lxml'))
            print(res)

        >>> {'Method:': 'Decision - Unanimous', 'Round:': '5', 'Time:': '5:00', 'Time format:':
                '5 Rnd (5-5-5-5-5)', 'Referee:': 'Mike Beltran'}
        >>> {'Method:': 'Submission', 'Round:': '1', 'Time:': '1:31', 'Time format:': '3 Rnd (5-5-5)',
                'Referee:': 'Kerry Hatley'}
        >>> {'Method:': 'Decision - Split', 'Round:': '3', 'Time:': '5:00', 'Time format:': '3 Rnd (5-5-5)',
                'Referee:': 'Kerry Hatley'}
        >>> {'Method:': 'Submission', 'Round:': '1', 'Time:': '4:55', 'Time format:': '3 Rnd (5-5-5)',
                'Referee:': 'Chris Tognoni'}
        >>> {'Method:': 'Decision - Unanimous', 'Round:': '3', 'Time:': '5:00', 'Time format:':
                '3 Rnd (5-5-5)', 'Referee:': 'Vitor Ribeiro'}
        >>> {'Method:': 'Overturned', 'Round:': '2', 'Time:': '3:42', 'Time format:': '3 Rnd (5-5-5)',
                'Referee:': 'Herb Dean'}
        >>> {'Method:': 'Decision - Split', 'Round:': '3', 'Time:': '5:00', 'Time format:': '3 Rnd (5-5-5)',
                'Referee:': 'Marc Goddard'}
        >>> {'Method:': 'Other', 'Round:': '2', 'Time:': '5:00', 'Time format:': '2 Rnd (5-5)',
                'Referee:': 'Moritaka Oshiro'}
        >>> {'Method:': 'Decision - Unanimous', 'Round:': '3', 'Time:': '5:00', 'Time format:':
                '3 Rnd (5-5-5)', 'Referee:': 'Marc Goddard'}
    """

	res = (
		one_fight_page
		.find_all('div', {'class': 'b-fight-details__fight'})[0]
		.find_all('div', {'class': 'b-fight-details__content'})[0]
	)
	details_dict = {}
	for i in range(1, len(res.contents[1]), 2):
		needed_rows = [val for val in res.contents[1].contents[i].contents if str(val).strip() != '']
		if len(needed_rows) > 2:
			print(f'Expected to see 2 rows, but {len(needed_rows)} arge given!')
		if 'contents' in dir(needed_rows[0]):
			key = needed_rows[0].contents[0]
		else:
			key = needed_rows[0]
		key = str(key).strip()  # .lower()

		if 'contents' in dir(needed_rows[1]):
			value = needed_rows[1].contents[0]
		else:
			value = needed_rows[1]
		value = str(value).strip()  # .lower()

		details_dict[key] = value
	return details_dict


def get_total_or_significant_statistics(one_fight_page: BeautifulSoup, statstype: str = 'totals') -> Dict[str, Any]:
	"""
    Returns list of per round statistics

    Example 1:

        for fight_uri in [
            'http://www.ufcstats.com/fight-details/72c3e5eacde4f0e5',
            'http://www.ufcstats.com/fight-details/96b62bd56b252bab',
            'http://www.ufcstats.com/fight-details/5a2b86570110191b',
        ]:
            res = get_total_or_significant_statistics(one_fight_page=BeautifulSoup(requests.get(fight_uri).content, 'lxml'))
            print(res)

        >>> {'Round 1': {'Ctrl': ['0:00', '0:00'],
                         'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                         'KD': ['0', '0'],
                         'Rev.': ['0', '0'],
                         'Sig. str.': ['21 of 51', '25 of 47'],
                         'Sig. str. %': ['41%', '53%'],
                         'Sub. att': ['0', '0'],
                         'Td %': ['---', '0%'],
                         'Total str.': ['21 of 51', '25 of 47']},
             'Round 2': {'Ctrl': ['0:00', '0:32'],
                         'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                         'KD': ['0', '3'],
                         'Rev.': ['0', '0'],
                         'Sig. str.': ['25 of 66', '19 of 48'],
                         'Sig. str. %': ['37%', '39%'],
                         'Sub. att': ['0', '0'],
                         'Td %': ['---', '---'],
                         'Total str.': ['31 of 72', '24 of 53']},
             'Round 3': {'Ctrl': ['0:00', '3:02'],
                         'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                         'KD': ['0', '0'],
                         'Rev.': ['0', '0'],
                         'Sig. str.': ['6 of 21', '14 of 23'],
                         'Sig. str. %': ['28%', '60%'],
                         'Sub. att': ['0', '0'],
                         'Td %': ['---', '100%'],
                         'Total str.': ['31 of 55', '23 of 35']},
             'Round 4': {'Ctrl': ['0:00', '3:54'],
                         'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                         'KD': ['0', '0'],
                         'Rev.': ['0', '0'],
                         'Sig. str.': ['4 of 10', '16 of 20'],
                         'Sig. str. %': ['40%', '80%'],
                         'Sub. att': ['1', '0'],
                         'Td %': ['---', '100%'],
                         'Total str.': ['33 of 42', '34 of 40']},
             'Round 5': {'Ctrl': ['0:00', '4:21'],
                         'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                         'KD': ['0', '0'],
                         'Rev.': ['0', '0'],
                         'Sig. str.': ['4 of 6', '11 of 14'],
                         'Sig. str. %': ['66%', '78%'],
                         'Sub. att': ['0', '1'],
                         'Td %': ['---', '66%'],
                         'Total str.': ['14 of 19', '20 of 26']}}

        >>> {'Round 1': {'Ctrl': ['1:06', '0:00'],
                         'Fighter': ['Alexandre Pantoja', 'Alex Perez'],
                         'KD': ['0', '0'],
                         'Rev.': ['0', '0'],
                         'Sig. str.': ['8 of 12', '10 of 14'],
                         'Sig. str. %': ['66%', '71%'],
                         'Sub. att': ['1', '0'],
                         'Td %': ['100%', '0%'],
                         'Total str.': ['8 of 12', '10 of 14']}}

        >>> {'Round 1': {'Ctrl': ['0:00', '2:00'],
                         'Fighter': ["Don'Tale Mayes", 'Hamdy Abdelwahab'],
                         'KD': ['0', '1'],
                         'Rev.': ['0', '0'],
                         'Sig. str.': ['11 of 40', '21 of 40'],
                         'Sig. str. %': ['27%', '52%'],
                         'Sub. att': ['0', '0'],
                         'Td %': ['---', '50%'],
                         'Total str.': ['11 of 40', '44 of 67']},
             'Round 2': {'Ctrl': ['0:00', '0:45'],
                         'Fighter': ["Don'Tale Mayes", 'Hamdy Abdelwahab'],
                         'KD': ['0', '0'],
                         'Rev.': ['0', '0'],
                         'Sig. str.': ['24 of 56', '19 of 41'],
                         'Sig. str. %': ['42%', '46%'],
                         'Sub. att': ['0', '0'],
                         'Td %': ['---', '---'],
                         'Total str.': ['27 of 59', '20 of 42']},
             'Round 3': {'Ctrl': ['0:00', '3:51'],
                         'Fighter': ["Don'Tale Mayes", 'Hamdy Abdelwahab'],
                         'KD': ['0', '0'],
                         'Rev.': ['0', '0'],
                         'Sig. str.': ['12 of 20', '18 of 29'],
                         'Sig. str. %': ['60%', '62%'],
                         'Sub. att': ['0', '0'],
                         'Td %': ['---', '100%'],
                         'Total str.': ['16 of 24', '42 of 55']}}

    Example 2:
        for fight_uri in [
            'http://www.ufcstats.com/fight-details/72c3e5eacde4f0e5',
            'http://www.ufcstats.com/fight-details/96b62bd56b252bab',
            'http://www.ufcstats.com/fight-details/5a2b86570110191b',
        ]:
            res = get_total_or_significant_statistics(
                    one_fight_page=BeautifulSoup(requests.get(fight_uri).content, 'lxml'),
                    statstype='significant strikes'
                  )
            print(res)

        >>> {'Round 1': {'Body': ['1 of 2', '3 of 3'],
                         'Clinch': ['0 of 1', '0 of 0'],
                         'Distance': ['21 of 50', '25 of 47'],
                         'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                         'Ground': ['0 of 0', '0 of 0'],
                         'Head': ['20 of 49', '17 of 37'],
                         'Leg': ['0 of 0', '5 of 7'],
                         'Sig. str': ['21 of 51', '25 of 47'],
                         'Sig. str. %': ['41%', '53%']},
             'Round 2': {'Body': ['4 of 7', '4 of 6'],
                         'Clinch': ['1 of 1', '0 of 0'],
                         'Distance': ['24 of 65', '19 of 47'],
                         'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                         'Ground': ['0 of 0', '0 of 1'],
                         'Head': ['21 of 59', '13 of 40'],
                         'Leg': ['0 of 0', '2 of 2'],
                         'Sig. str': ['25 of 66', '19 of 48'],
                         'Sig. str. %': ['37%', '39%']},
             'Round 3': {'Body': ['1 of 1', '2 of 3'],
                         'Clinch': ['0 of 1', '0 of 1'],
                         'Distance': ['6 of 20', '7 of 13'],
                         'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                         'Ground': ['0 of 0', '7 of 9'],
                         'Head': ['5 of 20', '12 of 20'],
                         'Leg': ['0 of 0', '0 of 0'],
                         'Sig. str': ['6 of 21', '14 of 23'],
                         'Sig. str. %': ['28%', '60%']},
             'Round 4': {'Body': ['0 of 0', '1 of 1'],
                         'Clinch': ['0 of 0', '0 of 0'],
                         'Distance': ['4 of 10', '5 of 6'],
                         'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                         'Ground': ['0 of 0', '11 of 14'],
                         'Head': ['4 of 10', '15 of 19'],
                         'Leg': ['0 of 0', '0 of 0'],
                         'Sig. str': ['4 of 10', '16 of 20'],
                         'Sig. str. %': ['40%', '80%']},
             'Round 5': {'Body': ['0 of 0', '0 of 1'],
                         'Clinch': ['0 of 0', '0 of 0'],
                         'Distance': ['4 of 6', '1 of 4'],
                         'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                         'Ground': ['0 of 0', '10 of 10'],
                         'Head': ['4 of 6', '10 of 12'],
                         'Leg': ['0 of 0', '1 of 1'],
                         'Sig. str': ['4 of 6', '11 of 14'],
                         'Sig. str. %': ['66%', '78%']}}

        >>> {'Round 1': {'Body': ['1 of 1', '0 of 0'],
                         'Clinch': ['1 of 1', '0 of 1'],
                         'Distance': ['7 of 11', '10 of 13'],
                         'Fighter': ['Alexandre Pantoja', 'Alex Perez'],
                         'Ground': ['0 of 0', '0 of 0'],
                         'Head': ['7 of 11', '9 of 13'],
                         'Leg': ['0 of 0', '1 of 1'],
                         'Sig. str': ['8 of 12', '10 of 14'],
                         'Sig. str. %': ['66%', '71%']}}

        >>> {'Round 1': {'Body': ['2 of 4', '1 of 2'],
                         'Clinch': ['0 of 0', '2 of 2'],
                         'Distance': ['11 of 40', '13 of 30'],
                         'Fighter': ["Don'Tale Mayes", 'Hamdy Abdelwahab'],
                         'Ground': ['0 of 0', '6 of 8'],
                         'Head': ['6 of 31', '19 of 37'],
                         'Leg': ['3 of 5', '1 of 1'],
                         'Sig. str': ['11 of 40', '21 of 40'],
                         'Sig. str. %': ['27%', '52%']},
             'Round 2': {'Body': ['6 of 8', '4 of 4'],
                         'Clinch': ['2 of 5', '0 of 0'],
                         'Distance': ['22 of 51', '13 of 32'],
                         'Fighter': ["Don'Tale Mayes", 'Hamdy Abdelwahab'],
                         'Ground': ['0 of 0', '6 of 9'],
                         'Head': ['14 of 44', '14 of 36'],
                         'Leg': ['4 of 4', '1 of 1'],
                         'Sig. str': ['24 of 56', '19 of 41'],
                         'Sig. str. %': ['42%', '46%']},
             'Round 3': {'Body': ['4 of 5', '0 of 0'],
                         'Clinch': ['0 of 0', '0 of 1'],
                         'Distance': ['12 of 20', '4 of 12'],
                         'Fighter': ["Don'Tale Mayes", 'Hamdy Abdelwahab'],
                         'Ground': ['0 of 0', '14 of 16'],
                         'Head': ['8 of 15', '18 of 29'],
                         'Leg': ['0 of 0', '0 of 0'],
                         'Sig. str': ['12 of 20', '18 of 29'],
                         'Sig. str. %': ['60%', '62%']}}

    """

	assert statstype in ['totals', 'significant strikes'], \
		"statstype could be of type 'totals' or 'significant strikes' only!"

	# [2] - total strikes table or [4] - significant strikes
	take_section = 2 if statstype == 'totals' else 4

	# total stats by rounds
	stats_table = (
		one_fight_page
		.find_all('section', {'class': 'b-fight-details__section js-fight-section'})[take_section]
		.find_all('table', {'class': 'b-fight-details__table js-fight-table'})[0]
	)

	stats_table_columns = (
		stats_table
		.find_all('thead', {'class': 'b-fight-details__table-head_rnd'})[0]
		.find_all('tr', {'class': 'b-fight-details__table-row'})[0]
		.find_all('th', {'class': 'b-fight-details__table-col'})
	)
	stats_table_columns = [name.contents[0].strip() for name in stats_table_columns]

	rounds = (
		stats_table
		.find_all('tbody', {'class': 'b-fight-details__table-body'})[0]
		.find_all('thead', {'class': 'b-fight-details__table-row b-fight-details__table-row_type_head'})
	)
	rounds = [round_.find_all('th', {'class': 'b-fight-details__table-col'})[0].contents[0].strip() for round_ in
			  rounds]

	round_stats = (
		stats_table
		.find_all('tbody', {'class': 'b-fight-details__table-body'})[0]
		.find_all('tr', {'class': 'b-fight-details__table-row'})
	)
	stats_per_rounds_dict = {}
	for round_number, one_round in enumerate(round_stats):
		one_round = one_round.find_all('td', {'class': 'b-fight-details__table-col'})

		stats_per_rounds_dict[rounds[round_number]] = {}
		for i, elem in enumerate(one_round):
			elem_list = elem.find_all('p', {'class': 'b-fight-details__table-text'})
			if i == 0:
				elem_list = [
					[val.contents[0] for val in elem.contents if str(val).lower().strip() != ''][0].strip()
					for elem in elem_list
				]
			else:
				elem_list = [val.contents[0].strip() for val in elem_list]
			stats_per_rounds_dict[rounds[round_number]][stats_table_columns[i]] = elem_list
	return stats_per_rounds_dict


def get_per_round_stats(one_fight_page: BeautifulSoup) -> Dict[str, Any]:
	full_stats_dict = {}
	total_stats_dict = get_total_or_significant_statistics(
		one_fight_page=one_fight_page,
		statstype='totals'
	)
	signif_strikes_dict = get_total_or_significant_statistics(
		one_fight_page=one_fight_page, statstype='significant strikes'
	)
	for round_number in total_stats_dict:
		full_stats_dict[round_number] = {
			**total_stats_dict.get(round_number, {}),
			**signif_strikes_dict.get(round_number, {})
		}
	return full_stats_dict


def get_one_fight_stats(fight_uri: str) -> Dict[Any, Any]:
	"""
    Parses fight_uri page (ex. http://www.ufcstats.com/fight-details/72c3e5eacde4f0e5) and returns fight statistics

    Args:
        fight_uri: for example "http://www.ufcstats.com/fight-details/72c3e5eacde4f0e5"
    Returns:
        fight_stats_dict: see example below

    Example:

        fight_uris = [
            'http://www.ufcstats.com/fight-details/72c3e5eacde4f0e5',
            'http://www.ufcstats.com/fight-details/96b62bd56b252bab',
            'http://www.ufcstats.com/fight-details/5a2b86570110191b',
        ]
        for fight_uri in tqdm(fight_uris):
            fight_stats_dict = get_one_fight_stats(fight_uri=fight_uri)
            print(fight_stats_dict)

        >>> {'Method:': 'Decision - Unanimous',
             'Referee:': 'Mike Beltran',
             'Round:': '5',
             'Time format:': '5 Rnd (5-5-5-5-5)',
             'Time:': '5:00',
             'fight_name': "ufc women's bantamweight title bout",
             'names': ['Julianna Pena', 'Amanda Nunes'],
             'per_round_stats': {'Round 1': {'Body': ['1 of 2', '3 of 3'],
                                             'Clinch': ['0 of 1', '0 of 0'],
                                             'Ctrl': ['0:00', '0:00'],
                                             'Distance': ['21 of 50', '25 of 47'],
                                             'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                                             'Ground': ['0 of 0', '0 of 0'],
                                             'Head': ['20 of 49', '17 of 37'],
                                             'KD': ['0', '0'],
                                             'Leg': ['0 of 0', '5 of 7'],
                                             'Rev.': ['0', '0'],
                                             'Sig. str': ['21 of 51', '25 of 47'],
                                             'Sig. str.': ['21 of 51', '25 of 47'],
                                             'Sig. str. %': ['41%', '53%'],
                                             'Sub. att': ['0', '0'],
                                             'Td %': ['---', '0%'],
                                             'Total str.': ['21 of 51', '25 of 47']},
                                 'Round 2': {'Body': ['4 of 7', '4 of 6'],
                                             'Clinch': ['1 of 1', '0 of 0'],
                                             'Ctrl': ['0:00', '0:32'],
                                             'Distance': ['24 of 65', '19 of 47'],
                                             'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                                             'Ground': ['0 of 0', '0 of 1'],
                                             'Head': ['21 of 59', '13 of 40'],
                                             'KD': ['0', '3'],
                                             'Leg': ['0 of 0', '2 of 2'],
                                             'Rev.': ['0', '0'],
                                             'Sig. str': ['25 of 66', '19 of 48'],
                                             'Sig. str.': ['25 of 66', '19 of 48'],
                                             'Sig. str. %': ['37%', '39%'],
                                             'Sub. att': ['0', '0'],
                                             'Td %': ['---', '---'],
                                             'Total str.': ['31 of 72', '24 of 53']},
                                 'Round 3': {'Body': ['1 of 1', '2 of 3'],
                                             'Clinch': ['0 of 1', '0 of 1'],
                                             'Ctrl': ['0:00', '3:02'],
                                             'Distance': ['6 of 20', '7 of 13'],
                                             'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                                             'Ground': ['0 of 0', '7 of 9'],
                                             'Head': ['5 of 20', '12 of 20'],
                                             'KD': ['0', '0'],
                                             'Leg': ['0 of 0', '0 of 0'],
                                             'Rev.': ['0', '0'],
                                             'Sig. str': ['6 of 21', '14 of 23'],
                                             'Sig. str.': ['6 of 21', '14 of 23'],
                                             'Sig. str. %': ['28%', '60%'],
                                             'Sub. att': ['0', '0'],
                                             'Td %': ['---', '100%'],
                                             'Total str.': ['31 of 55', '23 of 35']},
                                 'Round 4': {'Body': ['0 of 0', '1 of 1'],
                                             'Clinch': ['0 of 0', '0 of 0'],
                                             'Ctrl': ['0:00', '3:54'],
                                             'Distance': ['4 of 10', '5 of 6'],
                                             'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                                             'Ground': ['0 of 0', '11 of 14'],
                                             'Head': ['4 of 10', '15 of 19'],
                                             'KD': ['0', '0'],
                                             'Leg': ['0 of 0', '0 of 0'],
                                             'Rev.': ['0', '0'],
                                             'Sig. str': ['4 of 10', '16 of 20'],
                                             'Sig. str.': ['4 of 10', '16 of 20'],
                                             'Sig. str. %': ['40%', '80%'],
                                             'Sub. att': ['1', '0'],
                                             'Td %': ['---', '100%'],
                                             'Total str.': ['33 of 42', '34 of 40']},
                                 'Round 5': {'Body': ['0 of 0', '0 of 1'],
                                 'Clinch': ['0 of 0', '0 of 0'],
                                 'Ctrl': ['0:00', '4:21'],
                                 'Distance': ['4 of 6', '1 of 4'],
                                 'Fighter': ['Julianna Pena', 'Amanda Nunes'],
                                 'Ground': ['0 of 0', '10 of 10'],
                                 'Head': ['4 of 6', '10 of 12'],
                                 'KD': ['0', '0'],
                                 'Leg': ['0 of 0', '1 of 1'],
                                 'Rev.': ['0', '0'],
                                 'Sig. str': ['4 of 6', '11 of 14'],
                                 'Sig. str.': ['4 of 6', '11 of 14'],
                                 'Sig. str. %': ['66%', '78%'],
                                 'Sub. att': ['0', '1'],
                                 'Td %': ['---', '66%'],
                                 'Total str.': ['14 of 19', '20 of 26']}}}

        >>> {'Method:': 'Submission',
             'Referee:': 'Kerry Hatley',
             'Round:': '1',
             'Time format:': '3 Rnd (5-5-5)',
             'Time:': '1:31',
             'fight_name': 'flyweight bout',
             'names': ['Alexandre Pantoja', 'Alex Perez'],
             'per_round_stats': {'Round 1': {'Body': ['1 of 1', '0 of 0'],
                                             'Clinch': ['1 of 1', '0 of 1'],
                                             'Ctrl': ['1:06', '0:00'],
                                             'Distance': ['7 of 11', '10 of 13'],
                                             'Fighter': ['Alexandre Pantoja', 'Alex Perez'],
                                             'Ground': ['0 of 0', '0 of 0'],
                                             'Head': ['7 of 11', '9 of 13'],
                                             'KD': ['0', '0'],
                                             'Leg': ['0 of 0', '1 of 1'],
                                             'Rev.': ['0', '0'],
                                             'Sig. str': ['8 of 12', '10 of 14'],
                                             'Sig. str.': ['8 of 12', '10 of 14'],
                                             'Sig. str. %': ['66%', '71%'],
                                             'Sub. att': ['1', '0'],
                                             'Td %': ['100%', '0%'],
                                             'Total str.': ['8 of 12', '10 of 14']}}}

        >>> {'Method:': 'Decision - Split',
             'Referee:': 'Kerry Hatley',
             'Round:': '3',
             'Time format:': '3 Rnd (5-5-5)',
             'Time:': '5:00',
             'fight_name': 'heavyweight bout',
             'names': ["Don'Tale Mayes", 'Hamdy Abdelwahab'],
             'per_round_stats': {'Round 1': {'Body': ['2 of 4', '1 of 2'],
                                 'Clinch': ['0 of 0', '2 of 2'],
                                 'Ctrl': ['0:00', '2:00'],
                                 'Distance': ['11 of 40', '13 of 30'],
                                 'Fighter': ["Don'Tale Mayes",
                                             'Hamdy Abdelwahab'],
                                 'Ground': ['0 of 0', '6 of 8'],
                                 'Head': ['6 of 31', '19 of 37'],
                                 'KD': ['0', '1'],
                                 'Leg': ['3 of 5', '1 of 1'],
                                 'Rev.': ['0', '0'],
                                 'Sig. str': ['11 of 40', '21 of 40'],
                                 'Sig. str.': ['11 of 40', '21 of 40'],
                                 'Sig. str. %': ['27%', '52%'],
                                 'Sub. att': ['0', '0'],
                                 'Td %': ['---', '50%'],
                                 'Total str.': ['11 of 40', '44 of 67']},
                     'Round 2': {'Body': ['6 of 8', '4 of 4'],
                                 'Clinch': ['2 of 5', '0 of 0'],
                                 'Ctrl': ['0:00', '0:45'],
                                 'Distance': ['22 of 51', '13 of 32'],
                                 'Fighter': ["Don'Tale Mayes",
                                             'Hamdy Abdelwahab'],
                                 'Ground': ['0 of 0', '6 of 9'],
                                 'Head': ['14 of 44', '14 of 36'],
                                 'KD': ['0', '0'],
                                 'Leg': ['4 of 4', '1 of 1'],
                                 'Rev.': ['0', '0'],
                                 'Sig. str': ['24 of 56', '19 of 41'],
                                 'Sig. str.': ['24 of 56', '19 of 41'],
                                 'Sig. str. %': ['42%', '46%'],
                                 'Sub. att': ['0', '0'],
                                 'Td %': ['---', '---'],
                                 'Total str.': ['27 of 59', '20 of 42']},
                     'Round 3': {'Body': ['4 of 5', '0 of 0'],
                                 'Clinch': ['0 of 0', '0 of 1'],
                                 'Ctrl': ['0:00', '3:51'],
                                 'Distance': ['12 of 20', '4 of 12'],
                                 'Fighter': ["Don'Tale Mayes",
                                             'Hamdy Abdelwahab'],
                                 'Ground': ['0 of 0', '14 of 16'],
                                 'Head': ['8 of 15', '18 of 29'],
                                 'KD': ['0', '0'],
                                 'Leg': ['0 of 0', '0 of 0'],
                                 'Rev.': ['0', '0'],
                                 'Sig. str': ['12 of 20', '18 of 29'],
                                 'Sig. str.': ['12 of 20', '18 of 29'],
                                 'Sig. str. %': ['60%', '62%'],
                                 'Sub. att': ['0', '0'],
                                 'Td %': ['---', '100%'],
                                 'Total str.': ['16 of 24', '42 of 55']}}}
    """

	fight_stats_dict = {}
	one_fight_stats_page = requests.get(fight_uri)
	one_fight_stats_page = BeautifulSoup(one_fight_stats_page.content, 'lxml')
	fight_stats_dict['names'] = get_fighters_names(one_fight_page=one_fight_stats_page)
	fight_stats_dict['fight_name'] = get_one_fight_name(one_fight_page=one_fight_stats_page)
	fight_stats_dict['winloose'] = get_winloose_status(one_fight_page=one_fight_stats_page)
	details_dict = get_one_fight_details(one_fight_page=one_fight_stats_page)
	fight_stats_dict.update(details_dict)
	try:
		fight_stats_dict['per_round_stats'] = get_per_round_stats(one_fight_page=one_fight_stats_page)
	except Exception as e:
		print("can't get per round statistics!")
		print(e, end='\n\n')
	return fight_stats_dict



