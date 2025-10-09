import threading


class OBDState:
    _instance = None
    _lock = threading.Lock()

    # 클래스 레벨의 상태 변수 선언
    speed = "N/A"
    rpm = "N/A"
    throttle_pos = "N/A"
    load = "N/A"
    coolant_temp = "N/A"
    intake_temp = "N/A"
    timing_advance = "N/A"
    short_fuel_trim_1 = "N/A"
    long_fuel_trim_1 = "N/A"
    o2_b1s1 = "N/A"
    o2_b1s2 = "N/A"
    save_score = "N/A"
    distance = "N/A"
    acceleration = "N/A"
    dceleration = "N/A"
    lat = "N/A"
    lon = "N/A"
    collison = "N/A"

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(OBDState, cls).__new__(cls)
        return cls._instance

    @classmethod
    def update(cls, **kwargs):
        with cls._lock:
            for key, value in kwargs.items():
                setattr(cls, key, value)

    @classmethod
    def get_state(cls):
        with cls._lock:
            return {
                "rpm": cls.rpm,
                "speed": cls.speed,
                "coolant_temp": cls.coolant_temp,
                "intake_temp": cls.intake_temp,
                "throttle_pos": cls.throttle_pos,
                "timing_advance": cls.timing_advance,
                "short_fuel_trim_1": cls.short_fuel_trim_1,
                "long_fuel_trim_1": cls.long_fuel_trim_1,
                "o2_b1s1": cls.o2_b1s1,
                "o2_b1s2": cls.o2_b1s2,
                "load": cls.load,
                "save_score": cls.save_score,
                "distance": cls.distance,
                "acceleration": cls.acceleration,
                "dceleration": cls.dceleration,
                "lat": cls.lat,
                "lon": cls.lon,
                "collison": cls.collison
            }

