import pickle
import sys
from pathlib import Path
from urllib.error import URLError
# make project root importable so "src.file_paths" can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.file_paths import PROCESSED_FILES

with open(PROCESSED_FILES['unwanted_dict'], 'rb') as f:
    unwanted = pickle.load(f)

check = 'Q49231'

print(check in unwanted['city'], check in unwanted['subdivision'])