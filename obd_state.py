"""OBD-II 측정값을 스레드 안전하게 공유하기 위한 싱글턴 클래스."""

import threading


class OBDState:
    """OBD-II 데이터(속도, RPM 등)를 저장하고 공유하는 간단한 컨테이너."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """싱글턴 인스턴스를 생성하거나 기존 인스턴스를 반환합니다."""

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
        """수신된 값을 갱신합니다. ``None`` 값은 무시합니다."""

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
        """현재 저장된 모든 값을 튜플로 반환합니다."""

        with cls._lock:
            return cls.speed, cls.rpm, cls.throttle_pos, cls.load
