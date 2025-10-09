# obd_state.py

import threading

class OBDState:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(OBDState, cls).__new__(cls)
                cls.speed = "N/A"
                cls.rpm = "N/A"
                cls.throttle_pos = "N/A"
                cls.load = "N/A"
        return cls._instance

    @classmethod
    def update(cls, speed=None, rpm=None, throttle_pos=None, load=None):
        with cls._lock:
            if speed is not None:
                cls.speed = speed
            if rpm is not None:
                cls.rpm = rpm
            if throttle_pos is not None:
                cls.throttle_pos = throttle_pos
            if load is not None:
                cls.load = load

    @classmethod
    def get_state(cls):
        with cls._lock:
            return cls.speed, cls.rpm, cls.throttle_pos, cls.load
