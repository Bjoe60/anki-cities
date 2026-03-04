import pandas as pd
import pickle
import time
from json import JSONDecodeError
from urllib.parse import unquote
from SPARQLWrapper import SPARQLWrapper, JSON
from file_paths import PROCESSED_FILES

MAPS_TO_REMOVE = {'https://en.wikipedia.org/wiki/Module:Location_map/data/Abkhazia', 'https://en.wikipedia.org/wiki/Module:Location_map/data/USA_American_Samoa_central', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Continental_Asia', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Canton_of_Basel-Land', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Borneo', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Switzerland_Canton_of_Z%C3%BCrich', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Canton_of_Zurich', 'https://en.wikipedia.org/wiki/Module:Location_map/data/United_Kingdom_Channel_Islands', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Argentina_Chubut', 'https://en.wikipedia.org/wiki/Module:Location_map/data/UK_England_Essex', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Netherlands_Flevoland', 'https://en.wikipedia.org/wiki/Module:Location_map/data/East_Germany', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Syria_Golan', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Gran_Canaria', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Canton_of_Graubunden', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Canton_of_Grisons', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Ukraine_Kiev_Oblast', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Kyushu', 'https://en.wikipedia.org/wiki/Module:Location_map/data/China_Liaoning_topography', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Brazil_Minas_Gerais_state', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Burma', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Canton_of_Neuchatel', 'https://en.wikipedia.org/wiki/Module:Location_map/data/United_States_New_York', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Norfolk_Island', 'https://en.wikipedia.org/wiki/Module:Location_map/data/CAN_ON_York', 'https://en.wikipedia.org/wiki/Module:Location_map/data/US_Virgin_Islands_Saint_Croix', 'https://en.wikipedia.org/wiki/Module:Location_map/data/San_Francisco_Bay_Area', 'https://en.wikipedia.org/wiki/Module:Location_map/data/USA_San_Francisco_Bay_Area', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Australia_Victoria_Baw_Baw_Shire', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Sonoma_County', 'https://en.wikipedia.org/wiki/Module:Location_map/data/SEQ', 'https://en.wikipedia.org/wiki/Module:Location_map/data/USA_Southeast', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Brazil_Sao_Paulo', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Tenerife', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Ethiopia_Tigray_Region', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Japan_Tohoku_Region', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Visayas', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Switzerland_Canton_of_Vaud', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Finland_%C3%85land', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Hubei', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Scandinavia_LCC_map', 'https://en.wikipedia.org/wiki/Module:Location_map/data/Timor-Leste'}

DIRECT_UNWANTED_ENDED_CITY_CLASS = """
SELECT DISTINCT ?city WHERE {
	?city wdt:P31/wdt:P279* wd:Q7930989 . # City or town

	# A city prop has end time
	?city p:P31 ?t .
	?t ps:P31 ?type .
	?type wdt:P279* wd:Q7930989 .
	?t pq:P582 [] .

	# Should not have a city prop without end time
	OPTIONAL {
		?city p:P31 ?t2 .
		?t2 ps:P31 ?type2 .
		?type2 wdt:P279* wd:Q7930989 .
		OPTIONAL { ?t2 pq:P582 ?et2 . }
		FILTER(!BOUND(?et2)) .
	}
	FILTER(!BOUND(?type2)) .
}
"""

DIRECT_UNWANTED_VILLAGE = """
SELECT DISTINCT ?city WHERE {
	?city wdt:P31/wdt:P279* wd:Q7930989 .
	?city p:P31 ?statement .
	?statement ps:P31 ?type .
	?type wdt:P279* wd:Q532 . # Village
	FILTER NOT EXISTS { ?statement pq:P582 ?end } # No end-time
}
"""

CANDIDATE_HISTORIC = """
SELECT DISTINCT ?city WHERE {
	?city wdt:P31/wdt:P279* wd:Q15243209 . # Historic
}
"""

CANDIDATE_FORMER_SETTLEMENT = """
SELECT DISTINCT ?city WHERE {
	?city wdt:P31/wdt:P279* wd:Q22674925 . # Former settlement (includes ancient city)
	OPTIONAL {
		?city p:P31 ?statement .
		?statement ps:P31/wdt:P279* wd:Q22674925 .
		?statement pq:P582 ?end_time .
	}

	# Filter to only include former settlements without an "end time"
	FILTER(!BOUND(?end_time))
}
"""

DIRECT_UNWANTED_DISSOLVED = """
SELECT DISTINCT ?city WHERE {
	?city wdt:P31/wdt:P279* wd:Q7930989 .
	?city wdt:P576 [] . # Dissolved
}
"""

CANDIDATE_ARCHAEOLOGICAL_SITE = """
SELECT DISTINCT ?city WHERE {
	?city wdt:P31/wdt:P279* wd:Q7930989 . # City or town
	?city wdt:P31/wdt:P279* wd:Q839954 . # Archaeological site
	OPTIONAL {
		?city p:P31 ?statement .
		?statement ps:P31/wdt:P279* wd:Q839954 .
		?statement pq:P582 ?end_time .
	}

	# Filter to only include archaeological sites without an "end time"
	FILTER(!BOUND(?end_time))
}
"""

DIRECT_UNWANTED_REPLACED = """
SELECT DISTINCT ?city WHERE {
  ?city wdt:P31/wdt:P279* wd:Q7930989 .
  ?city p:P1366 ?statement .
  ?statement ps:P1366 ?replacement .

  FILTER NOT EXISTS { ?statement pq:P518  ?x }   # applies to part
  FILTER NOT EXISTS { ?statement pq:P1001 ?x }   # applies to jurisdiction
  FILTER NOT EXISTS { ?statement pq:P6001 ?x }   # applies to people
  FILTER NOT EXISTS { ?statement pq:P3831 ?x }   # object has role
  FILTER NOT EXISTS { ?statement pq:P582  ?x }   # end time
}
"""

ACTIVE_NON_FORMER_URBAN_CLASS_QUERY = """
SELECT DISTINCT ?city WHERE {
	VALUES ?city { %s }
	?city p:P31 ?statement .
	?statement ps:P31 ?class .
	?class wdt:P279* wd:Q7930989 .

	# Exclude former/historic/archaeological-type classes (and their subclasses)
	FILTER NOT EXISTS {
		VALUES ?excludedType { wd:Q22674925 wd:Q15243209 wd:Q839954 wd:Q19953632 wd:Q15661340 }
		?class wdt:P279* ?excludedType .
	}

	# Only active class statements (no end time)
	FILTER NOT EXISTS { ?statement pq:P582 ?end_time . }
}
"""

UNWANTED_SUBDIV_QUERY_1 = """
SELECT DISTINCT ?city WHERE {
	?city wdt:P31/wdt:P279* wd:Q1799794 . # Subdivision
	?city wdt:P576 [] . # Dissolved
}
"""

UNWANTED_SUBDIV_QUERY_2 = """
SELECT DISTINCT ?city WHERE {
  ?city wdt:P31/wdt:P279* wd:Q1799794 . # Subdivision

  ?city p:P1366 ?statement .
  ?statement ps:P1366 ?replacement . # Is replaced by another subdiv

  FILTER NOT EXISTS {
    ?statement pq:P518 ?appliesToPart . # Should not be a replacement that only applies to a part of the subdiv
  }
}
"""

# When checked, it seems we do not have to also check for end date here as all samples are still former
FORMER_SUBDIV_QUERY = """
SELECT DISTINCT ?city WHERE {
	?city wdt:P31/wdt:P279* wd:Q19953632 . # former administrative territorial entity
}
"""

CHINA_CURRENT_SUBDIV_QUERY = """
SELECT DISTINCT ?city WHERE {
	?city wdt:P31/wdt:P279* wd:Q50231 . # administrative territorial entity of the People's Republic of China
	FILTER NOT EXISTS { ?city wdt:P31 wd:Q19953632 . } # former administrative territorial entity
}
"""

UNWANTED_URBAN_AREA_QUERY = """
SELECT DISTINCT ?city WHERE {
	?city wdt:P31/wdt:P279* wd:Q1907114 . # Metropolitan area
	FILTER NOT EXISTS { ?city wdt:P31 wd:Q1549591 . }
}
"""

LOCATION_MAP_QUERY = """
SELECT DISTINCT ?item ?article ?depicts ?depictsLabel WHERE {
	VALUES ?wikimedia_map { wd:Q18711811 wd:Q36330215 }
	?item wdt:P31 ?wikimedia_map .
	FILTER NOT EXISTS { ?item p:P31/ps:P31 wd:Q108292642 . }
	?item wdt:P180 ?depicts .
	FILTER NOT EXISTS { ?depicts p:P31/ps:P31/wdt:P279* wd:Q515 . FILTER(?depicts != wd:Q334) } # City (except for Singapore)
	FILTER NOT EXISTS { ?depicts p:P31/ps:P31/wdt:P279* wd:Q3957 } # Town
	FILTER NOT EXISTS { ?depicts p:P31/ps:P31/wdt:P279* wd:Q178512 } # Public transport
	?article schema:about ?item ;
					 schema:isPartOf <https://en.wikipedia.org/> .

	SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
"""


sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent='Bjoe1839/1.0 (bjorn60@gmail.com) bot')


