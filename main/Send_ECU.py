import datetime

import requests

from obd_state import OBDState
def send_data_to_server(state_data):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Timestamp를 데이터에 추가
    data_with_timestamp = {"timestamp": timestamp, **state_data}

    url = "https://sw--zqbli.run.goorm.site/ecu"
    response = requests.post(url, json=data_with_timestamp)

    if response.status_code == 200:
        print("Data successfully sent to server.")
    else:
        print(f"Failed to send data with status code: {response.status_code}, {response.text}")


def periodic_data_sender():
    obd_state_instance = OBDState()  # 싱글턴 인스턴스를 가져옵니다.
    while True:
        state_data = obd_state_instance.get_state()
        send_data_to_server(state_data)  # 인스턴스 대신 상태 데이터를 전달합니다.
        #time.sleep(0.2)