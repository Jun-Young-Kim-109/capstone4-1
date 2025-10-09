import threading
import cv2
from collections import deque
import wiringpi
import time
import datetime
import requests
import os
import asyncio
from add_info_to_frame import add_info_to_frame
from gyro_sensor import get_gyro_data  # gyro_sensor 모듈 import
import subprocess
import logging

# 로그 설정: 로그 레벨을 DEBUG로 설정하고, 로그 메시지 형식을 정의합니다.
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
        self.frame_buffer = deque(maxlen=frame_rate * 120)  # 버퍼 크기를 30초 치로 조정
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
                frame, self.obd_error_shown = add_info_to_frame(gray_frame, self.frame_rate, self.obd_error_shown,
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

    def start_recording(self):
        if len(self.frame_buffer) < self.frame_rate * 60:
            print("Warning: Insufficient pre-collision data.")
        else:
            print("Collision sensor triggered. Storing frames for video...")
        self.is_recording = True
        self.record_start_time = time.time() - 60  # Adjust for pre-collision frames

    def manage_recording(self, gray_frame):
        with self.lock:
            self.frame_buffer.append(gray_frame)
            # 버퍼에 프레임 추가 시 로그 출력
            #logging.debug(f'Frame added to buffer. Buffer size: {len(self.frame_buffer)}/{self.frame_buffer.maxlen}')

            if self.is_recording and (time.time() - self.record_start_time >= 120):
                self.stop_recording()
                #logging.debug('Stopping recording after 30 seconds.')

    def stop_recording(self):
        print("Stopping recording and creating video...")
        self.is_recording = False
        self.prepare_video_file()
        while self.frame_buffer:
            self.record_frame(self.frame_buffer.popleft())
        if self.out:
            self.out.release()
            self.out = None
        self.reencode_video_to_h264()
        asyncio.run(self.send_video_to_server_async())

    def reencode_video_to_h264(self):
        output_filename = self.video_filename.replace(".mp4", "_h264.mp4")
        command = [
            'ffmpeg',
            '-y',
            '-i', self.video_filename,
            '-vcodec', 'libx264', '-preset', 'fast',
            '-crf', '22', '-acodec', 'aac', '-strict', '-2',
            output_filename
        ]
        try:
            subprocess.run(command, check=True)
            print(f"Reencoding complete: {output_filename}")
            self.video_filename = output_filename
        except subprocess.CalledProcessError as e:
            print(f"Failed to reencode video: {e}")

    def record_frame(self, gray_frame):
        if self.out is None:
            self.prepare_video_file()
        self.out.write(gray_frame)

    def prepare_video_file(self):
        timestamp = datetime.datetime.fromtimestamp(self.record_start_time + 15).strftime("%Y-%m-%d-%H-%M-%S")
        self.video_filename = os.path.join(self.video_directory, f"{timestamp}.mp4")
        if self.src == 0:
            self.out = cv2.VideoWriter(self.video_filename, self.fourcc, self.frame_rate, (self.width, self.height), isColor=False)
        else:
            self.out = cv2.VideoWriter(self.video_filename, self.fourcc, self.frame_rate, (self.width, self.height))

    async def send_video_to_server_async(self):
        if self.out:
            self.out.release()
            self.out = None
        threading.Thread(target=self.send_video_to_server, args=(self.video_filename,)).start()

    def send_video_to_server(self, filename):
        print("Preparing to send video...")
        try:
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                print(f"Sending {filename} to server...")
                with open(filename, 'rb') as f:
                    files = {'video': (filename, f, 'video/mp4')}
                    response = requests.post(self.url, files=files)
                    print(f"Server response: {response.status_code}, {response.text}")
            else:
                print("Video file does not exist or is empty.")
        except Exception as e:
            print(f"Failed to send video: {e}")

    def stop(self):
        self.running = False
        if self.out:
            self.out.release()
        self.cap.release()