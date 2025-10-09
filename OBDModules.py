import obd
import calculate_distance
import datetime
from obd_state import OBDState
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
save_score = 100;
class OBDConnection:
    def __init__(self):
        self.obd_connection = None
        self.obd_connected = False
        self.initialize_connection()

    def initialize_connection(self):
        try:
            self.obd_connection = obd.Async()
            if self.obd_connection.is_connected():
                self.obd_connected = True
            else:
                print("Failed to connect to OBD. Running without OBD connection.")
        except Exception as e:
            print(f"Error occurred while connecting to OBD: {e}")
#############################
#      Global Values        #
#                           #
#############################



#########################################
#   Functions to retrieve ECU data      #
#########################################

# Functions written as so defined by Python-OBD authors
# https://python-obd.readthedocs.io/en/latest/Async%20Connections/
def get_speed(s):
    global speed
    if not s.is_null():
        speed = int(s.value.magnitude)
        #print(f"Speed: {speed} km/h")
        OBDState.update(speed=speed)

def get_fuel_rail_press(fp):
    global fuel_rail_press
    if not fp.is_null():
        fuel_rail_press = float(fp.value.magnitude) * .145038  # kp to psi
        #print(f"Fuel Rail Pressure: {fuel_rail_press:.2f} psi")

def get_intake_temp(it):
    global intake_temp
    if not it.is_null():
        intake_temp = int(it.value.magnitude)  # C
        #print(f"Intake Temperature: {intake_temp} C")

def get_afr(af):
    global afr
    if not af.is_null():
        afr = float(af.value.magnitude) * 14.64 # Convert to AFR for normal gasoline engines
        #print(f"AFR (Air-Fuel Ratio): {afr:.2f}")

def get_rpm(r):
    global rpm
    if not r.is_null():
        rpm = int(r.value.magnitude)
        #print(f"RPM: {rpm}")
        OBDState.update(rpm=rpm)

def get_load(l):
    global load
    if not l.is_null():
        load = int(l.value.magnitude)
        #print(f"Engine Load: {load}%")
        OBDState.update(load=load)

def get_coolant_temp(ct):
    global coolant_temp
    if not ct.is_null():
        coolant_temp = int(ct.value.magnitude) # C
        #print(f"Coolant Temperature: {coolant_temp} C")

def get_intake_press(ip):
    global intake_pressure
    if not ip.is_null():
        intake_pressure = float(ip.value.magnitude)
        #print(f"Intake Manifold Pressure: {intake_pressure} kPa")

def get_baro_press(bp):
    global baro_pressure
    if not bp.is_null():
        baro_pressure = float(bp.value.magnitude)
        #print(f"Barometric Pressure: {baro_pressure} kPa")

def get_dtc(c):
    global codes
    if not c.is_null():
        codes = c.value
        #print(f"Diagnostic Trouble Codes: {codes}")

def get_timing_a(ta):
    global timing_advance
    if not ta.is_null():
        timing_advance = str(ta.value).replace("degree", "") # in degrees / remove text from val
        timing_advance = float(timing_advance)
        #print(f"Timing Advance: {timing_advance} degrees")

def get_maf(m):
    global maf
    if not m.is_null():
        maf = str(m.value).replace("gps", "")  # grams / second / remove text from val
        maf = float(maf)
        #print(f"MAF (Mass Air Flow): {maf} grams/sec")

def get_fuel_status(fs):
    global fuel_status
    if not fs.is_null():
        fuel_status = fs.value
        #print(f"Fuel System Status: {fuel_status}")

def get_o2(o):
    global o2_trim
    if not o.is_null():
        o2_trim = str(o.value).replace("percent", "")  # +/- 3 percent normal range - negative = rich, positive = lean
        o2_trim = float(o2_trim)
        #print(f"O2 Trim: {o2_trim}%")

def get_throttle_pos(tp):
    global throttle_pos
    if not tp.is_null():
        throttle_pos = int(tp.value.magnitude)
        #print(f"Throttle Position: {throttle_pos}%")
        OBDState.update(throttle_pos=throttle_pos)

def get_short_fuel_trim_1(sft1):
    global short_fuel_trim_1
    if not sft1.is_null():
        short_fuel_trim_1 = float(sft1.value.magnitude)
        #print(f"Short Fuel Trim 1: {short_fuel_trim_1}%")

def get_long_fuel_trim_1(lft1):
    global long_fuel_trim_1
    if not lft1.is_null():
        long_fuel_trim_1 = float(lft1.value.magnitude)
        #print(f"Long Fuel Trim 1: {long_fuel_trim_1}%")

def get_o2_sensors(os):
    global o2_sensors
    if not os.is_null():
        o2_sensors = os.value
        #print(f"O2 Sensors: {o2_sensors}")

def get_o2_b1s1(o2b1s1):
    global o2_b1s1
    if not o2b1s1.is_null():
        o2_b1s1 = float(o2b1s1.value.magnitude)
        #print(f"O2 B1S1: {o2_b1s1}")

def get_o2_b1s2(o2b1s2):
    global o2_b1s2
    if not o2b1s2.is_null():
        o2_b1s2 = float(o2b1s2.value.magnitude)
        #print(f"O2 B1S2: {o2_b1s2}")



def ecu_connections(obd_connection):
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
    obd_connection.start()