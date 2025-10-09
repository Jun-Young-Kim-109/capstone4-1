"""OBD-II 비동기 연결과 센서 데이터를 관리하는 모듈."""

import datetime

import obd

import calculate_distance  # 다른 모듈에서 사용하는 전역 상태와 호환성을 유지하기 위해 남겨둡니다.
from obd_state import OBDState

# 아래 전역 변수들은 각 콜백에서 업데이트됩니다. 화면 표시, 기록 등
# 다른 기능에서 동일한 값을 사용할 수 있도록 중앙에서 관리합니다.
rpm = 0
load = 0
maf = 0.0
o2_trim = 0.0
timing_advance = 0.0
coolant_temp = 0
fuel_rail_press = 0.0
intake_temp = 0
afr = 0.0
speed = 0
throttle_pos = 0
rapid_acceleration_count = 0
rapid_deceleration_count = 0
fuel_status = ""
short_fuel_trim_1 = 0.0
long_fuel_trim_1 = 0.0
o2_sensors = ""
o2_b1s1 = 0.0
o2_b1s2 = 0.0
fuel_status_display = ""
o2_sensors_display = ""
distance = 0
codes = []
driving_score = 100
engine_load = 0
previous_speed = 0
logging_start_time = None
safety_message = None
safety_message_start_time = None
message_display_time = 5
previous_driving_score = 100
previous_distance = 0
score_decreased = False
speed_conditions = []
rpm_conditions = []
load_conditions = []
recording = False
obd_connection = None
logging_active = False
LOGGING_INTERVAL = 0.2  # seconds
last_logging_time = datetime.datetime.now()
is_recording = False
save_score = 100


class OBDConnection:
    """OBD-II 어댑터와의 비동기 연결을 설정하는 편의 클래스."""

    def __init__(self):
        self.obd_connection = None
        self.obd_connected = False
        self.initialize_connection()

    def initialize_connection(self):
        """비동기 OBD 연결을 초기화하고 연결 여부를 기록합니다."""

        try:
            self.obd_connection = obd.Async()
            if self.obd_connection.is_connected():
                self.obd_connected = True
            else:
                print("Failed to connect to OBD. Running without OBD connection.")
        except Exception as e:
            print(f"Error occurred while connecting to OBD: {e}")


#########################################
#   Functions to retrieve ECU data      #
#########################################

# Functions written as so defined by Python-OBD authors
# https://python-obd.readthedocs.io/en/latest/Async%20Connections/
def get_speed(s):
    """속도를 km/h 단위의 정수로 저장하고 공유 상태를 갱신합니다."""

    global speed
    if not s.is_null():
        speed = int(s.value.magnitude)
        OBDState.update(speed=speed)


def get_fuel_rail_press(fp):
    """연료 레일 압력을 psi 단위로 변환해 저장합니다."""

    global fuel_rail_press
    if not fp.is_null():
        fuel_rail_press = float(fp.value.magnitude) * 0.145038  # kPa -> psi


def get_intake_temp(it):
    """흡기 온도를 섭씨 값으로 저장합니다."""

    global intake_temp
    if not it.is_null():
        intake_temp = int(it.value.magnitude)


def get_afr(af):
    """연료-공기비(AFR)를 가솔린 엔진 기준으로 환산합니다."""

    global afr
    if not af.is_null():
        afr = float(af.value.magnitude) * 14.64


def get_rpm(r):
    """엔진 회전수를 RPM 단위로 저장하고 공유 상태를 갱신합니다."""

    global rpm
    if not r.is_null():
        rpm = int(r.value.magnitude)
        OBDState.update(rpm=rpm)


def get_load(l):
    """엔진 부하(%)를 저장하고 공유 상태를 갱신합니다."""

    global load
    if not l.is_null():
        load = int(l.value.magnitude)
        OBDState.update(load=load)


def get_coolant_temp(ct):
    """냉각수 온도를 섭씨로 저장합니다."""

    global coolant_temp
    if not ct.is_null():
        coolant_temp = int(ct.value.magnitude)


def get_intake_press(ip):
    """흡기 매니폴드 압력을 kPa 단위로 저장합니다."""

    global intake_pressure
    if not ip.is_null():
        intake_pressure = float(ip.value.magnitude)


def get_baro_press(bp):
    """대기압을 kPa 단위로 저장합니다."""

    global baro_pressure
    if not bp.is_null():
        baro_pressure = float(bp.value.magnitude)


