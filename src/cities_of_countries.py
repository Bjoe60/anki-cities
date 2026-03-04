import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
from functools import cmp_to_key
import numpy as np
import os
import time
from urllib.parse import unquote
from math import sin, cos, tan, pi, atan, log
import pickle
from collections import Counter
from file_paths import INPUT_FILES, PROCESSED_FILES, OUTPUT_FILES
from urllib.parse import quote

TEST_ID = ""

user_agent = os.getenv('WIKIDATA_USER_AGENT', 'CitiesBot/1.0 (https://github.com/yourusername/anki-cities)')
headers = {'User-Agent': user_agent, 'Accept-Encoding': 'gzip'}
session = requests.Session()
session.headers.update(headers)
N_QUERY = 50
COORD_DIFF = 0.001 # Used to calculate if a map is bigger than another
DOWNLOAD_BATCH_SIZE = 50
DOWNLOAD_PAUSE_SECONDS = 2

file_target = '/home/bjoe/.local/share/Anki2/Shared decks/collection.media'

query_url = 'https://commons.wikimedia.org/w/api.php?action=query&format=json&maxlag=5&redirects&prop=redirects|imageinfo&iiprop=url|extmetadata&iiextmetadatafilter=Artist|LicenseUrl|AttributionRequired&iiurlwidth=1100&iiurlheight=680'
query_url_low_res = 'https://commons.wikimedia.org/w/api.php?action=query&format=json&maxlag=5&redirects&prop=redirects|imageinfo&iiprop=url|extmetadata&iiextmetadatafilter=Artist|LicenseUrl|AttributionRequired&iiurlwidth=800&iiurlheight=500'
query_url_wikipedia = 'https://en.wikipedia.org/w/api.php?action=query&format=json&maxlag=5&redirects&prop=redirects|imageinfo&iiprop=url|extmetadata&iiextmetadatafilter=Artist|LicenseUrl|AttributionRequired&iiurlwidth=1100&iiurlheight=680&titles='
revision_url = 'https://en.wikipedia.org/w/api.php?action=query&format=json&maxlag=5&redirects&prop=revisions&rvprop=content&rvslots=main&titles=' # If needed add 'rvsection=0'
country_img_base = 'Module:Location map/data/'
wikipedia_base_url = 'https://en.wikipedia.org/wiki/'
UNKNOWN_ENTITY = 'http://www.wikidata.org/entity/Q24238356'
UNWANTED_MAPS = {'Argentina_Greater_Buenos_Aires_location_map.svg', 'Artsakh_administrative_map_2021.svg', 'Bangladesh_Bhola_District_adm_location_map.svg', 'Mongar_Bhutan_location_map.png', 'Trongsa_Bhutan_location_map.png', 'Trashigang_Bhutan_location_map.png', 'Thimphu_Bhutan_location_map.png', 'Punakha_Bhutan_location_map.png', 'Wangdue_Phodrang_Bhutan_location_map.png', 'Sarpang_Bhutan_location_map.png', 'Bumthang_Bhutan_location_map.png', 'Lower_Egypt_ancient_nomes_position_map.jpg', 'Mediterranean_Sea_location_map.svg', 'Location_map_Jabodetabek.png', 'Kepulauan_Selayar.png', 'Japan_location_map_with_Tokyo_Greater_Area_Inset.svg', 'Greater_Mexico_City.JPG', 'Raionul_Cantemir_location_map.jpg', 'Pacific_Ocean_laea_location_map.svg', 'North_Sea_location_map.svg', 'Al_Khor_localities.png', 'Umm_Salal_localities.png', 'Location_map_Ireland_County_Cavan.png', 'Southeast_Asia_location_map.svg', 'Open_street_map_central_london.svg', 'Location_map_San_Francisco_County.png', 'Location_Map_San_Francisco_Bay_Area.png', 'Location_map_Barcelona.png', 'Location_map_Seville.png', 'Raionul_Leova_location_map.jpg', 'Raionul_Ungheni_location_map.jpg', 'Antofagasta_Region_Relief.jpg', 'Gagauzia_map.jpg', 'Map_Concarneau.jpg', "Sana'a_Governorate_Map.png", 'Location_map_of_Penang_2023.svg', 'Location_map_Ethiopia_Tigray.png', 'Bangladesh_Patuakhali_District_adm_location_map.svg', 'Mesopotamia_location_map2.svg', 'Agean_non_political.jpg', 'Turkije_satelliet.jpg', 'Map_of_the_Black_Sea_with_bathymetry_and_surrounding_relief.svg', 'Africa_location_map.svg', 'Napa_County_California_Location_Map.png', 'Sonoma_County_California_Location_Map.png', 'Atlantic_Ocean_laea_location_map.svg', 'Krk_location_map.png', 'Location_of_the_province_Daniel_Alcides_Carrión_in_Pasco.svg', 'Bangladesh_Barguna_District_adm_location_map.svg', 'Venetian_lagoon_locator_map.svg', 'Gabon_Wouleu-Ntem_location.svg', 'Krapina-Zagorje_County_OpenStreetMap.svg', 'Seenu_atoll.png', 'Alpes-de-Haute-Provence.jpg', 'Australia_South_Australia_City_of_Adelaide_location_map.svg', 'Dimos_Skydras.png', 'KG-Batken-Leilek.svg', 'KG-CHU-Kemin.svg', 'KG-CHU-Sokuluk_N.svg', 'KG-CHU-Ysyk-Ata.svg', 'KG-Osh-Kara-Suu.svg', 'KG-Osh-Aravan.svg', 'KG-Jalal-Abad-Toktogul.svg', 'KG-Jalal-Abad-Aksy.svg', 'KG-Jalal-Abad-Nooken.svg', 'Qikiqtaaluk_locator_map_2021.svg', 'Samtse_Bhutan_location_map.png', 'Pemagatshel_Bhutan_location_map.png', 'Chukha_Bhutan_location_map.png', 'Egypt_Nile_Delta_location_map.svg', 'Relief_Map_of_Siberian_Federal_District.jpg', 'Panfilovmap800000.svg', 'Europe_blank_laea_location_map.svg', 'West_Asia_non_political_with_water_system.jpg', 'Languedoc-Roussillon-Loc.png', 'Location_map_Denmark_Funen.png', 'KG-Osh-Alay.svg', 'British_Isles.svg', 'Israel_outline_jezreel.png', 'Qatar_Doha_location_map.svg', 'Island_of_Ireland_location_map.svg', 'Baltic_states_location_map.svg', 'Caribbean_location_map.svg', 'European_Russia_location_map_(2014–2022,_Crimea_disputed).svg', "Location_map_Indonesia_Bird's_Head_Peninsular.png", 'Topological_map_of_Neu_Guinea.png', 'Timor.png', 'Balkans_relief_location_map.jpg', 'Iberian_Peninsula_location_map.svg', 'Location_map_Ryukyu_Islands.png', 'South_Asia_non_political,_with_rivers.jpg', 'Central_Europe_location_map.svg', 'West_Bank_location_map.svg', 'Asia_laea_location_map.svg', 'Pyrenees_map_shaded_relief-fr.svg', 'Micronesia_regions_map.png', 'Levant_adm_location_map.svg', 'USA_Hawaii_island_chain_location_map.svg', 'Middle_East_location_map.svg', 'Scandinavia_location_map.svg', 'Golan_Heights_relief_v2.png', 'Locaation_map_Denmark_Zealand.png', 'Map-of-Komárom-Esztergom.svg', 'Map-of-Győr-Moson-Sopron.svg'}
# ONLY_ONE_MAP = {'0480_Woodlands_County,_Alberta,_Detailed.svg', 'Greece_(ancient)_IonianIslands_(cropped).svg', 'Indonesia_Kulon_Progo_Regency_location_map.svg', 'Location_map_Guadalcanal.png', '2_Regional_District_of_Fraser-Fort_George_British_Columbia.svg', 'Indonesia_Kebumen_Regency_location_map.svg', 'Indonesia_Majalengka_Regency_location_map.svg', 'Outline_Map_of_Central_Russia.svg', 'Location_map_of_Gloucester_County,_New_Jersey.svg', '0226_Mountain_View_County,_Alberta,_Detailed.svg', '3_Regional_District_of_Kitimat-Stikine_British_Columbia.svg', '0340_County_Of_Warner_No_5,_Alberta,_Detailed.svg', '4_Regional_District_of_Mount_Waddington_British_Columbia.svg', 'Indonesia_Sidoarjo_Regency_location_map.svg', 'Location_map_of_Mercer_County,_New_Jersey.svg', 'Wallis-et-Futuna_collectivity_location_map.svg', '0191_Kneehill_County,_Alberta,_Detailed.svg', 'Location_map_of_Brown_County,_Indiana.svg', 'Kabupaten_Tanah_Laut_Location_Map.svg', 'Norway_Troms_og_Finnmark_adm_location_map.svg', 'Luxembourg_Diekirch_location_map.svg', 'Outline_Map_of_Altai_Republic.svg', 'Indonesia_Bojonegoro_Regency_location_map.svg', 'United_States_Virgin_Islands_Saint_Croix_location_map.svg', 'Belo_Horizonte_location_map.svg', '0012_Athabasca_County,_Alberta,_Detailed.svg', '0049_Camrose_County,_Alberta,_Detailed.svg', 'Isle_of_Skye_UK_location_map.svg', 'USA_Mid-Atlantic_location_map.svg', 'Easter_Island_location_map.svg', '0015_County_Of_Barrhead_No_11,_Alberta,_Detailed.svg', '0053_Cardston_County,_Alberta,_Detailed.svg', '4353_Lac_La_Biche_County,_Alberta,_Detailed.svg', '20_Qathet_Regional_District_British_Columbia.svg', 'Haliburton_locator_map_2021.svg', 'Indonesia_Bogor_Regency_location_map.svg', 'Csongrad_location_map.svg', 'India_Dadra_and_Nagar_Haveli_location_map.svg', 'Indonesia_Karanganyar_Regency_location_map.svg', 'Nouvelle-Calédonie_collectivity_location_map_centered.svg', '0290_Municipal_District_Of_Spirit_River_No_133,_Alberta,_Detailed.svg', '0346_Westlock_County,_Alberta,_Detailed.svg', 'West_Bank_location_map.svg', '21_Squamish-Lillooet_Regional_District_British_Columbia.svg', 'Indonesia_Badung_Regency_location_map.svg', 'Philippines_location_map_(Visayas).svg', 'Location_map_of_Salem_County,_New_Jersey.svg', 'Kelbajar_Rayon.PNG', 'Indonesia_Kalimantan_location_map.svg', '0361_Municipality_Of_Crowsnest_Pass,_Alberta,_Detailed.svg', '0349_Wheatland_County,_Alberta,_Detailed.svg', '23_Regional_District_of_Bulkley-Nechako_British_Columbia.svg', '0036_Municipal_District_Of_Bonnyville_No_87,_Alberta,_Detailed.svg', 'Locator_map_AZO_TER.svg', 'Al_Wakrah_localities.png', 'Outline_Map_of_Volga_Federal_District.svg', '0312_Municipal_District_Of_Taber,_Alberta,_Detailed.svg', '10_Cariboo_Regional_District_British_Columbia.svg', 'USA_District_of_Columbia_location_map.svg', '0020_Beaver_County,_Alberta,_Detailed.svg', 'Duck_Lake_No._463_Coloured_Map.svg', 'Indonesia_Banyuwangi_Regency_location_map.svg', 'Shetland_UK_location_map.svg', '8_Sunshine_Coast_Regional_District_British_Columbia.svg', '28_Northern_Rockies_Regional_Municipality_British_Columbia.svg', 'Seychelles_location_map.svg', 'Location_map_Pomurska.png', 'Kurily.svg', 'Saint-Martin_collectivity_location_map.svg', 'Bantayan_island_group.png', '0506_Big_Lakes_County,_Alberta,_Detailed.svg', 'Sula_Islands_Locator_Topography.png', 'Argentina_Tierra_del_Fuego_and_Staten_Island_location_map.svg', '7_North_Coast_Regional_District_British_Columbia.svg', '22_Strathcona_Regional_District_British_Columbia.svg', 'Levant_adm_location_map.svg', 'Locator_map_Azores_Pico.png', 'Outer_Hebrides_UK_location_map.svg', 'Relief_Map_of_Northwestern_Federal_District.jpg', 'Tahiti_location_map.png', 'Turks_and_Caicos_Islands_location_map.svg', 'Australia_Victoria_Queenscliffe_Borough_location_map.svg', 'Indonesia_Purworejo_Regency_location_map.svg', 'Norway_Viken_adm_location_map.svg', 'Canada_Vancouver_Island_location_map.svg'}
imgs_dic = {}
pushpin_imgs = set()
pushpin_imgs_count = Counter()
normal_imgs = set()
low_res_imgs = set()
all_urls = set()

