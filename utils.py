from config import INPUT_COST_PER_TOKEN, OUTPUT_COST_PER_TOKEN

def calculate_cost(input_tokens, output_tokens):
    input_cost = input_tokens * INPUT_COST_PER_TOKEN
    output_cost = output_tokens * OUTPUT_COST_PER_TOKEN
    return input_cost + output_cost