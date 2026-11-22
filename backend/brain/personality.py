from config.settings import APP_NAME, OWNER_NAME
class Personality:

    def __init__(self):

        self.name = APP_NAME

        self.owner = OWNER_NAME

        self.mode = "Friendly"

    def intro(self):

        return (
            f"Hello {self.owner}! "
            f"I'm {self.name}. "
            f"My current personality is {self.mode}."
        )

    def greeting(self):

        if self.mode == "Friendly":
            return f"👋 Hello {self.owner}! Nice to see you."

        if self.mode == "Professional":
            return "Good day."

        return "Hello."