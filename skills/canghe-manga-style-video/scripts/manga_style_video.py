#!/usr/bin/env python3
"""
漫画风格视频生成器
专门用于生成日式/国漫风格的动画视频
"""

import os
import sys
import json
import base64
import argparse
import urllib.request
import ssl
from pathlib import Path
from typing import Optional

# 忽略SSL验证
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# API配置
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seedance-1-5-pro-251215"

# 漫画风格预设模板
MANGA_STYLES = {
    "japanese": {
        "name": "日式治愈系",
        "prompt": "日式动画风格，吉卜力工作室风格，手绘水彩质感，柔和粉彩色调，线条简洁流畅，温馨治愈，细腻的背景描绘，宫崎骏风格"
    },
    "ghibli": {
        "name": "吉卜力风格",
        "prompt": "Studio Ghibli style, hand-painted watercolor texture, soft pastel colors, detailed backgrounds, warm and healing atmosphere, Hayao Miyazaki animation style"
    },
    "chinese": {
        "name": "国风水墨",
        "prompt": "中国传统水墨画风格，国风动画，淡雅色调，山水意境，工笔线条，古风手绘，诗意唯美"
    },
    "cartoon": {
        "name": "美式卡通",
        "prompt": "迪士尼皮克斯风格，3D卡通渲染，色彩鲜艳饱满，可爱萌系角色，流畅的动画动作，family-friendly风格"
    },
    "sketch": {
        "name": "铅笔素描",
        "prompt": "铅笔素描风格，手绘线条，黑白灰色调，速写质感，艺术感强烈，细腻的线条勾勒"
    },
    "watercolor": {
        "name": "水彩手绘",
        "prompt": "水彩画风格，透明质感，色彩晕染，手绘笔触，柔和边缘，艺术性插画风格"
    },
    "manga_comic": {
        "name": "日式漫画",
        "prompt": "日式少年漫画风格，黑白网点，速度线效果，动态构图，漫画分镜感，线条粗犷有力"
    },
    "chibi": {
        "name": "Q版萌系",
        "prompt": "Q版大头比例，萌系可爱风格，圆润线条，明亮色彩，卡通渲染，治愈系表情"
    }
}


def get_api_key():
    """获取API Key"""
    key = os.environ.get("ARK_API_KEY")
    if not key:
        print("❌ 错误: 请设置 ARK_API_KEY 环境变量", file=sys.stderr)
        sys.exit(1)
    return key


def image_to_base64(image_path: str) -> str:
    """将图片转为base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def generate_manga_video(
    prompt: str,
    style: str = "japanese",
    image_path: Optional[str] = None,
    duration: int = 10,
    ratio: str = "9:16",
    resolution: str = "1080p",
    model: str = DEFAULT_MODEL,
    wait: bool = True
) -> dict:
    """
    生成漫画风格视频
    
    Args:
        prompt: 视频内容描述
        style: 漫画风格 (japanese/ghibli/chinese/cartoon/sketch/watercolor/manga_comic/chibi)
        image_path: 参考图片路径（可选）
        duration: 时长（秒）
        ratio: 比例
        resolution: 分辨率
        model: 模型ID
        wait: 是否等待完成
    
    Returns:
        生成结果
    """
    api_key = get_api_key()
    
    # 获取风格提示词
    style_config = MANGA_STYLES.get(style, MANGA_STYLES["japanese"])
    style_prompt = style_config["prompt"]
    
    # 组合完整提示词
    full_prompt = f"{prompt}，{style_prompt}"
    
    print(f"🎨 风格: {style_config['name']}")
    print(f"📝 提示词: {full_prompt[:100]}...")
    print()
    
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
    
    content.append({"type": "text", "text": full_prompt})
    
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
    
    if not wait:
        return result
    
    # 等待完成
    print("\n⏳ 等待视频生成...")
    import time
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
            print(f"\n🎉 视频生成成功!")
            print(f"   时长: {result.get('duration')}秒")
            print(f"   分辨率: {result.get('resolution')}")
            print(f"   URL: {video_url}")
            return result
        
        elif status == "failed":
            print(f"\n❌ 生成失败: {result}")
            sys.exit(1)
        
        else:
            print(f"   状态: {status}...", end="\r", flush=True)


def download_video(video_url: str, output_path: str):
    """下载视频"""
    print(f"\n📥 下载视频...")
    
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


def main():
    parser = argparse.ArgumentParser(
        description="漫画风格视频生成器 - 专门生成日式/国漫风格动画",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
可用的漫画风格:
  japanese     - 日式治愈系（默认）
  ghibli       - 吉卜力风格
  chinese      - 国风水墨
  cartoon      - 美式卡通
  sketch       - 铅笔素描
  watercolor   - 水彩手绘
  manga_comic  - 日式漫画
  chibi        - Q版萌系

使用示例:
  # 生成日式治愈风格视频
  python3 manga_style_video.py "女孩在樱花树下" --style japanese
  
  # 基于参考图片生成
  python3 manga_style_video.py "奶奶在包饺子" --style japanese --image character.png
  
  # 生成国风水墨风格
  python3 manga_style_video.py "山水意境" --style chinese --duration 10
        """
    )
    
    parser.add_argument("prompt", help="视频内容描述")
    parser.add_argument("--style", default="japanese", 
                       choices=list(MANGA_STYLES.keys()),
                       help="漫画风格（默认: japanese）")
    parser.add_argument("--image", help="参考图片路径（可选）")
    parser.add_argument("--duration", type=int, default=10,
                       help="视频时长（秒，默认10）")
    parser.add_argument("--ratio", default="9:16",
                       choices=["16:9", "9:16", "1:1", "4:3"],
                       help="视频比例（默认9:16）")
    parser.add_argument("--resolution", default="1080p",
                       choices=["480p", "720p", "1080p"],
                       help="分辨率（默认1080p）")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                       help=f"模型ID（默认: {DEFAULT_MODEL}）")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--no-wait", action="store_true",
                       help="不等待，只创建任务")
    parser.add_argument("--list-styles", action="store_true",
                       help="列出所有可用的漫画风格")
    
    args = parser.parse_args()
    
    # 列出风格
    if args.list_styles:
        print("🎨 可用的漫画风格:")
        for key, config in MANGA_STYLES.items():
            print(f"  {key:12} - {config['name']}")
        return
    
    # 生成视频
    try:
        result = generate_manga_video(
            prompt=args.prompt,
            style=args.style,
            image_path=args.image,
            duration=args.duration,
            ratio=args.ratio,
            resolution=args.resolution,
            model=args.model,
            wait=not args.no_wait
        )
        
        # 下载视频
        if not args.no_wait and result.get("content", {}).get("video_url"):
            video_url = result["content"]["video_url"]
            
            if args.output:
                output_path = args.output
            else:
                import time
                output_path = f"~/Desktop/manga_{args.style}_{int(time.time())}.mp4"
            
            output_path = os.path.expanduser(output_path)
            download_video(video_url, output_path)
            
            print(f"\n✨ 漫画风格视频已保存!")
            print(f"   文件: {output_path}")
            print(f"   风格: {MANGA_STYLES[args.style]['name']}")
    
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
