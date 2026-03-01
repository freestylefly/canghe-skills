## 通过飞书发送视频文件（OpenClaw）

在 OpenClaw 中，你可以使用此 skill 生成视频后，通过飞书 App 将视频发送到聊天中。

### 完整步骤概览

生成视频 → 保存到本地 → 使用 message 工具发送 → 飞书 API 处理 → 视频上传到飞书 CDN → 发送到聊天

### 第一步：生成视频文件

使用 `seedance-video` skill 生成视频：

```bash
python3 /root/.openclaw/workspace/skills/seedance-video-generation/seedance.py \
  create \
  --prompt "新年祝福场景..." \
  --ratio 9:16 \
  --duration 5 \
  --resolution 1080p \
  --generate-audio true \
  --wait \
  --download /root/.openclaw/workspace
```

输出：本地视频文件路径，例如：
`/root/.openclaw/workspace/seedance_cgt-20260212104701-nqcr7_1770864513.mp4`

### 第二步：使用 message 工具发送视频

调用 OpenClaw 的 `message` 工具：

```python
message(
  action="send",           # 动作：发送消息
  channel="feishu",        # 目标频道：飞书
  filePath="/root/.openclaw/workspace/seedance_cgt-20260212104701-nqcr7_1770864513.mp4",  # 本地视频路径
  message="视频说明文字"    # 可选的附加说明
)
```

### 第三步：message 工具内部处理流程

`message` 工具接收到请求后，执行以下操作：

#### 3.1 读取本地文件

```python
with open(filePath, 'rb') as f:
    file_content = f.read()
```

#### 3.2 调用飞书 Open API

工具会调用飞书开放平台的 API，主要步骤：

**a) 获取上传凭证**

```
POST https://open.feishu.cn/open-apis/drive/v1/medias/upload_all
```

请求参数：
- `file_type`: video/mp4
- `file_name`: seedance_cgt-xxx.mp4
- `file_size`: [文件大小]

响应：
```json
{
  "code": 0,
  "data": {
    "upload_token": "xxxxx",
    "upload_url": "https://xxx.com/upload..."
  }
}
```

**b) 上传文件到飞书 CDN**

```
PUT {upload_url}
Content-Type: video/mp4
Authorization: Bearer {upload_token}

[视频二进制数据]
```

**c) 发送消息到飞书聊天**

```
POST https://open.feishu.cn/open-apis/im/v1/messages/send
```

请求参数：
```json
{
  "receive_id_type": "open_id",
  "receive_id": "ou_f323dd2c97951b029f7c43505c4b7566",
  "msg_type": "file",
  "content": "{\"file_key\":\"xxx\",\"file_name\":\"视频.mp4\"}"
}
```

### 权限认证

在整个流程中，需要以下权限：

| 环节 | 所需权限 | 配置位置 |
|------|---------|---------|
| 生成视频 | 火山引擎 ARK_API_KEY | 环境变量 |
| 读取本地文件 | 文件系统读取权限 | `/root/.openclaw/workspace/` |
| 飞书 API 调用 | 飞书 app_access_token | OpenClaw 飞书配置 |

飞书 app_access_token 获取：

```
POST https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal
```

使用配置在 OpenClaw 中的 `feishu.app_id` 和 `feishu.app_secret`。

### 飞书处理与分发

飞书接收到消息后：
1. **存储视频**：视频文件上传到飞书 CDN 存储
2. **生成资源 key**：为视频分配唯一的 `file_key`
3. **分发到客户端**：飞书接收端收到消息，从 CDN 下载视频预览，在聊天窗口显示视频播放器

### 完整流程图

```
┌─────────────────┐
│   用户请求       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ seedance生成视频 │ → API调用火山引擎
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  保存到本地文件  │ → /root/.openclaw/workspace/
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ message工具调用  │ → 读取本地文件
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 飞书API上传     │ → 1.获取upload_token
│                 │ → 2.上传到飞书CDN
│                 │ → 3.发送消息
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 飞书分发到客户端 │
└─────────────────┘
```

### 关键技术细节

1. **文件大小限制**：飞书支持最大 100MB 的视频文件，超过限制需要使用分块上传
2. **支持的视频格式**：MP4（推荐）、MOV、AVI、WebM
3. **上传超时**：大文件上传可能超时，建议控制视频在 10MB 以内
4. **API 速率限制**：飞书 API 有 QPS 限制，频繁发送需要注意限流

### 总结

整个流程的核心是：1. 本地生成 → 2. 本地保存 → 3. 工具封装 → 4. API 上传 → 5. 飞书分发

OpenClaw 的 `message` 工具已经封装了步骤 3-5，你只需要提供本地文件路径即可！
