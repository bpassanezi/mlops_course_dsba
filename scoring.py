
# Define very simple room for scoring
def scoring_function(surface: float, num_rooms: float = 0) -> int:
    current_value = 10
    if surface > 50:
        current_value += 100
    if num_rooms >= 2:
        current_value = current_value*2

    return current_value