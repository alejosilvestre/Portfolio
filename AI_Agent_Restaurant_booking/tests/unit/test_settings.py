"""
===========================================================
TEST SETTINGS - Tests para config/settings.py
===========================================================

Tests unitarios para la configuración de la aplicación.
"""

import pytest
import os
from unittest.mock import patch, MagicMock


class TestLoadConfig:
    """Tests para la función load_config."""

    def test_load_config_with_all_required_vars(self, mock_env_vars):
        """Verifica carga exitosa con todas las variables requeridas."""
        with patch("config.settings.load_dotenv"):
            from config.settings import load_config

            config = load_config()

            assert config["OPENAI_API_KEY"] == "test-openai-key"
            assert config["GOOGLE_MAPS_API_KEY"] == "test-google-maps-key"
            assert config["TAVILY_API_KEY"] == "test-tavily-key"
            assert config["MODEL_NAME"] == "gpt-4o-mini"
            assert config["TEMPERATURE"] == 0.3

    def test_load_config_missing_openai_key_raises_error(self, monkeypatch):
        """Verifica error cuando falta OPENAI_API_KEY."""
        monkeypatch.setenv("OPENAI_API_KEY", "")
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test-key")
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")

        with patch("config.settings.load_dotenv"):
            # Reimportar para aplicar cambios
            import importlib
            import config.settings as settings_module

            with pytest.raises(ValueError) as exc_info:
                importlib.reload(settings_module)
                settings_module.load_config()

            assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_load_config_missing_google_maps_key_raises_error(self, monkeypatch):
        """Verifica error cuando falta GOOGLE_MAPS_API_KEY."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "")
        monkeypatch.setenv("TAVILY_API_KEY", "test-key")

        with patch("config.settings.load_dotenv"):
            import importlib
            import config.settings as settings_module

            with pytest.raises(ValueError) as exc_info:
                importlib.reload(settings_module)
                settings_module.load_config()

            assert "GOOGLE_MAPS_API_KEY" in str(exc_info.value)

    def test_load_config_missing_tavily_key_raises_error(self, monkeypatch):
        """Verifica error cuando falta TAVILY_API_KEY."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test-key")
        monkeypatch.setenv("TAVILY_API_KEY", "")

        with patch("config.settings.load_dotenv"):
            import importlib
            import config.settings as settings_module

            with pytest.raises(ValueError) as exc_info:
                importlib.reload(settings_module)
                settings_module.load_config()

            assert "TAVILY_API_KEY" in str(exc_info.value)

    def test_load_config_default_values(self, mock_env_vars, monkeypatch):
        """Verifica valores por defecto."""
        # No establecer MODEL_NAME para usar default
        monkeypatch.delenv("MODEL_NAME", raising=False)

        with patch("config.settings.load_dotenv"):
            from config.settings import load_config

            config = load_config()

            # Debería usar el default "gpt-4o-mini"
            assert config["MODEL_NAME"] == "gpt-4o-mini"

    def test_load_config_temperature_conversion(self, mock_env_vars, monkeypatch):
        """Verifica conversión de TEMPERATURE a float."""
        monkeypatch.setenv("TEMPERATURE", "0.7")

        with patch("config.settings.load_dotenv"):
            from config.settings import load_config

            config = load_config()

            assert isinstance(config["TEMPERATURE"], float)
            assert config["TEMPERATURE"] == 0.7

    def test_langsmith_tracing_enabled(self, mock_env_vars, monkeypatch):
        """Verifica habilitación de LangSmith tracing."""
        monkeypatch.setenv("LANGSMITH_TRACING", "true")
        monkeypatch.setenv("LANGSMITH_API_KEY", "test-langsmith-key")

        with patch("config.settings.load_dotenv"):
            from config.settings import load_config

            config = load_config()

            assert config["LANGSMITH_TRACING"] is True

    def test_langsmith_tracing_disabled(self, mock_env_vars, monkeypatch):
        """Verifica deshabilitación de LangSmith tracing."""
        monkeypatch.setenv("LANGSMITH_TRACING", "false")

        with patch("config.settings.load_dotenv"):
            from config.settings import load_config

            config = load_config()

            assert config["LANGSMITH_TRACING"] is False

    def test_load_config_data_dir(self, mock_env_vars):
        """Verifica configuración de DATA_DIR."""
        with patch("config.settings.load_dotenv"):
            from config.settings import load_config

            config = load_config()

            assert "DATA_DIR" in config
            assert "data" in config["DATA_DIR"]

    def test_load_config_threshold_values(self, mock_env_vars):
        """Verifica valores de threshold."""
        with patch("config.settings.load_dotenv"):
            from config.settings import load_config

            config = load_config()

            # Verificar que los thresholds tienen valores por defecto
            assert "THRESHOLD_REQUIREMENT_EXTRACTION" in config
            assert isinstance(config["THRESHOLD_REQUIREMENT_EXTRACTION"], float)
            assert "THRESHOLD_CV_FAITHFULNESS" in config
            assert isinstance(config["THRESHOLD_CV_FAITHFULNESS"], float)

    def test_langsmith_sets_environment_variables(self, mock_env_vars, monkeypatch):
        """Verifica que LangSmith configura variables de entorno."""
        monkeypatch.setenv("LANGSMITH_TRACING", "true")
        monkeypatch.setenv("LANGSMITH_API_KEY", "test-langsmith-key")
        monkeypatch.setenv("LANGSMITH_PROJECT", "test-project")

        with patch("config.settings.load_dotenv"):
            from config.settings import load_config

            load_config()

            # Verificar que se establecen las variables de entorno
            assert os.environ.get("LANGSMITH_TRACING") == "true"
            assert os.environ.get("LANGCHAIN_API_KEY") == "test-langsmith-key"

    def test_deepeval_configuration(self, mock_env_vars, monkeypatch):
        """Verifica configuración de DeepEval."""
        monkeypatch.setenv("DEEPEVAL_API_KEY", "test-deepeval-key")
        monkeypatch.setenv("CONFIDENT_API_KEY", "test-confident-key")

        with patch("config.settings.load_dotenv"):
            from config.settings import load_config

            config = load_config()

            assert config["DEEPEVAL_API_KEY"] == "test-deepeval-key"
            assert config["CONFIDENT_API_KEY"] == "test-confident-key"
