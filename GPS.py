import serial
import pynmea2
from datetime import datetime, timedelta

# 전역 변수로 위도, 경도, 시속을 저장합니다.
latitude = None
longitude = None
speed_kmh = None

def parseGPS(data):
    global latitude, longitude, speed_kmh
    if 'GGA' in data:
        try:
            msg = pynmea2.parse(data)
            # Combine date and time to get a complete datetime object
            current_utc_datetime = datetime.combine(datetime.utcnow().date(), msg.timestamp)
            # Adjust for the timezone difference to KST (UTC+9)
            kst_datetime = current_utc_datetime + timedelta(hours=9)
            latitude = msg.latitude
            longitude = msg.longitude
            # If speed has already been captured, print all data together
            if speed_kmh is not None:
                print("시간: {} -- 위도: {} -- 경도: {} -- 시속: {:.2f} km/h".format(
                    kst_datetime.strftime("%H:%M:%S"), latitude, longitude, speed_kmh))
                speed_kmh = None  # Reset speed after printing
        except pynmea2.ParseError as e:
            print(f"Parse error: {e}")

    elif 'VTG' in data:  # For speed in km/h
        try:
            msg = pynmea2.parse(data)
            # Convert knots to km/h if the speed is provided in knots
            speed_kmh = float(msg.spd_over_grnd_kts) * 1.852 if msg.spd_over_grnd_kts else None
        except pynmea2.ParseError as e:
            print(f"Parse error: {e}")

serialPort = serial.Serial("/dev/ttyS0", 9600, timeout=0.5)

while True:
    data = serialPort.readline().decode('ascii', errors='replace').strip()
    parseGPS(data)

