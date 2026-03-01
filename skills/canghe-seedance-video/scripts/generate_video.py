#!/usr/bin/env python3
"""
Seedance 视频生成工具
使用 volcenginesdkarkruntime SDK 调用 Seedance API
"""

import os
import sys
import json
import time
import argparse
from typing import Optional, List, Dict

# 尝试导入 SDK
try:
    from volcenginesdkarkruntime import Ark
    HAS_SDK = True
except ImportError:
    HAS_SDK = False
    print("错误: 请先安装 SDK: pip install 'volcengine-python-sdk[ark]'")
    sys.exit(1)

# API 配置
API_KEY = os.environ.get("SEEDANCE_API_KEY", "8183a3de-9119-4524-9f59-e47b265229b6")
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"


def create_video_task(
    client: Ark,
    model: str,
    prompt: str,
    duration: int = 5,
    ratio: str = "16:9",
    watermark: bool = False,
    return_last_frame: bool = False,
    image_url: Optional[str] = None
) -> dict:
    """
    创建视频生成任务
    
    Args:
        client: Ark 客户端
        model: 模型 ID (如 doubao-seedance-1-5-pro-251215)
        prompt: 视频描述提示词
        duration: 视频时长秒数 (默认 5秒)
        ratio: 宽高比 (默认 16:9)
        watermark: 是否添加水印
        return_last_frame: 是否返回最后一帧
        image_url: 首帧图片 URL (图生视频时使用)
    
    Returns:
        任务创建结果
    """
    # 构建 content
    content = [{
        "type": "text",
        "text": prompt
    }]
    
    # 如果提供了图片 URL，添加图片内容 (图生视频)
    if image_url:
        content.append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })
    
    try:
        result = client.content_generation.tasks.create(
            model=model,
            content=content,
            duration=duration,
            ratio=ratio,
            watermark=watermark,
            return_last_frame=return_last_frame
        )
        # 获取任务ID - SDK 返回的可能是一个字符串或对象
        if hasattr(result, 'id'):
            task_id = result.id
        else:
            task_id = str(result)
        
        return {
            "success": True,
            "task_id": task_id,
            "response": result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_task_status(client: Ark, task_id: str) -> dict:
    """
    查询视频生成任务状态
    
    Args:
        client: Ark 客户端
        task_id: 任务 ID
    
    Returns:
        任务状态信息
    """
    try:
        result = client.content_generation.tasks.get(task_id=task_id)
        
        # 提取视频 URL 和最后一帧 URL
        video_url = None
        last_frame_url = None
        
        if hasattr(result, 'content'):
            if hasattr(result.content, 'video_url'):
                video_url = result.content.video_url
            if hasattr(result.content, 'last_frame_url'):
                last_frame_url = result.content.last_frame_url
        
        return {
            "success": True,
            "task_id": result.id,
            "status": result.status,  # queued, running, succeeded, failed
            "model": result.model,
            "video_url": video_url,
            "last_frame_url": last_frame_url,
            "created_at": result.created_at,
            "updated_at": result.updated_at,
            "error": getattr(result, 'error', None),
            "response": result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def wait_for_video(
    client: Ark,
    task_id: str,
    max_wait: int = 600,
    poll_interval: int = 5
) -> dict:
    """
    等待视频生成完成
    
    Args:
        client: Ark 客户端
        task_id: 任务 ID
        max_wait: 最大等待时间(秒)
        poll_interval: 轮询间隔(秒)
    
    Returns:
        最终任务状态
    """
    print(f"⏳ 等待视频生成完成...")
    print(f"   任务ID: {task_id}")
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status = get_task_status(client, task_id)
        
        if not status["success"]:
            print(f"❌ 查询状态失败: {status['error']}")
            return status
        
        task_status = status["status"]
        elapsed = int(time.time() - start_time)
        
        if task_status == "succeeded":
            print(f"\n✅ 视频生成成功!")
            print(f"   耗时: {elapsed}秒")
            if status["video_url"]:
                print(f"   视频URL: {status['video_url']}")
            if status["last_frame_url"]:
                print(f"   尾帧URL: {status['last_frame_url']}")
            return status
        
        elif task_status == "failed":
            print(f"\n❌ 视频生成失败")
            if status["error"]:
                print(f"   错误: {status['error']}")
            return status
        
        else:
            # queued 或 running
            print(f"[{elapsed}s] 状态: {task_status}...", end="\r", flush=True)
        
        time.sleep(poll_interval)
    
    print(f"\n⏱️ 等待超时 ({max_wait}秒)")
    return {"success": False, "error": "Timeout", "status": task_status}


def download_file(url: str, output_path: str) -> bool:
    """
    下载文件
    
    Args:
        url: 文件 URL
        output_path: 保存路径
    
    Returns:
        是否成功
    """
    import requests
    
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"下载失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Seedance 文生视频工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 文生视频
  python3 generate_video.py "一只可爱的猫咪" --wait -o cat.mp4
  
  # 图生视频 (需要提供图片 URL)
  python3 generate_video.py "猫咪动起来" --image-url https://example.com/cat.jpg --wait
  
  # 查询任务状态
  python3 generate_video.py --status <task_id>
        """
    )
    
    parser.add_argument("prompt", nargs="?", help="视频描述提示词")
    parser.add_argument("-m", "--model", default="doubao-seedance-1-5-pro-251215",
                       help="模型 ID (默认: doubao-seedance-1-5-pro-251215)")
    parser.add_argument("-o", "--output", default="output.mp4",
                       help="输出文件路径 (默认: output.mp4)")
    parser.add_argument("-d", "--duration", type=int, default=5,
                       help="视频时长秒数 (默认: 5)")
    parser.add_argument("-r", "--ratio", default="16:9",
                       help="宽高比 (默认: 16:9, 可选: 9:16, 1:1, 4:3 等)")
    parser.add_argument("--watermark", action="store_true",
                       help="添加水印")
    parser.add_argument("--return-last-frame", action="store_true",
                       help="返回最后一帧图片")
    parser.add_argument("--image-url",
                       help="首帧图片 URL (图生视频时使用)")
    parser.add_argument("--wait", action="store_true",
                       help="等待视频生成完成")
    parser.add_argument("--status",
                       help="查询指定任务ID的状态")
    
    args = parser.parse_args()
    
    # 初始化客户端
    client = Ark(
        base_url=BASE_URL,
        api_key=API_KEY
    )
    
    # 查询任务状态模式
    if args.status:
        result = get_task_status(client, args.status)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return
    
    # 创建视频任务模式
    if not args.prompt:
        parser.error("需要提供提示词 (或使用 --status 查询任务)")
    
    print(f"🎬 创建视频生成任务")
    print(f"   模型: {args.model}")
    print(f"   提示词: {args.prompt}")
    print(f"   时长: {args.duration}秒")
    print(f"   比例: {args.ratio}")
    if args.image_url:
        print(f"   首帧图片: {args.image_url}")
    
    # 创建任务
    result = create_video_task(
        client=client,
        model=args.model,
        prompt=args.prompt,
        duration=args.duration,
        ratio=args.ratio,
        watermark=args.watermark,
        return_last_frame=args.return_last_frame,
        image_url=args.image_url
    )
    
    if not result["success"]:
        print(f"❌ 创建任务失败: {result['error']}")
        sys.exit(1)
    
    task_id = result["task_id"]
    print(f"✅ 任务已创建")
    print(f"   任务ID: {task_id}")
    
    # 等待完成并下载
    if args.wait:
        final_status = wait_for_video(client, task_id)
        
        if final_status.get("success") and final_status.get("video_url"):
            video_url = final_status["video_url"]
            print(f"\n📥 正在下载视频...")
            
            if download_file(video_url, args.output):
                print(f"✅ 视频已保存: {args.output}")
            else:
                print(f"❌ 下载视频失败")
                print(f"   视频URL: {video_url}")
        else:
            print(f"❌ 视频生成未完成或失败")
            sys.exit(1)
    else:
        print(f"\n💡 使用以下命令查询状态和下载:")
        print(f"   python3 generate_video.py --status {task_id} --wait -o {args.output}")


if __name__ == "__main__":
    main()
