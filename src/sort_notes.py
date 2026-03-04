import pandas as pd
import csv
from file_paths import INPUT_FILES, OUTPUT_FILES

# Sorts the rows of exported deck (to keep order when first downloaded)
# Assuming exported notes as .txt with all options selected

def sort_cities_notes():
    header = '''#separator:tab
#html:true
#guid column:1
#notetype column:2
#deck column:3
#tags column:10\n''' # Remember newline at the end

    # File paths for the two CSV files
    file1 = INPUT_FILES['Notes']
    file2 = OUTPUT_FILES['Cities of countries_header']
    output_file = OUTPUT_FILES['Cities of countries sorted']

    try:
        # Load both CSV files
        df1_header = pd.read_csv(file1, sep='\t', header=None, nrows=6)
        df1 = pd.read_csv(file1, sep='\t', header=None, skiprows=6, dtype='unicode')
        df2 = pd.read_csv(file2, usecols=['wikidata_id', 'countryLabel', 'type', 'population'], dtype='unicode')

        # Extract the columns to use for merging and sorting
        key_column_file1 = df1.columns[3]
        tags_column = int(df1_header.iloc[5, 0][13:]) - 1

        # Merge df1 with the sorting column from df2 based on the key columns
        merged_df = pd.merge(df1, df2, left_on=key_column_file1, right_on='wikidata_id', how='left')

        # Sort the merged dataframe by type and population (country as tie-breaker)
        if 'population' in merged_df.columns:
            merged_df['population'] = merged_df['population'].str.replace(',', '', regex=False)
            merged_df['population'] = pd.to_numeric(merged_df['population'], errors='coerce').astype('Int64')
            type_order = {'city': 0, 'urban-area': 0, 'subdivision': 1}
            merged_df['type_sort'] = merged_df['type'].apply(
                lambda t: min(type_order.get(x, 99) for x in str(t).split('|')) if pd.notnull(t) else 99
            )
            merged_df = merged_df.sort_values(by=['type_sort', 'population', 'countryLabel'], ascending=[True, False, True])
            merged_df = merged_df.drop(columns=['type_sort'])
            merged_df['population'] = merged_df['population'].astype(object)
            merged_df['population'] = merged_df['population'].apply(lambda x: f'{x:,}' if not pd.isnull(x) else x) # Add decimal separators "1,000,000"

        # Drop the merge key column from df2 if you only want the original df1 columns
        # Drop any extra columns added by the merge if only original df1 columns are desired
        merged_df = merged_df[df1.columns]

        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            # Write the header text at the beginning of the file
            f.write(header)

            # Save the DataFrame to the file without the index
            merged_df.to_csv(f, index=False, encoding='utf-8', header=False, sep='\t', escapechar='\\', quoting=csv.QUOTE_STRINGS)

        print(f"Successfully sorted notes and saved to: {output_file}")

    except FileNotFoundError:
        print("Error: One or both input files not found. Please check the file paths in filepath_config.py.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    sort_cities_notes()