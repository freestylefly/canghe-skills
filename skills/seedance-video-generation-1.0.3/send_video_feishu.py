#!/usr/bin/env python3
"""
飞书视频发送工具
直接使用飞书 API 上传视频并发送
"""

import os
import sys
import json
import requests
from pathlib import Path

# 飞书配置 - 从 OpenClaw 配置读取
APP_ID = "cli_a9005be686f89bd3"
APP_SECRET = "UvUMxhBGbejzqbeuR5BQqeZnjCrnsCiC"


def get_tenant_access_token():
    """获取飞书 tenant_access_token"""
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}
    )
    result = resp.json()
    if result.get("code") == 0:
        return result["tenant_access_token"]
    else:
        raise Exception(f"获取 token 失败: {result}")


def upload_file_to_feishu(token: str, file_path: str) -> str:
    """
    上传文件到飞书
    
    Args:
        token: tenant_access_token
        file_path: 本地文件路径
    
    Returns:
        file_key: 飞书文件 key
    """
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    # 构建 multipart body
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
    
    # 读取文件内容
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    body_bytes = "\r\n".join(body).encode("utf-8") + b"\r\n"
    body_bytes += file_content + b"\r\n"
    body_bytes += f"------{boundary}--\r\n".encode("utf-8")
    
    # 发送请求
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
        raise Exception(f"上传文件失败: {result}")


def send_media_message(token: str, user_id: str, file_key: str) -> dict:
    """
    发送媒体消息（视频）
    
    Args:
        token: tenant_access_token
        user_id: 用户 open_id
        file_key: 文件 key
    
    Returns:
        发送结果
    """
    resp = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        params={"receive_id_type": "open_id"},
        json={
            "receive_id": user_id,
            "msg_type": "media",
            "content": json.dumps({
                "file_key": file_key,
                "image_key": ""  # 视频缩略图（可选）
            })
        }
    )
    
    result = resp.json()
    if result.get("code") == 0:
        return result["data"]
    else:
        raise Exception(f"发送消息失败: {result}")


def send_video_to_feishu(file_path: str, user_id: str = None) -> dict:
    """
    发送视频到飞书
    
    Args:
        file_path: 视频文件路径
        user_id: 用户 open_id（默认使用当前会话用户）
    
    Returns:
        发送结果
    """
    # 默认用户
    if user_id is None:
        user_id = "ou_20bf7fe6e4ec0f2f928e8ebc1c0a6e76"
    
    # 检查文件
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    file_size = os.path.getsize(file_path) / 1024 / 1024
    print(f"📁 文件: {file_path}")
    print(f"📦 大小: {file_size:.1f} MB")
    
    # 获取 token
    print("🔑 获取 access token...")
    token = get_tenant_access_token()
    
    # 上传文件
    print("☁️  上传文件到飞书...")
    file_key = upload_file_to_feishu(token, file_path)
    print(f"✅ 文件上传成功: {file_key[:30]}...")
    
    # 发送消息
    print("📤 发送消息...")
    result = send_media_message(token, user_id, file_key)
    print(f"✅ 消息发送成功!")
    print(f"   消息ID: {result['message_id']}")
    print(f"   聊天ID: {result['chat_id']}")
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="发送视频到飞书")
    parser.add_argument("file_path", help="视频文件路径")
    parser.add_argument("--user-id", help="目标用户 open_id")
    
    args = parser.parse_args()
    
    try:
        result = send_video_to_feishu(args.file_path, args.user_id)
        print(f"\n🎉 完成! 请在飞书中查看视频")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
