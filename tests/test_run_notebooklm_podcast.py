import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_notebooklm_podcast.py"
SPEC = importlib.util.spec_from_file_location("run_notebooklm_podcast", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class RuntimePathsTests(unittest.TestCase):
    def test_runtime_paths_keep_state_and_logs_outside_delivery_folder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "karpathy-podcast"

            runtime = MODULE.runtime_paths(output_dir, "karpathy")

            self.assertEqual(runtime.state_path.name, "karpathy.notebooklm.state.json")
            self.assertEqual(runtime.log_path.name, "karpathy.notebooklm.log")
            self.assertNotEqual(runtime.state_path.parent, output_dir)
            self.assertNotEqual(runtime.log_path.parent, output_dir)
            self.assertEqual(runtime.audio_path, output_dir.resolve() / "karpathy.m4a")


class DownloadProgressTests(unittest.TestCase):
    def test_download_when_ready_emits_terminal_progress_until_audio_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / "ready.mp3"
            attempts = [
                mock.Mock(returncode=1, stderr="Audio overview is not ready yet.", stdout=""),
                mock.Mock(returncode=0, stderr="", stdout="downloaded"),
            ]

            def fake_run_retry(*_args, **_kwargs):
                result = attempts.pop(0)
                if result.returncode == 0:
                    audio_path.write_bytes(b"mp3")
                return result

            stdout = io.StringIO()
            with (
                mock.patch.object(MODULE, "run_retry", side_effect=fake_run_retry),
                mock.patch.object(MODULE.time, "sleep"),
                mock.patch.object(MODULE.time, "monotonic", side_effect=[0, 1, 2]),
                contextlib.redirect_stdout(stdout),
            ):
                MODULE.download_when_ready(
                    "nlm",
                    {},
                    "notebook-id",
                    audio_path,
                    timeout_seconds=10,
                    poll_seconds=1,
                )

            output = stdout.getvalue()
            self.assertIn("poll 1", output)
            self.assertIn("not ready", output)
            self.assertIn("downloaded", output)


class NotebookLmPyStatusTests(unittest.TestCase):
    def test_latest_notebooklm_py_audio_status_reads_artifact_json(self):
        payload = {
            "artifacts": [
                {"id": "older", "type_id": "audio", "status": "completed"},
                {"id": "latest", "type_id": "audio", "status": "in_progress"},
            ]
        }

        status = MODULE.latest_notebooklm_py_audio_status(payload)

        self.assertEqual(status["id"], "latest")
        self.assertEqual(status["status"], "in_progress")


if __name__ == "__main__":
    unittest.main()
