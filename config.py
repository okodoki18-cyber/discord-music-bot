import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SOUNDCLOUD_CLIENT_ID = os.getenv('SOUNDCLOUD_CLIENT_ID')
PREFIX = os.getenv('PREFIX', '!')

# Bot Settings
INACTIVITY_TIMEOUT = 300  # 5 minutes in seconds
MAX_QUEUE_SIZE = 100
EMBED_COLOR = 0x00ff00  # Green

# Voice Channel Settings
AUTO_LEAVE_DELAY = 60  # 1 minute after inactivity
