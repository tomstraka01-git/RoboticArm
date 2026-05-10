import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7) as hands:
    while True:
        ret, frame = cap.read()
        frame = cv2.flip(frame, 1)  # mirror so it feels natural
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # get a specific landmark — index fingertip is landmark 8
                index_tip = hand_landmarks.landmark[8]
                x = index_tip.x  # 0.0 to 1.0 across screen width
                y = index_tip.y  # 0.0 to 1.0 across screen height
                z = index_tip.z  # depth, negative = closer to camera

                print(f"Index tip: x={x:.2f} y={y:.2f} z={z:.2f}")

        cv2.imshow("Hands", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()