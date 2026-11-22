"""ASTRA vision service: face presence + emotion via webcam.

Privacy rules:
- frames processed locally only, never uploaded
- only landmark coordinates are used; no video is stored
- requires explicit enabling (presence mode)
"""

import time


class VisionService:
    def __init__(self):
        self.enabled = False
        self.present = False          # face currently in frame
        self.mood = "normal"          # happy / sad / neutral / unknown
        self.last_seen = 0.0
        self._face_cascade = None
        self._hands = None
        self._mp = None

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def enable(self):
        self.enabled = True
        self._load_models()

    def disable(self):
        self.enabled = False
        self.present = False

    def _load_models(self):
        try:
            import cv2  # noqa
            self._cv2 = cv2
        except Exception as exc:
            print(f"[vision] opencv unavailable: {exc}")
            self._cv2 = None
            return

        try:
            import mediapipe as mp
            self._mp = mp
            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                max_num_faces=1, refine_landmarks=False
            )
            self._hands = mp.solutions.hands.Hands(
                max_num_faces=1, max_num_hands=1
            )
        except Exception as exc:
            print(f"[vision] mediapipe unavailable: {exc}")
            self._face_mesh = None
            self._hands = None

    # ---------------------------------------------------------
    # Frame processing (called by camera loop)
    # ---------------------------------------------------------

    def process_frame(self, frame):
        """frame: numpy array from cv2. Returns dict of detections."""
        if not self.enabled or self._cv2 is None:
            return {"enabled": False}

        rgb = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
        result = {"enabled": True, "present": False, "mood": "unknown", "gesture": None}

        if self._face_mesh is not None:
            faces = self._face_mesh.process(rgb)
            if faces.multi_face_landmarks:
                result["present"] = True
                result["mood"] = self._estimate_mood(faces.multi_face_landmarks[0])
                self.present = True
                self.last_seen = time.time()

        if self._hands is not None:
            hands = self._hands.process(rgb)
            if hands.multi_hand_landmarks:
                result["gesture"] = self._classify_gesture(hands.multi_hand_landmarks[0])

        if not result["present"]:
            self.present = False

        self.mood = result["mood"] if result["present"] else "absent"
        return result

    # ---------------------------------------------------------
    # Simple heuristics (no ML model files needed)
    # ---------------------------------------------------------

    def _estimate_mood(self, landmarks) -> str:
        """Very rough mouth-corner heuristic from face mesh landmarks.
        Real emotion model can replace this later."""
        try:
            # landmark 61 = left mouth corner, 291 = right mouth corner,
            # 0 = forehead top area, 17 = chin — crude smile ratio
            lm = landmarks.landmark
            mouth_w = abs(lm[291].x - lm[61].x)
            face_h = abs(lm[152].y - lm[10].y) or 1e-6
            ratio = mouth_w / face_h
            if ratio > 0.55:
                return "happy"
            return "neutral"
        except Exception:
            return "neutral"

    def _classify_gesture(self, hand) -> str:
        """Basic gesture: open palm vs pinch (thumb+index close)."""
        try:
            lm = hand.landmark
            thumb_tip = lm[4]
            index_tip = lm[8]
            dist = abs(thumb_tip.x - index_tip.x) + abs(thumb_tip.y - index_tip.y)
            return "pinch" if dist < 0.08 else "open_palm"
        except Exception:
            return None


vision = VisionService()
