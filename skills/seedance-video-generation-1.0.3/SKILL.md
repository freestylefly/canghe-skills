---
name: seedance-video
description: "Generate AI videos using ByteDance Seedance. Use when the user wants to: (1) generate videos from text prompts, (2) generate videos from images (first frame, first+last frame, reference images), or (3) query/manage video generation tasks. Supports Seedance 1.5 Pro (with audio), 1.0 Pro, 1.0 Pro Fast, and 1.0 Lite models."
version: 1.0.0
category: file-generation
argument-hint: "[text prompt or task ID]"
---

# Seedance Video Generation

Generate AI videos using ByteDance Seedance models via the Volcengine Ark API.

## Prerequisites

The user must set the `ARK_API_KEY` environment variable. You can set it by running:

```bash
export ARK_API_KEY="your-api-key-here"
```

**Base URL**: `https://ark.cn-beijing.volces.com/api/v3`

## Supported Models

| Model | Model ID | Capabilities |
|-------|----------|-------------|
| Seedance 1.5 Pro | `doubao-seedance-1-5-pro-251215` | Text-to-video, Image-to-video (first frame, first+last frame), Audio support, Draft mode |
| Seedance 1.0 Pro | `doubao-seedance-1-0-pro-250428` | Text-to-video, Image-to-video (first frame, first+last frame) |
| Seedance 1.0 Pro Fast | `doubao-seedance-1-0-pro-fast-250528` | Text-to-video, Image-to-video (first frame only) |
| Seedance 1.0 Lite T2V | `doubao-seedance-1-0-lite-t2v-250219` | Text-to-video only |
| Seedance 1.0 Lite I2V | `doubao-seedance-1-0-lite-i2v-250219` | Image-to-video (first frame, first+last frame, reference images 1-4) |

**Default model**: `doubao-seedance-1-5-pro-251215` (latest, supports audio)

## Execution (Recommended: Python CLI Tool)

A Python CLI tool is provided at `~/.claude/skills/seedance-video/seedance.py` for robust execution with proper error handling, automatic retries, and local image base64 conversion. **Prefer using this tool over raw curl commands.**

### Quick Examples with Python CLI

```bash
# Text-to-video (create + wait + download)
python3 ~/.claude/skills/seedance-video/seedance.py create --prompt "小猫对着镜头打哈欠" --wait --download ~/Desktop

# Image-to-video from local file
python3 ~/.claude/skills/seedance-video/seedance.py create --prompt "人物缓缓转头微笑" --image /path/to/photo.jpg --wait --download ~/Desktop

# Image-to-video from URL
python3 ~/.claude/skills/seedance-video/seedance.py create --prompt "风景画面缓缓推进" --image "https://example.com/image.jpg" --wait --download ~/Desktop

# First + last frame
python3 ~/.claude/skills/seedance-video/seedance.py create --prompt "花朵从含苞到盛开" --image first.jpg --last-frame last.jpg --wait --download ~/Desktop

# Reference images (Lite I2V)
python3 ~/.claude/skills/seedance-video/seedance.py create --prompt "[图1]的人物在跳舞" --ref-images ref1.jpg ref2.jpg --model doubao-seedance-1-0-lite-i2v-250219 --wait --download ~/Desktop

# Custom parameters
python3 ~/.claude/skills/seedance-video/seedance.py create --prompt "城市夜景延时摄影" --ratio 21:9 --duration 8 --resolution 1080p --generate-audio false --wait --download ~/Desktop

# Draft mode (cheaper preview)
python3 ~/.claude/skills/seedance-video/seedance.py create --prompt "海浪拍打沙滩" --draft true --wait --download ~/Desktop

# Generate final video from draft
python3 ~/.claude/skills/seedance-video/seedance.py create --draft-task-id <DRAFT_TASK_ID> --resolution 720p --wait --download ~/Desktop

# Query task status
python3 ~/.claude/skills/seedance-video/seedance.py status <TASK_ID>

# Wait for an existing task
python3 ~/.claude/skills/seedance-video/seedance.py wait <TASK_ID> --download ~/Desktop

# List tasks
python3 ~/.claude/skills/seedance-video/seedance.py list --status succeeded

# Delete/cancel task
python3 ~/.claude/skills/seedance-video/seedance.py delete <TASK_ID>
```

## Alternative: Raw curl Commands

### Step 1: Create Video Generation Task

Determine the generation mode based on user input, then call the API.

#### Mode A: Text-to-Video

```bash
TASK_RESULT=$(curl -s -X POST "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedance-1-5-pro-251215",
    "content": [
      {
        "type": "text",
        "text": "YOUR_PROMPT_HERE"
      }
    ],
    "ratio": "16:9",
    "duration": 5,
    "resolution": "720p",
    "generate_audio": true
  }')

TASK_ID=$(echo "$TASK_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Task created: $TASK_ID"
```

