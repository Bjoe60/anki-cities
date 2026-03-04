import pandas as pd
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file1 = os.path.join(base_dir, "data", "output", "Cities of countries_header.csv")
file2 = os.path.join(base_dir, "data", "output", "Cities of countries_header original.csv")

df1 = pd.read_csv(file1, dtype=str, keep_default_na=False)
df2 = pd.read_csv(file2, dtype=str, keep_default_na=False)

differences_found = False

# Check shape differences
if df1.shape != df2.shape:
    differences_found = True
    print(f"Shape difference: {file1} has {df1.shape}, {file2} has {df2.shape}")

# Check column differences
if list(df1.columns) != list(df2.columns):
    differences_found = True
    only_in_1 = set(df1.columns) - set(df2.columns)
    only_in_2 = set(df2.columns) - set(df1.columns)
    if only_in_1:
        print(f"Columns only in file 1: {only_in_1}")
    if only_in_2:
        print(f"Columns only in file 2: {only_in_2}")
else:
    # Compare cell-by-cell on common rows/columns
    common_rows = min(len(df1), len(df2))
    diff_count = 0
    # ignore_cols = {"maps"}
    ignore_cols = {}
    set_compare_cols = {"tags"}

    for col in df1.columns:
        if col in ignore_cols:
            continue
        if col in set_compare_cols:
            s1 = df1[col].iloc[:common_rows].apply(lambda x: frozenset(x.split()) if x else frozenset())
            s2 = df2[col].iloc[:common_rows].apply(lambda x: frozenset(x.split()) if x else frozenset())
            mask = s1 != s2
        else:
            mask = df1[col].iloc[:common_rows] != df2[col].iloc[:common_rows]
        if mask.any():
            differences_found = True
            diff_indices = mask[mask].index.tolist()
            diff_count += len(diff_indices)
            for idx in diff_indices[:5]:  # Show up to 5 per column
                print(f"Row {idx}, Column '{col}': '{df1.at[idx, col]}' vs '{df2.at[idx, col]}'")
            if len(diff_indices) > 5:
                print(f"  ... and {len(diff_indices) - 5} more differences in column '{col}'")

    if diff_count:
        print(f"\nTotal differing cells: {diff_count}")

    # Check for extra rows
    if len(df1) > common_rows:
        differences_found = True
        print(f"\nFile 1 has {len(df1) - common_rows} extra rows")
    if len(df2) > common_rows:
        differences_found = True
        print(f"\nFile 2 has {len(df2) - common_rows} extra rows")

if not differences_found:
    print("No differences found between the two files.")
