import subprocess


def configure_camera(device, width=640, height=480, frame_rate=30):
    try:
        subprocess.run(['v4l2-ctl', '-d', device, '--set-fmt-video=width={},height={},pixelformat=0'.format(width, height)], check=True)
        subprocess.run(['v4l2-ctl', '-d', device, '--set-parm={}'.format(frame_rate)], check=True)
        print(f"Camera {device} configured: {width}x{height} at {frame_rate}fps")
    except subprocess.CalledProcessError as e:
        print(f"Failed to configure camera {device}: {e}")