#### Mode B: Image-to-Video (First Frame)

The user provides one image as the first frame. The image can be a URL or local file path (convert to base64).

**With image URL:**
```bash
TASK_RESULT=$(curl -s -X POST "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedance-1-5-pro-251215",
    "content": [
      {
        "type": "text",
        "text": "YOUR_PROMPT_HERE"
      },
      {
        "type": "image_url",
        "image_url": { "url": "IMAGE_URL_HERE" },
        "role": "first_frame"
      }
    ],
    "ratio": "adaptive",
    "duration": 5,
    "resolution": "720p",
    "generate_audio": true
  }')

TASK_ID=$(echo "$TASK_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Task created: $TASK_ID"
```

**With local image file (convert to base64):**
```bash
IMG_PATH="/path/to/image.png"
IMG_EXT="${IMG_PATH##*.}"
IMG_EXT_LOWER=$(echo "$IMG_EXT" | tr '[:upper:]' '[:lower:]')
IMG_BASE64=$(base64 < "$IMG_PATH" | tr -d '\n')
IMG_DATA_URL="data:image/${IMG_EXT_LOWER};base64,${IMG_BASE64}"

TASK_RESULT=$(curl -s -X POST "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedance-1-5-pro-251215",
    "content": [
      {
        "type": "text",
        "text": "YOUR_PROMPT_HERE"
      },
      {
        "type": "image_url",
        "image_url": { "url": "'"$IMG_DATA_URL"'" },
        "role": "first_frame"
      }
    ],
    "ratio": "adaptive",
    "duration": 5,
    "resolution": "720p",
    "generate_audio": true
  }')

TASK_ID=$(echo "$TASK_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Task created: $TASK_ID"
```

#### Mode C: Image-to-Video (First + Last Frame)

Requires two images. Supported by: Seedance 1.5 Pro, 1.0 Pro, 1.0 Lite I2V.

```bash
TASK_RESULT=$(curl -s -X POST "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedance-1-5-pro-251215",
    "content": [
      {
        "type": "text",
        "text": "YOUR_PROMPT_HERE"
      },
      {
        "type": "image_url",
        "image_url": { "url": "FIRST_FRAME_IMAGE_URL" },
        "role": "first_frame"
      },
      {
        "type": "image_url",
        "image_url": { "url": "LAST_FRAME_IMAGE_URL" },
        "role": "last_frame"
      }
    ],
    "ratio": "adaptive",
    "duration": 5,
    "resolution": "720p",
    "generate_audio": true
  }')

TASK_ID=$(echo "$TASK_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Task created: $TASK_ID"
```

#### Mode D: Reference Image-to-Video (Seedance 1.0 Lite I2V only)

Provide 1-4 reference images. Use `[图1]`, `[图2]` in prompt to reference specific images.

```bash
TASK_RESULT=$(curl -s -X POST "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedance-1-0-lite-i2v-250219",
    "content": [
      {
        "type": "text",
        "text": "[图1]的人物在跳舞"
      },
      {
        "type": "image_url",
        "image_url": { "url": "REF_IMAGE_URL_1" },
        "role": "reference_image"
      }
    ],
    "ratio": "16:9",
    "duration": 5,
    "resolution": "720p"
  }')

TASK_ID=$(echo "$TASK_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Task created: $TASK_ID"
```

### Step 2: Poll for Task Completion

Video generation is asynchronous. Poll the task status until it completes.

```bash
echo "Waiting for video generation to complete..."
while true; do
  STATUS_RESULT=$(curl -s -X GET "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/${TASK_ID}" \
    -H "Authorization: Bearer $ARK_API_KEY")

  STATUS=$(echo "$STATUS_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")

  if [ "$STATUS" = "succeeded" ]; then
    echo "Video generation succeeded!"
    VIDEO_URL=$(echo "$STATUS_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['content']['video_url'])")
    echo "Video URL: $VIDEO_URL"
    break
  elif [ "$STATUS" = "failed" ]; then
    ERROR_MSG=$(echo "$STATUS_RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error',{}).get('message','Unknown error'))" 2>/dev/null || echo "Unknown error")
    echo "Video generation failed: $ERROR_MSG"
    break
  elif [ "$STATUS" = "expired" ]; then
    echo "Video generation task expired."
    break
  else
    echo "Status: $STATUS - still processing..."
    sleep 15
  fi
done
```

### Step 3: Download and Open Video

```bash
OUTPUT_PATH="$HOME/Desktop/seedance_video_$(date +%Y%m%d_%H%M%S).mp4"
curl -s -o "$OUTPUT_PATH" "$VIDEO_URL"
echo "Video saved to: $OUTPUT_PATH"
open "$OUTPUT_PATH"
```

