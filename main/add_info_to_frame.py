import datetime

import cv2

from obd_state import OBDState


def add_info_to_frame(frame, fps, obd_error_shown, obd_connected, obd_connection):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, current_time, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"FPS: {fps}", (500, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # OBD 상태 정보를 가져옵니다.
    obd_state = OBDState.get_state()

    # 각 상태 정보를 추출합니다.
    speed_text = str(obd_state.get("speed", "N/A"))
    rpm_text = str(obd_state.get("rpm", "N/A"))
    throttle_text = str(obd_state.get("throttle_pos", "N/A"))
    load_text = str(obd_state.get("load", "N/A"))

    # 프레임에 OBD 정보를 추가합니다.
    obd_info_text = f"Speed: {speed_text} RPM: {rpm_text} Throttle: {throttle_text} Load: {load_text}"
    cv2.putText(frame, obd_info_text, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    return frame, obd_error_shown