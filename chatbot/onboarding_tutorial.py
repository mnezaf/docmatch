class ChatBot:
    """Constructs the onboarding message and stores the state of which tasks were completed."""

    WELCOME_BLOCK = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                "Welcome to Docmatch! :wave: I am here to help you :blush:\n\n"
            ),
        },
    }
    DIVIDER_BLOCK = {"type": "divider"}

    SYMPTOM_BLOCK = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                "*Please describe your signs and symptoms. When finished please type \'done\'.*"
            ),
        },
    }

    def __init__(self, channel):
        self.channel = channel
        self.username = "docmatch"
        self.icon_emoji = "icon.jpeg"
        self.timestamp = ""
        self.reaction_task_completed = False
        self.pin_task_completed = False

    def get_message_onboarding(self):
        return {
            "ts": self.timestamp,
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "blocks": [
                self.WELCOME_BLOCK,
                self.SYMPTOM_BLOCK,
                self.DIVIDER_BLOCK,
            ],
        }

    def get_message_payload(self, block):
        return {
            "ts": self.timestamp,
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "blocks": [block],
        }

    @staticmethod
    def _get_checkmark(task_completed: bool) -> str:
        if task_completed:
            return ":white_check_mark:"
        return ":white_large_square:"

    @staticmethod
    def _get_task_block(text, information):
        return [
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": information}]},
        ]
    