## Optional Parameters Reference

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | `doubao-seedance-1-5-pro-251215` | Model ID to use |
| `ratio` | string | `16:9` (text2vid) / `adaptive` (img2vid) | Aspect ratio: `16:9`, `4:3`, `1:1`, `3:4`, `9:16`, `21:9`, `adaptive` |
| `duration` | integer | `5` | Video duration in seconds (4-12 for 1.5 Pro, 2-12 for others). Set `-1` for auto (1.5 Pro only) |
| `resolution` | string | `720p` | Resolution: `480p`, `720p`, `1080p` |
| `seed` | integer | `-1` | Random seed for reproducibility. -1 = random |
| `camera_fixed` | boolean | `false` | Fix camera position |
| `watermark` | boolean | `false` | Add watermark to video |
| `generate_audio` | boolean | `true` | Generate synchronized audio (Seedance 1.5 Pro only) |
| `draft` | boolean | `false` | Generate draft/preview video at lower cost (Seedance 1.5 Pro only, forces 480p) |
| `return_last_frame` | boolean | `false` | Return last frame image URL (for chaining consecutive videos) |
| `service_tier` | string | `default` | `default` (online) or `flex` (offline, 50% cheaper, slower) |
| `execution_expires_after` | integer | `172800` | Task timeout in seconds (3600-259200) |

## Additional Operations

### Query Task Status

```bash
curl -s -X GET "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/${TASK_ID}" \
  -H "Authorization: Bearer $ARK_API_KEY" | python3 -m json.tool
```

### List Tasks

```bash
# List all tasks (paginated)
curl -s -X GET "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks?page_num=1&page_size=10" \
  -H "Authorization: Bearer $ARK_API_KEY" | python3 -m json.tool

# Filter by status
curl -s -X GET "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks?page_num=1&page_size=10&filter.status=succeeded" \
  -H "Authorization: Bearer $ARK_API_KEY" | python3 -m json.tool
```

### Cancel or Delete Task

```bash
curl -s -X DELETE "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/${TASK_ID}" \
  -H "Authorization: Bearer $ARK_API_KEY"
```

Note: `queued` tasks will be cancelled; `succeeded`/`failed`/`expired` tasks will be deleted from history.

### Generate Consecutive Videos (Using Last Frame)

Set `return_last_frame: true` on the first task, then use the returned `last_frame_url` as the first frame of the next task.

```bash
# Get last frame URL from completed task
LAST_FRAME_URL=$(curl -s -X GET "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/${TASK_ID}" \
  -H "Authorization: Bearer $ARK_API_KEY" | python3 -c "import sys,json; print(json.load(sys.stdin)['content']['last_frame_url'])")

# Use it as first frame for the next video
# ... (use Mode B with LAST_FRAME_URL as the image URL)
```

### Draft Mode (Seedance 1.5 Pro)

Generate a cheap preview first, then produce the final video if satisfied:

```bash
# Step 1: Create draft
DRAFT_RESULT=$(curl -s -X POST "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedance-1-5-pro-251215",
    "content": [
      { "type": "text", "text": "YOUR_PROMPT_HERE" }
    ],
    "draft": true,
    "resolution": "480p"
  }')
DRAFT_TASK_ID=$(echo "$DRAFT_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Step 2: After draft succeeds, generate final video from draft
FINAL_RESULT=$(curl -s -X POST "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedance-1-5-pro-251215",
    "content": [
      {
        "type": "draft_task",
        "draft_task": { "id": "'"$DRAFT_TASK_ID"'" }
      }
    ],
    "resolution": "720p"
  }')
```

## Image Requirements

- Formats: jpeg, png, webp, bmp, tiff, gif (1.5 Pro also supports heic, heif)
- Aspect ratio (width/height): between 0.4 and 2.5
- Dimensions: 300-6000 px per side
- Max file size: 30 MB

## 通过飞书发送视频文件（OpenClaw）

详见 [how_to_send_video_via_feishu_app.md](how_to_send_video_via_feishu_app.md)

## Rules

1. **Always check** that `ARK_API_KEY` is set before making API calls: `[ -z "$ARK_API_KEY" ] && echo "Error: ARK_API_KEY not set" && exit 1`
2. **Default to Seedance 1.5 Pro** (`doubao-seedance-1-5-pro-251215`) unless user requests a specific model.
3. **Default to 720p, 16:9, 5 seconds, with audio** for text-to-video.
4. **Default to adaptive ratio** for image-to-video (auto-adapts to the input image).
5. **Poll interval**: 15 seconds between status checks.
6. **Video URLs expire in 24 hours** - always download immediately after generation.
7. **Task history is kept for 7 days only**.
8. For local image files, convert to base64 data URL format before sending.
9. Always show the user the task ID so they can check status later.
10. When generation fails, display the error message clearly and suggest possible fixes.
