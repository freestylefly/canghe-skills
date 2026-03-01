#!/usr/bin/env python3
"""
Seedance 视频生成辅助模块
被 manga_drama.py 调用 - 使用直接 API 调用（无需 SDK）
"""

import os
import sys
import json
import base64
import urllib.request
import ssl
import time
from pathlib import Path

# 添加 common 模块到路径
COMMON_DIR = Path(__file__).parent.parent.parent / "common"
sys.path.insert(0, str(COMMON_DIR))

# 导入环境变量工具
try:
    from env_utils import load_env, require_env_key
except ImportError:
    print("错误: 无法加载 env_utils 模块", file=sys.stderr)
    sys.exit(1)

# 忽略SSL验证
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# API配置
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seedance-1-5-pro-251215"


def image_to_base64(image_path: str) -> str:
    """将图片转为base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_image(image_path: str) -> str:
    """
    分析图片，提取角色特征描述

    使用简单的文件名分析，实际可以集成图像识别API
    """
    filename = Path(image_path).stem
    return f"图片中的主角（基于文件名: {filename}）"


def download_video(video_url: str, output_path: str):
    """下载视频"""
    print(f"📥 下载视频...")

    # 使用curl下载（避免Python SSL问题）
    import subprocess
    result = subprocess.run(
        ["curl", "-L", "-o", output_path, video_url, "--max-time", "120"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"✅ 下载完成: {output_path}")
    else:
        print(f"⚠️  下载失败，请手动下载: {video_url}")


def generate_video_task(
    prompt: str,
    image_path: str = None,
    model: str = DEFAULT_MODEL,
    duration: int = 5,
    ratio: str = "9:16",
    resolution: str = "1080p",
    output_dir: str = "~/Desktop",
    send_feishu: bool = False
) -> str:
    """
    直接调用 Seedance API 生成视频（无需 SDK）

    Returns:
        生成的视频路径
    """
    # 加载环境变量获取 API Key
    load_env()
    api_key = require_env_key("ARK_API_KEY")

    # 生成输出文件名
    timestamp = int(time.time())
    output_file = Path(output_dir).expanduser() / f"scene_{timestamp}.mp4"

    # 构建请求
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    content = []

    # 如果有参考图片
    if image_path and os.path.exists(image_path):
        print(f"📷 使用参考图片: {image_path}")
        img_base64 = image_to_base64(image_path)
        ext = Path(image_path).suffix.lower().lstrip(".")
        mime_type = "png" if ext == "png" else "jpeg"
        img_url = f"data:image/{mime_type};base64,{img_base64}"
        content.append({"type": "image_url", "image_url": {"url": img_url}})

    content.append({"type": "text", "text": prompt})

    body = {
        "model": model,
        "content": content,
        "duration": duration,
        "ratio": ratio,
        "resolution": resolution
    }

    # 创建任务
    print("🎬 创建视频生成任务...")
    req = urllib.request.Request(
        f"{BASE_URL}/contents/generations/tasks",
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    resp = urllib.request.urlopen(req, context=ssl_context, timeout=30)
    result = json.loads(resp.read().decode("utf-8"))
    task_id = result.get("id")

    print(f"✅ 任务创建: {task_id}")

    # 等待完成
    print("⏳ 等待视频生成...")
    while True:
        time.sleep(10)
        req = urllib.request.Request(
            f"{BASE_URL}/contents/generations/tasks/{task_id}",
            headers=headers
        )
        resp = urllib.request.urlopen(req, context=ssl_context, timeout=30)
        result = json.loads(resp.read().decode("utf-8"))
        status = result.get("status")

        if status == "succeeded":
            video_url = result.get("content", {}).get("video_url", "")
            print(f"🎉 视频生成成功!")
            print(f"   时长: {result.get('duration')}秒")
            print(f"   分辨率: {result.get('resolution')}")
            print(f"   URL: {video_url}")

            # 下载视频
            download_video(video_url, str(output_file))
            return str(output_file)

        elif status == "failed":
            print(f"❌ 生成失败: {result}")
            raise Exception(f"视频生成失败: {result}")

        else:
            print(f"   状态: {status}...", end="\r", flush=True)
