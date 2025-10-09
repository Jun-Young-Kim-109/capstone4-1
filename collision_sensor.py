# collision_sensor.py
import wiringpi

# GPIO 핀 초기 설정
pin = 15  # 사용할 GPIO 핀 번호
wiringpi.wiringPiSetup()  # wiringPi 라이브러리 초기화
wiringpi.pinMode(pin, 0)  # 핀 모드를 입력으로 설정

def check_collision():
    if wiringpi.digitalRead(pin):
        # 스위치가 눌렸을 때(일반적으로 1을 반환)
        return "충돌 없음"
    else:
        # 스위치가 떨어져 있을 때(일반적으로 0을 반환)
        return "충돌 감지됨!!"
