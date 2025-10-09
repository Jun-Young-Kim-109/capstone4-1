"""MPU-6050 자이로/가속도 센서 데이터를 읽어오는 헬퍼 함수 모음."""

import math

import smbus


def read_byte(adr, bus, address):
    """지정한 레지스터에서 1바이트를 읽어 반환합니다."""

    return bus.read_byte_data(address, adr)


def read_word(adr, bus, address):
    """연속된 두 레지스터에서 2바이트 데이터를 읽어 하나의 정수로 합칩니다."""

    high = bus.read_byte_data(address, adr)
    low = bus.read_byte_data(address, adr + 1)
    val = (high << 8) + low
    return val


def read_word_2c(adr, bus, address):
    """MPU-6050의 2의 보수(2's complement) 형식을 파이썬 정수로 변환합니다."""

    val = read_word(adr, bus, address)
    if val >= 0x8000:
        return -((65535 - val) + 1)
    return val


def dist(a, b):
    """두 값의 피타고라스 거리를 계산합니다."""

    return math.sqrt((a * a) + (b * b))


def get_y_rotation(x, y, z):
    """가속도 값으로부터 Y축 회전각(롤)을 계산합니다."""

    radians = math.atan2(x, dist(y, z))
    return -math.degrees(radians)


def get_x_rotation(x, y, z):
    """가속도 값으로부터 X축 회전각(피치)을 계산합니다."""

    radians = math.atan2(y, dist(x, z))
    return math.degrees(radians)


def get_gyro_data():
    """자이로/가속도 원시 데이터와 보정된 값을 모두 반환합니다."""

    power_mgmt_1 = 0x6B
    power_mgmt_2 = 0x6C
    bus = smbus.SMBus(5)  # 라즈베리파이 400/CM4의 I2C-6 버스를 사용합니다.
    address = 0x68  # MPU-6050 기본 I2C 주소

    # 슬립 모드에서 센서를 깨웁니다.
    bus.write_byte_data(address, power_mgmt_1, 0)

    # 자이로스코프 원시 값 읽기
    gyro_xout = read_word_2c(0x43, bus, address)
    gyro_yout = read_word_2c(0x45, bus, address)
    gyro_zout = read_word_2c(0x47, bus, address)

    # 가속도계 원시 값 읽기
    accel_xout = read_word_2c(0x3B, bus, address)
    accel_yout = read_word_2c(0x3D, bus, address)
    accel_zout = read_word_2c(0x3F, bus, address)

    # 센서 데이터 시트에 따라 16384로 나누면 g 단위 값이 됩니다.
    accel_xout_scaled = accel_xout / 16384.0
    accel_yout_scaled = accel_yout / 16384.0
    accel_zout_scaled = accel_zout / 16384.0

    # 기울어진 각도를 추정합니다.
    x_rotation = get_x_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled)
    y_rotation = get_y_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled)

    return {
        'gyro_xout': gyro_xout,
        'gyro_yout': gyro_yout,
        'gyro_zout': gyro_zout,
        'accel_xout_scaled': accel_xout_scaled,
        'accel_yout_scaled': accel_yout_scaled,
        'accel_zout_scaled': accel_zout_scaled,
        'x_rotation': x_rotation,
        'y_rotation': y_rotation,
    }
