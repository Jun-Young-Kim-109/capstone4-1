# Master Branch Code Analysis

> NOTE: The repository currently exposes only the `work` branch, whose HEAD commit message indicates that it mirrors the "main" branch code. The following analysis therefore documents the effective master-branch codebase as represented in this branch.

## High-Level Architecture
- **`jun.py`** orchestrates the application. It sets up dual camera capture threads (pedal view on `/dev/video0`, driver face on `/dev/video2`), integrates OBD-II telemetry, and coordinates collision-triggered buffered recording with asynchronous upload to remote endpoints.【F:jun.py†L1-L202】【F:jun.py†L203-L318】
- **`threadingvideo.py`** is an earlier variant of the threading logic. It similarly implements buffered capture for two cameras, but manages its own OBD connection and lacks the centralized state-sharing provided in `jun.py`. The file appears to be legacy/testing code kept for reference.【F:threadingvideo.py†L1-L199】【F:threadingvideo.py†L200-L313】
- **`OBDModules.py`** defines asynchronous callbacks for querying numerous OBD-II PIDs, feeding results into a global `OBDState` singleton for thread-safe sharing. It also wraps connection initialization via `OBDConnection` and exposes `ecu_connections` to register watched commands.【F:OBDModules.py†L1-L198】【F:OBDModules.py†L199-L226】
- **Sensor modules** such as `gyro_sensor.py`, `collision_sensor.py`, and `Sensor.py` expose hardware-specific functionality (MPU-6050 gyro/accelerometer via I2C, digital collision switch via GPIO 15, and a console demo loop respectively).【F:gyro_sensor.py†L1-L60】【F:collision_sensor.py†L1-L15】【F:Sensor.py†L1-L32】
- **Utility modules** include `calculate_distance.py` (integrates traveled distance from speed samples), `GPS.py` (parses NMEA sentences for position/speed), and `obd_state.py` (thread-safe telemetry cache).【F:calculate_distance.py†L1-L26】【F:GPS.py†L1-L39】【F:obd_state.py†L1-L31】

## Data Flow Overview
1. **OBD-II Telemetry**
   - `jun.py` instantiates `OBDConnection` and passes the connection to `OBDModules.ecu_connections`, registering asynchronous watchers for speed, RPM, throttle position, engine load, and other metrics.【F:jun.py†L203-L260】【F:OBDModules.py†L1-L198】
   - The callbacks update `OBDState`, enabling `VideoCaptureThread` to overlay live telemetry on camera frames without directly querying the adapter each frame.【F:jun.py†L73-L143】【F:obd_state.py†L1-L31】

2. **Video Capture & Recording**
   - Two instances of `VideoCaptureThread` capture frames from the pedal and face cameras. Each maintains a deque buffer holding up to two minutes of frames to provide pre- and post-event coverage when recording is triggered.【F:jun.py†L27-L158】
   - A hardware button on GPIO pin 15 (via wiringPi) starts a 3-second countdown; once held long enough, buffered frames are flushed to disk, encoded to H.264 via `ffmpeg`, and uploaded asynchronously to configured endpoints.【F:jun.py†L59-L158】
   - Collision detection (via `handle_collision_detected`) or manual presses reuse the same mechanism to ensure consistent behavior.【F:jun.py†L118-L145】

3. **Sensor Telemetry**
   - Gyro data from `gyro_sensor.get_gyro_data()` is overlaid on the face-camera stream, while the pedal stream displays OBD-derived telemetry and optional warnings about connection issues.【F:jun.py†L88-L118】【F:gyro_sensor.py†L1-L60】
   - The standalone `Sensor.py` script demonstrates raw sensor readings and collision status output for diagnostic purposes.【F:Sensor.py†L1-L32】

4. **GPS & Distance Tracking**
   - `GPS.py` reads NMEA sentences over `/dev/ttyS0`, pairing `GGA` (position) with `VTG` (speed) messages to log localized coordinates and speed in KST. This module currently runs as a blocking loop, suggesting intended separate execution on the hardware platform.【F:GPS.py†L1-L39】
   - `calculate_distance.calculate_distance` integrates distance using elapsed time and latest speed sample; the function is referenced in `OBDModules` for future usage but not yet wired into `jun.py`.【F:calculate_distance.py†L1-L26】【F:OBDModules.py†L1-L198】

## Notable Observations
- **Thread Safety & Shared State**: `jun.py` introduces a shared `frame_buffer_lock` passed to both camera threads, but each thread keeps its own buffer. The lock currently guards per-thread buffer writes; consider whether cross-thread coordination is necessary or if independent locks per thread suffice.【F:jun.py†L203-L260】
- **Resource Management**: `VideoCaptureThread.stop_recording` ensures `VideoWriter` resources are released before re-encoding and uploading. However, error handling around `ffmpeg` execution could benefit from logging integration for easier diagnostics.【F:jun.py†L130-L205】
- **Legacy Module**: `threadingvideo.py` duplicates much of `jun.py` with subtle differences (e.g., direct OBD queries instead of using `OBDState`). If `jun.py` supersedes it, consider deprecating or consolidating to reduce maintenance overhead.【F:threadingvideo.py†L1-L199】【F:threadingvideo.py†L200-L313】
- **GPIO & WiringPi**: Multiple modules assume `wiringPiSetup()` succeeds. On non-Raspberry Pi environments, these calls will fail; stubbing or conditional initialization may be necessary for development/testing contexts.【F:jun.py†L41-L110】【F:collision_sensor.py†L1-L15】

## Potential Enhancement Areas
- **Error Recovery**: Implement retries/backoff around camera initialization, OBD connections, and HTTP uploads to improve resilience during transient failures.
- **Configuration Management**: Extract hard-coded paths (video devices, output directories, upload URLs) into a configuration file or environment variables to simplify deployment changes.
- **Testing Strategy**: Abstract hardware interactions behind interfaces to enable unit testing without physical devices.

This analysis should help onboard developers to the effective master branch codebase and highlight focal points for further development.