total_tags = set()

# Pre-compiled regex patterns
_Q_ID_FULL_RE = re.compile(r'^Q\d+$')
_Q_ID_PREFIX_RE = re.compile(r'^Q\d+')
_ARTIST_RE = re.compile(r'(?: title=".*?")|\n|(?:</?(div|span).*?>)|(?:<sup.*?>.*?</sup>)')
_formula_cache = {}

def escape_characters(text):
    return text.replace(';;', quote(';;')).replace('|', quote('|')).replace('\xa0', '&nbsp;')

def get_wikitext_value(value, wikitext):
	pat1 = value + r'[^\S\n]*=[^\S\n]*(:?\'([^\']*)\'|(.*?))[^\S\n]*(,|\s*\})'
	match = re.search(pat1, wikitext)
	if not match:
		return ''

	pat2 = r'\[\[|(\|.*?)?\]\]||{{.*?(}}|$)|<.*?>.*?</.*?>'
	match = re.sub(pat2, '', match.group(1)).strip("'")

	return match

def get_file_name(url):
	return unquote(re.sub(r'.*/(?:\d+px-)?(.*)', r'\1', url)).replace(' ', '_')

def get_x(longitude, left, right):
	width = (right - left) % 360
	if width == 0:
		width = 360
	distanceFromLeft = (longitude - left) % 360
	if distanceFromLeft - width / 2 >= 180:
		distanceFromLeft = distanceFromLeft - 360
	return 100 * distanceFromLeft / width

