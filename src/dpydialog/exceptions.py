import discord


class TimedMessage(Exception):
    def __init__(self, message: discord.Message, timestamp: float,
                 *args) -> None:
        self.message = message
        self.timestamp = timestamp
        super().__init__(*args)


class TimedOut(TimedMessage):
    """The dialog has timed out.
    
    """
class Cancelled(TimedMessage):
    """The dialog has been cancelled.
    
    """
