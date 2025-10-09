def calculate_driving_score(speed, rpm, load, throttle_pos):
    global driving_score

    speed_weight = 0.1
    rpm_weight = 0.1
    load_weight = 0.1
    throttle_pos_weight = 0.1

    # Store previous driving score
    previous_driving_score = driving_score

    # Decrease driving score based on speed, RPM, and load
    if int(speed) >= 80:
        speed_ratio = (int(speed) - 20) / 80  # Adjust speed range and calculate ratio (0 to 1)
        speed_penalty = (speed_ratio ** 0.5) * speed_weight  # Apply square root of ratio to penalty unit
        driving_score -= speed_penalty

    if int(rpm) >= 2500:
        rpm_ratio = (int(rpm) - 1800) / 2000  # Adjust RPM range and calculate ratio (0 to 1)
        rpm_penalty = (rpm_ratio ** 0.5) * rpm_weight  # Apply square root of ratio to penalty unit
        driving_score -= rpm_penalty

    if int(load) >= 50:
        load_ratio = (int(load) - 35) / 65  # Adjust load range and calculate ratio (0 to 1)
        load_penalty = (load_ratio ** 0.5) * load_weight  # Apply square root of ratio to penalty unit
        driving_score -= load_penalty

    if int(throttle_pos) >= 30:
        throttle_pos_ratio = (
                                         int(throttle_pos) - 25) / 75  # Adjust throttle position range and calculate ratio (0 to 1)
        throttle_pos_penalty = (
                                           throttle_pos_ratio ** 0.5) * throttle_pos_weight  # Apply square root of ratio to penalty unit
        driving_score -= throttle_pos_penalty

    driving_score = max(driving_score, 0)

    return driving_score