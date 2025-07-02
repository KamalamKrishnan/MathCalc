import cv2
from cvzone.HandTrackingModule import HandDetector
import time

cap = cv2.VideoCapture(0)
detector = HandDetector(detectionCon=0.9, maxHands=2)

expression = ""
last_added = ""
last_action_time = 0
cooldown = 1.0  # seconds
show_result = False

# Number mappings (Left Hand)
number_dict = {
    (0, 0, 0, 0, 0): '0',
    (0, 1, 0, 0, 0): '1',
    (0, 1, 1, 0, 0): '2',
    (0, 1, 1, 1, 0): '3',
    (0, 1, 1, 1, 1): '4',
    (1, 1, 1, 1, 1): '5',
    (1, 0, 0, 0, 0): '6',
    (1, 1, 0, 0, 0): '7',
    (1, 1, 1, 0, 0): '8',
    (1, 0, 1, 1, 1): '9',
}

# Operator mappings (Right Hand)
operator_dict = {
    (1, 0, 0, 0, 0): '+',      # Thumb
    (0, 1, 0, 0, 0): '-',      # Index
    (0, 1, 1, 0, 0): '*',      # Index + Middle
    (1, 1, 0, 0, 0): '/',      # Thumb + Index
}

font = cv2.FONT_HERSHEY_SIMPLEX


def stable_match(fingers, target, tolerance=0):
    return sum([f1 != f2 for f1, f2 in zip(fingers, target)]) <= tolerance


while True:
    success, img = cap.read()
    hands, img = detector.findHands(img)

    current_time = time.time()

    if hands:
        left_fingers = right_fingers = None

        for hand in hands:
            fingers = detector.fingersUp(hand)
            if hand["type"] == "Left":
                left_fingers = tuple(fingers)
            elif hand["type"] == "Right":
                right_fingers = tuple(fingers)

        # LEFT HAND: Number Input
        if left_fingers:
            for pattern, digit in number_dict.items():
                if stable_match(left_fingers, pattern):
                    if current_time - last_action_time > cooldown and last_added != digit:
                        expression += digit
                        last_added = digit
                        last_action_time = current_time
                        show_result = False
                        break

        # RIGHT HAND: Operator Input or Action
        if right_fingers:
            # Operators
            for pattern, op in operator_dict.items():
                if stable_match(right_fingers, pattern):
                    if current_time - last_action_time > cooldown and last_added != op:
                        expression += op
                        last_added = op
                        last_action_time = current_time
                        show_result = False
                        break

            # Evaluate = Right ✊ (Fist)
            if stable_match(right_fingers, (0, 0, 0, 0, 0)):
                if current_time - last_action_time > cooldown:
                    try:
                        result = eval(expression)
                        expression = str(round(result, 2))
                        show_result = True
                    except:
                        expression = "Error"
                        show_result = True
                    last_action_time = current_time
                    last_added = ""

            # Clear All = Right 🖐️ (All fingers up)
            elif stable_match(right_fingers, (1, 1, 1, 1, 1)):
                if current_time - last_action_time > cooldown:
                    expression = ""
                    last_action_time = current_time
                    last_added = ""
                    show_result = False

            # Delete Last = Right Pinky Only
            elif stable_match(right_fingers, (0, 0, 0, 0, 1)):
                if current_time - last_action_time > cooldown and len(expression) > 0:
                    expression = expression[:-1]
                    last_action_time = current_time
                    last_added = ""
                    show_result = False

    # Display Expression or Result
    if expression != "":
        label = "Result:" if show_result else "Expr:"
        color = (0, 0, 0)
        cv2.putText(img, f"{label} {expression}",
                    (50, 70), font, 1.2, color, 3)

    cv2.imshow("Gesture Math Calculator", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
