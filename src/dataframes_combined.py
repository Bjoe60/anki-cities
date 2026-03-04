import pandas as pd
import numpy as np
from urllib.parse import unquote
import pickle
from file_paths import INPUT_FILES, PROCESSED_FILES, OUTPUT_FILES

def create_dataframes_combined():
    df_wikidata = pd.read_csv('data/processed/All countries.csv', dtype='unicode', keep_default_na=False, na_values=[''])
    df_dbpedia = pd.read_csv(PROCESSED_FILES['DBPedia'], dtype='unicode') 

    # Merge
    df = pd.merge(df_wikidata, df_dbpedia, left_on='wikipedia_url', right_on='wikipedia_id', how='left', suffixes=('_wikidata', '_dbpedia'))

    # Loading list of unwanted cities
    with open(PROCESSED_FILES['unwanted_dict'], 'rb') as f: 
        unwanted = pickle.load(f)

    print(len(df.index), 'rows before filtering')
    # Removing unwanted cities
    df = df[~(df['type'].isin(['city', 'urban-area']) & df['wikidata_id'].isin(unwanted['city']))]
    df = df[~((df['type'] == 'subdivision') & df['wikidata_id'].isin(unwanted['subdivision']))]
    # Remove Q7473516 (Tokyo duplicate)
    df = df[~df['wikidata_id'].isin(['Q7473516'])]
    # Keep only urban-areas that are on Geonames
    df = df[~((df['type'] == 'urban-area') & (df['geonameid'].isna()))]
    df = df[~df['city'].str.endswith(' area')]
    df = df[~df['city'].str.endswith(' Area')]
    df = df[~df['city'].str.startswith('Greater')]

    # Merge duplicate wikidata_id rows, combining their types
    type_merged = df.groupby('wikidata_id')['type'].apply(lambda ts: '|'.join(sorted(set(ts)))).reset_index()
    df = df.drop_duplicates(subset='wikidata_id', keep='first').drop(columns='type')
    df = df.merge(type_merged, on='wikidata_id')

    # Choose sample from population
    df['population_dbpedia'] = df['population_dbpedia'].apply(lambda x: x.split('|')[0] if isinstance(x, str) and not len(x.split('|')) > 3 else pd.NA)
    df.loc[df['population_wikidata'] == 'http://www.wikidata.org/.well-known/genid/87cd17fb88bb3fc7650e83dcb98fba7b', 'population_wikidata'] = pd.NA # Remove "unknown" values
    df['population_wikidata'] = df['population_wikidata'].fillna(df['population_dbpedia'])
    df['native_dbpedia'] = df['native_dbpedia'].apply(lambda x: '/'.join([s for s in x.split('|') if s and s != '/']) if not pd.isnull(x) else x)
    df['native_wikidata'] = df['native_wikidata'].fillna(df['native_dbpedia'])
    df['native_wikidata'] = df['native_wikidata'].replace('.', '')

    # Delete rows with no label on wikidata
    df = df[~df['city'].str.match(r'^Q\d+$')]
    df = df.drop(df[df['coords'].str.match('http')].index)

    # Rename/delete columns
    df = df.drop(['native_dbpedia', 'population_dbpedia', 'wikipedia_id'], axis=1)
    df = df.rename(columns={'native_wikidata': 'native', 'population_wikidata': 'population'})

    print(len(df.index), 'rows after filtering')

    df.to_csv(PROCESSED_FILES['All countries combined'], index=False) 