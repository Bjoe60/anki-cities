import pandas as pd
import sys
import pickle
import time
from pathlib import Path
from urllib.error import URLError
# make project root importable so "src.file_paths" can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.file_paths import INPUT_FILES, PROCESSED_FILES
from SPARQLWrapper import SPARQLWrapper, JSON

geonames = pd.read_csv(INPUT_FILES['Geonames'], sep='\t', header=None, usecols=[0, 1, 6, 7, 8, 14], names=['geonameid', 'name', 'featureClass', 'featureCode', 'country',  'population'], dtype={'geonameid': 'Int64', 'name': str, 'featureClass': str, 'featureCode': str, 'country': str, 'population': 'unicode'})

# Filter for featureClass 'P' (populated places) or 'A' (administrative divisions)
populated_places = geonames[(geonames['featureClass'] == 'P') | (geonames['featureClass'] == 'A')]

print(f"Number of populated places: {len(populated_places)}")

with open(PROCESSED_FILES['unwanted_dict'], 'rb') as f: 
    unwanted = pickle.load(f)

# Find geonames IDs that are in the unwanted lists
unwanted_city_wikidata_ids = set(unwanted['city'])
# unwanted_subdivision_wikidata_ids = set(unwanted['subdivision'])
unwanted_subdivision_wikidata_ids = set()

unwanted_geonameids = set()
# Make SPARQL query to get geonameids for unwanted cities and subdivisions
sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent='Bjoe1839/1.0 (bjorn60@gmail.com) bot')
CHECKPOINT_FILE = Path(PROCESSED_FILES['unwanted_dict']).with_name('unwanted_geonames_checkpoint.pkl')
OUTPUT_CSV_FILE = Path(PROCESSED_FILES['unwanted_dict']).with_name('unwanted_geonames_wikidata_matches.csv')

all_unwanted_wikidata_ids = sorted(
    wid for wid in (unwanted_city_wikidata_ids | unwanted_subdivision_wikidata_ids)
    if isinstance(wid, str) and wid.startswith('Q')
)

def chunked(values, size):
    for start in range(0, len(values), size):
        yield values[start:start + size]


def is_transient_network_error(exc):
    error_code = getattr(exc, 'code', None)
    if error_code in {429, 502, 503, 504}:
        return True

    if isinstance(exc, URLError):
        reason = getattr(exc, 'reason', None)
        if isinstance(reason, OSError):
            return True
        return True

    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True

    return False


def load_checkpoint(expected_total_ids):
    if not CHECKPOINT_FILE.exists():
        return {
            'next_batch_index': 0,
            'mapped_wikidata_ids': set(),
            'unwanted_geonameids': set(),
            'mapping_pairs': set(),
        }

    with open(CHECKPOINT_FILE, 'rb') as f:
        checkpoint = pickle.load(f)

    if checkpoint.get('total_ids') != expected_total_ids:
        return {
            'next_batch_index': 0,
            'mapped_wikidata_ids': set(),
            'unwanted_geonameids': set(),
            'mapping_pairs': set(),
        }

    return {
        'next_batch_index': int(checkpoint.get('next_batch_index', 0)),
        'mapped_wikidata_ids': set(checkpoint.get('mapped_wikidata_ids', [])),
        'unwanted_geonameids': set(checkpoint.get('unwanted_geonameids', [])),
        'mapping_pairs': set(tuple(pair) for pair in checkpoint.get('mapping_pairs', [])),
    }


def save_checkpoint(next_batch_index, total_ids, mapped_ids, geoname_ids, mapping_pairs):
    checkpoint = {
        'next_batch_index': next_batch_index,
        'total_ids': total_ids,
        'mapped_wikidata_ids': sorted(mapped_ids),
        'unwanted_geonameids': sorted(geoname_ids),
        'mapping_pairs': sorted(mapping_pairs),
    }
    with open(CHECKPOINT_FILE, 'wb') as f:
        pickle.dump(checkpoint, f)


