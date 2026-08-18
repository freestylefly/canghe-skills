import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import seedance_video


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class AtlasVideoTests(unittest.TestCase):
    @patch.dict(os.environ, {"ATLASCLOUD_API_KEY": "test-key"}, clear=False)
    @patch.object(seedance_video, "download_video")
    @patch.object(seedance_video.time, "sleep", return_value=None)
    @patch.object(seedance_video.urllib.request, "urlopen")
    def test_atlas_submits_once_and_polls_prediction(
        self,
        urlopen,
        _sleep,
        download_video
    ):
        urlopen.side_effect = [
            FakeResponse({"code": 200, "data": {"id": "prediction-1"}}),
            FakeResponse({
                "code": 200,
                "data": {
                    "status": "completed",
                    "outputs": ["https://example.com/video.mp4"]
                }
            })
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "character.png"
            image_path.write_bytes(b"png-data")
            result = seedance_video.generate_video_task(
                prompt="漫画角色挥手",
                image_path=str(image_path),
                duration=5,
                resolution="1080p",
                output_dir=temp_dir,
                provider="atlas"
            )

        self.assertEqual(urlopen.call_count, 2)
        submit_request = urlopen.call_args_list[0].args[0]
        prediction_request = urlopen.call_args_list[1].args[0]
        submit_body = json.loads(submit_request.data.decode("utf-8"))
        self.assertEqual(submit_request.method, "POST")
        self.assertEqual(
            submit_body["model"],
            "bytedance/seedance-2.5/image-to-video"
        )
        self.assertEqual(submit_body["ratio"], "adaptive")
        self.assertTrue(submit_body["image"].startswith("data:image/png;base64,"))
        self.assertIn("/model/prediction/prediction-1", prediction_request.full_url)
        download_video.assert_called_once_with(
            "https://example.com/video.mp4",
            result
        )

    @patch.dict(os.environ, {"ARK_API_KEY": "test-key"}, clear=False)
    @patch.object(seedance_video, "download_video")
    @patch.object(seedance_video.time, "sleep", return_value=None)
    @patch.object(seedance_video.urllib.request, "urlopen")
    def test_volcengine_remains_the_default_provider(
        self,
        urlopen,
        _sleep,
        download_video
    ):
        urlopen.side_effect = [
            FakeResponse({"id": "task-1"}),
            FakeResponse({
                "status": "succeeded",
                "content": {"video_url": "https://example.com/volc.mp4"}
            })
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "character.png"
            image_path.write_bytes(b"png-data")
            result = seedance_video.generate_video_task(
                prompt="漫画角色挥手",
                image_path=str(image_path),
                output_dir=temp_dir
            )

        submit_request = urlopen.call_args_list[0].args[0]
        submit_body = json.loads(submit_request.data.decode("utf-8"))
        self.assertIn("ark.cn-beijing.volces.com", submit_request.full_url)
        self.assertEqual(
            submit_body["model"],
            "doubao-seedance-1-5-pro-251215"
        )
        download_video.assert_called_once_with(
            "https://example.com/volc.mp4",
            result
        )


if __name__ == "__main__":
    unittest.main()
