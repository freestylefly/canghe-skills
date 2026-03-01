#!/usr/bin/env python3
"""
Seedance Video Generation CLI Tool
Usage:
  python3 seedance.py create --prompt "描述" [options]
  python3 seedance.py create --prompt "描述" --image /path/to/image.png [options]
  python3 seedance.py create --prompt "描述" --image url1 --last-frame url2 [options]
  python3 seedance.py create --prompt "描述" --ref-images url1 url2 [options]
  python3 seedance.py create --draft-task-id <task_id> [options]
  python3 seedance.py status <task_id>
  python3 seedance.py wait <task_id> [--interval 15] [--download ~/Desktop]
  python3 seedance.py list [--status succeeded] [--page 1] [--page-size 10]
  python3 seedance.py delete <task_id>
  python3 seedance.py send-feishu <file_path> [--user-id ou_xxx]
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# Feishu API configuration
FEISHU_APP_ID = "cli_a9005be686f89bd3"
FEISHU_APP_SECRET = "UvUMxhBGbejzqbeuR5BQqeZnjCrnsCiC"
FEISHU_DEFAULT_USER = "ou_20bf7fe6e4ec0f2f928e8ebc1c0a6e76"


def get_feishu_token():
    """Get Feishu tenant_access_token."""
    import requests
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}
    )
    result = resp.json()
    if result.get("code") == 0:
        return result["tenant_access_token"]
    else:
        raise Exception(f"Failed to get Feishu token: {result}")


def upload_file_to_feishu(token, file_path):
    """Upload file to Feishu and return file_key."""
    import requests
    
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    # Build multipart body
    body = []
    body.append(f"------{boundary}")
    body.append('Content-Disposition: form-data; name="file_type"')
    body.append("")
    body.append("mp4")
    body.append(f"------{boundary}")
    body.append('Content-Disposition: form-data; name="file_name"')
    body.append("")
    body.append(os.path.basename(file_path))
    body.append(f"------{boundary}")
    body.append(f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(file_path)}"')
    body.append("Content-Type: video/mp4")
    body.append("")
    
    # Read file content
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    body_bytes = "\r\n".join(body).encode("utf-8") + b"\r\n"
    body_bytes += file_content + b"\r\n"
    body_bytes += f"------{boundary}--\r\n".encode("utf-8")
    
    # Send request
    resp = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/files",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary=----{boundary}"
        },
        data=body_bytes
    )
    
    result = resp.json()
    if result.get("code") == 0:
        return result["data"]["file_key"]
    else:
        raise Exception(f"Failed to upload file: {result}")


def send_media_to_feishu(token, user_id, file_key):
    """Send media message to Feishu user."""
    import requests
    
    resp = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        params={"receive_id_type": "open_id"},
        json={
            "receive_id": user_id,
            "msg_type": "media",
            "content": json.dumps({
                "file_key": file_key,
                "image_key": ""
            })
        }
    )
    
    result = resp.json()
    if result.get("code") == 0:
        return result["data"]
    else:
        raise Exception(f"Failed to send message: {result}")


def send_video_to_feishu(file_path, user_id=None):
    """Send video file to Feishu."""
    if user_id is None:
        user_id = FEISHU_DEFAULT_USER
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_size = os.path.getsize(file_path) / 1024 / 1024
    print(f"📁 File: {file_path}")
    print(f"📦 Size: {file_size:.1f} MB")
    
    print("🔑 Getting Feishu access token...")
    token = get_feishu_token()
    
    print("☁️  Uploading file to Feishu...")
    file_key = upload_file_to_feishu(token, file_path)
    print(f"✅ File uploaded: {file_key[:30]}...")
    
    print("📤 Sending message...")
    result = send_media_to_feishu(token, user_id, file_key)
    print(f"✅ Message sent!")
    print(f"   Message ID: {result['message_id']}")
    print(f"   Chat ID: {result['chat_id']}")
    
    return result


BASE_URL = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
DEFAULT_MODEL = "doubao-seedance-1-5-pro-251215"


def get_api_key():
    key = os.environ.get("ARK_API_KEY")
    if not key:
        print("Error: ARK_API_KEY environment variable is not set.", file=sys.stderr)
        print("Set it with: export ARK_API_KEY='your-api-key-here'", file=sys.stderr)
        sys.exit(1)
    return key


def api_request(method, url, data=None):
    """Make an API request and return parsed JSON response."""
    api_key = get_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read().decode("utf-8")
            if resp_body:
                return json.loads(resp_body)
            return {}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get("error", {}).get("message", error_body)
        except json.JSONDecodeError:
            error_msg = error_body
        print(f"API Error (HTTP {e.code}): {error_msg}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network Error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def image_to_data_url(image_path):
    """Convert a local image file to a base64 data URL."""
    p = Path(image_path)
    if not p.exists():
        print(f"Error: Image file not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    ext = p.suffix.lower().lstrip(".")
    mime_map = {
        "jpg": "jpeg", "jpeg": "jpeg", "png": "png",
        "webp": "webp", "bmp": "bmp", "tiff": "tiff",
        "tif": "tiff", "gif": "gif", "heic": "heic", "heif": "heif",
    }
    mime_ext = mime_map.get(ext, ext)

    file_size = p.stat().st_size
    if file_size > 30 * 1024 * 1024:
        print(f"Error: Image file too large ({file_size / 1024 / 1024:.1f} MB). Max 30 MB.", file=sys.stderr)
        sys.exit(1)

    with open(p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    return f"data:image/{mime_ext};base64,{b64}"


def resolve_image(image_input):
    """Resolve image input to a URL or data URL. Accepts URL or local file path."""
    if image_input.startswith(("http://", "https://", "data:")):
        return image_input
    return image_to_data_url(image_input)


def cmd_create(args):
    """Create a video generation task."""
    content = []

    # Draft task mode
    if args.draft_task_id:
        content.append({
            "type": "draft_task",
            "draft_task": {"id": args.draft_task_id}
        })
    else:
        # Text prompt
        if args.prompt:
            content.append({"type": "text", "text": args.prompt})

        # Image inputs
        if args.ref_images:
            # Reference image mode (Lite I2V only)
            for img in args.ref_images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": resolve_image(img)},
                    "role": "reference_image"
                })
        elif args.image:
            # First frame
            content.append({
                "type": "image_url",
                "image_url": {"url": resolve_image(args.image)},
                "role": "first_frame"
            })
            # Last frame (optional)
            if args.last_frame:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": resolve_image(args.last_frame)},
                    "role": "last_frame"
                })

    if not content:
        print("Error: Must provide --prompt, --image, or --draft-task-id.", file=sys.stderr)
        sys.exit(1)

    body = {
        "model": args.model,
        "content": content,
    }

    # Optional parameters
    if args.ratio:
        body["ratio"] = args.ratio
    if args.duration is not None:
        body["duration"] = args.duration
    if args.resolution:
        body["resolution"] = args.resolution
    if args.seed is not None:
        body["seed"] = args.seed
    if args.camera_fixed is not None:
        body["camera_fixed"] = args.camera_fixed
    if args.watermark is not None:
        body["watermark"] = args.watermark
    if args.generate_audio is not None:
        body["generate_audio"] = args.generate_audio
    if args.draft is not None:
        body["draft"] = args.draft
    if args.return_last_frame is not None:
        body["return_last_frame"] = args.return_last_frame
    if args.service_tier:
        body["service_tier"] = args.service_tier

    result = api_request("POST", BASE_URL, body)
    task_id = result.get("id", "")

    print(json.dumps({"task_id": task_id, "status": "created", "response": result}, indent=2))

    # Auto-wait if requested
    if args.wait:
        return cmd_wait_logic(
            task_id, 
            args.interval or 15, 
            args.download,
            getattr(args, 'send_feishu', False),
            getattr(args, 'feishu_user_id', None)
        )

    return task_id


def cmd_status(args):
    """Query task status."""
    url = f"{BASE_URL}/{args.task_id}"
    result = api_request("GET", url)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def cmd_wait_logic(task_id, interval=15, download_dir=None, send_feishu=False, feishu_user_id=None):
    """Wait for task completion, optionally download result and send to Feishu."""
    url = f"{BASE_URL}/{task_id}"
    print(f"Waiting for task {task_id} to complete (polling every {interval}s)...")

    while True:
        result = api_request("GET", url)
        status = result.get("status", "unknown")

        if status == "succeeded":
            video_url = result.get("content", {}).get("video_url", "")
            last_frame_url = result.get("content", {}).get("last_frame_url")
            duration = result.get("duration", "?")
            resolution = result.get("resolution", "?")
            ratio = result.get("ratio", "?")

            print(f"\nVideo generation succeeded!")
            print(f"  Duration: {duration}s | Resolution: {resolution} | Ratio: {ratio}")
            print(f"  Video URL: {video_url}")
            if last_frame_url:
                print(f"  Last Frame URL: {last_frame_url}")

            # Download
            if download_dir and video_url:
                download_path = Path(download_dir).expanduser()
                download_path.mkdir(parents=True, exist_ok=True)
                filename = f"seedance_{task_id}_{int(time.time())}.mp4"
                filepath = download_path / filename

                print(f"\nDownloading video to {filepath}...")
                try:
                    urllib.request.urlretrieve(video_url, str(filepath))
                    print(f"Saved to: {filepath}")

                    # Open on macOS
                    if sys.platform == "darwin":
                        os.system(f'open "{filepath}"')
                except Exception as e:
                    print(f"Download failed: {e}", file=sys.stderr)
                    filepath = None

            # Send to Feishu if requested
            if send_feishu and filepath:
                try:
                    print("\n📱 Sending to Feishu...")
                    send_video_to_feishu(str(filepath), feishu_user_id)
                    print("🎉 Video sent to Feishu successfully!")
                except Exception as e:
                    print(f"⚠️  Failed to send to Feishu: {e}", file=sys.stderr)

            print(json.dumps(result, indent=2, ensure_ascii=False))
            return result

        elif status == "failed":
            error = result.get("error", {})
            print(f"\nVideo generation failed!")
            print(f"  Error: {error.get('code', 'unknown')} - {error.get('message', 'Unknown error')}")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)

        elif status == "expired":
            print(f"\nVideo generation task expired.")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)

        else:
            print(f"  Status: {status}...", flush=True)
            time.sleep(interval)


def cmd_wait(args):
    """Wait for task completion."""
    return cmd_wait_logic(
        args.task_id, 
        args.interval, 
        args.download,
        getattr(args, 'send_feishu', False),
        getattr(args, 'feishu_user_id', None)
    )


def cmd_list(args):
    """List video generation tasks."""
    params = []
    if args.page:
        params.append(f"page_num={args.page}")
    if args.page_size:
        params.append(f"page_size={args.page_size}")
    if args.status:
        params.append(f"filter.status={args.status}")

    url = BASE_URL
    if params:
        url += "?" + "&".join(params)

    result = api_request("GET", url)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def cmd_send_feishu(args):
    """Send a video file to Feishu."""
    try:
        result = send_video_to_feishu(args.file_path, args.user_id)
        print(f"\n🎉 Video sent to Feishu successfully!")
        return result
    except Exception as e:
        print(f"\n❌ Failed to send: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args):
    """Cancel or delete a task."""
    url = f"{BASE_URL}/{args.task_id}"
    api_request("DELETE", url)
    print(f"Task {args.task_id} cancelled/deleted successfully.")


def parse_bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("true", "1", "yes"):
        return True
    if v.lower() in ("false", "0", "no"):
        return False
    raise argparse.ArgumentTypeError(f"Boolean expected, got '{v}'")


def main():
    parser = argparse.ArgumentParser(description="Seedance Video Generation CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # create
    p_create = subparsers.add_parser("create", help="Create a video generation task")
    p_create.add_argument("--prompt", "-p", help="Text prompt describing the video")
    p_create.add_argument("--image", "-i", help="First frame image (URL or local file path)")
    p_create.add_argument("--last-frame", help="Last frame image (URL or local file path)")
    p_create.add_argument("--ref-images", nargs="+", help="Reference images for Lite I2V (1-4 URLs or paths)")
    p_create.add_argument("--draft-task-id", help="Draft task ID to generate final video from")
    p_create.add_argument("--model", "-m", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL})")
    p_create.add_argument("--ratio", choices=["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"], help="Aspect ratio")
    p_create.add_argument("--duration", "-d", type=int, help="Duration in seconds (4-12 for 1.5 Pro)")
    p_create.add_argument("--resolution", "-r", choices=["480p", "720p", "1080p"], help="Resolution")
    p_create.add_argument("--seed", type=int, help="Random seed (-1 for random)")
    p_create.add_argument("--camera-fixed", type=parse_bool, help="Fix camera position (true/false)")
    p_create.add_argument("--watermark", type=parse_bool, help="Add watermark (true/false)")
    p_create.add_argument("--generate-audio", type=parse_bool, help="Generate audio (true/false, 1.5 Pro only)")
    p_create.add_argument("--draft", type=parse_bool, help="Draft/preview mode (true/false, 1.5 Pro only)")
    p_create.add_argument("--return-last-frame", type=parse_bool, help="Return last frame URL (true/false)")
    p_create.add_argument("--service-tier", choices=["default", "flex"], help="Service tier")
    p_create.add_argument("--wait", "-w", action="store_true", help="Wait for completion after creating")
    p_create.add_argument("--interval", type=int, default=15, help="Poll interval in seconds (default: 15)")
    p_create.add_argument("--download", help="Download directory (e.g. ~/Desktop)")
    p_create.add_argument("--send-feishu", action="store_true", help="Auto-send video to Feishu after download (requires --download)")
    p_create.add_argument("--feishu-user-id", help="Target Feishu user open_id (default: current user)")

    # status
    p_status = subparsers.add_parser("status", help="Query task status")
    p_status.add_argument("task_id", help="Task ID to query")

    # wait
    p_wait = subparsers.add_parser("wait", help="Wait for task completion")
    p_wait.add_argument("task_id", help="Task ID to wait for")
    p_wait.add_argument("--interval", type=int, default=15, help="Poll interval in seconds (default: 15)")
    p_wait.add_argument("--download", help="Download directory (e.g. ~/Desktop)")
    p_wait.add_argument("--send-feishu", action="store_true", help="Auto-send video to Feishu after download")
    p_wait.add_argument("--feishu-user-id", help="Target Feishu user open_id (default: current user)")

    # list
    p_list = subparsers.add_parser("list", help="List video generation tasks")
    p_list.add_argument("--status", choices=["queued", "running", "cancelled", "succeeded", "failed", "expired"])
    p_list.add_argument("--page", type=int, default=1)
    p_list.add_argument("--page-size", type=int, default=10)

    # send-feishu
    p_send = subparsers.add_parser("send-feishu", help="Send a video file to Feishu")
    p_send.add_argument("file_path", help="Path to the video file")
    p_send.add_argument("--user-id", help="Target Feishu user open_id (default: current user)")

    # delete
    p_delete = subparsers.add_parser("delete", help="Cancel or delete a task")
    p_delete.add_argument("task_id", help="Task ID to cancel/delete")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "create": cmd_create,
        "status": cmd_status,
        "wait": cmd_wait,
        "list": cmd_list,
        "send-feishu": cmd_send_feishu,
        "delete": cmd_delete,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
