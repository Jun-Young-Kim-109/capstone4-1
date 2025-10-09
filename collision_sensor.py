"""충돌 감지 스위치 상태를 판별하는 간단한 유틸리티."""

import wiringpi


# GPIO 핀 번호. 필요 시 다른 핀으로 교체할 수 있습니다.
pin = 15

# wiringPi 라이브러리를 초기화하고 입력 모드로 전환합니다.
wiringpi.wiringPiSetup()
wiringpi.pinMode(pin, 0)


def check_collision():
    """충돌 감지 스위치 상태를 읽어 사람이 이해하기 쉬운 문자열로 반환합니다."""

    if wiringpi.digitalRead(pin):
        # 스위치가 눌린 상태(= 회로가 닫혀 "1"을 반환)라면 아직 충돌이 없는 상황입니다.
        return "충돌 없음"
    # 스위치가 열린 상태라면 센서가 충격을 감지한 것입니다.
    return "충돌 감지됨!!"
