"""Proctoring configuration and weights."""

# Risk Weights
TAB_SWITCH_WEIGHT = 10
TAB_SWITCH_REPEATED_WEIGHT = 15
TAB_SWITCH_FREQUENT_WEIGHT = 25

WINDOW_BLUR_WEIGHT = 5
WINDOW_BLUR_REPEATED_WEIGHT = 10
WINDOW_BLUR_FREQUENT_WEIGHT = 20

COPY_WEIGHT = 10
PASTE_WEIGHT = 20

DEVTOOLS_WEIGHT = 40

# ── NOT_IMPLEMENTED: Require audi_video microservice (CV/audio AI pipeline) ──
# These weights are defined for reference but will never be triggered
# without the audi_video service wired in (YOLO + STT + LLM analysis).
# See kf-proctoring-testing skill → references/audi-video-integration.md
NO_FACE_WEIGHT = 15
MULTIPLE_PERSONS_WEIGHT = 25

HEAD_POSE_WEIGHT = 8
HEAD_POSE_REPEATED_WEIGHT = 15

VOICE_DETECTED_WEIGHT = 20
CONTINUOUS_CONVERSATION_WEIGHT = 35

PHONE_DETECTED_WEIGHT = 80
FULLSCREEN_EXIT_WEIGHT = 20

# Risk Policy
RISK_TERMINATION_THRESHOLD = 100
# Risk decay: score reduces by 10% every 60 seconds with no violations.
# Formula: decayed = prev * (1 - DECAY_PERCENT) ^ (seconds / INTERVAL)
# Tuning guide:
#   5% / 60s → gentle, score 100 → 61 after 10 min clean
#  10% / 60s → moderate, score 100 → 35 after 10 min clean (default)
#  20% / 60s → aggressive, score 100 → 11 after 10 min clean
#   0% / 60s → purely cumulative, score never decays (debug/testing)
RISK_DECAY_PERCENT = 0.10  # 10% decay per interval
RISK_DECAY_INTERVAL = 60   # seconds per decay step

# Session Configuration
FRAME_CAPTURE_INTERVAL = 1.0  # Seconds
DEBOUNCE_INTERVAL = 5.0       # Ignore duplicate events within 5 seconds
WEBSOCKET_HEARTBEAT_TIMEOUT = 30
HIGH_RISK_AUTO_TERMINATE = True