def get_y(latitude, top, bottom):
	return 100 * (top - latitude) / (top - bottom)

def get_custom(latitude, longitude, formula):
	if formula not in _formula_cache:
		code_str = formula.replace('$1', 'lat').replace('$2', 'lon').replace('^', '**').replace('ln', 'log')
		_formula_cache[formula] = compile(code_str, '<formula>', 'eval')
	return eval(_formula_cache[formula], {"__builtins__": {}},
				{'lat': latitude, 'lon': longitude, 'sin': sin, 'cos': cos, 'tan': tan, 'pi': pi, 'atan': atan, 'log': log})

def get_pin_loc(long_lat, pushpin_info):
	if pushpin_info['top']:
		# If map is simple
		pin_x = get_x(long_lat[0], pushpin_info['left'], pushpin_info['right'])
		pin_y = get_y(long_lat[1], pushpin_info['top'], pushpin_info['bottom'])
	else:
		# If coordinates should be calculated using custom formula
		pin_x = get_custom(long_lat[1], long_lat[0], pushpin_info['x'])
		pin_y = get_custom(long_lat[1], long_lat[0], pushpin_info['y'])

	if not (0 < pin_x < 100 and 0 < pin_y < 100):
		return []

	return [round(pin_x, 3), round(pin_y, 3)]


