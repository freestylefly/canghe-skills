#!/usr/bin/env python3
"""
Seedance 视频生成辅助模块
被 manga_drama.py 调用
"""

import os
import sys
import subprocess
from pathlib import Path


def analyze_image(image_path: str) -> str:
    """
    分析图片，提取角色特征描述
    
    使用简单的文件名分析，实际可以集成图像识别API
    """
    # 这里可以集成火山引擎的视觉理解API
    # 暂时返回基于文件名的描述
    filename = Path(image_path).stem
    return f"图片中的主角（基于文件名: {filename}）"


def generate_video_task(
    prompt: str,
    image_path: str = None,
    model: str = "doubao-seedance-1-5-pro-251215",
    duration: int = 5,
    ratio: str = "9:16",
    resolution: str = "1080p",
    output_dir: str = "~/Desktop",
    send_feishu: bool = False
) -> str:
    """
    调用 seedance-video-generation 生成视频
    
    Returns:
        生成的视频路径
    """
    # 构建命令
    seedance_path = Path(__file__).parent.parent / "seedance-video-generation-1.0.3" / "seedance.py"
    
    cmd = [
        "python3", str(seedance_path),
        "create",
        "--prompt", prompt,
        "--model", model,
        "--duration", str(duration),
        "--ratio", ratio,
        "--resolution", resolution,
        "--wait",
        "--download", output_dir
    ]
    
    if image_path:
        cmd.extend(["--image", image_path])
    
    if send_feishu:
        cmd.append("--send-feishu")
    
    # 执行命令
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(seedance_path.parent)
    )
    
    if result.returncode != 0:
        raise Exception(f"视频生成失败: {result.stderr}")
    
    # 解析输出，获取视频路径
    # 从输出中提取保存路径
    output_lines = result.stdout.split('\n')
    video_path = None
    for line in output_lines:
        if "Saved to:" in line or "下载视频到" in line:
            video_path = line.split(":")[-1].strip()
            break
    
    if not video_path:
        # 尝试从其他输出行查找
        import re
        for line in output_lines:
            match = re.search(r'(~\/[^\s]+\.mp4|\/Users\/[^\s]+\.mp4)', line)
            if match:
                video_path = match.group(0)
                break
    
    return video_path or f"{output_dir}/generated_video.mp4"
