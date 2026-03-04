import pandas as pd

duplicate_check = 'wikipedia_id'
df = pd.read_csv('dbpedia.csv', dtype='unicode')
df = df[df.duplicated(subset=[duplicate_check], keep=False)].drop_duplicates(subset=[duplicate_check])
df = df.sort_values(duplicate_check)
for i in df[duplicate_check]:
    print(i)