def get_pushpin_info(frt_wikitext):
	img = get_wikitext_value(r'image\w?', frt_wikitext).replace(' ', '_').strip("'" + '"_')
	name = get_wikitext_value('name', frt_wikitext).strip("'" + '"').title()

	frt_top = get_wikitext_value('top', frt_wikitext)
	if frt_top:
		frt_top = float(frt_top)
		frt_bottom = float(get_wikitext_value('bottom', frt_wikitext))
		frt_left = float(get_wikitext_value('left', frt_wikitext))
		frt_right = float(get_wikitext_value('right', frt_wikitext))
		frt_x = None
		frt_y = None
	else:
		frt_x = get_wikitext_value('x', frt_wikitext)
		frt_y = get_wikitext_value('y', frt_wikitext)
		frt_top = None
		frt_bottom = None
		frt_left = None
		frt_right = None

	return {
		'name': name,
		'img': img,
		'top': frt_top if frt_top is not None else '',
		'bottom': frt_bottom if frt_bottom is not None else '',
		'left': frt_left if frt_left is not None else '',
		'right': frt_right if frt_right is not None else '',
		'x': frt_x if frt_x is not None else '',
		'y': frt_y if frt_y is not None else ''
	}

def is_map_bigger(long_lat, map1_name, map2_name, imgs_dic):
	map1 = imgs_dic[map1_name]
	map2 = imgs_dic[map2_name]
	long_lat2 = [long_lat[0], long_lat[1] + COORD_DIFF]
	map1_pin1 = get_pin_loc(long_lat, map1)
	map1_pin2 = get_pin_loc(long_lat2, map1)
	map2_pin1 = get_pin_loc(long_lat, map2)
	map2_pin2 = get_pin_loc(long_lat2, map2)

	m1_diff = m2_diff = 0
	for mp1, mp2, cp1, cp2 in zip(map1_pin1, map1_pin2, map2_pin1, map2_pin2):
		m1_diff += abs(mp2 - mp1)
		m2_diff += abs(cp2 - cp1)

	return 1 if m1_diff < m2_diff else -1