def run_sparql_query_with_retries(query, max_retries=5, base_delay_seconds=2):
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    for attempt in range(max_retries + 1):
        try:
            return sparql.query().convert()
        except Exception as e:
            if (not is_transient_network_error(e)) or attempt == max_retries:
                raise

            delay = base_delay_seconds * (2 ** attempt)
            print(f"SPARQL query failed ({e}). Retrying in {delay}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(delay)


batch_size = 200
chunks = list(chunked(all_unwanted_wikidata_ids, batch_size))
total_batches = len(chunks)

checkpoint = load_checkpoint(len(all_unwanted_wikidata_ids))
mapped_wikidata_ids = checkpoint['mapped_wikidata_ids']
unwanted_geonameids = checkpoint['unwanted_geonameids']
mapping_pairs = checkpoint['mapping_pairs']
start_batch_index = min(checkpoint['next_batch_index'], total_batches)

if start_batch_index > 0:
    print(f"Resuming from batch {start_batch_index + 1}/{max(total_batches, 1)}")

for batch_index in range(start_batch_index, total_batches):
    wikidata_chunk = chunks[batch_index]
    index = batch_index + 1
    print(f"Querying unwanted IDs batch {index}/{total_batches}")
    values = ' '.join(f"wd:{wid}" for wid in wikidata_chunk)
    query = f"""
    SELECT ?item ?geonameid WHERE {{
      VALUES ?item {{ {values} }}
      ?item wdt:P1566 ?geonameid .
    }}
    """
    try:
        results = run_sparql_query_with_retries(query)
    except Exception as e:
        save_checkpoint(batch_index, len(all_unwanted_wikidata_ids), mapped_wikidata_ids, unwanted_geonameids, mapping_pairs)
        print(f"Stopped at batch {index}/{total_batches} due to network issue: {e}")
        print(f"Progress saved to {CHECKPOINT_FILE}. Re-run to continue from this batch.")
        sys.exit(1)

    for result in results["results"]["bindings"]:
        item_value = result["item"]["value"]
        wikidata_id = item_value.rsplit('/', 1)[-1]
        mapped_wikidata_ids.add(wikidata_id)

        geonameid_value = result["geonameid"]["value"]
        try:
            geonameid_int = int(geonameid_value)
            unwanted_geonameids.add(geonameid_int)
            mapping_pairs.add((wikidata_id, geonameid_int))
        except ValueError:
            continue

    save_checkpoint(batch_index + 1, len(all_unwanted_wikidata_ids), mapped_wikidata_ids, unwanted_geonameids, mapping_pairs)

if CHECKPOINT_FILE.exists() and start_batch_index < total_batches:
    CHECKPOINT_FILE.unlink()

print(f"Unwanted Wikidata IDs: {len(all_unwanted_wikidata_ids)}")
print(f"Mapped to GeoNames IDs via Wikidata P1566: {len(mapped_wikidata_ids)}")
print(f"Unique unwanted GeoNames IDs found: {len(unwanted_geonameids)}")

unmapped_count = len(set(all_unwanted_wikidata_ids) - mapped_wikidata_ids)
print(f"Unwanted Wikidata IDs without P1566: {unmapped_count}")

mapping_df = pd.DataFrame(sorted(mapping_pairs), columns=['wikidata_id', 'geonameid'])
mapping_df['unwanted_type'] = mapping_df['wikidata_id'].apply(
    lambda wikidata_id: 'city' if wikidata_id in unwanted_city_wikidata_ids else 'subdivision'
)

unwanted_rows = populated_places[populated_places['geonameid'].isin(unwanted_geonameids)]
output_df = mapping_df.merge(unwanted_rows, on='geonameid', how='inner')
output_df = output_df[['geonameid', 'wikidata_id', 'unwanted_type', 'name', 'featureClass', 'featureCode', 'country', 'population']]
output_df['population'] = pd.to_numeric(output_df['population'], errors='coerce').fillna(0).astype(int)
output_df = output_df.sort_values(by=['population', 'unwanted_type', 'wikidata_id', 'geonameid'], ascending=[False, True, True, True])

output_df.to_csv(OUTPUT_CSV_FILE, index=False)

print(f"Saved full matched table to {OUTPUT_CSV_FILE}")
print(f"Rows saved: {len(output_df)}")