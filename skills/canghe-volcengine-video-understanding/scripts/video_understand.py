#!/usr/bin/env python3
"""
火山视频理解工具
使用火山方舟视频理解 API 分析视频内容
"""

import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from typing import Optional

# API 配置
API_KEY = os.environ.get("ARK_API_KEY", "")
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seed-2-0-pro-260215"
DEFAULT_FPS = 1


def get_api_key():
    """获取 API Key"""
    key = os.environ.get("ARK_API_KEY")
    if not key:
        print("错误: 请设置 ARK_API_KEY 环境变量", file=sys.stderr)
        print("export ARK_API_KEY='your-api-key'", file=sys.stderr)
        sys.exit(1)
    return key


def upload_video_file(api_key: str, file_path: str, fps: int = 1) -> str:
    """
    使用 Files API 上传视频文件，支持预处理配置
    
    Args:
        api_key: API 密钥
        file_path: 本地视频文件路径
        fps: 视频采样帧率（默认 1）
    
    Returns:
        file_id: 上传后的文件 ID
    """
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        # 使用 requests 的 multipart 上传，包含预处理配置
        with open(file_path, "rb") as f:
            files = {
                "file": (os.path.basename(file_path), f, "video/mp4"),
                "purpose": (None, "user_data")
            }
            
            # 添加预处理配置 - FPS
            data = {
                "preprocess_configs[video][fps]": str(fps)
            }
            
            response = requests.post(
                f"{BASE_URL}/files",
                headers=headers,
                files=files,
                data=data,
                timeout=120
            )
            
            print(f"上传响应状态: {response.status_code}")
            
            if response.status_code != 200:
                print(f"响应内容: {response.text[:500]}")
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("id"):
                return result["id"]
            else:
                raise Exception(f"上传失败: {result}")
    except Exception as e:
        raise Exception(f"上传文件失败: {e}")


def create_video_understanding_task(
    api_key: str,
    model: str,
    file_id: str,
    instruction: str,
    fps: int = 1
) -> dict:
    """
    创建视频理解任务 - 使用 Responses API 和 Files API file_id
    
    Args:
        api_key: API 密钥
        model: 模型 ID
        file_id: Files API 上传后的文件 ID
        instruction: 用户指令/问题
        fps: 帧率（默认 1）
    
    Returns:
        任务创建结果
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 使用 Responses API 格式，引用 file_id
    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_video",
                        "file_id": file_id
                    },
                    {
                        "type": "input_text",
                        "text": instruction
                    }
                ]
            }
        ]
    }
    
    try:
        print(f"使用 Responses API，文件 ID: {file_id}")
        response = requests.post(
            f"{BASE_URL}/responses",
            headers=headers,
            json=payload,
            timeout=300
        )
        
        if response.status_code != 200:
            print(f"错误响应: {response.text[:1000]}")
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise Exception(f"创建任务失败: {e}")


def wait_for_file_processing(api_key: str, file_id: str, max_wait: int = 180) -> dict:
    """
    等待文件处理完成
    
    Args:
        api_key: API 密钥
        file_id: 文件 ID
        max_wait: 最大等待时间（秒）
    
    Returns:
        文件信息
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    start_time = time.time()
    
    print("⏳ 等待视频预处理完成...")
    check_count = 0
    
    while time.time() - start_time < max_wait:
        response = requests.get(
            f"{BASE_URL}/files/{file_id}",
            headers=headers,
            timeout=30
        )
        result = response.json()
        
        status = result.get("status", "unknown")
        check_count += 1
        
        # 每10次检查打印一次状态
        if check_count % 10 == 0:
            print(f"   状态: {status} ({int(time.time() - start_time)}s)...", end="\r", flush=True)
        
        # active 或 processed 状态都可以使用
        if status in ["active", "processed"]:
            print(f"\n✅ 视频预处理完成 (状态: {status}, 耗时: {int(time.time() - start_time)}s)")
            return result
        elif status == "error":
            raise Exception(f"文件处理失败: {result}")
        
        time.sleep(2)
    
    # 超时但如果是 active 状态，也尝试继续
    print(f"\n⚠️  等待超时，但文件状态为 {status}，尝试继续...")
    return result


def analyze_video(
    file_path: str,
    instruction: str,
    model: str = DEFAULT_MODEL,
    fps: int = DEFAULT_FPS,
    wait: bool = True
) -> dict:
    """
    分析视频内容 - 使用 Files API 上传（推荐方式）
    
    Args:
        file_path: 视频文件路径
        instruction: 用户指令/问题
        model: 模型 ID
        fps: 帧率
        wait: 是否等待完成
    
    Returns:
        分析结果
    """
    api_key = get_api_key()
    
    # 检查文件
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    file_size = os.path.getsize(file_path) / 1024 / 1024
    print(f"📁 视频文件: {file_path}")
    print(f"📦 文件大小: {file_size:.1f} MB")
    print(f"🤖 使用模型: {model}")
    print(f"🎬 FPS: {fps}")
    print(f"📝 指令: {instruction}")
    print()
    
    # 步骤 1: 使用 Files API 上传视频
    print("☁️  使用 Files API 上传视频...")
    file_id = upload_video_file(api_key, file_path, fps)
    print(f"✅ 上传成功，文件ID: {file_id}")
    print()
    
    # 步骤 2: 等待文件处理完成
    wait_for_file_processing(api_key, file_id)
    print()
    
    # 步骤 3: 创建理解任务
    print("🧠 分析视频内容...")
    print("⏳ 这可能需要一些时间，请耐心等待...")
    print()
    
    result = create_video_understanding_task(
        api_key=api_key,
        model=model,
        file_id=file_id,
        instruction=instruction,
        fps=fps
    )
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="火山视频理解 - 分析视频内容",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础分析
  python3 video_understand.py /path/to/video.mp4 "描述这个视频的内容"
  
  # 指定模型和帧率
  python3 video_understand.py /path/to/video.mp4 "总结视频要点" --model doubao-seed-2-0-pro-260215 --fps 2
  
  # 详细分析
  python3 video_understand.py /path/to/video.mp4 "分析视频中的人物情感和动作" --fps 1
        """
    )
    
    parser.add_argument("video_path", help="视频文件路径")
    parser.add_argument("instruction", help="分析指令/问题")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"模型ID (默认: {DEFAULT_MODEL})")
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS, help=f"帧率 (默认: {DEFAULT_FPS})")
    parser.add_argument("--output", "-o", help="输出结果到文件")
    
    args = parser.parse_args()
    
    try:
        # 执行分析
        result = analyze_video(
            file_path=args.video_path,
            instruction=args.instruction,
            model=args.model,
            fps=args.fps
        )
        
        # 格式化输出
        print("\n" + "="*60)
        print("📊 分析结果")
        print("="*60)
        
        # 提取回答内容 - Responses API 格式
        content = ""
        if "output" in result:
            # Responses API 格式
            for item in result.get("output", []):
                if item.get("type") == "message":
                    for content_item in item.get("content", []):
                        if content_item.get("type") == "output_text":
                            content = content_item.get("text", "")
                            break
        elif "choices" in result and len(result["choices"]) > 0:
            # Chat API 格式（兼容）
            content = result["choices"][0].get("message", {}).get("content", "")
        
        if content:
            print(content)
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 保存到文件
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 结果已保存: {args.output}")
        
        print("\n✅ 分析完成!")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
