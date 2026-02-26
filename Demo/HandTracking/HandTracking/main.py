import cv2
import numpy as np
import pyarrow as pa
from dora import Node
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands


def _landmark_vec(landmarks, idx):
    """Return landmark at idx as numpy array [x, y, z]."""
    lm = landmarks.landmark[idx]
    return np.array([lm.x, lm.y, lm.z])


def _tip_vector(landmarks, tip_idx, mcp_idx):
    """Return vector from MCP to tip for a finger."""
    tip = _landmark_vec(landmarks, tip_idx)
    mcp = _landmark_vec(landmarks, mcp_idx)
    return tip - mcp


def _hand_frame(landmarks_norm, is_right):
    """Build hand frame: origin at wrist, z toward middle MCP, x normal to palm."""
    origin = _landmark_vec(landmarks_norm, mp_hands.HandLandmark.WRIST)
    mid_mcp = _landmark_vec(landmarks_norm, mp_hands.HandLandmark.MIDDLE_FINGER_MCP)
    unit_z = mid_mcp - origin
    unit_z = unit_z / np.linalg.norm(unit_z)

    if is_right:
        vec_y = _landmark_vec(landmarks_norm, mp_hands.HandLandmark.PINKY_MCP) - origin
    else:
        vec_y = _landmark_vec(landmarks_norm, mp_hands.HandLandmark.INDEX_FINGER_MCP) - origin

    unit_x = np.cross(vec_y, unit_z)
    unit_x = unit_x / np.linalg.norm(unit_x)
    unit_y = np.cross(unit_z, unit_x)

    R = np.array([unit_x, -unit_y, unit_z]).reshape((3, 3))
    return R


def _process_hand(hand_proc, image):
    """Process image, draw landmarks, extract hand poses. Returns (image, r_res, l_res)."""
    image.flags.writeable = False
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hand_proc.process(image)
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    r_res = None
    l_res = None

    if not results.multi_hand_landmarks:
        return image, r_res, l_res

    for index, handedness in enumerate(results.multi_handedness):
        if handedness.classification[0].score <= 0.8:
            continue

        is_right = handedness.classification[0].label == "Right"
        hand_landmarks = results.multi_hand_world_landmarks[index]
        hand_landmarks_norm = results.multi_hand_landmarks[index]

        tip1 = _tip_vector(hand_landmarks, mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.INDEX_FINGER_MCP)
        tip2 = _tip_vector(hand_landmarks, mp_hands.HandLandmark.MIDDLE_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_MCP)
        tip3 = _tip_vector(hand_landmarks, mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.RING_FINGER_MCP)
        tip4 = _tip_vector(hand_landmarks, mp_hands.HandLandmark.THUMB_TIP, mp_hands.HandLandmark.THUMB_MCP)

        R = _hand_frame(hand_landmarks_norm, is_right)
        tip1_rot = R @ tip1
        tip2_rot = R @ tip2
        tip3_rot = R @ tip3
        tip4_rot = R @ tip4

        mp_drawing.draw_landmarks(
            image,
            hand_landmarks_norm,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style(),
        )

        tips = {"tip1": tip1_rot, "tip2": tip2_rot, "tip3": tip3_rot, "tip4": tip4_rot}
        prefix = "r" if is_right else "l"
        result = {f"{prefix}_{k}": v for k, v in tips.items()}

        if is_right:
            r_res = [result]
        else:
            l_res = [result]

    return image, r_res, l_res


def process_img(hand_proc, image):
    """Process image for hand tracking. Returns (image, r_res, l_res)."""
    return _process_hand(hand_proc, image)


def main():
    node = Node()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Camera 0 failed to open. Check device, permissions, or try another index.")
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera opened: {w}x{h}")

    with mp_hands.Hands(
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as hands:
        for event in node:
            if event["type"] == "INPUT" and event["id"] == "tick":
                ret, frame = cap.read()
                if not ret:
                    print("Camera read failed")
                    continue

                frame = cv2.flip(frame, 1)
                frame, r_res, l_res = process_img(hands, frame)

                if r_res is not None:
                    node.send_output("r_hand_pos", pa.array(r_res))
                if l_res is not None:
                    node.send_output("l_hand_pos", pa.array(l_res))

                try:
                    cv2.imshow("MediaPipe Hands", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                except cv2.error as e:
                    raise RuntimeError(
                        f"Display error (headless?): {e}. "
                        "Set DISPLAY or use X11 forwarding."
                    ) from e

            elif event["type"] == "ERROR":
                raise RuntimeError(event["error"])


if __name__ == "__main__":
    main()