def run_sparql_query_with_504_retries(query, max_retries=5, base_delay_seconds=2):
	"""Run a SPARQL query and retry on transient endpoint failures."""
	sparql.setQuery(query)
	sparql.setReturnFormat(JSON)
	retryable_http_codes = {429, 500, 502, 503, 504}

	for attempt in range(max_retries + 1):
		try:
			return sparql.query().convert()
		except Exception as e:
			error_code = getattr(e, 'code', None)
			message = str(e)
			is_retryable_http = error_code in retryable_http_codes
			is_malformed_json = isinstance(e, JSONDecodeError) or 'JSONDecodeError' in message or 'Invalid control character' in message
			is_retryable_message = any(token in message.lower() for token in [
				'gateway timeout', 'bad gateway', 'service unavailable', 'temporarily unavailable'
			])
			is_retryable = is_retryable_http or is_malformed_json or is_retryable_message
			is_last_attempt = attempt == max_retries

			if not is_retryable or is_last_attempt:
				raise

			delay = base_delay_seconds * (2 ** attempt)
			error_label = f"HTTP {error_code}" if error_code is not None else type(e).__name__
			print(f"SPARQL query failed with {error_label}. Retrying in {delay}s (attempt {attempt + 1}/{max_retries})...")
			time.sleep(delay)