def process_cities_and_maps(df, map_dict):
	global pushpin_imgs, pushpin_imgs_count, total_tags
	print('-'*30, 'Getting cities', '-'*30)

	df['maps'] = np.nan # Initialize new column
	df['maps'] = df['maps'].astype(object)

	for idx in df.index:
		country = country_label = None
		subdivisions_country = []
		subdivisions_country_label = []

		# Cache row values
		row = df.loc[idx]
		country = row['country']
		country_label = row['countryLabel']

		# Cache physicals and other columns
		physicals = row['physicals']
		physical_labels = row['physicalLabels']
		physicals2 = row['physicals2']
		physical2_labels = row['physical2Labels']
		partofs = row['partofs']
		partof_labels = row['partofLabels']
		subdivisions_data = [
			(row['subdivisions'], row['subdivisionLabels']),
			(row['subdivisions2'], row['subdivision2Labels']),
			(row['subdivisions3'], row['subdivision3Labels']),
			(row['subdivisions4'], row['subdivision4Labels']),
			(row['subdivisions5'], row['subdivision5Labels']),
			(row['subdivisions6'], row['subdivision6Labels'])
		]
		sub_country_labels = row['sub_countryLabels'].split('|')

		# Process subdivisions and physicals
		subdivisions_country.append(country)
		subdivisions_country_label.append(country_label)
		if pd.notnull(physicals):
			subdivisions_country.extend(physicals.split('|'))
			physical_labels = [p for p in physical_labels.split('|') if not _Q_ID_FULL_RE.match(p)]
			subdivisions_country_label.extend(physical_labels)
		if pd.notnull(physicals2):
			subdivisions_country.extend(physicals2.split('|'))
		if pd.notnull(partofs):
			subdivisions_country.extend(partofs.split('|'))

		# Create tags
		for i in range(len(sub_country_labels)):
			sc = sub_country_labels[i]
			if sc == country_label:
				# Begins tag as bottom layer subdivision and adds super tags until country/unknown
				s_label = subdivisions_data[0][1].split('|')[i]

				for j in range(1, len(subdivisions_data)):
					next_sub = subdivisions_data[j][0].split('|')[i]
					next_sub_label = subdivisions_data[j][1].split('|')[i]


					# Skip e.g. "Q182783" as a tag
					if _Q_ID_PREFIX_RE.match(s_label):
						s_label = next_sub_label
						continue

					if next_sub == UNKNOWN_ENTITY:
						break
					s_label = f"{next_sub_label}::{s_label}"
					if next_sub == country:
						break
				subdivisions_country_label.append(s_label)
				for j in range(len(subdivisions_data)):
					s = subdivisions_data[j][0].split('|')[i]
					subdivisions_country.append(s)

		# Cache maps
		maps = list({map_dict.get(sub, '').replace(wikipedia_base_url, '').replace('_', ' ')
					 for sub in subdivisions_country if sub in map_dict})

		if not maps:
			print(f'*** {row["city"]} has no maps!')

		# Update tags
		tags = {f'cities::{t}' for t in row['type'].split('|')}

		subdivisions_country_label = [s for s in subdivisions_country_label if not s.endswith('unknown')]
		subdivisions_country_label = [
			f'{country_label}::{tag}' if not tag.startswith(country_label + '::') and tag != country_label else tag
			for tag in subdivisions_country_label
		]
		simplified_subdivision_tags = {st for st in subdivisions_country_label
										 if not any(st != other and st in other
													  for other in subdivisions_country_label)}
		tags.update(f"cities::{tag.replace(' ', '-').replace(',', '')}" for tag in simplified_subdivision_tags)
		tags.add('cities::version-2026-03-04')

		# Update dataframe
		df.at[idx, 'maps'] = maps
		df.at[idx, 'tags'] = ' '.join(tags)

		# Just for the total count
		total_tags.update(tags)

		# Update pushpin_imgs
		pushpin_imgs.update(maps)
		for map_name in maps:
			pushpin_imgs_count[map_name] += 1

	return df

