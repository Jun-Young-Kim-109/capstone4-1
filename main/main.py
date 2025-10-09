import threading
import cv2
import OBDModules
import Send_ECU
from GPS import update_gps_data
from Video import VideoCaptureThread
from configure_camera import configure_camera


def main():
    obd_connection = None
    obd_connected = False
    obd_conn = OBDModules.OBDConnection()

    if obd_conn.obd_connected:
        obd_connection = obd_conn.obd_connection
        obd_connected = obd_conn.obd_connected

        # 스레드 생성 및 시작
        OBDModules.ecu_connections(obd_conn.obd_connection)
        data_sender_thread = threading.Thread(target=Send_ECU.periodic_data_sender)
        data_sender_thread.daemon = True  # 프로그램 종료 시 스레드도 함께 종료
        data_sender_thread.start()

        # GPS 데이터 업데이트를 위한 스레드 생성 및 시작
        gps_update_thread = threading.Thread(target=update_gps_data)
        gps_update_thread.daemon = True
        gps_update_thread.start()


    start_event = threading.Event()
    frame_buffer_lock = threading.Lock()
    configure_camera('/dev/video0', 640, 480, 30)
    configure_camera('/dev/video2', 640, 480, 30)

    pedal_thread = VideoCaptureThread(src=0, width=640, height=480, frame_rate=30, video_directory="pedalvideo",
                                      url="https://sw--zqbli.run.goorm.site/pedalvideo", start_event=start_event,
                                      lock=frame_buffer_lock, obd_connection=obd_connection, obd_connected=obd_connected)
    face_thread = VideoCaptureThread(src=2, width=640, height=480, frame_rate=30, video_directory="facevideo",
                                     url="https://sw--zqbli.run.goorm.site/facevideo", start_event=start_event,
                                     lock=frame_buffer_lock, obd_connection=None, obd_connected=False)

    pedal_thread.start()
    face_thread.start()
    start_event.set()

    while pedal_thread.is_alive() or face_thread.is_alive():
        if pedal_thread.frame is not None:
            pedal_frame = cv2.resize(pedal_thread.frame, (640, 480))
            cv2.imshow('Pedal Video Recorder', pedal_frame)
        if face_thread.frame is not None:
            face_frame = cv2.resize(face_thread.frame, (640, 480))
            cv2.imshow('Face Video Recorder', face_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            if pedal_thread.is_alive():
                pedal_thread.stop()
            if face_thread.is_alive():
                face_thread.stop()
            break

    pedal_thread.join()
    face_thread.join()
    cv2.destroyAllWindows()


if __name__ == "__main__":
     main()