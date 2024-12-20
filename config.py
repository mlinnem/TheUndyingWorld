import os

INPUT_COST_PER_TOKEN = 3 / 1_000_000  # $3 per 1 million tokens
OUTPUT_COST_PER_TOKEN = 15 / 1_000_000  # $15 per 1 million tokens
MAX_CONTEXT_TOKENS = 200_000
MAX_OUTPUT_TOKENS = 8192
CACHE_POINT_TRIGGER_TOKEN_COUNT = 9000
PROMPTS_FILE = "prompts.json"

# Ensure the prompts file exists
if not os.path.exists(PROMPTS_FILE):
    with open(PROMPTS_FILE, 'w') as f:
        f.write('{}')