def add_more_populations(df):
	# Fill out missing populations using Geonames
	geonames = pd.read_csv(INPUT_FILES['Geonames'], sep='\t', header=None, usecols=[0, 1, 14], names=['geonameid', 'name', 'population'], dtype={'geonameid': 'Int64', 'name': str, 'population': 'unicode'})

	df['geonameid'] = df['geonameid'].astype('Int64')
	df = df.merge(geonames[['geonameid', 'population']], on='geonameid', how='left', suffixes=('', '_geonames'))
	df['population'] = df['population'].fillna(df['population_geonames'])
	return df


def request_pushpin_maps_info(df, pushpin_imgs):
	global imgs_dic
	print('\n' + '-'*30, 'Requesting pushpin maps', '-'*30)

	pushpin_imgs_list = list(pushpin_imgs) # Convert set to list for indexing
	print(len(pushpin_imgs_list), 'pushpin images')
	print()
	renames = {}
	while(pushpin_imgs_list):
		current_imgs, pushpin_imgs_list = pushpin_imgs_list[:N_QUERY], pushpin_imgs_list[N_QUERY:] # Extracts 50 elements to query at a time
		titles = '|'.join(current_imgs).replace('_', ' ').replace('+', '%2B')
		response = session.get(revision_url + titles).json() # Module:
		for key, img in response['query']['pages'].items():
			title = img['title']
			if 'missing' in img:
				# Remove pushpin maps that don't exist
				print('*****', title, 'is missing??')
				continue
			wikitext = img['revisions'][0]['slots']['main']['*']
			require = re.search(r"return require\('(.*?)'\)", wikitext)
			if require:
				pushpin_imgs.add(require.group(1))
				new_title = require.group(1)

				# Replace wrong pushpin id in imgs_dic keys and df['maps']
				imgs_dic[new_title] = imgs_dic.pop(title, None) # If title exist, move to new_title
				renames[title] = new_title

				continue

			pushpin_info = get_pushpin_info(wikitext)
			imgs_dic[title] = pushpin_info

	# Apply all renames in a single pass
	if renames:
		df['maps'] = df['maps'].apply(lambda ms: [renames.get(m, m) for m in ms] if isinstance(ms, list) else ms)

	return imgs_dic, pushpin_imgs

