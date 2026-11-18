"""Memory checks for the DGX Spark lessons (local-first fork). Read-only helpers."""

import io
import json

import pytest

import workshop_support
from workshop_support import spark


def meminfo(tmp_path, gb):
    path = tmp_path / "meminfo"
    path.write_text(f"MemTotal: {128 * 1024 ** 2} kB\nMemAvailable: {int(gb * 1024 ** 2)} kB\n")
    return path


def test_available_memory_reads_meminfo(tmp_path):
    assert spark.available_memory_gb(meminfo(tmp_path, 12.5)) == pytest.approx(12.5)
    assert spark.available_memory_gb(tmp_path / "missing") is None


def test_running_chat_model_is_reported_with_the_stop_instruction(tmp_path, capsys):
    assert not spark.check_memory_for("GRPO training", 45, meminfo_path=meminfo(tmp_path, 10), chat_running=True)
    out = capsys.readouterr().out
    assert "NVIDIA Sync -> Models -> Stop" in out and "114 GB" in out


def test_enough_memory_after_stopping_reminds_to_restart(tmp_path, capsys):
    assert spark.check_memory_for("GRPO training", 45, meminfo_path=meminfo(tmp_path, 110), chat_running=False)
    out = capsys.readouterr().out
    assert "OK" in out and "NVIDIA Sync -> Models -> Start" in out


def test_low_memory_without_the_chat_model_points_at_other_processes(tmp_path, capsys):
    assert not spark.check_memory_for("GRPO training", 45, meminfo_path=meminfo(tmp_path, 10), chat_running=None)
    assert "other notebook kernels" in capsys.readouterr().out


def test_chat_model_running_asks_the_gateway(monkeypatch):
    monkeypatch.setenv("NVIDIA_BASE_URL", "http://local-gateway:8000/v1")
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        return io.BytesIO(json.dumps({"data": [{"id": workshop_support.get_model("chat")}]}).encode())

    monkeypatch.setattr(spark.urllib.request, "urlopen", fake_urlopen)
    assert spark.chat_model_running() is True
    assert seen["url"] == "http://local-gateway:8000/v1/models"
    monkeypatch.setattr(spark.urllib.request, "urlopen",
                        lambda request, timeout: io.BytesIO(b'{"data": [{"id": "Qwen/Qwen3-Embedding-0.6B"}]}'))
    assert spark.chat_model_running() is False

    def refused(request, timeout):
        raise OSError("connection refused")
    monkeypatch.setattr(spark.urllib.request, "urlopen", refused)
    assert spark.chat_model_running() is None


def test_hosted_mode_has_no_local_chat_model(monkeypatch):
    monkeypatch.delenv("NVIDIA_BASE_URL", raising=False)
    assert spark.chat_model_running() is None