def get_active_non_former_urban_city_ids(candidate_city_ids, chunk_size=200):
	"""Return candidate city IDs that still have an active non-former urban class."""
	if not candidate_city_ids:
		return set()

	active_ids = set()
	candidate_list = sorted(candidate_city_ids)

	for start in range(0, len(candidate_list), chunk_size):
		print(f"Batch {start // chunk_size + 1} / {(len(candidate_list) - 1) // chunk_size + 1}")
		chunk = candidate_list[start:start + chunk_size]
		values = ' '.join(f"wd:{city_id}" for city_id in chunk)
		query = ACTIVE_NON_FORMER_URBAN_CLASS_QUERY % values
		results = run_sparql_query_with_504_retries(query)

		for result in results["results"]["bindings"]:
			active_ids.add(result["city"]["value"].replace('http://www.wikidata.org/entity/', ''))

	return active_ids

def create_unwanted_dict():
	"""Creates unwanted city and town lists and saves to unwanted_dict.pkl."""
	unwanted = {'city': set(), 'subdivision': set()}
	CITY_TOWN_IDS = {"Q7930989": "city", "Q56061": "subdivision"}

	city_direct_unwanted_queries = [
		DIRECT_UNWANTED_ENDED_CITY_CLASS,
		# DIRECT_UNWANTED_VILLAGE,
		DIRECT_UNWANTED_DISSOLVED,
		DIRECT_UNWANTED_REPLACED,
	]
	city_candidate_queries = [
		CANDIDATE_HISTORIC,
		CANDIDATE_FORMER_SETTLEMENT,
		CANDIDATE_ARCHAEOLOGICAL_SITE,
	]

	for query in city_direct_unwanted_queries:
		print("Running direct unwanted city query:")
		print(query)
		results = run_sparql_query_with_504_retries(query)

		for result in results["results"]["bindings"]:
			unwanted['city'].add(result["city"]["value"].replace('http://www.wikidata.org/entity/', ''))
		
		print(f"Number of results: {len(results['results']['bindings'])}")

	candidates = set()
	for query in city_candidate_queries:
		print("Running candidate query (historic/former/archaeological)...")
		results = run_sparql_query_with_504_retries(query)

		for result in results["results"]["bindings"]:
			candidates.add(result["city"]["value"].replace('http://www.wikidata.org/entity/', ''))
		
		print(f"Number of results: {len(results['results']['bindings'])}")

	print(f"Found {len(candidates)} candidates. Checking for active non-former urban classes...")
	active_non_former_cities = get_active_non_former_urban_city_ids(candidates)
	print(f"Keeping {len(active_non_former_cities)} cities that have an active non-former urban class.")
	unwanted['city'].update(candidates - active_non_former_cities)

	for query in [UNWANTED_SUBDIV_QUERY_1, UNWANTED_SUBDIV_QUERY_2]:
		print("Running query for subdivision:")
		print(query)
		results = run_sparql_query_with_504_retries(query)

		for result in results["results"]["bindings"]:
			unwanted['subdivision'].add(result["city"]["value"].replace('http://www.wikidata.org/entity/', ''))
		
		print(f"Number of results: {len(results['results']['bindings'])}")

	# Generate former subdivs, but remove current china
	results = run_sparql_query_with_504_retries(FORMER_SUBDIV_QUERY)

	former_subdivs = set()

	for result in results["results"]["bindings"]:
		former_subdivs.add(result["city"]["value"].replace('http://www.wikidata.org/entity/', ''))

	results = run_sparql_query_with_504_retries(CHINA_CURRENT_SUBDIV_QUERY)

	for result in results["results"]["bindings"]:
		former_subdivs.remove(result["city"]["value"].replace('http://www.wikidata.org/entity/', ''))

	unwanted['subdivision'].update(former_subdivs)

	# Metropolitan areas are unwanted as cities/urban-areas and subdivisions
	print("Running query for unwanted metropolitan areas...")
	results = run_sparql_query_with_504_retries(UNWANTED_URBAN_AREA_QUERY)
	for result in results["results"]["bindings"]:
		qid = result["city"]["value"].replace('http://www.wikidata.org/entity/', '')
		unwanted['city'].add(qid)
		unwanted['subdivision'].add(qid)
	print(f"Number of unwanted metropolitan areas: {len(results['results']['bindings'])}")

	with open(PROCESSED_FILES['unwanted_dict'], 'wb') as f: 
		pickle.dump(unwanted, f)

	print(f"{PROCESSED_FILES['unwanted_dict']} created.") 
	return unwanted

