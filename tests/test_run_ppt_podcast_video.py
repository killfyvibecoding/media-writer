import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_ppt_podcast_video.py"
SPEC = importlib.util.spec_from_file_location("run_ppt_podcast_video", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PPTPodcastVideoTests(unittest.TestCase):
    def test_sorted_slide_images_use_numeric_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for name in ["slide_010.png", "slide_002.png", "slide_001.png"]:
                (root / name).write_bytes(b"png")

            ordered = MODULE.sorted_slide_images(root)

            self.assertEqual([p.name for p in ordered], ["slide_001.png", "slide_002.png", "slide_010.png"])

    def test_manifest_contains_required_defaults(self):
        manifest = MODULE.build_manifest(
            status="complete",
            output_dir=Path("/tmp/out"),
            stem="demo",
            audio=Path("/tmp/audio.m4a"),
            slide_source=Path("/tmp/slides"),
            slides_dir=Path("/tmp/out/demo_slides"),
            slide_count=3,
            transcript=Path("/tmp/out/demo_transcript.vtt"),
            keyword_overlays=[{"text": "AI基建", "start": 1.0, "end": 2.4, "slide": 1}],
            project_dir=Path("/tmp/out/demo_video_project"),
            output_video=Path("/tmp/out/demo_video.mp4"),
            render_command=["npx", "hyperframes", "render", "--output", "/tmp/out/demo_video.mp4"],
        )

        self.assertEqual(manifest["mode"], "ppt_podcast_video")
        self.assertEqual(manifest["style"], "strong_narrative_dynamic")
        self.assertEqual(manifest["aspect_ratio"], "16:9")
        self.assertEqual(manifest["slide_count"], 3)
        self.assertEqual(manifest["keyword_overlays"][0]["text"], "AI基建")

    def test_dry_run_writes_project_and_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            slides = root / "slides"
            slides.mkdir()
            (slides / "slide_001.png").write_bytes(b"png")
            (slides / "slide_002.png").write_bytes(b"png")
            audio = root / "audio.m4a"
            audio.write_bytes(b"audio")
            transcript = root / "transcript.vtt"
            transcript.write_text(
                "WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nAI 基建开始进入现实世界。\n",
                encoding="utf-8",
            )

            result = MODULE.run_pipeline(
                slide_source=slides,
                audio=audio,
                output_dir=root / "out",
                stem="demo",
                transcript=transcript,
                title="Demo Video",
                no_render=True,
                emit_json=False,
            )

            manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "project_ready")
            self.assertEqual(manifest["slide_count"], 2)
            self.assertTrue(Path(manifest["hyperframes_project"]).joinpath("index.html").exists())
            self.assertTrue(Path(manifest["hyperframes_project"]).joinpath("DESIGN.md").exists())

    def test_render_commands_are_lint_inspect_render_in_order(self):
        calls = []

        def fake_run(cmd, cwd):
            calls.append(cmd)
            return MODULE.CommandResult(returncode=0, stdout="ok", stderr="")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "project"
            project.mkdir()
            output = root / "video.mp4"
            output.write_bytes(b"mp4")

            MODULE.run_hyperframes_render(project, output, run_command=fake_run)

        self.assertEqual(calls[0][:3], ["npx", "hyperframes", "lint"])
        self.assertEqual(calls[1][:3], ["npx", "hyperframes", "inspect"])
        self.assertEqual(calls[2][:3], ["npx", "hyperframes", "render"])

    def test_json_transcript_is_parsed_and_long_captions_are_split(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript = Path(temp_dir) / "transcript.json"
            transcript.write_text(
                json.dumps(
                    {
                        "segments": [
                            {
                                "start": 0,
                                "end": 6,
                                "text": "AI 基建不是一个抽象概念，它正在变成企业、产品和个人工作流里真正可复用的底层能力，这意味着内容生产也会被重新组织。",
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            cues = MODULE.parse_transcript(transcript)

            self.assertGreater(len(cues), 1)
            self.assertEqual(cues[0]["start"], 0.0)
            self.assertLessEqual(max(len(str(cue["text"])) for cue in cues), 44)

    def test_render_failure_preserves_doctor_log(self):
        calls = []

        def fake_run(cmd, cwd):
            calls.append(cmd)
            if cmd[:3] == ["npx", "hyperframes", "inspect"]:
                return MODULE.CommandResult(returncode=1, stdout="", stderr="layout error")
            return MODULE.CommandResult(returncode=0, stdout="doctor ok", stderr="")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "project"
            project.mkdir()

            with self.assertRaises(MODULE.HyperFramesCommandError) as raised:
                MODULE.run_hyperframes_render(project, root / "video.mp4", run_command=fake_run)

        self.assertIn(["npx", "hyperframes", "doctor"], calls)
        self.assertEqual(raised.exception.logs[-1]["cmd"], ["npx", "hyperframes", "doctor"])

    def test_copy_asset_allows_same_source_and_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            asset = root / "audio.m4a"
            asset.write_bytes(b"audio")

            copied = MODULE.copy_asset(asset, root, asset.name)

            self.assertEqual(copied, asset.resolve())
            self.assertEqual(asset.read_bytes(), b"audio")

    def test_audio_extension_is_validated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            audio = root / "audio.txt"
            audio.write_text("not audio", encoding="utf-8")

            with self.assertRaises(ValueError):
                MODULE.ensure_audio_file(audio)

    def test_slide_segments_fit_known_audio_duration(self):
        segments = MODULE.segment_slides(1.0, 4)

        self.assertEqual(len(segments), 4)
        self.assertAlmostEqual(segments[-1]["start"] + segments[-1]["duration"], 1.0)


if __name__ == "__main__":
    unittest.main()