def insert_correct_pushpin_maps(df, imgs_dic):
	global normal_imgs, low_res_imgs, pushpin_imgs_count
	print('\n' + '-'*30, 'Inserting correct pushpin maps', '-'*30)
	point_regex = re.compile(r'Point\((.*)\)')
	rows_to_drop = []
	js_xy_cache = {}
	for idx in df.index:
		row = df.loc[idx]
		maps = row['maps']
		coords = row['coords']

		# Extract long_lat using the compiled regex
		match = point_regex.search(coords)
		if match:
			long_lat = match.group(1).split(' ')
		else:
			# Remove items with no coordinates
			rows_to_drop.append(idx)
			continue

		# Convert long_lat to floats
		long_lat = list(map(float, long_lat))

		# Sort maps using `is_map_bigger`
		maps = sorted(set(maps), key=cmp_to_key(lambda x,y: is_map_bigger(long_lat, x, y, imgs_dic)), reverse=True)


		new_maps = []

		# Process maps in reverse order
		for map_name in reversed(maps):
			img_data = imgs_dic[map_name]

			# Skip unwanted maps
			if img_data['img'] in UNWANTED_MAPS:
				continue


			# Get pin location
			pin_loc = get_pin_loc(long_lat, img_data)
			if not pin_loc:
				continue

			if pushpin_imgs_count[map_name] <= 5:
				low_res_imgs.add(img_data['img'])
			else:
				normal_imgs.add(img_data['img'])

			# Replace mathematical functions with corresponding JavaScript functions (cached per map)
			if map_name not in js_xy_cache:
				_new_xy = {}
				for x_y in ['x', 'y']:
					_new_xy[x_y] = img_data[x_y].replace('^', '**').replace('ln', 'Math.log').replace('pi', 'Math.PI') \
						.replace('sin', 'Math.sin').replace('cos', 'Math.cos') \
						.replace('atan', 'Math.atan').replace('tan', 'Math.tan')
				js_xy_cache[map_name] = _new_xy
			new_xy = js_xy_cache[map_name]

			# Create HTML string for the map
			map_html = f'<img src="{img_data["img"]}">|||{img_data["name"]}|{img_data["top"]}|{img_data["bottom"]}|{img_data["left"]}|{img_data["right"]}|{new_xy["x"]}|{new_xy["y"]}'
			new_maps.insert(0, map_html)
		
		# Drop city if no valid map survived filtering
		if not new_maps:
			rows_to_drop.append(idx)
			continue

		# Prepend coordinates
		new_maps.insert(0, f'{long_lat[0]} {long_lat[1]}')

		# Update the DataFrame with the joined maps
		df.at[idx, 'maps'] = ';;'.join(new_maps)
	
	if rows_to_drop:
		df.drop(index=rows_to_drop, inplace=True)

	return df, normal_imgs, low_res_imgs

def get_usernames_and_update_html(df, normal_imgs, low_res_imgs):
	global all_urls
	print('\n' + '-'*30, 'Usernames from images', '-'*30)

	# print('use low res:', low_res_imgs)
	print('normal resolution:', len(normal_imgs))
	print('low resolution (uncommon):', len(low_res_imgs))

	normal_imgs_file = ['File:' + img for img in normal_imgs]
	low_res_imgs_file = ['File:' + img for img in low_res_imgs]

	print((len(normal_imgs_file)), 'images')
	print()
	replacements = {}
	for (imgs, q_url) in [(normal_imgs_file, query_url), (low_res_imgs_file, query_url_low_res)]:
		while(imgs):
			current_imgs, imgs = imgs[:N_QUERY], imgs[N_QUERY:] # Extracts 50 elements to query at a time
			titles = '|'.join(current_imgs).replace('_', ' ').replace('+', '%2B')
			response = session.get(f'{q_url}&titles={titles}').json() # File:
			for key, img in response['query']['pages'].items():
				if not 'imageinfo' in img:
					# Images on wikipedia not on commons
					print(img)
					resp = session.get(query_url_wikipedia + img['title']).json()['query']['pages']
					img = list(resp.values())[0]

				title = img['title'].replace('File:', '').replace(' ', '_')
				new_title = title + '.png' if title.endswith('.svg') else title

				redir_title = ""
				if 'redirects' in img:
					redir_title = img['redirects'][0]['title'].replace('File:', '').replace(' ', '_')

				img_info = img['imageinfo'][0]

				artist = ''
				lic_url = ''
				if 'AttributionRequired' in img_info['extmetadata'] and img_info['extmetadata']['AttributionRequired']['value'] == 'true' and 'Artist' in img_info['extmetadata']:
					artist = _ARTIST_RE.sub('', img_info['extmetadata']['Artist']['value'])
					artist = artist.replace('href="//', 'href="https://')
					artist = escape_characters(artist)
					lic_url = img_info['extmetadata']['LicenseUrl']['value']

				if artist or new_title != title:
					replacements[title + '">||'] = f'{new_title}">|{artist}|{lic_url}'
					if redir_title:
						replacements[redir_title + '">||'] = f'{new_title}">|{artist}|{lic_url}'

				all_urls.add(img_info['thumburl'])

	print('Done getting usernames. Replacing...')
	# Apply all replacements in a single pass over the column
	if replacements:
		def apply_replacements(text):
			for old, new in replacements.items():
				text = text.replace(old, new)
			return text
		df['maps'] = df['maps'].apply(apply_replacements)

	return df, all_urls

