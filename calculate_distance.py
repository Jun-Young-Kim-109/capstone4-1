"""주행 속도를 바탕으로 이동 거리를 근사 계산하는 도우미 함수."""

import datetime

# 전역 변수 초기화: 계산 결과를 누적하기 위해 이전 상태를 기억합니다.
distance = 0.0
logging_start_time = None
previous_distance = 0.0


def calculate_distance(speed):
    """마지막 호출 이후 경과 시간과 속도를 이용해 이동 거리를 누적합니다."""

    global distance, logging_start_time, previous_distance

    if logging_start_time is None:
        logging_start_time = datetime.datetime.now()

    current_time = datetime.datetime.now()
    time_difference = current_time - logging_start_time
    time_difference_seconds = time_difference.total_seconds()

    # 속도(km/h)를 m/s로 변환하지 않고 시간(초)을 이용해 km 단위 거리를 추정합니다.
    current_distance = (speed / 3600) * time_difference_seconds

    distance = previous_distance + current_distance

    previous_distance = distance
    logging_start_time = current_time

    return distance


if __name__ == "__main__":
    # 60 km/h로 1초 동안 이동했을 때의 거리를 간단히 출력합니다.
    print(calculate_distance(60))
