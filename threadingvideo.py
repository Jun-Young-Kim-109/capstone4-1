"""단일 스크립트로 두 대의 카메라 영상을 녹화하고 업로드하는 예제."""

import threading
import cv2
import obd
from collections import deque
import wiringpi
import time
import datetime
import requests
import os
import asyncio
from gyro_sensor import get_gyro_data  # gyro_sensor 모듈 import
import subprocess
from threading import Lock


class VideoCaptureThread(threading.Thread):
    """카메라 프레임을 읽고 충돌 시 녹화/업로드를 수행하는 스레드."""

    def __init__(self, src, width, height, frame_rate, video_directory, url, start_event, lock):
        super(VideoCaptureThread, self).__init__()
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
        self.obd_connection = obd.OBD() if obd.OBD().is_connected() else None
        self.running = True
        self.is_recording = False
        # 버퍼 크기를 2분치로 조정
        self.frame_buffer = deque(maxlen=frame_rate * 120)
        self.press_time = None
        self.out = None
        self.frame = None
        self.obd_error_shown = False
        self.obd_connected = self.obd_connection is not None
        self.record_start_time = None
        self.warning_display_time = 3  # Warning 메시지를 표시할 시간 (초)
        self.src = src
        self.lock = lock  # Lock 객체 저장
        wiringpi.wiringPiSetup()
        # GPIO 핀을 입력으로 설정하고, 내부 풀업 저항을 활성화
        self.pin = 15
        wiringpi.pinMode(self.pin, 0)  # 0은 입력 모드
        
    def prepare_directory(self):
        """출력 디렉터리가 존재하지 않으면 생성합니다."""

        if not os.path.exists(self.video_directory):
            os.makedirs(self.video_directory)

    def run(self):
        """카메라 프레임을 읽어 충돌 여부에 따라 녹화 상태를 제어합니다."""

        self.start_event.wait()  # 모든 스레드가 준비될 때까지 대기
        countdown = None
        warning_start_time = None
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            current_time = time.time()

            if self.press_time and 0 <= current_time - self.press_time < 3:
                # Dynamically show countdown
                countdown_text = str(3 - int(current_time - self.press_time))
                cv2.putText(frame, countdown_text, (self.width//2, self.height//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            elif self.press_time and current_time - self.press_time >= 3:
                # Start displaying "Warning!!" after countdown
                if warning_start_time is None:
                    warning_start_time = current_time  # Initialize warning start time

            # Display "Warning!!" for a certain duration
            if warning_start_time and 0 <= current_time - warning_start_time <= self.warning_display_time:
                cv2.putText(frame, "Warning!!", (self.width//2 - 50, self.height//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            # Reset warning display logic after the duration
            if warning_start_time and current_time - warning_start_time > self.warning_display_time:
                warning_start_time = None  # Reset warning timer


            # [추가] 카메라 소스가 0인 경우만 특정 처리를 적용
            if self.src == 0:
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                self.frame = gray_frame
                frame, self.obd_error_shown = add_info_to_frame(gray_frame, self.frame_rate, self.obd_error_shown, self.obd_connected, self.obd_connection)
            elif self.src == 2:
                gray_frame = frame
                self.frame = gray_frame  # 3채널 컬러 영상을 그대로 사용
                gyro_data = get_gyro_data()  # 자이로 데이터 가져오기
                # 자이로 데이터를 화면에 표시
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 현재 타임스탬프
                
                # 타임스탬프와 자이로 데이터를 결합한 문자열 생성
                gyro_text = f"{timestamp} - X: {gyro_data['gyro_xout'] / 131:.2f} - Y: {gyro_data['gyro_yout'] / 131:.2f} - Z: {gyro_data['gyro_zout'] / 131:.2f}"
                
                # 생성한 문자열을 화면에 표시 (색상을 검정색으로 변경)
                cv2.putText(frame, gyro_text, (10, self.height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            

            # 버튼 상태 검사
            if not wiringpi.digitalRead(self.pin):  # 0은 LOW 상태
                if self.press_time is None:
                    self.press_time = time.time()
                elapsed_time = time.time() - self.press_time
                if elapsed_time >= 3 and not self.is_recording:
                    self.start_recording()
            else:
                self.press_time = None

            self.manage_recording(gray_frame)

    def handle_collision_detected(self):
        """외부 충돌 이벤트를 처리해 녹화를 시작합니다."""

        if self.press_time is None:
            self.press_time = time.time()
        else:
            elapsed_time = time.time() - self.press_time
            if elapsed_time < 3:
                self.countdown = 3 - int(elapsed_time)
            elif not self.is_recording and elapsed_time >= 3:
                self.start_recording()

    def start_recording(self):
        """충돌 시 녹화 상태를 활성화합니다."""

        if len(self.frame_buffer) < self.frame_rate * 60:
            print("Warning: 충돌 전 데이터가 1분보다 모자랍니다.")
        else:
            print("Collision sensor triggered. Storing frames for video...")
        self.is_recording = True
        self.record_start_time = time.time() - 60  # Adjust for pre-collision frames

    def manage_recording(self, gray_frame):
        """프레임을 버퍼에 저장하고 일정 시간이 지나면 자동으로 종료합니다."""

        with self.lock:  # 프레임 버퍼에 접근하기 전에 Lock을 획득
            self.frame_buffer.append(gray_frame)
            if self.is_recording and (time.time() - self.record_start_time >= 120):
                self.stop_recording()

    def stop_recording(self):
        """녹화를 중단하고 파일 저장 및 업로드를 수행합니다."""

        print("Stopping recording and creating video...")
        self.is_recording = False

        # 비디오 파일 준비 및 프레임 기록
        self.prepare_video_file()
        while self.frame_buffer:
            self.record_frame(self.frame_buffer.popleft())
        if self.out:
            self.out.release()
            self.out = None

        # H.264 코덱으로 비디오 재인코딩
        self.reencode_video_to_h264()

        # 재인코딩된 비디오 파일을 서버로 비동기 전송
        asyncio.run(self.send_video_to_server_async())

    def reencode_video_to_h264(self):
        """비디오 파일을 H.264 코덱으로 재인코딩"""
        output_filename = self.video_filename.replace(".mp4", "up.mp4")
        command = [
            'ffmpeg',  # -y 옵션 추가로 파일 덮어쓰기 활성화
            '-i', self.video_filename,
            '-vcodec', 'libx264', '-preset', 'fast',
            '-crf', '22', '-acodec', 'aac', '-strict', '-2',
            output_filename
        ]
        try:
            subprocess.run(command, check=True)
            print(f"Reencoding complete: {output_filename}")
            # 기존 파일 대신 재인코딩된 파일을 사용
            self.video_filename = output_filename
        except subprocess.CalledProcessError as e:
            print(f"Failed to reencode video: {e}")

    def record_frame(self, gray_frame):
        """VideoWriter를 초기화한 뒤 프레임을 기록합니다."""

        if self.out is None:
            self.prepare_video_file()
        self.out.write(gray_frame)

    def prepare_video_file(self):
        """파일 이름을 생성하고 VideoWriter 객체를 초기화합니다."""

        timestamp = datetime.datetime.fromtimestamp(self.record_start_time + 60).strftime("%Y-%m-%d-%H-%M-%S")
        # Include the video_directory in the path to the video file
        self.video_filename = os.path.join(self.video_directory, f"{timestamp}.mp4")

        # src가 0인 경우 흑백 영상 처리, 그 외는 컬러 영상 처리
        if self.src ==0:
            self.out = cv2.VideoWriter(self.video_filename, self.fourcc, self.frame_rate, (self.width, self.height), isColor=False)
        else:
            self.out = cv2.VideoWriter(self.video_filename, self.fourcc, self.frame_rate, (self.width, self.height))

        

    async def send_video_to_server_async(self):
        """메인 스레드를 차단하지 않고 업로드를 수행합니다."""

        if self.out:
            self.out.release()  # Release the video file
            self.out = None
        # Use threading to avoid blocking the main thread
        threading.Thread(target=self.send_video_to_server, args=(self.video_filename,)).start()

    def send_video_to_server(self, filename):
        """HTTP POST 요청으로 영상을 서버에 업로드합니다."""

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
        """카메라 리소스를 해제하고 스레드를 종료합니다."""

        self.running = False
        if self.out:
            self.out.release()
        self.cap.release()
def add_info_to_frame(frame, fps, obd_error_shown, obd_connected, obd_connection):
    """프레임에 시간, FPS, OBD 데이터를 덧붙입니다."""

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, current_time, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"FPS: {fps}", (500, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    speed_text = rpm_text = throttle_text = load_text = "N/A"

    if obd_connected and obd_connection and obd_connection.is_connected():
        try:
            speed_response = obd_connection.query(obd.commands.SPEED)
            rpm_response = obd_connection.query(obd.commands.RPM)
            throttle_response = obd_connection.query(obd.commands.THROTTLE_POS)
            load_response = obd_connection.query(obd.commands.ENGINE_LOAD)

            speed_text = f"{int(speed_response.value.to('km/h').magnitude)} km/h" if speed_response.value is not None else "N/A"
            rpm_text = f"{int(rpm_response.value.magnitude)} RPM" if rpm_response.value is not None else "N/A"
            throttle_text = f"{int(throttle_response.value.magnitude)}%" if throttle_response.value is not None else "N/A"
            load_text = f"{int(load_response.value.magnitude)}%" if load_response.value is not None else "N/A"
        except Exception as e:
            if not obd_error_shown:
                print(f"OBD-II error: {e}")
                obd_error_shown = True
    elif not obd_error_shown:
        #print("OBD-II connection not established.")
        obd_error_shown = True
    
    cv2.putText(frame, f"Speed: {speed_text} RPM: {rpm_text} Throttle: {throttle_text} Load: {load_text}", (60, frame.shape[0]-50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    return frame, obd_error_shown
    
def configure_camera(device, width=640, height=480, frame_rate=30):
    """카메라 해상도와 프레임레이트를 설정합니다."""
    try:
        # 비디오 포맷 설정
        subprocess.run(['v4l2-ctl', '-d', device, '--set-fmt-video=width={},height={},pixelformat=0'.format(width, height)], check=True)
        # 프레임레이트 설정
        subprocess.run(['v4l2-ctl', '-d', device, '--set-parm={}'.format(frame_rate)], check=True)
        print(f"Camera {device} configured: {width}x{height} at {frame_rate}fps")
    except subprocess.CalledProcessError as e:
        print(f"Failed to configure camera {device}: {e}")

def main():
    """두 카메라 스레드를 실행하고 GUI에 실시간으로 표시합니다."""

    start_event = threading.Event()  # 스레드 시작을 위한 이벤트 생성
    frame_buffer_lock = Lock()  # 프레임 버퍼 동기화를 위한 Lock 객체 생성
    # 카메라 설정을 초기화합니다.
    configure_camera('/dev/video0', 640, 480, 30)
    configure_camera('/dev/video2', 640, 480, 30)

    # 비디오 캡처 스레드 생성 및 시작
    pedal_thread = VideoCaptureThread(src=0, width=640, height=480, frame_rate=30, video_directory="pedalvideo", url="https://sw--zqbli.run.goorm.site/pedalvideo", start_event=start_event, lock=frame_buffer_lock)
    face_thread = VideoCaptureThread(src=2, width=640  , height=480, frame_rate=30, video_directory="facevideo", url="https://sw--zqbli.run.goorm.site/facevideo", start_event=start_event, lock=frame_buffer_lock)

    pedal_thread.start()
    face_thread.start()

    # 모든 스레드가 준비되었다고 가정하고 이벤트를 설정하여 동시에 시작하도록 함
    start_event.set()

    # 동시에 두 비디오 스트림 보여주기
    while pedal_thread.is_alive() or face_thread.is_alive():
        if pedal_thread.frame is not None:
            pedal_frame = cv2.resize(pedal_thread.frame, (640, 480))
            cv2.imshow('Pedal Video Recorder', pedal_frame)

        if face_thread.frame is not None:
            face_frame = cv2.resize(face_thread.frame, (640, 480))
            cv2.imshow('Face Video Recorder', face_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            if pedal_thread.isAlive():
                pedal_thread.stop()
            if face_thread.isAlive():
                face_thread.stop()
            break

    pedal_thread.join()
    face_thread.join()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