def download_images(all_urls):
	print('\n' + '-'*30, 'Downloading images', '-'*30)
	request_count = 0
	for url in all_urls:
		title = get_file_name(url)
		if not os.path.isfile(file_target + title): # If not already downloaded
			r = session.get(url) # img.png
			request_count += 1

			retries_429 = 0
			while r.status_code == 429 and retries_429 < 5:
				retries_429 += 1
				retry_after = int(r.headers.get('Retry-After', DOWNLOAD_PAUSE_SECONDS * retries_429))
				print(url, f'({retries_429}/5) retrying in {retry_after}s')
				time.sleep(retry_after)
				r = session.get(url)
				request_count += 1

			if r.status_code != 200:
				print(url, 'returned', r.status_code)
				continue

			print(title)
			with open(file_target + title, "wb") as f:
				f.write(r.content)

def finalize_dataframe_and_save(df, total_tags):
	print("total tags:", len(total_tags))

	df['population'] = df['population'].str.replace('.', '', regex=False)
	df['population'] = df['population'].astype('Int64')
	type_order = {'city': 0, 'urban-area': 0, 'subdivision': 1}
	df['type_sort'] = df['type'].apply(lambda t: min(type_order.get(x, 99) for x in t.split('|')))
	df = df.sort_values(by=['type_sort', 'population', 'countryLabel'], ascending=[True, False, True])
	df['population'] = df['population'].astype(object)
	df['population'] = df['population'].apply(lambda x: f'{x:,}' if not pd.isnull(x) else x) # Add decimal separators "1,000,000"

	# Save to file without Anki file header
	df.to_csv(OUTPUT_FILES['Cities of countries_header'], index=False, encoding='utf-8')

	COLUMNS = ['Wikidata ID', 'English', 'Native', 'Wikipedia ID', 'Population', 'Maps', 'Tags']
	df = df.rename(columns={'wikidata_id': 'Wikidata ID', 'city': 'English', 'native': 'Native', 'wikipedia_url': 'Wikipedia ID', 'population': 'Population', 'maps': 'Maps', 'tags': 'Tags'})
	df = df.reindex(columns=COLUMNS)
	with open(OUTPUT_FILES['Cities of countries'], 'w', encoding='utf-8', newline='') as f:
		# Write the header text at the beginning of the file
		f.write(f'#separator:Comma\n#html:true\n#notetype:Cities\n#deck:Cities of Your Country\n#tags column:{COLUMNS.index("Tags") + 1}\n#columns:{",".join(COLUMNS)}\n')

		# Save the DataFrame to the file without the index
		df.to_csv(f, index=False, header=False, encoding='utf-8')

def create_cities_of_countries_dataframe():
	global imgs_dic, pushpin_imgs, pushpin_imgs_count, normal_imgs, low_res_imgs, all_urls, total_tags

	with open(PROCESSED_FILES['map_dict'], 'rb') as f:
		map_dict = pickle.load(f)

	df = pd.read_csv(PROCESSED_FILES['All countries combined'], dtype='unicode', keep_default_na=False, na_values=[''])
	if TEST_ID:
		df = df[df['wikidata_id'] == TEST_ID]

	df = process_cities_and_maps(df, map_dict)
	df = add_more_populations(df)
	imgs_dic, pushpin_imgs = request_pushpin_maps_info(df, pushpin_imgs)
	df, normal_imgs, low_res_imgs = insert_correct_pushpin_maps(df, imgs_dic)
	df, all_urls = get_usernames_and_update_html(df, normal_imgs, low_res_imgs)
	download_images(all_urls)
	finalize_dataframe_and_save(df, total_tags)