def get_dtc(c):
    """진단 Trouble Code 목록을 저장합니다."""

    global codes
    if not c.is_null():
        codes = c.value


def get_timing_a(ta):
    """점화 시기(advance)를 degree 단위로 파싱합니다."""

    global timing_advance
    if not ta.is_null():
        timing_advance = str(ta.value).replace("degree", "")
        timing_advance = float(timing_advance)


def get_maf(m):
    """질량 유량(MAF)을 g/s 단위로 저장합니다."""

    global maf
    if not m.is_null():
        maf = str(m.value).replace("gps", "")
        maf = float(maf)


def get_fuel_status(fs):
    """연료 시스템 상태 텍스트를 저장합니다."""

    global fuel_status
    if not fs.is_null():
        fuel_status = fs.value


def get_o2(o):
    """산소 센서 트림(%)을 저장합니다."""

    global o2_trim
    if not o.is_null():
        o2_trim = str(o.value).replace("percent", "")
        o2_trim = float(o2_trim)


def get_throttle_pos(tp):
    """스로틀 위치를 퍼센트로 저장하고 공유 상태를 갱신합니다."""

    global throttle_pos
    if not tp.is_null():
        throttle_pos = int(tp.value.magnitude)
        OBDState.update(throttle_pos=throttle_pos)


def get_short_fuel_trim_1(sft1):
    """연료 트림(단기)을 퍼센트로 저장합니다."""

    global short_fuel_trim_1
    if not sft1.is_null():
        short_fuel_trim_1 = float(sft1.value.magnitude)


def get_long_fuel_trim_1(lft1):
    """연료 트림(장기)을 퍼센트로 저장합니다."""

    global long_fuel_trim_1
    if not lft1.is_null():
        long_fuel_trim_1 = float(lft1.value.magnitude)


def get_o2_sensors(os):
    """O2 센서 구성을 문자열로 유지합니다."""

    global o2_sensors
    if not os.is_null():
        o2_sensors = os.value


def get_o2_b1s1(o2b1s1):
    """Bank1 Sensor1의 산소 센서 전압을 저장합니다."""

    global o2_b1s1
    if not o2b1s1.is_null():
        o2_b1s1 = float(o2b1s1.value.magnitude)


def get_o2_b1s2(o2b1s2):
    """Bank1 Sensor2의 산소 센서 전압을 저장합니다."""

    global o2_b1s2
    if not o2b1s2.is_null():
        o2_b1s2 = float(o2b1s2.value.magnitude)


def ecu_connections(obd_connection):
    """모든 관심 명령을 비동기 연결에 등록하고 수신을 시작합니다."""

    if obd_connection:
        obd_connection.watch(obd.commands.SPEED, callback=get_speed)
        obd_connection.watch(obd.commands.RPM, callback=get_rpm)
        obd_connection.watch(obd.commands.ENGINE_LOAD, callback=get_load)
        obd_connection.watch(obd.commands.GET_DTC, callback=get_dtc)
        obd_connection.watch(obd.commands.COOLANT_TEMP, callback=get_coolant_temp)
        obd_connection.watch(obd.commands.INTAKE_TEMP, callback=get_intake_temp)
        obd_connection.watch(obd.commands.FUEL_RAIL_PRESSURE_DIRECT, callback=get_fuel_rail_press)
        obd_connection.watch(obd.commands.COMMANDED_EQUIV_RATIO, callback=get_afr)
        obd_connection.watch(obd.commands.MAF, callback=get_maf)
        obd_connection.watch(obd.commands.TIMING_ADVANCE, callback=get_timing_a)
        obd_connection.watch(obd.commands.LONG_O2_TRIM_B1, callback=get_o2)
        obd_connection.watch(obd.commands.THROTTLE_POS, callback=get_throttle_pos)
        obd_connection.watch(obd.commands.FUEL_STATUS, callback=get_fuel_status)
        obd_connection.watch(obd.commands.SHORT_FUEL_TRIM_1, callback=get_short_fuel_trim_1)
        obd_connection.watch(obd.commands.LONG_FUEL_TRIM_1, callback=get_long_fuel_trim_1)
        obd_connection.watch(obd.commands.O2_SENSORS, callback=get_o2_sensors)
        obd_connection.watch(obd.commands.O2_B1S1, callback=get_o2_b1s1)
        obd_connection.watch(obd.commands.O2_B1S2, callback=get_o2_b1s2)
        # 모든 watch 등록 후 반드시 start()를 호출해야 실제 데이터가 수신됩니다.
        obd_connection.start()
