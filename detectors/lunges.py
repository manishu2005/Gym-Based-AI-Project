from core.base_excercise import BaseExercise

class LungesDetector(BaseExercise):
    DOWN_THRESHOLD = 100
    UP_THRESHOLD = 160
    MIN_VISIBILITY = 0.7
    BALANCE_TOLERANCE = 0.10

    LEFT_SHOULDER = 11
    LEFT_ANKLE = 27
    LEFT_KNEE = 25
    RIGHT_SHOULDER = 12
    RIGHT_KNEE = 26
    RIGHT_ANKLE = 28
    
    LEFT_HIP = 23
    RIGHT_HIP = 24

    def __init__(self):
        super().__init__()

    def reset(self) -> None:
        self.reps =0
        self.stage =None

    
    def process(self, landmarks)->dict:
        left_knee_angle = self.calculate_angle(
            self.get_points(landmarks, self.LEFT_HIP),
            self.get_points(landmarks, self.LEFT_KNEE),
            self.get_points(landmarks, self.LEFT_ANKLE)
        )

        right_knee_angle = self.calculate_angle(
            self.get_points(landmarks, self.RIGHT_HIP),
            self.get_points(landmarks, self.RIGHT_KNEE),
            self.get_points(landmarks, self.RIGHT_ANGLE)
        )

        if left_knee_angle <= right_knee_angle:
            front_knee_angle = left_knee_angle
            front_hip_idx = self.LEFT_HIP
            front_ankle_idx = self.LEFT_ANKLE
            front_knee_idx = self.LEFT_KNEE
            shoulder_idx_for_torso = self.LEFT_SHOULDER
        else:
            front_knee_angle = right_knee_angle
            front_hip_idx = self.RIGHT_HIP
            front_ankle_idx = self.RIGHT_ANKLE
            front_knee_idx = self.RIGHT_KNEE
            shoulder_idx_for_torso = self.RIGHT_SHOULDER

        key_landmarks_visible = (
            landmarks[front_hip_idx].visibility >= self.MIN_VISIBILITY and
            landmarks[front_knee_idx].visibility >= self.MIN_VISIBILITY and
            landmarks[front_ankle_idx].visibility >= self.MIN_VISIBILITY
        )

        if key_landmarks_visible:
            if front_knee_angle < self.DOWN_THRESHOLD:
                self.stage = "down"

            if front_knee_angle > self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self.reps += 1

        torso_angle = self.calculate_angle(
            self.get_points(landmarks, shoulder_idx_for_torso),
            self.get_points(landmarks, front_hip_idx),
            self.get_points(landmarks, front_knee_idx),

        )

        shoulder_mid_x = (landmarks[self.LEFT_SHOULDER].x + landmarks[self.RIGHT_SHOULDER].x) /2
        hip_mid_x = (landmarks[self.LEFT_HIP].x + landmarks[self.RIGHT_HIP].x) / 2
        lateral_offset = abs(shoulder_mid_x - hip_mid_x)

        if lateral_offset <= self.BALANCE_TOLERANCE:
            balance_status = "BALANCED"
        else:
            balance_status = "OFF BALANCE"
        return{
            "reps": self.reps,
            "front_knee_angle":int(front_knee_angle),
            "torso_angle": int(torso_angle),
            "balance_status":balance_status,
        }