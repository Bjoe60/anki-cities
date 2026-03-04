import pandas as pd

# Finds which rows that df2 is missing compared to df1
df1 = pd.read_csv("data/species with identificationfull.csv", dtype='unicode')
df2 = pd.read_csv("data/species with identification.csv", dtype='unicode')

# Use a left join to identify rows that are unique to df1
merged = df1.merge(df2, how='left', indicator=True)

# Filter rows that are only in df1
missing_rows = merged[merged['_merge'] == 'left_only']

# Drop the '_merge' column to clean up the output
df_diff = missing_rows.drop(columns=['_merge'])

print('df1:', len(df1))
print('df2:', len(df2))
print('df_diff:', len(df_diff))

df_diff.to_csv('dataframe diff.csv', index=False)