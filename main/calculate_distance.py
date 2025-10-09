# distance_calculator.py

import datetime

# 전역 변수 초기화
distance = 0.0
logging_start_time = None
previous_distance = 0.0

def calculate_distance(speed):
    global distance, logging_start_time, previous_distance

    if logging_start_time is None:
        logging_start_time = datetime.datetime.now()

    current_time = datetime.datetime.now()
    time_difference = current_time - logging_start_time
    time_difference_seconds = time_difference.total_seconds()
    current_distance = (speed / 3600) * time_difference_seconds

    distance = previous_distance + current_distance

    previous_distance = distance
    logging_start_time = current_time

    return distance

