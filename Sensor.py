"""자이로스코프와 충돌 센서 상태를 주기적으로 출력하는 스크립트."""

import time

import gyro_sensor
import collision_sensor
import wiringpi
from wiringpi import GPIO


def _print_gyro_data(gyro_data):
    """센서에서 읽은 자이로스코프 및 가속도 정보를 보기 좋게 출력합니다."""

    print("자이로스코프 데이터")
    print("------------------")
    print(f"자이로 X축: {gyro_data['gyro_xout']}, 스케일 조정: {gyro_data['gyro_xout'] / 131}")
    print(f"자이로 Y축: {gyro_data['gyro_yout']}, 스케일 조정: {gyro_data['gyro_yout'] / 131}")
    print(f"자이로 Z축: {gyro_data['gyro_zout']}, 스케일 조정: {gyro_data['gyro_zout'] / 131}")

    print("\n가속도계 데이터")
    print("----------------")
    print(f"가속도 X축: {gyro_data['accel_xout_scaled']}")
    print(f"가속도 Y축: {gyro_data['accel_yout_scaled']}")
    print(f"가속도 Z축: {gyro_data['accel_zout_scaled']}")
    print(f"X축 회전각: {gyro_data['x_rotation']}도")
    print(f"Y축 회전각: {gyro_data['y_rotation']}도")


def _print_collision_status(collision_status):
    """충돌 센서의 현재 상태를 출력합니다."""

    print("\n충돌 상태:", collision_status)


try:
    while True:
        # 자이로/가속도 센서로부터 최신 데이터를 읽어옵니다.
        gyro_data = gyro_sensor.get_gyro_data()

        # 충돌 감지 스위치 상태를 확인합니다.
        collision_status = collision_sensor.check_collision()

        _print_gyro_data(gyro_data)
        _print_collision_status(collision_status)

        # 1초 간격으로 상태를 출력하여 과도한 로그를 방지합니다.
        time.sleep(1)
except KeyboardInterrupt:
    # Ctrl+C 입력 시 깔끔하게 종료합니다.
    pass
finally:
    # GPIO 핀을 입력 모드로 복구하여 다른 프로그램과 충돌하지 않도록 합니다.
    wiringpi.pinMode(15, GPIO.INPUT)
