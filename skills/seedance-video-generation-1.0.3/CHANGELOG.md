# 更新日志

## v1.1.0 (2026-02-12)

### 新增功能

- **飞书视频发送指南**：新增 `how_to_send_video_via_feishu_app.md` 文档，详细说明如何在 OpenClaw 中将生成的视频通过飞书 App 发送到聊天中。
  - 完整的操作步骤：生成视频 → 本地保存 → message 工具发送 → 飞书 API 上传 → 飞书分发
  - 包含 message 工具调用示例
  - 飞书 Open API 调用细节（上传凭证、CDN 上传、消息发送）
  - 权限认证说明（ARK_API_KEY、飞书 app_access_token）
  - 关键技术细节（文件大小限制、支持格式、超时处理、速率限制）

## v1.0.0

- 初始版本
- 支持 Seedance 1.5 Pro、1.0 Pro、1.0 Pro Fast、1.0 Lite 模型
- 文本生成视频、图片生成视频（首帧、首尾帧、参考图）
- Python CLI 工具 (`seedance.py`)
- 完整的 curl 命令示例
