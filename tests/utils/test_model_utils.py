import pathlib
import unittest.mock

import pytest

import strands_agents_builder
import strands_agents_builder.utils.model_utils


@pytest.fixture
def cwd(tmp_path):
    with unittest.mock.patch.object(strands_agents_builder.utils.model_utils.pathlib.Path, "cwd") as mock_cwd:
        mock_cwd.return_value = tmp_path
        yield tmp_path


@pytest.fixture
def custom_model_dir(cwd):
    dir = cwd / ".models"
    dir.mkdir()

    return dir


@pytest.fixture
def packaged_model_dir():
    return pathlib.Path(strands_agents_builder.models.__file__).parent


@pytest.fixture
def config_str():
    return '{"model_id": "test"}'


@pytest.fixture
def config_path(config_str, tmp_path):
    path = tmp_path / "config.json"
    path.write_text(config_str)

    return path


def test_load_path_custom(custom_model_dir):
    model_path = custom_model_dir / "test.py"
    model_path.touch()

    tru_path = strands_agents_builder.utils.model_utils.load_path("test")
    exp_path = model_path
    assert tru_path == exp_path


@pytest.mark.parametrize("name", ["bedrock", "ollama"])
def test_load_path_packaged(name, packaged_model_dir):
    tru_path = strands_agents_builder.utils.model_utils.load_path(name).resolve()
    exp_path = packaged_model_dir / f"{name}.py"
    assert tru_path == exp_path


def test_load_path_missing():
    with pytest.raises(ImportError):
        strands_agents_builder.utils.model_utils.load_path("invalid")


def test_load_config_str(config_str):
    tru_config = strands_agents_builder.utils.model_utils.load_config(config_str)
    exp_config = {"model_id": "test"}
    assert tru_config == exp_config


def test_load_config_path(config_path):
    tru_config = strands_agents_builder.utils.model_utils.load_config(str(config_path))
    exp_config = {"model_id": "test"}
    assert tru_config == exp_config


def test_load_model(custom_model_dir):
    model_path = custom_model_dir / "test_model.py"
    model_path.write_text("def instance(**config): return config")

    tru_result = strands_agents_builder.utils.model_utils.load_model(model_path, {"k1": "v1"})
    exp_result = {"k1": "v1"}
    assert tru_result == exp_result
