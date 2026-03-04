import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON, SPARQLExceptions
from urllib.parse import unquote
import urllib.request
import time
import re
from file_paths import INPUT_FILES, PROCESSED_FILES, OUTPUT_FILES

# ALL: 66 mins

COUNTRIES = {
	'Q142': ('France', 'Q484170'),
	'Q148': ("People's Republic of China", ''), # Q1289426
	'Q30': ('United States of America', 'Q13360155'),
	'Q408': ('Australia', 'Q1867183'),

	'Q183': ('Germany', 'Q262166'),
	'Q34': ('Sweden', 'Q127448'),
	'Q29': ('Spain', 'Q2074737'),
	'Q889': ('Afghanistan', 'Q496825'),
	'Q262': ('Algeria', 'Q2989398'),
	'Q222': ('Albania', 'Q5154045'),
	'Q228': ('Andorra', 'Q24279'),
	'Q916': ('Angola', 'Q1841580'),
	'Q781': ('Antigua and Barbuda', 'Q1647142'),
	'Q414': ('Argentina', 'Q3243765'),
	'Q399': ('Armenia', 'Q3685430'),
	'Q40': ('Austria', 'Q667509'),
	'Q227': ('Azerbaijan', 'Q15129871'),
	'Q398': ('Bahrain', 'Q867606'),
	'Q902': ('Bangladesh', 'Q620471'),
	'Q244': ('Barbados', 'Q1631888'),
	'Q184': ('Belarus', 'Q2043199'),
	'Q31': ('Belgium', 'Q493522'),
	'Q242': ('Belize', ''),
	'Q962': ('Benin', 'Q1780506'),
	'Q917': ('Bhutan', ''),
	'Q750': ('Bolivia', 'Q1062710'),
	'Q225': ('Bosnia and Herzegovina', 'Q2706302'),
	'Q963': ('Botswana', ''),
	'Q155': ('Brazil', 'Q3184121'),
	'Q921': ('Brunei', 'Q60047'),
	'Q219': ('Bulgaria', 'Q1906268'),
	'Q965': ('Burkina Faso', 'Q2566190'),
	'Q967': ('Burundi', 'Q1577513'),
	'Q424': ('Cambodia', 'Q14846918'),
	'Q1009': ('Cameroon', 'Q3076994'),
	'Q16': ('Canada', ''),
	'Q1011': ('Cape Verde', 'Q12712989'),
	'Q929': ('Central African Republic', 'Q1911973'),
	'Q657': ('Chad', 'Q7630629'),
	'Q298': ('Chile', 'Q1840161'),
	'Q739': ('Colombia', 'Q2555896'),
	'Q970': ('Comoros', ''),
	'Q800': ('Costa Rica', 'Q953822'),
	'Q224': ('Croatia', 'Q57058'),
	'Q241': ('Cuba', 'Q558330'),
	'Q229': ('Cyprus', 'Q16739079'),
	'Q213': ('Czech Republic', 'Q5153359'),
	'Q974': ('Democratic Republic of the Congo', 'Q7703797'),
	'Q35': ('Denmark', 'Q2177636'),
	'Q977': ('Djibouti', ''),
	'Q784': ('Dominica', 'Q1405085'),
	'Q786': ('Dominican Republic', 'Q6005581'),
	'Q574': ('East Timor', 'Q1512109'),
	'Q736': ('Ecuador', 'Q2579179'),
	'Q79': ('Egypt', 'Q10577534'),
	'Q792': ('El Salvador', 'Q3556889'),
	'Q983': ('Equatorial Guinea', ''),
	'Q986': ('Eritrea', ''),
	'Q191': ('Estonia', 'Q612229'),
	'Q1050': ('Eswatini', 'Q2280192'),
	'Q115': ('Ethiopia', 'Q690840'),
	'Q702': ('Federated States of Micronesia', 'Q3327903'),
	'Q712': ('Fiji', ''),
	'Q33': ('Finland', 'Q856076'),
	'Q1000': ('Gabon', ''),
	'Q230': ('Georgia', 'Q2655841'),
	'Q117': ('Ghana', 'Q545769'),
	'Q41': ('Greece', 'Q1349648'),
	'Q769': ('Grenada', 'Q531645'),
	'Q774': ('Guatemala', 'Q1872284'),
	'Q1006': ('Guinea', 'Q1853398'),
	'Q1007': ('Guinea-Bissau', 'Q7444736'),
	'Q734': ('Guyana', ''),
	'Q790': ('Haiti', 'Q3685462'),
	'Q783': ('Honduras', 'Q2602693'),
	'Q28': ('Hungary', 'Q2590631'),
	'Q189': ('Iceland', 'Q955655'),
	'Q668': ('India', 'Q1149652'),
	'Q252': ('Indonesia', 'Q3191695'),
	'Q794': ('Iran', 'Q11353'),
	'Q796': ('Iraq', 'Q4117798'),
	'Q801': ('Israel', 'Q1288520'),
	'Q38': ('Italy', 'Q747074'),
	'Q1008': ('Ivory Coast', 'Q617807'),
	'Q766': ('Jamaica', 'Q936955'),
	'Q17': ('Japan', ''),
	'Q810': ('Jordan', ''),
	'Q232': ('Kazakhstan', 'Q2643128'),
	'Q114': ('Kenya', ''),
	'Q710': ('Kiribati', ''),
	'Q817': ('Kuwait', ''),
	'Q813': ('Kyrgyzstan', 'Q4389100'),
	'Q819': ('Laos', 'Q5283521'),
	'Q211': ('Latvia', ''),
	'Q822': ('Lebanon', 'Q6936383'),
	'Q1013': ('Lesotho', ''),
	'Q1014': ('Liberia', 'Q2421044'),
	'Q1016': ('Libya', 'Q16124843'),
	'Q347': ('Liechtenstein', 'Q203300'),
	'Q37': ('Lithuania', 'Q1363145'),
	'Q32': ('Luxembourg', 'Q2919801'),
	'Q1019': ('Madagascar', 'Q3192808'),
	'Q1020': ('Malawi', 'Q1058387'),
	'Q833': ('Malaysia', 'Q67925073'),
	'Q826': ('Maldives', 'Q23442'),
	'Q912': ('Mali', 'Q1758856'),
	'Q233': ('Malta', ''),
	'Q709': ('Marshall Islands', 'Q23442'),
	'Q1025': ('Mauritania', 'Q2989470'),
	'Q1027': ('Mauritius', ''),
	'Q96': ('Mexico', 'Q1952852'),
	'Q217': ('Moldova', 'Q4229812'),
	'Q711': ('Mongolia', 'Q1518096'),
	'Q236': ('Montenegro', 'Q838549'),
	'Q1028': ('Morocco', 'Q2989400'),
	'Q1029': ('Mozambique', 'Q2068214'),
	'Q836': ('Myanmar', 'Q7830262'),
	'Q1030': ('Namibia', ''),
	'Q697': ('Nauru', 'Q319796'),
	'Q837': ('Nepal', 'Q3492039'),
	'Q55': ('Netherlands', 'Q2039348'),
	'Q664': ('New Zealand', ''),
	'Q811': ('Nicaragua', 'Q318727'),
	'Q1032': ('Niger', 'Q605291'),
	'Q1033': ('Nigeria', 'Q1639634'),
	'Q423': ('North Korea', 'Q18544917'),
	'Q221': ('North Macedonia', 'Q646793'),
	'Q20': ('Norway', 'Q755707'),
	'Q842': ('Oman', 'Q3250615'),
	'Q843': ('Pakistan', 'Q18670606'),
	'Q695': ('Palau', ''),
	'Q804': ('Panama', 'Q3710488'),
	'Q691': ('Papua New Guinea', 'Q14942893'),
	'Q733': ('Paraguay', 'Q917092'),
	'Q419': ('Peru', 'Q2179958'),
	'Q928': ('Philippines', 'Q24764'),
	'Q36': ('Poland', 'Q15334'),
	'Q45': ('Portugal', 'Q13217644'),
	'Q846': ('Qatar', ''),
	'Q27': ('Ireland', ''),
	'Q971': ('Republic of the Congo', 'Q5154054'),
	'Q218': ('Romania', 'Q659103'),
	'Q159': ('Russia', ''),
	'Q1037': ('Rwanda', 'Q3058029'),
	'Q763': ('Saint Kitts and Nevis', ''),
	'Q760': ('Saint Lucia', ''),
	'Q757': ('Saint Vincent and the Grenadines', ''),
	'Q683': ('Samoa', 'Q23442'),
	'Q851': ('São Tomé and Príncipe', ''),
	'Q851': ('Saudi Arabia', 'Q66661665'),
	'Q1041': ('Senegal', 'Q2989649'),
	'Q403': ('Serbia', 'Q783930'),
	'Q1042': ('Seychelles', ''),
	'Q1044': ('Sierra Leone', ''),
	'Q334': ('Singapore', ''),
	'Q214': ('Slovakia', 'Q6784672'),
	'Q215': ('Slovenia', 'Q328584'),
	'Q685': ('Solomon Islands', ''),
	'Q1045': ('Somalia', 'Q18555638'),
	'Q258': ('South Africa', 'Q1500352'),
	'Q884': ('South Korea', 'Q24024848'),
	'Q958': ('South Sudan', ''),
	'Q854': ('Sri Lanka', 'Q1990968'),
	'Q1049': ('Sudan', 'Q505830'),
	'Q730': ('Suriname', 'Q1539014'),
	'Q39': ('Switzerland', 'Q70208'),
	'Q858': ('Syria', 'Q2915776'),
	'Q865': ('Taiwan', 'Q12081657'),
	'Q863': ('Tajikistan', 'Q6148126'),
	'Q924': ('Tanzania', 'Q2409750'),
	'Q869': ('Thailand', 'Q1077097'),
	'Q778': ('The Bahamas', ''),
	'Q1005': ('The Gambia', ''),
	'Q945': ('Togo', ''),
	'Q678': ('Tonga', ''),
	'Q754': ('Trinidad and Tobago', ''),
	'Q948': ('Tunisia', 'Q41067667'),
	'Q43': ('Turkey', 'Q1147395'),
	'Q874': ('Turkmenistan', 'Q5283544'),
	'Q672': ('Tuvalu', 'Q23442'),
	'Q1036': ('Uganda', 'Q7630601'),
	'Q212': ('Ukraine', 'Q104841013'),
	'Q878': ('United Arab Emirates', ''),
	'Q145': ('United Kingdom', ''),
	'Q77': ('Uruguay', 'Q3685434'),
	'Q265': ('Uzbekistan', 'Q2631599'),
	'Q686': ('Vanuatu', ''),
	'Q717': ('Venezuela', 'Q6063801'),
	'Q881': ('Vietnam', 'Q2389082'),
	'Q805': ('Yemen', 'Q6617100'),
	'Q953': ('Zambia', 'Q63241909'),
	'Q954': ('Zimbabwe', ''),
	'Q223': ('Greenland', ''),
	'Q1246': ('Kosovo', ''),
	'Q5785': ('Cayman Islands', 'Q23442'),
	'Q26988': ('Cook Islands', 'Q23442'),
	'Q4628': ('Faroe Islands', 'Q23442'),
	'Q25305': ('British Virgin Islands', 'Q23442'),
	# 'Q237': ('Vatican City', ''),
	# 'Q192184': ('Saint Helena, Ascension and Tristan da Cunha', ''),
	# 'Q25279': ('Curaçao', ''),
	# 'Q23635': ('Bermuda', ''),
	# 'Q21203': ('Aruba', ''),
	# 'Q36823': ('Tokelau', ''),
	# 'Q26273': ('Sint Maarten', ''),
	# 'Q34020': ('Niue', '')
}

