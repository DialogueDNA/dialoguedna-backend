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
                    "emotions:run",
                    "summary:run"
                },
            "enterprise":
                {
                    "*"
                }
        }