"""GPS 데이터 파싱 및 실시간 출력 스크립트.

이 모듈은 라즈베리파이와 같은 장치에 연결된 시리얼 GPS 모듈로부터 NMEA
문장을 읽어 사람이 이해하기 쉬운 형식으로 가공합니다. ``GGA`` 문장에서
위치 정보를, ``VTG`` 문장에서 속도 정보를 추출한 뒤 가능한 경우 둘을 한
화면에 출력합니다.
"""

import serial
import pynmea2
from datetime import datetime, timedelta

# 전역 변수로 위도(latitude), 경도(longitude), 시속(speed_kmh)을 저장합니다.
latitude = None
longitude = None
speed_kmh = None


def parseGPS(data):
    """NMEA 문장을 분석하여 전역 상태를 갱신하고 출력합니다."""

    global latitude, longitude, speed_kmh

    # ``GGA`` 문장은 위도와 경도, 고도 등 핵심 위치 정보를 제공합니다.
    if 'GGA' in data:
        try:
            msg = pynmea2.parse(data)
            # UTC 날짜와 시간을 결합해 ``datetime`` 객체를 만든 뒤 한국 표준시(KST)로 변환합니다.
            current_utc_datetime = datetime.combine(datetime.utcnow().date(), msg.timestamp)
            kst_datetime = current_utc_datetime + timedelta(hours=9)
            latitude = msg.latitude
            longitude = msg.longitude

            # 이미 속도 데이터가 준비되어 있다면 위치와 함께 출력합니다.
            if speed_kmh is not None:
                print(
                    "시간: {} -- 위도: {} -- 경도: {} -- 시속: {:.2f} km/h".format(
                        kst_datetime.strftime("%H:%M:%S"), latitude, longitude, speed_kmh
                    )
                )
                speed_kmh = None  # 다음 속도 값을 기다릴 수 있도록 초기화합니다.
        except pynmea2.ParseError as e:
            # GPS 신호가 불안정할 때 발생할 수 있는 파싱 오류를 사용자에게 알립니다.
            print(f"Parse error: {e}")

    # ``VTG`` 문장은 진행 방향과 속도 정보를 제공합니다.
    elif 'VTG' in data:
        try:
            msg = pynmea2.parse(data)
            # 속도가 노트 단위로 제공되면 km/h로 변환합니다. 값이 없으면 ``None``으로 남깁니다.
            speed_kmh = float(msg.spd_over_grnd_kts) * 1.852 if msg.spd_over_grnd_kts else None
        except pynmea2.ParseError as e:
            print(f"Parse error: {e}")


# 시리얼 포트를 초기화합니다. 연결된 장치에 따라 포트 이름과 속도를 조정하세요.
serialPort = serial.Serial("/dev/ttyS0", 9600, timeout=0.5)


while True:
    # GPS 모듈로부터 한 줄의 NMEA 문장을 읽어와 분석합니다.
    data = serialPort.readline().decode('ascii', errors='replace').strip()
    parseGPS(data)

