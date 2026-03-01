#!/usr/bin/env python3
"""
飞书视频发送工具 - 支持分片上传大文件
"""

import os
import sys
import json
import requests
from pathlib import Path

# 飞书配置
APP_ID = "cli_a9005be686f89bd3"
APP_SECRET = "UvUMxhBGbejzqbeuR5BQqeZnjCrnsCiC"
FEISHU_DEFAULT_USER = "ou_20bf7fe6e4ec0f2f928e8ebc1c0a6e76"

# 分片大小: 5MB
CHUNK_SIZE = 5 * 1024 * 1024


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


def upload_file_with_chunks(token: str, file_path: str) -> str:
    """
    使用分片上传大文件到飞书
    
    流程:
    1. 初始化分片上传 (获取 upload_id)
    2. 逐个上传分片
    3. 完成上传 (合并分片)
    """
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    
    print(f"📁 文件: {file_name}")
    print(f"📦 大小: {file_size / 1024 / 1024:.1f} MB")
    print(f"📊 分片大小: {CHUNK_SIZE / 1024 / 1024} MB")
    print()
    
    # 步骤 1: 初始化分片上传
    print("1️⃣  初始化分片上传...")
    headers = {"Authorization": f"Bearer {token}"}
    
    init_resp = requests.post(
        "https://open.feishu.cn/open-apis/drive/v1/files/upload_prepare",
        headers=headers,
        json={
            "file_name": file_name,
            "size": file_size,
            "parent_type": "im",  # 发送到 IM
            "parent_node": FEISHU_DEFAULT_USER
        }
    )
    init_result = init_resp.json()
    
    if init_result.get("code") != 0:
        raise Exception(f"初始化失败: {init_result}")
    
    upload_id = init_result["data"]["upload_id"]
    block_size = init_result["data"].get("block_size", CHUNK_SIZE)
    print(f"   ✅ 初始化成功，upload_id: {upload_id[:20]}...")
    print()
    
    # 步骤 2: 上传分片
    print("2️⃣  上传分片...")
    block_index = 0
    uploaded_size = 0
    
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(block_size)
            if not chunk:
                break
            
            # 上传当前分片
            upload_resp = requests.post(
                "https://open.feishu.cn/open-apis/drive/v1/files/upload_part",
                headers=headers,
                params={"upload_id": upload_id, "block_index": block_index},
                data=chunk
            )
            
            if upload_resp.json().get("code") != 0:
                raise Exception(f"分片 {block_index} 上传失败: {upload_resp.json()}")
            
            uploaded_size += len(chunk)
            block_index += 1
            
            progress = (uploaded_size / file_size) * 100
            print(f"   分片 {block_index}: {len(chunk)/1024:.0f} KB ({progress:.1f}%)")
    
    print(f"   ✅ 分片上传完成，共 {block_index} 个分片")
    print()
    
    # 步骤 3: 完成上传
    print("3️⃣  完成上传，合并分片...")
    finish_resp = requests.post(
        "https://open.feishu.cn/open-apis/drive/v1/files/upload_finish",
        headers=headers,
        json={"upload_id": upload_id}
    )
    finish_result = finish_resp.json()
    
    if finish_result.get("code") != 0:
        raise Exception(f"完成上传失败: {finish_result}")
    
    file_token = finish_result["data"]["file_token"]
    print(f"   ✅ 文件上传成功，file_token: {file_token[:20]}...")
    print()
    
    return file_token


def send_video_message(token: str, user_id: str, file_token: str) -> dict:
    """发送视频消息"""
    resp = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        params={"receive_id_type": "open_id"},
        json={
            "receive_id": user_id,
            "msg_type": "media",
            "content": json.dumps({
                "file_token": file_token,
                "image_key": ""
            })
        }
    )
    
    result = resp.json()
    if result.get("code") == 0:
        return result["data"]
    else:
        raise Exception(f"发送消息失败: {result}")


def send_video(file_path: str, user_id: str = None) -> dict:
    """发送视频到飞书（支持大文件分片上传）"""
    if user_id is None:
        user_id = FEISHU_DEFAULT_USER
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    print("="*60)
    print("🎬 飞书视频发送工具（支持分片上传）")
    print("="*60)
    print()
    
    # 获取 token
    print("🔑 获取飞书 access token...")
    token = get_tenant_access_token()
    print("   ✅ Token 获取成功")
    print()
    
    # 分片上传
    file_token = upload_file_with_chunks(token, file_path)
    
    # 发送消息
    print("📤 发送视频消息...")
    result = send_video_message(token, user_id, file_token)
    print(f"✅ 消息发送成功!")
    print(f"   消息ID: {result['message_id']}")
    print(f"   聊天ID: {result['chat_id']}")
    print()
    print("🎉 完成! 请在飞书中查看视频")
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="发送视频到飞书（支持分片上传大文件）")
    parser.add_argument("file_path", help="视频文件路径")
    parser.add_argument("--user-id", help="目标用户 open_id")
    
    args = parser.parse_args()
    
    try:
        send_video(args.file_path, args.user_id)
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)
