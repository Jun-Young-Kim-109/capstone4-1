import datetime
import os
import threading
import time
from collections import deque

import cv2
import wiringpi

from main import Video
from main.gyro_sensor import get_gyro_data


class VideoCaptureThread(threading.Thread):
    def __init__(self, src, width, height, frame_rate, video_directory, url, start_event, lock, obd_connection, obd_connected):
        super(VideoCaptureThread, self).__init__()
        self.obd_connection = obd_connection
        self.obd_connected = obd_connected
        self.start_event = start_event  # 스레드 시작 이벤트
        self.cap = cv2.VideoCapture(src)
        if not self.cap.isOpened():
            raise Exception("Error: Camera is not opened.")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, frame_rate)
        self.width = width
        self.height = height
        self.frame_rate = frame_rate
        self.fourcc = cv2.VideoWriter_fourcc(*'MP4V')
        self.video_directory = video_directory
        self.url = url
        self.prepare_directory()
        self.running = True
        self.is_recording = False
        self.frame_buffer = deque(maxlen=frame_rate * 30)  # 버퍼 크기를 30초 치로 조정
        self.press_time = None
        self.out = None
        self.frame = None
        self.obd_error_shown = False
        self.record_start_time = None
        self.warning_display_time = 3  # Warning 메시지를 표시할 시간 (초)
        self.src = src
        self.lock = lock  # Lock 객체 저장
        wiringpi.wiringPiSetup()
        self.pin = 15
        wiringpi.pinMode(self.pin, 0)  # 0은 입력 모드

    def prepare_directory(self):
        if not os.path.exists(self.video_directory):
            os.makedirs(self.video_directory)

    def run(self):
        self.start_event.wait()  # 모든 스레드가 준비될 때까지 대기
        countdown = None
        warning_start_time = None
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            current_time = time.time()

            if self.press_time and 0 <= current_time - self.press_time < 3:
                countdown_text = str(3 - int(current_time - self.press_time))
                cv2.putText(frame, countdown_text, (self.width // 2, self.height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (255, 255, 255), 2)
            elif self.press_time and current_time - self.press_time >= 3:
                if warning_start_time is None:
                    warning_start_time = current_time

            if warning_start_time and 0 <= current_time - warning_start_time <= self.warning_display_time:
                cv2.putText(frame, "Warning!!", (self.width // 2 - 50, self.height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (255, 255, 255), 2)

            if warning_start_time and current_time - warning_start_time > self.warning_display_time:
                warning_start_time = None  # Reset warning timer

            if self.src == 0:
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                self.frame = gray_frame
                frame, self.obd_error_shown = jun.add_info_to_frame(gray_frame, self.frame_rate, self.obd_error_shown,
                                                                    self.obd_connected, self.obd_connection)
            elif self.src == 2:
                gray_frame = frame
                self.frame = gray_frame
                gyro_data = get_gyro_data()
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                gyro_text = f"{timestamp} - X: {gyro_data['gyro_xout'] / 131:.2f} - Y: {gyro_data['gyro_yout'] / 131:.2f} - Z: {gyro_data['gyro_zout'] / 131:.2f}"
                cv2.putText(frame, gyro_text, (10, self.height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            if not wiringpi.digitalRead(self.pin):
                if self.press_time is None:
                    self.press_time = time.time()
                elapsed_time = time.time() - self.press_time
                if elapsed_time >= 3 and not self.is_recording:
                    self.start_recording()
            else:
                self.press_time = None

            self.manage_recording(gray_frame)