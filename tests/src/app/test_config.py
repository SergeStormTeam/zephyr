import sys
import importlib


def import_config_module() -> object:
    """
    Helper function to import the config module after modifying environment variables.

    Returns:
            object: The imported config module.
    """

    if "app.config" in sys.modules:
        del sys.modules["config"]

    return importlib.import_module("app.config")


def test_get_env_variable(monkeypatch) -> None:
    """
    Test the _get_env_variable function to ensure it retrieves environment variables correctly.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
    """

    monkeypatch.setenv("TEST_ENV_VAR", "test_value")
    cfg = import_config_module()

    assert cfg._get_env_variable("TEST_ENV_VAR", None) == "test_value"
    assert cfg._get_env_variable("NON_EXISTENT_VAR", "default_value") == "default_value"
    assert cfg._get_env_variable("NON_EXISTENT_VAR", None) is None
