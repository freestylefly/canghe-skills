---
name: manga-drama
description: 漫剧生成器 - 基于 Seedance 的漫画风格短剧生成工具。支持以主角图片为基础，自动生成漫剧分镜脚本并生成视频。适用于创作漫画风格的短视频、角色故事、动画短片等。当用户想要生成漫画风格的视频短剧、角色故事或漫剧时使用此技能。
---

# 漫剧生成器

基于 Seedance 视频生成能力，专门用于创作**漫画风格的短剧**（漫剧）。

## 核心功能

- **主角识别**：分析提供的角色图片，提取角色特征
- **自动分镜**：根据主题自动生成漫剧分镜脚本
- **图生视频**：以主角图片为基础生成各分镜视频
- **漫画风格**：内置漫画风格提示词模板
- **分镜管理**：支持自定义分镜脚本

## 前置要求

1. 设置环境变量：
```bash
export ARK_API_KEY="your-api-key"
```

2. 需要依赖技能：**seedance-video-generation**

## 使用方法

### 1. 快速生成漫剧（推荐）

提供主角图片和主题，自动生成完整漫剧：

```bash
cd ~/.openclaw/workspace/skills/manga-drama
python3 scripts/manga_drama.py generate \
  --image /path/to/character.png \
  --theme "校园日常" \
  --scenes 3 \
  --send-feishu
```

### 2. 根据脚本生成漫剧

先创建脚本，再生成视频：

```bash
# 创建脚本模板
python3 scripts/manga_drama.py create-script \
  --output my_drama.json \
  --title "我的漫剧" \
  --character "双马尾女孩" \
  --num-scenes 4

# 编辑脚本文件后生成
python3 scripts/manga_drama.py from-script \
  --script my_drama.json \
  --image /path/to/character.png \
  --send-feishu
```

## 分镜模板

内置5种漫剧分镜类型：

| 分镜类型 | 名称 | 说明 |
|---------|------|------|
| introduction | 主角登场 | 介绍主角，展示角色特征 |
| action | 动作场景 | 主角进行某个动作 |
| emotion | 情感表达 | 表达某种情感 |
| interaction | 互动场景 | 与环境或其他元素互动 |
| ending | 结尾定格 | 漫剧结尾，定格画面 |

## 脚本格式

```json
{
  "title": "漫剧标题",
  "character": "主角描述",
  "style": "漫画风格",
  "total_scenes": 3,
  "scenes": [
    {
      "scene_number": 1,
      "type": "introduction",
      "name": "主角登场",
      "prompt": "双马尾女孩站在画面中央，微笑看向镜头，漫画风格...",
      "duration": 5,
      "ratio": "9:16",
      "resolution": "1080p"
    }
  ]
}
```

## 参数说明

### generate 命令

| 参数 | 必需 | 说明 |
|------|------|------|
| `--image` | ✅ | 主角图片路径 |
| `--theme` | ✅ | 漫剧主题/剧情描述 |
| `--scenes` | ❌ | 分镜数量（默认3） |
| `--output` | ❌ | 输出目录（默认~/Desktop） |
| `--send-feishu` | ❌ | 发送到飞书 |

### from-script 命令

| 参数 | 必需 | 说明 |
|------|------|------|
| `--script` | ✅ | 脚本文件路径 |
| `--image` | ✅ | 主角图片路径 |
| `--send-feishu` | ❌ | 发送到飞书 |

### create-script 命令

| 参数 | 必需 | 说明 |
|------|------|------|
| `--output` | ✅ | 输出脚本文件路径 |
| `--title` | ❌ | 漫剧标题 |
| `--character` | ❌ | 主角描述 |
| `--num-scenes` | ❌ | 分镜数量 |

## 使用示例

### 示例 1：生成校园日常漫剧

```bash
python3 scripts/manga_drama.py generate \
  --image ~/Desktop/girl_character.png \
  --theme "校园日常" \
  --scenes 3 \
  --send-feishu
```

生成3个分镜：
1. 主角登场（校园门口）
2. 动作场景（上课/运动）
3. 结尾定格（温馨画面）

### 示例 2：创建自定义漫剧

```bash
# 创建脚本
python3 scripts/manga_drama.py create-script \
  --output spring_festival.json \
  --title "春节团圆" \
  --character "白发奶奶" \
  --num-scenes 5

# 编辑 spring_festival.json 文件
# 然后生成
python3 scripts/manga_drama.py from-script \
  --script spring_festival.json \
  --image ~/Desktop/grandma.png \
  --send-feishu
```

## 风格特点

- **漫画质感**：手绘风格，线条清晰
- **柔和色彩**：温馨治愈的色调
- **电影构图**：专业的画面构图
- **角色一致性**：基于同一张主角图片生成

## 技术细节

### 调用流程

```
1. 分析主角图片 → 提取角色特征
2. 根据主题 → 生成分镜脚本
3. 每个分镜 → 调用 Seedance 图生视频
4. 可选 → 发送到飞书
```

### 视频规格

- **默认比例**：9:16（竖屏，适合手机观看）
- **默认分辨率**：1080p
- **默认时长**：每分镜5秒
- **风格**：漫画/手绘风格

## 输出结构

```
~/Desktop/drama_我的漫剧/
├── drama_script_xxx.json    # 脚本文件
├── scene_1_introduction.mp4 # 分镜1
├── scene_2_action.mp4       # 分镜2
├── scene_3_emotion.mp4      # 分镜3
└── ...
```

## 注意事项

1. **主角图片质量**：清晰的角色图片能获得更好的生成效果
2. **提示词优化**：可以编辑脚本文件自定义每个分镜的提示词
3. **生成时间**：每个分镜约30-60秒，多个分镜需要耐心等待
4. **文件大小**：1080p视频较大，发送飞书可能需要分片上传

## 进阶用法

### 自定义分镜提示词

编辑生成的脚本文件，修改 `prompt` 字段：

```json
{
  "prompt": "{character}在樱花树下读书，花瓣飘落，漫画风格，温馨治愈..."
}
```

### 批量生成系列漫剧

创建多个脚本，批量生成：

```bash
for script in scripts/*.json; do
  python3 scripts/manga_drama.py from-script \
    --script "$script" \
    --image ~/Desktop/character.png
done
```

## 参考文档

- [Seedance 视频生成](../seedance-video-generation-1.0.3/SKILL.md)
- [火山方舟文档](https://www.volcengine.com/docs/82379)
