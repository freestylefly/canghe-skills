---
name: volcengine-video-understanding
description: 火山视频理解 - 使用火山方舟视频理解 API 分析视频内容。通过 Files API 上传视频（推荐），支持大文件（最大512MB），可用于视频内容分析、物体识别、动作理解等。当用户需要分析视频、理解视频内容、提取视频信息时激活此技能。
---

# 火山视频理解

使用字节跳动火山方舟视频理解 API（doubao-seed-2-0-pro-260215 等模型）对视频进行深度理解和分析。

**推荐方式**：Files API 上传 + Responses API 分析
- 支持最大 **512MB** 视频文件
- 自动视频预处理（FPS采样）
- 文件可重复使用（存储7天）

## 功能

- **视频上传**：通过 Files API 上传本地视频（推荐，最大512MB）
- **内容理解**：分析视频场景、人物、动作、情感
- **视频问答**：基于视频内容回答用户问题
- **视频描述**：自动生成视频描述和摘要

## 前置要求

设置环境变量：
```bash
export ARK_API_KEY="your-api-key-here"
```

## 使用方法

### 1. 基础视频分析（Files API 方式 - 推荐）

```bash
cd ~/.openclaw/workspace/skills/volcengine-video-understanding
python3 scripts/video_understand.py /path/to/video.mp4 "描述这个视频的内容"
```

### 2. 视频问答

```bash
python3 scripts/video_understand.py /path/to/video.mp4 "视频中出现了哪些人物？"
```

### 3. 情感分析

```bash
python3 scripts/video_understand.py /path/to/video.mp4 "分析视频中人物的情感变化"
```

### 4. 指定模型和帧率

```bash
python3 scripts/video_understand.py /path/to/video.mp4 "总结视频要点" \
  --model doubao-seed-2-0-pro-260215 \
  --fps 2
```

### 5. 保存结果到文件

```bash
python3 scripts/video_understand.py /path/to/video.mp4 "描述视频" --output result.json
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `video_path` | 必填 | 视频文件路径 |
| `instruction` | 必填 | 分析指令/问题 |
| `--model` | doubao-seed-2-0-pro-260215 | 模型 ID |
| `--fps` | 1 | 视频采样帧率（预处理） |
| `--output` | - | 结果输出文件路径 |

## 支持的模型

- `doubao-seed-2-0-pro-260215` (默认)
- `doubao-seed-2-0-lite-250728`
- `doubao-seed-1-6-251015`
- 其他 Seed 系列视频理解模型

## 分析示例

### 示例 1：视频内容描述
```bash
python3 scripts/video_understand.py ~/Desktop/video.mp4 "详细描述这个视频的内容，包括场景、人物和动作"
```

### 示例 2：视频摘要
```bash
python3 scripts/video_understand.py ~/Desktop/video.mp4 "用3句话总结这个视频的要点"
```

### 示例 3：动作识别
```bash
python3 scripts/video_understand.py ~/Desktop/video.mp4 "视频中的人物在做什么动作？按时间顺序描述"
```

### 示例 4：场景分析
```bash
python3 scripts/video_understand.py ~/Desktop/video.mp4 "分析视频中的场景变化和环境特征"
```

## 技术细节

### 调用流程

1. **上传视频**：通过 Files API 上传本地视频文件，指定 FPS 预处理配置
2. **等待处理**：等待视频预处理完成（状态变为 processed）
3. **创建任务**：调用 Responses API 进行视频理解
4. **获取结果**：返回分析结果

### API 格式

**Files API 上传**：
```bash
curl https://ark.cn-beijing.volces.com/api/v3/files \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -F 'purpose=user_data' \
  -F 'file=@video.mp4' \
  -F 'preprocess_configs[video][fps]=1'
```

**Responses API 分析**：
```json
{
  "model": "doubao-seed-2-0-pro-260215",
  "input": [
    {
      "role": "user",
      "content": [
        {
          "type": "input_video",
          "file_id": "file-xxxx"
        },
        {
          "type": "input_text",
          "text": "用户指令"
        }
      ]
    }
  ]
}
```

### FPS 设置建议

| FPS | 适用场景 |
|-----|----------|
| 0.3-0.5 | 慢节奏视频、静态场景、节省token |
| 1 | 一般视频分析（默认） |
| 2-3 | 快速动作、细节分析 |

## 限制

- **视频格式**：MP4（推荐）、MOV、AVI
- **文件大小**：最大 512MB（Files API 方式）
- **存储时间**：上传的文件默认存储 7 天
- **处理时间**：根据视频长度和复杂度，通常 10-60 秒

## Python API 使用

```python
from scripts.video_understand import analyze_video

result = analyze_video(
    file_path="/path/to/video.mp4",
    instruction="描述视频内容",
    model="doubao-seed-2-0-pro-260215",
    fps=1
)

# 提取回答
text = ""
for item in result.get("output", []):
    if item.get("type") == "message":
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                text = content.get("text", "")
                break

print(text)
```

## 错误处理

常见错误及解决方案：

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| API Key 错误 | 未设置或错误 | 检查 ARK_API_KEY 环境变量 |
| 文件不存在 | 路径错误 | 检查文件路径 |
| 上传失败 | 文件过大或格式不支持 | 检查文件大小（<512MB）和格式 |
| 处理超时 | 视频过长或复杂 | 缩短视频或降低 FPS |

## 参考文档

- [火山方舟视频理解文档](https://www.volcengine.com/docs/82379/1895586)
- [Files API 文档](https://www.volcengine.com/docs/82379/xxxx)
- [Responses API 文档](https://www.volcengine.com/docs/82379/xxxx)
