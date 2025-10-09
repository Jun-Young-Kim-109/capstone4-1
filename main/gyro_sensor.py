# gyro_sensor.py
import smbus
import math

# 이하의 코드는 이전에 제공된 자이로스코프 코드와 동일하며,
# main 함수 대신 get_gyro_data 함수를 정의합니다.

def read_byte(adr, bus, address):
    return bus.read_byte_data(address, adr)

def read_word(adr, bus, address):
    high = bus.read_byte_data(address, adr)
    low = bus.read_byte_data(address, adr+1)
    val = (high << 8) + low
    return val

def read_word_2c(adr, bus, address):
    val = read_word(adr, bus, address)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val

def dist(a, b):
    return math.sqrt((a*a)+(b*b))

def get_y_rotation(x, y, z):
    radians = math.atan2(x, dist(y, z))
    return -math.degrees(radians)

def get_x_rotation(x, y, z):
    radians = math.atan2(y, dist(x, z))
    return math.degrees(radians)

def get_gyro_data():
    power_mgmt_1 = 0x6b
    power_mgmt_2 = 0x6c
    bus = smbus.SMBus(5)
    address = 0x68

    bus.write_byte_data(address, power_mgmt_1, 0)

    gyro_xout = read_word_2c(0x43, bus, address)
    gyro_yout = read_word_2c(0x45, bus, address)
    gyro_zout = read_word_2c(0x47, bus, address)

    accel_xout = read_word_2c(0x3b, bus, address)
    accel_yout = read_word_2c(0x3d, bus, address)
    accel_zout = read_word_2c(0x3f, bus, address)

    accel_xout_scaled = accel_xout / 16384.0
    accel_yout_scaled = accel_yout / 16384.0
    accel_zout_scaled = accel_zout / 16384.0

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
        'y_rotation': y_rotation
    }
