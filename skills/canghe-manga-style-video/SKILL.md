---
name: manga-style-video
description: 漫画风格视频生成器 - 专门生成日式治愈系、国风水墨、美式卡通等漫画风格的动画视频。内置8种漫画风格模板，支持图生视频，一键生成高质量漫画动画。当用户需要生成漫画风格、动画风格、手绘风格的视频时使用此技能。
---

# 漫画风格视频生成器

专门用于生成**漫画/动画风格**的视频，内置多种风格模板，无需复杂的提示词工程。

## 核心特点

- 🎨 **8种漫画风格** - 日式、国风、美式等预设风格
- 🖼️ **图生视频** - 基于参考图片保持角色一致性
- ✨ **优化提示词** - 内置专业漫画风格描述词
- 🎬 **一键生成** - 简单命令快速生成

## 支持的漫画风格

| 风格代码 | 名称 | 特点 |
|---------|------|------|
| `japanese` | 日式治愈系 | 吉卜力风格、手绘水彩、温馨治愈 |
| `ghibli` | 吉卜力风格 | Studio Ghibli、宫崎骏动画风格 |
| `chinese` | 国风水墨 | 中国传统水墨、淡雅诗意、工笔线条 |
| `cartoon` | 美式卡通 | 迪士尼皮克斯、3D卡通、色彩鲜艳 |
| `sketch` | 铅笔素描 | 手绘线条、黑白灰、艺术感 |
| `watercolor` | 水彩手绘 | 透明质感、色彩晕染、艺术插画 |
| `manga_comic` | 日式漫画 | 黑白网点、速度线、动态构图 |
| `chibi` | Q版萌系 | 大头比例、可爱萌系、圆润线条 |

## 前置要求

```bash
export ARK_API_KEY="your-api-key"
```

## 使用方法

### 1. 基础使用

生成日式治愈风格视频：

```bash
cd ~/.openclaw/workspace/skills/manga-style-video
python3 scripts/manga_style_video.py "女孩在樱花树下读书"
```

### 2. 指定风格

```bash
# 国风水墨风格
python3 scripts/manga_style_video.py "山水意境" --style chinese

# 美式卡通风格
python3 scripts/manga_style_video.py "可爱小动物" --style cartoon

# 吉卜力风格
python3 scripts/manga_style_video.py "乡村风景" --style ghibli
```

### 3. 基于参考图片

```bash
# 使用角色图片作为参考
python3 scripts/manga_style_video.py "奶奶在包饺子" \
  --style japanese \
  --image ~/Desktop/character.png
```

### 4. 完整参数

```bash
python3 scripts/manga_style_video.py "春节团圆场景" \
  --style japanese \
  --image character.png \
  --duration 10 \
  --ratio 9:16 \
  --resolution 1080p \
  --output ~/Desktop/my_video.mp4
```

## 参数说明

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `prompt` | ✅ | - | 视频内容描述 |
| `--style` | ❌ | japanese | 漫画风格 |
| `--image` | ❌ | - | 参考图片路径 |
| `--duration` | ❌ | 10 | 时长（秒） |
| `--ratio` | ❌ | 9:16 | 比例（16:9/9:16/1:1/4:3） |
| `--resolution` | ❌ | 1080p | 分辨率 |
| `--output` | ❌ | - | 输出路径 |
| `--no-wait` | ❌ | false | 不等待完成 |

## 使用示例

### 示例1：生成日式治愈风格

```bash
python3 scripts/manga_style_video.py \
  "白发奶奶在厨房忙碌，窗外阳光洒进来" \
  --style japanese \
  --duration 8
```

### 示例2：国风水墨风格

```bash
python3 scripts/manga_style_video.py \
  "古代女子在荷塘边弹琴，荷花盛开" \
  --style chinese \
  --ratio 16:9
```

### 示例3：基于角色生成漫剧

```bash
# 分镜1：角色登场
python3 scripts/manga_style_video.py \
  "双马尾女孩站在校门口微笑" \
  --style chibi \
  --image girl.png \
  --output scene1.mp4

# 分镜2：动作场景
python3 scripts/manga_style_video.py \
  "女孩在教室认真读书" \
  --style chibi \
  --image girl.png \
  --output scene2.mp4
```

### 示例4：生成Q版萌系视频

```bash
python3 scripts/manga_style_video.py \
  "小猫咪在草地上打滚，超级可爱" \
  --style chibi \
  --duration 5
```

## 查看所有风格

```bash
python3 scripts/manga_style_video.py --list-styles
```

输出：
```
🎨 可用的漫画风格:
  japanese     - 日式治愈系
  ghibli       - 吉卜力风格
  chinese      - 国风水墨
  cartoon      - 美式卡通
  sketch       - 铅笔素描
  watercolor   - 水彩手绘
  manga_comic  - 日式漫画
  chibi        - Q版萌系
```

## 风格提示词示例

### 日式治愈系 (japanese)
```
日式动画风格，吉卜力工作室风格，手绘水彩质感，柔和粉彩色调，
线条简洁流畅，温馨治愈，细腻的背景描绘，宫崎骏风格
```

### 国风水墨 (chinese)
```
中国传统水墨画风格，国风动画，淡雅色调，山水意境，
工笔线条，古风手绘，诗意唯美
```

### Q版萌系 (chibi)
```
Q版大头比例，萌系可爱风格，圆润线条，明亮色彩，
卡通渲染，治愈系表情
```

## 技术细节

### 调用接口

- **API**: `POST /api/v3/contents/generations/tasks`
- **模型**: `doubao-seedance-1-5-pro-251215`（默认）
- **图生视频**: 支持 base64 图片上传

### 生成流程

```
1. 选择漫画风格 → 获取对应提示词模板
2. 组合用户描述 + 风格提示词
3. 调用 Seedance API 生成视频
4. 等待生成完成 → 下载视频
```

## 输出文件

默认保存到 `~/Desktop/`，文件名格式：
```
manga_{风格}_{时间戳}.mp4
```

## 注意事项

1. **参考图片** - 清晰的角色图片能获得更好的风格化效果
2. **提示词** - 描述场景和动作即可，风格由 `--style` 参数控制
3. **生成时间** - 每个视频约30-60秒
4. **文件大小** - 1080p视频较大，建议搭配 `--duration` 控制时长

## 对比：普通视频 vs 漫画风格视频

| 普通提示词 | 漫画风格提示词（本技能自动生成） |
|-----------|------------------------------|
| "女孩在樱花树下" | "女孩在樱花树下，日式动画风格，吉卜力工作室风格，手绘水彩质感，柔和粉彩色调，线条简洁流畅，温馨治愈" |

## 进阶技巧

### 批量生成漫剧分镜

```bash
# 创建脚本
for i in 1 2 3; do
  python3 scripts/manga_style_video.py \
    "分镜$i的场景描述" \
    --style japanese \
    --image character.png \
    --output scene_$i.mp4 &
done
wait
```

### 自定义风格组合

如果想要特定的混合风格，可以直接使用 `seedance-video-generation` 技能，手动编写提示词。

## 参考文档

- [Seedance 视频生成](../seedance-video-generation-1.0.3/SKILL.md)
- [火山方舟文档](https://www.volcengine.com/docs/82379)