# COUNTRIES = {
#     'Q35': ('Denmark', 'Q2177636'),
# }

filename = 'data/processed/All countries.csv'

CITY_ID = {'Q7930989': 'city', 'Q702492': 'urban-area'} # City or town, Urban area
N_QUERY = 70

FILTER_QUERIES = {('Q142', 'Q484170')} # Times out without population filter
POPULATION_FILTER = '?city wdt:P1082 ?pop . FILTER (?pop >= 1000) .'

IDS_QUERY = """
SELECT DISTINCT ?city WHERE {
	?city wdt:P31/wdt:P279* wd:%s.
	?city wdt:P17 wd:%s.
	?city wdt:P625 ?coords .
	?city rdfs:label ?cityLabel.
	FILTER(LANG(?cityLabel)="en").
}
"""

UNKNOWN_ENTITY = 'http://www.wikidata.org/entity/Q24238356'
UNKNOWN_QID = 'Q24238356'
WD_PREFIX = 'http://www.wikidata.org/entity/'
BATCH_SIZE = 300

_QID_RE = re.compile(r'^Q\d+$')
def is_valid_qid(qid):
	"""Check if a string is a valid Wikidata QID (Q followed by digits)."""
	return bool(_QID_RE.match(qid))

# Phase 1: Simplified city query - only gets direct subdivision (level 1), no nested chain.
# The 6-level subdivision chain is resolved separately in batch queries (Phase 3).
# Uses wdt:P131 (truthy/best-rank) instead of p:P131 with end-time filtering.
CITY_QUERY = """
SELECT DISTINCT
(?city AS ?wikidata_id)
(?cityLabel AS ?city)
(GROUP_CONCAT(DISTINCT ?sd; separator="|") AS ?sds)
(GROUP_CONCAT(DISTINCT ?sdLabel; separator="|") AS ?sdLabels)
(GROUP_CONCAT(DISTINCT ?nativeLabel; separator="/") AS ?nativeLabels)
(GROUP_CONCAT(DISTINCT ?phy1; separator="|") AS ?phys1)
(GROUP_CONCAT(DISTINCT ?phy1Label; separator="|") AS ?phy1Labels)
(GROUP_CONCAT(DISTINCT ?part; separator="|") AS ?parts)
(GROUP_CONCAT(DISTINCT ?partLabel; separator="|") AS ?partLabels)
(SAMPLE(?pop) AS ?population)
(SAMPLE(?coords_) AS ?coords)
(SAMPLE(?gn) AS ?geonameid)
(SAMPLE(?article_) AS ?wikipedia_url)
WHERE {
  ?city wdt:P31/wdt:P279* wd:%s ;
        wdt:P17 wd:%s ;
        wdt:P625 ?coords_ .
  %s
  OPTIONAL { ?city wdt:P131 ?sd . }
  OPTIONAL { ?city wdt:P1082 ?pop . }
  OPTIONAL { ?city wdt:P1566 ?gn . }
  OPTIONAL { ?city wdt:P1705 ?native . }
  OPTIONAL { ?city wdt:P706 ?phy1 . }
  OPTIONAL { ?city wdt:P361 ?part . }
  OPTIONAL {
    ?article_ schema:about ?city ;
              schema:isPartOf <https://en.wikipedia.org/> .
  }
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en" .
    ?city rdfs:label ?cityLabel .
    ?sd rdfs:label ?sdLabel .
    ?phy1 rdfs:label ?phy1Label .
    ?part rdfs:label ?partLabel .
    ?native rdfs:label ?nativeLabel .
  }
}
GROUP BY ?city ?cityLabel
"""