def create_map_dict():
	"""Creates a dictionary of location map depicts -> map link and saves to map_dict.pkl."""
	pd.set_option('display.max_colwidth', None)
	pd.set_option('display.max_rows', None)

	results = run_sparql_query_with_504_retries(LOCATION_MAP_QUERY)

	database = []
	for result in results["results"]["bindings"]:
		database.append({
			"item": result["item"]["value"],
			"article": result["article"]["value"],
			"depicts": result["depicts"]["value"],
			"depictsLabel": result["depictsLabel"]["value"]
		})

	database = [d for d in database if not d['article'] in MAPS_TO_REMOVE]
	df = pd.DataFrame(database)
	df = df[~df['article'].str.endswith('/doc')]

	duplicates = df[df['depicts'].duplicated(keep=False)]
	if len(duplicates) > 0:
		print("Duplicates in depicts:")
		duplicates = duplicates.sort_values(by=['depictsLabel'])
		print(duplicates[['article', 'depictsLabel']])
	else:
		print("No duplicates")

	duplicates_article = df[df['article'].duplicated(keep=False)]
	if len(duplicates_article) > 0:
		print("*** Duplicates in articles:")
		print(duplicates_article)

	def select_preferred_article(group):
			# Check if any article starts with "https://en.wikipedia.org/wiki/Module:Location_map/data/"
			preferred = group[group['article'].str.startswith("https://en.wikipedia.org/wiki/Module:Location_map/data/")]
			if not preferred.empty:
					return preferred.loc[preferred['article'].str.len().idxmax()]  # Pick the longest among the preferred
			else:
					return group.loc[group['article'].str.len().idxmax()]  # Pick the longest overall

	# Use include_group_columns=False to address the warning properly
	df = df.groupby('depicts', group_keys=False).apply(select_preferred_article)

	# Reset the index if necessary
	df.reset_index(drop=True, inplace=True)

	map_dict = df.set_index('depicts')['article'].to_dict()

	for k, v in map_dict.items():
		map_dict[k] = unquote(v)

	with open(PROCESSED_FILES['map_dict'], 'wb') as f:
		pickle.dump(map_dict, f)

	print(f"{PROCESSED_FILES['map_dict']} created.")
	return map_dict

def create_map_hashmap_files():
	"""Creates both unwanted_dict.pkl and map_dict.pkl."""
	create_unwanted_dict()
	create_map_dict()