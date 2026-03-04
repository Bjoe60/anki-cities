import pandas as pd

pd.set_option('display.max_rows', None)

df = pd.read_csv('Cities of countries.csv', dtype='unicode')
print(df['actual_country'].value_counts())