# Compress CITY_QUERY
CITY_QUERY = ' '.join(line.strip().replace(' .', '.') for line in CITY_QUERY.split('\n') if line.strip() and '#' not in line)

# Phase 3: Resolve subdivision parent chains (P131) in batches
PARENT_QUERY = """
SELECT ?sd ?parent WHERE {
  VALUES ?sd { %s }
  ?sd wdt:P131 ?parent .
}
"""

# Phase 3b: Get country (P17) for level-1 subdivisions with end-time filtering
P17_QUERY = """
SELECT ?sd ?subCountry WHERE {
  VALUES ?sd { %s }
  ?sd p:P17 ?sc .
  ?sc ps:P17 ?subCountry .
  OPTIONAL { ?sc pq:P582 ?ec . }
  FILTER(!BOUND(?ec))
}
"""

# Phase 3c: Get physical features (P706) for level-1 subdivisions
P706_QUERY = """
SELECT ?sd ?phy WHERE {
  VALUES ?sd { %s }
  ?sd wdt:P706 ?phy .
}
"""

# Phase 3d: Resolve best population (latest by point-in-time) for cities
# Excludes deprecated ranks and statements qualified with:
#   P1539 (female pop), P1540 (male pop), P1538 (households)
# P518 (applies to part) is fetched but soft-filtered in Python:
#   prefer statements without it, but fall back if all have it.
POPULATION_BEST_QUERY = """
SELECT ?city ?pop ?pit ?rank (BOUND(?atp) AS ?hasApliesToPart) WHERE {
  VALUES ?city { %s }
  ?city p:P1082 ?stmt .
  ?stmt wikibase:rank ?rank .
  FILTER(?rank != wikibase:DeprecatedRank)
  ?stmt ps:P1082 ?pop .
  FILTER NOT EXISTS { ?stmt pq:P1539 [] }
  FILTER NOT EXISTS { ?stmt pq:P1540 [] }
  FILTER NOT EXISTS { ?stmt pq:P1538 [] }
  OPTIONAL { ?stmt pq:P518 ?atp . }
  OPTIONAL { ?stmt pq:P585 ?pit . }
}
"""

