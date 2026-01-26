import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(BASE_DIR, "data", "data.xml")
STOPWORDS_FILE = os.path.join(BASE_DIR, "stopwords_arabic.txt")
PROTECTED_WORDS_FILE = os.path.join(BASE_DIR, "protected_words.txt")

QUERIES_BOOLEAN = os.path.join(BASE_DIR, "queries", "queries.boolean.txt")
QUERIES_RANKED = os.path.join(BASE_DIR, "queries", "queries.ranked.txt")

OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
INDEX_FILE = os.path.join(OUTPUT_DIR, "index.txt")
RESULTS_BOOLEAN_FILE = os.path.join(OUTPUT_DIR, "results.boolean.txt")
RESULTS_RANKED_FILE = os.path.join(OUTPUT_DIR, "results.ranked.txt")

TOP_K_RESULTS = 500
DEFAULT_PROXIMITY_DISTANCE = 15
USE_BM25 = True
BM25_K1 = 1.2
BM25_B = 0.75
PROTECT_WORDS = True

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "queries"), exist_ok=True)