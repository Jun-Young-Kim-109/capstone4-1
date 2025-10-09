import time

import serial
import pynmea2

from obd_state import OBDState


class SingletonMeta(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class GPSParser(metaclass=SingletonMeta):
    def __init__(self):
        self.latitude = None
        self.longitude = None
        self.speed_kmh = None
        self.serialPort = serial.Serial("/dev/ttyS0", 9600, timeout=0.5)

    def parseGPS(self, data):
        if 'GGA' in data:
            try:
                msg = pynmea2.parse(data)
                self.latitude = msg.latitude
                self.longitude = msg.longitude
            except pynmea2.ParseError as e:
                print(f"Parse error: {e}")
        elif 'VTG' in data:
            try:
                msg = pynmea2.parse(data)
                self.speed_kmh = float(msg.spd_over_grnd_kts) * 1.852 if msg.spd_over_grnd_kts else None
            except pynmea2.ParseError as e:
                print(f"Parse error: {e}")

    def update(self):
        data = self.serialPort.readline().decode('ascii', errors='replace').strip()
        self.parseGPS(data)

    def get_latitude(self):
        return self.latitude

    def get_longitude(self):
        return self.longitude

    def get_speed_kmh(self):
        return self.speed_kmh

def update_gps_data():
    gps_parser = GPSParser()
    while True:
        gps_parser.update()
        #time.sleep(1)  # 1초마다 업데이트
        lat = gps_parser.get_latitude()
        lon = gps_parser.get_longitude()
        OBDState.update(lat=lat)
        OBDState.update(lon=lon)
        #print(lat, lon)


