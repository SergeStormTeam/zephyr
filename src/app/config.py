import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger: logging.Logger = logging.getLogger(__name__)


def _get_env_variable(name: str, default: str | None = None) -> str | None:
    """
    Retrieves an environment variable, with an optional default value.

    Args:
        name (str): The name of the environment variable to retrieve.
        default (str | None): An optional default value to return if the environment variable is not set.

    Returns:
        str | None: The value of the environment variable, or the default value if it is not set.
    """

    try:
        value: str | None = os.getenv(name, default)

        if value in (None, ""):
            logger.warning(
                f"Environment variable '{name}' is not set, using default value: '{default if default is not None else 'None'}'"
            )
            return default

        return value
    except Exception as e:
        logger.error(f"Error retrieving environment variable '{name}': {e}")
        return default


# General Settings
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

# Server Settings
WEBSOCKET_RECONNECT_DEBOUNCE: int = 20
DATABASE_BACKUP_DEBOUNCE: int = 3
DATABASE_UPLOAD_BATCH_SIZE: int = 150

HTTP_URL: str | None = _get_env_variable("HTTP_URL")

SERVER_WS_URL: str | None = _get_env_variable("SERVER_WS_URL")
LAPTOP_WS_URL: str | None = _get_env_variable("LAPTOP_WS_URL")

SERVER_API_KEY: str | None = _get_env_variable("SERVER_API_KEY")

# Database Settings
DATABASE_FILENAME: str = "probedata.db"
DATABASE_QUEUE_MAX_SIZE: int = 1000

# Sensor Setting
SEA_LEVEL_PRESSURE: int = 1013
SENSOR_FAIL_SHUTDOWN_LIMIT: int = 5
SENSOR_READING_DEBOUNCE_TIME: float = 5
