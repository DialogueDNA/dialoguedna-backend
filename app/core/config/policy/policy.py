from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyConfig:
    POLICY = \
        {
            "free":
                {
                    "transcription:run"
                },
            "pro":
                {
                    "transcription:run",
                    "emotion_analysis:run",
                    "summary:run"
                },
            "enterprise":
                {
                    "*"
                }
        }