# sensor.py
import time
import gyro_sensor
import collision_sensor
import wiringpi
from wiringpi import GPIO

try:
    while True:
        gyro_data = gyro_sensor.get_gyro_data()
        collision_status = collision_sensor.check_collision()

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

        print("\n충돌 상태:", collision_status)

        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
	wiringpi.pinMode(15, GPIO.INPUT)
