---
name: seedance-video
description: 使用字节跳动 Seedance 模型生成视频。支持文生视频和图生视频功能，通过 volcengine-ark SDK 调用 API。当用户需要生成视频、创建视频内容或基于文字/图片制作视频时激活此技能。
---

# Seedance 视频生成

使用字节跳动 Seedance-1.5-pro 模型 (doubao-seedance-1-5-pro-251215) 根据文本或图片生成视频。

## 前置要求

安装 SDK:
```bash
pip install 'volcengine-python-sdk[ark]'
```

## 功能

- **文生视频**: 根据文本提示词生成视频
- **图生视频**: 根据首帧图片生成视频
- **自定义参数**: 支持设置时长、宽高比、水印等
- **任务管理**: 创建任务、查询状态、自动下载

## 使用方法

### 1. 快速生成视频 (文生视频)

```bash
cd ~/.openclaw/workspace/skills/seedance-video
python3 scripts/generate_video.py "一只可爱的猫咪在草地上玩耍" --wait -o cat.mp4
```

### 2. 自定义参数

```bash
python3 scripts/generate_video.py "日落时分的海边" \
  --duration 10 \
  --ratio 16:9 \
  --wait \
  -o sunset.mp4
```

### 3. 图生视频

```bash
python3 scripts/generate_video.py "猫咪动起来" \
  --image-url https://example.com/cat.jpg \
  --duration 5 \
  --wait
```

### 4. 仅创建任务（不等待）

```bash
python3 scripts/generate_video.py "星空下的城市" -o starry.mp4
# 返回任务ID
```

然后稍后查询状态并下载：
```bash
python3 scripts/generate_video.py --status <task_id> --wait -o starry.mp4
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `prompt` | 必填 | 视频描述提示词 |
| `-o, --output` | output.mp4 | 输出文件路径 |
| `-m, --model` | doubao-seedance-1-5-pro-251215 | 模型 ID |
| `-d, --duration` | 5 | 视频时长(秒) |
| `-r, --ratio` | 16:9 | 宽高比 (16:9, 9:16, 1:1, 4:3 等) |
| `--watermark` | false | 添加水印 |
| `--return-last-frame` | false | 返回最后一帧图片 |
| `--image-url` | 无 | 首帧图片 URL (图生视频) |
| `--wait` | false | 等待视频生成完成并下载 |
| `--status` | 无 | 查询指定任务ID的状态 |

## API 密钥配置

脚本已内置 API Key: `8183a3de-9119-4524-9f59-e47b265229b6`

如需更换，可设置环境变量：
```bash
export SEEDANCE_API_KEY="your-api-key"
```

## 提示词优化建议

根据 [Seedance-1.5-pro 提示词指南](https://www.volcengine.com/docs/82379/2168087)：

1. **具体描述**: 描述场景、主体、动作、环境等细节
2. **风格明确**: 指定摄影风格（如"电影感"、"纪录片风格"）
3. **光线描述**: 说明光线条件（如"黄金时刻"、"柔和自然光"）
4. **镜头语言**: 描述镜头运动（如"缓慢推进"、"稳定器拍摄"）

### 示例提示词

```
一只金毛犬在秋天的公园里奔跑，金色落叶飘落，下午的阳光透过树叶，电影感镜头，稳定器拍摄，4K画质
```

```
一个机器人在未来城市的霓虹灯街道上行走，赛博朋克风格，雨夜，倒影，广角镜头，电影色调
```

## Python API 使用

```python
from volcenginesdkarkruntime import Ark
from scripts.generate_video import create_video_task, wait_for_video

# 初始化客户端
client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key="your-api-key"
)

# 创建视频任务
result = create_video_task(
    client=client,
    model="doubao-seedance-1-5-pro-251215",
    prompt="一只鸟在天空中飞翔",
    duration=5
)

task_id = result["task_id"]

# 等待并获取结果
final_status = wait_for_video(client, task_id)
video_url = final_status["video_url"]
```

## 注意事项

- **异步生成**: 视频生成是异步过程，通常需要 30-60 秒
- **任务保存时间**: 任务数据仅保留 24 小时
- **限流**: 注意账号的 RPM 和并发数限制
- **视频比例**: 建议视频宽高比与首帧图片比例接近

## 任务状态

- `queued`: 排队中
- `running`: 生成中
- `succeeded`: 成功
- `failed`: 失败