# Phase 4: Resolve English labels for all entities encountered
LABEL_QUERY = """
SELECT ?entity ?entityLabel WHERE {
  VALUES ?entity { %s }
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en" .
    ?entity rdfs:label ?entityLabel .
  }
}
"""


sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent='Bjoe1839/1.0 (bjorn60@gmail.com) bot')
sparql.setMethod('POST')
sparql.setTimeout(600000)
sparql.addExtraURITag("timeout", "600000")


def run_sparql(query, retries=5):
	"""Execute SPARQL query with retry logic and exponential backoff. Returns results dict or None."""
	sparql.setQuery(query)
	sparql.setReturnFormat(JSON)
	for attempt in range(retries + 1):
		try:
			return sparql.query().convert()
		except Exception as e:
			if attempt < retries:
				delay = min(2 ** attempt, 4)  # 1, 2, 4
				print(f'*({delay}s, {e})', end=' ', flush=True)
				time.sleep(delay)
				sparql.setQuery(query + ' ' * (attempt + 1))
			else:
				print(f"*** TIMED OUT: {e}")
				print(query)
				return None
	return None


def batch_sparql(query_template, qids, batch_size=BATCH_SIZE):
	"""Run a SPARQL query in batches using VALUES clause. Retries failed batches at the end."""
	all_bindings = []
	qids = list(qids)
	if not qids:
		return all_bindings
	failed_batches = []  # (start_index, batch) tuples for retry
	n_batches = (len(qids) - 1) // batch_size + 1
	for i in range(0, len(qids), batch_size):
		batch = qids[i:i+batch_size]
		values_str = ' '.join(f'wd:{qid}' for qid in batch)
		result = run_sparql(query_template % values_str)
		if result and "results" in result:
			all_bindings.extend(result["results"]["bindings"])
		else:
			failed_batches.append(batch)
		if n_batches > 1:
			print(f'  batch {i//batch_size + 1}/{n_batches}', end='', flush=True)
	# Retry failed batches with smaller sub-batches
	if failed_batches:
		sub_batch_size = max(batch_size // 6, 10)
		total_qids = sum(len(b) for b in failed_batches)
		print(f'\n  Retrying {len(failed_batches)} failed batches ({total_qids} qids) in sub-batches of {sub_batch_size}...', end='', flush=True)
		time.sleep(30)
		still_failed = 0
		for batch in failed_batches:
			for j in range(0, len(batch), sub_batch_size):
				sub = batch[j:j+sub_batch_size]
				values_str = ' '.join(f'wd:{qid}' for qid in sub)
				result = run_sparql(query_template % values_str)
				if result and "results" in result:
					all_bindings.extend(result["results"]["bindings"])
				else:
					still_failed += len(sub)
			print('.', end='', flush=True)
		if still_failed:
			print(f' ({still_failed} qids still failed)', end='', flush=True)
	return all_bindings


def create_all_countries_dataframe():
	start_time = time.time()

	# ===== Phase 1: Query all cities with simplified query =====
	print("===== Phase 1: Querying cities =====")
	all_city_data = []  # List of (bindings, urban_type, country_id, country_label)

	for i, current_country in enumerate(COUNTRIES):
		print('\n' + str(i), COUNTRIES[current_country][0], end=" ", flush=True)
		urban_sub_ids = CITY_ID.copy()
		if COUNTRIES[current_country][1]:
			urban_sub_ids[COUNTRIES[current_country][1]] = 'subdivision'

		for urban_sub_id in urban_sub_ids:
			urban_type = urban_sub_ids[urban_sub_id]
			print(urban_type, end=" ", flush=True)

			extra_filter = POPULATION_FILTER if (current_country, urban_sub_id) in FILTER_QUERIES else ''

			# Try direct query first
			result = run_sparql(CITY_QUERY % (urban_sub_id, current_country, extra_filter))

			if result and "results" in result:
				bindings = result["results"]["bindings"]
				all_city_data.append((bindings, urban_type, current_country, COUNTRIES[current_country][0]))
				print(f'({len(bindings)})', end=' ', flush=True)
			else:
				# Fallback: get IDs first, then query in batches using CITY_QUERY
				print("-> batch fallback", end=" ", flush=True)
				ids_result = run_sparql(IDS_QUERY % (urban_sub_id, current_country))
				if ids_result and "results" in ids_result:
					all_ids = [r["city"]["value"].replace(WD_PREFIX, '') for r in ids_result["results"]["bindings"]]
					print(f'({len(all_ids)} ids)', end=' ', flush=True)
					all_bindings = []
					while all_ids:
						current_ids, all_ids = all_ids[:N_QUERY], all_ids[N_QUERY:]
						filter_str = 'FILTER(' + '||'.join(f'?city=wd:{id}' for id in current_ids) + ').'
						batch_result = run_sparql(CITY_QUERY % (urban_sub_id, current_country, filter_str))
						if batch_result and "results" in batch_result:
							all_bindings.extend(batch_result["results"]["bindings"])
						if all_ids:
							print(len(all_ids), end=' ', flush=True)
					if all_bindings:
						all_city_data.append((all_bindings, urban_type, current_country, COUNTRIES[current_country][0]))
					print(f'({len(all_bindings)})', end=' ', flush=True)

	# ===== Phase 2: Collect unique level-1 subdivision QIDs =====
	print("\n\n===== Phase 2: Collecting subdivisions =====")
	all_sd_qids = set()
	for bindings, _, _, _ in all_city_data:
		for b in bindings:
			sds_str = b.get("sds", {}).get("value", "")
			if sds_str:
				for uri in sds_str.split("|"):
					qid = uri.replace(WD_PREFIX, '')
					if qid and is_valid_qid(qid):
						all_sd_qids.add(qid)

	print(f"Found {len(all_sd_qids)} unique level-1 subdivisions")

	# ===== Phase 3: Resolve subdivision parent chains =====
	print("\n===== Phase 3: Resolving subdivision chains =====")
	parent_map = {}  # qid -> parent_qid (or None if no parent)
	current_level_qids = set(all_sd_qids)

	for depth in range(5):  # Up to 5 more levels (total 6 including level 1)
		to_resolve = current_level_qids - set(parent_map.keys())
		if not to_resolve:
			break

		print(f"\n  Chain level {depth + 2} ({len(to_resolve)} entities):", end='', flush=True)
		bindings = batch_sparql(PARENT_QUERY, to_resolve)

		next_level_qids = set()
		for b in bindings:
			sd_qid = b['sd']['value'].replace(WD_PREFIX, '')
			parent_qid = b['parent']['value'].replace(WD_PREFIX, '')
			if sd_qid not in parent_map and is_valid_qid(parent_qid):
				parent_map[sd_qid] = parent_qid
				next_level_qids.add(parent_qid)

		# Mark entities with no parent result as having no parent
		for qid in to_resolve:
			if qid not in parent_map:
				parent_map[qid] = None

		current_level_qids = next_level_qids

	# Get P17 (country) for level-1 subdivisions
	print(f"\n\n  P17 (country) for {len(all_sd_qids)} subdivisions:", end='', flush=True)
	p17_map = {}  # qid -> country_qid
	for b in batch_sparql(P17_QUERY, all_sd_qids):
		sd_qid = b['sd']['value'].replace(WD_PREFIX, '')
		country_qid = b['subCountry']['value'].replace(WD_PREFIX, '')
		if sd_qid not in p17_map and is_valid_qid(country_qid):
			p17_map[sd_qid] = country_qid

	# Get P706 (physical features) for level-1 subdivisions
	print(f"\n  P706 (physical) for {len(all_sd_qids)} subdivisions:", end='', flush=True)
	p706_map = {}  # qid -> [physical_qids]
	for b in batch_sparql(P706_QUERY, all_sd_qids):
		sd_qid = b['sd']['value'].replace(WD_PREFIX, '')
		phy_qid = b['phy']['value'].replace(WD_PREFIX, '')
		if not is_valid_qid(phy_qid):
			continue
		if sd_qid not in p706_map:
			p706_map[sd_qid] = []
		if phy_qid not in p706_map[sd_qid]:
			p706_map[sd_qid].append(phy_qid)

	# ===== Phase 3d: Resolve best population (latest point-in-time) =====
	print("\n\n===== Phase 3d: Resolving best populations =====")
	all_city_qids = set()
	for bindings, _, _, _ in all_city_data:
		for b in bindings:
			city_qid = b["wikidata_id"]["value"].replace(WD_PREFIX, '')
			all_city_qids.add(city_qid)

	print(f"  Population for {len(all_city_qids)} cities:", end='', flush=True)
	# Collect all (city, pop, pit, is_preferred, has_applies_to_part) tuples
	pop_candidates = {}  # qid -> [(pop_value, pit_value_or_empty, is_preferred, has_atp)]
	for b in batch_sparql(POPULATION_BEST_QUERY, all_city_qids):
		city_qid = b['city']['value'].replace(WD_PREFIX, '')
		pop_val = b['pop']['value']
		pit_val = b.get('pit', {}).get('value', '')
		is_preferred = b['rank']['value'] == 'http://wikiba.se/ontology#PreferredRank'
		has_atp = b['hasApliesToPart']['value'] == 'true'
		if city_qid not in pop_candidates:
			pop_candidates[city_qid] = []
		pop_candidates[city_qid].append((pop_val, pit_val, is_preferred, has_atp))

	# Selection priority for each city:
	#   1. Prefer PreferredRank; fall back to NormalRank if none preferred
	#   2. Within that pool, prefer statements WITHOUT "applies to part" (P518)
	#      but fall back to those with it if all have it
	#   3. Pick the one with the latest point-in-time
	best_pop = {}  # qid -> pop_value
	for qid, candidates in pop_candidates.items():
		# Step 1: rank filter
		preferred = [c for c in candidates if c[2]]
		pool = preferred if preferred else candidates
		# Step 2: soft-filter applies-to-part
		without_atp = [c for c in pool if not c[3]]
		pool = without_atp if without_atp else pool
		# Step 3: latest point-in-time
		if len(pool) == 1:
			best_pop[qid] = pool[0][0]
		else:
			pool.sort(key=lambda x: x[1] if x[1] else '', reverse=True)
			best_pop[qid] = pool[0][0]
	print(f" resolved {len(best_pop)} cities")

	# ===== Phase 4: Resolve labels for ALL entities =====
	print("\n===== Phase 4: Resolving labels =====")
	all_entity_qids = set(all_sd_qids)
	all_entity_qids.add(UNKNOWN_QID)

	# Add country QIDs so we get Wikidata labels for countries
	for _, _, cid, _ in all_city_data:
		all_entity_qids.add(cid)

	# Add chain parents at all levels
	for parent_qid in parent_map.values():
		if parent_qid:
			all_entity_qids.add(parent_qid)

	# Add P17 country values
	for country_qid in p17_map.values():
		all_entity_qids.add(country_qid)

	# Add P706 physical values
	for phys in p706_map.values():
		all_entity_qids.update(phys)

	# Walk all chains to collect every entity at every level
	for bindings, _, _, _ in all_city_data:
		for b in bindings:
			sds_str = b.get("sds", {}).get("value", "")
			if sds_str:
				for uri in sds_str.split("|"):
					current = uri.replace(WD_PREFIX, '')
					for _ in range(5):
						parent = parent_map.get(current)
						if parent:
							all_entity_qids.add(parent)
							current = parent
						else:
							break

	# Safety: filter out any blank-node / invalid QIDs before batch query
	all_entity_qids = {q for q in all_entity_qids if is_valid_qid(q)}
	print(f"  Labels for {len(all_entity_qids)} entities:", end='', flush=True)
	label_map = {}  # qid -> label
	for b in batch_sparql(LABEL_QUERY, all_entity_qids, batch_size=500):
		qid = b['entity']['value'].replace(WD_PREFIX, '')
		label_map[qid] = b['entityLabel']['value']

	# ===== Phase 5: Assemble database =====
	print("\n\n===== Phase 5: Assembling database =====")
	database = []
	unknown_label = label_map.get(UNKNOWN_QID, UNKNOWN_QID)

	for bindings, urban_type, country_id, country_label in all_city_data:
		for b in bindings:
			# Get level-1 subdivision URIs and labels from CITY_QUERY
			sds_str = b.get("sds", {}).get("value", "")
			sd_labels_str = b.get("sdLabels", {}).get("value", "")

			if sds_str:
				sd_uris = sds_str.split("|")
				sd_labels_list = sd_labels_str.split("|") if sd_labels_str else []
			else:
				sd_uris = []
				sd_labels_list = []

			# Build chains for each direct subdivision
			# Each chain = [(uri, label), ...] up to 6 levels
			chains = []
			for idx, sd_uri in enumerate(sd_uris):
				sd_qid = sd_uri.replace(WD_PREFIX, '')
				if not is_valid_qid(sd_qid):
					continue  # Skip blank nodes / invalid URIs
				sd_label = sd_labels_list[idx] if idx < len(sd_labels_list) else label_map.get(sd_qid, sd_qid)

				chain = [(sd_uri, sd_label)]
				current = sd_qid
				for _ in range(5):
					parent_qid = parent_map.get(current)
					if parent_qid:
						parent_uri = WD_PREFIX + parent_qid
						parent_label = label_map.get(parent_qid, parent_qid)
						chain.append((parent_uri, parent_label))
						current = parent_qid
					else:
						break

				# Pad to 6 levels with UNKNOWN_ENTITY
				while len(chain) < 6:
					chain.append((UNKNOWN_ENTITY, unknown_label))
				chains.append(chain[:6])

			if not chains:
				chains = [[(UNKNOWN_ENTITY, unknown_label)] * 6]

			# Build aligned pipe-separated strings for each level
			subdivisions = [''] * 6
			subdivision_labels = [''] * 6
			for level in range(6):
				uris = [chain[level][0] for chain in chains]
				labels = [chain[level][1] for chain in chains]
				subdivisions[level] = '|'.join(uris)
				subdivision_labels[level] = '|'.join(labels)

			# Sub-country labels from level-1 subdivisions
			sub_country_labels = []
			for chain in chains:
				sd0_qid = chain[0][0].replace(WD_PREFIX, '')
				if sd0_qid != UNKNOWN_QID:
					sc_qid = p17_map.get(sd0_qid)
					if sc_qid:
						sub_country_labels.append(label_map.get(sc_qid, sc_qid))
					else:
						sub_country_labels.append(unknown_label)
				else:
					sub_country_labels.append(unknown_label)

			# Physicals2 from level-1 subdivisions (P706 of the subdivision)
			physicals2_uris = []
			physical2_labels_list = []
			for chain in chains:
				sd0_qid = chain[0][0].replace(WD_PREFIX, '')
				if sd0_qid in p706_map:
					for phy_qid in p706_map[sd0_qid]:
						uri = WD_PREFIX + phy_qid
						if uri not in physicals2_uris:
							physicals2_uris.append(uri)
							physical2_labels_list.append(label_map.get(phy_qid, phy_qid))

			database.append({
				"wikidata_id": b["wikidata_id"]["value"],
				"city": b["city"]["value"],
				"subdivisions": subdivisions[0],
				"subdivisions2": subdivisions[1],
				"subdivisions3": subdivisions[2],
				"subdivisions4": subdivisions[3],
				"subdivisions5": subdivisions[4],
				"subdivisions6": subdivisions[5],
				"subdivisionLabels": subdivision_labels[0],
				"subdivision2Labels": subdivision_labels[1],
				"subdivision3Labels": subdivision_labels[2],
				"subdivision4Labels": subdivision_labels[3],
				"subdivision5Labels": subdivision_labels[4],
				"subdivision6Labels": subdivision_labels[5],
				"sub_countryLabels": '|'.join(sub_country_labels),
				"native": b.get("nativeLabels", {}).get("value") or None,
				"physicals": b.get("phys1", {}).get("value") or None,
				"physicalLabels": b.get("phy1Labels", {}).get("value") or None,
				"physicals2": '|'.join(physicals2_uris) if physicals2_uris else None,
				"physical2Labels": '|'.join(physical2_labels_list) if physical2_labels_list else None,
				"partofs": b.get("parts", {}).get("value") or None,
				"partofLabels": b.get("partLabels", {}).get("value") or None,
				"population": best_pop.get(b["wikidata_id"]["value"].replace(WD_PREFIX, ''), b.get("population", {}).get("value") if "population" in b else None),
				"geonameid": b.get("geonameid", {}).get("value") if "geonameid" in b else None,
				"coords": b["coords"]["value"],
				"type": urban_type,
				"wikipedia_url": b.get("wikipedia_url", {}).get("value") if "wikipedia_url" in b else None,
				"country": WD_PREFIX + country_id,
				"countryLabel": label_map.get(country_id, country_label)
			})

		print(f'  {country_label} ({urban_type}): {len(bindings)} cities')

	# ===== Phase 6: Create and save dataframe =====
	print("\nCreating dataframe")
	df = pd.DataFrame(database)
	print("Dataframe created")

	df['wikidata_id'] = df['wikidata_id'].str.replace(WD_PREFIX, '', regex=False)
	df['wikipedia_url'] = df['wikipedia_url'].str.replace('https://en.wikipedia.org/wiki/', '', regex=False)
	df['wikipedia_url'] = df['wikipedia_url'].apply(lambda x: unquote(str(x)).replace('_', ' ') if not pd.isnull(x) else x)

	df.to_csv(filename, index=False)
	print()
	print(time.time() - start_time, 'seconds')