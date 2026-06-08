# canghe-tianyancha

![Skill](https://img.shields.io/badge/Skill-Kimi%20Work-111827?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Output](https://img.shields.io/badge/Output-Single%20HTML-f97316?style=for-the-badge)
![Dependencies](https://img.shields.io/badge/Deps-Standard%20Library-10b981?style=for-the-badge)

把天眼查企业信息、招聘数据、司法风险、融资历史、股东结构、知识产权、对外投资和主要人员，整理成一份可以直接打开的企业洞察看板。

> 推荐搭配 **Kimi Work** 使用。Kimi Work 内置 `kimi_search_v2` 和 `PythonRun`，并且在天眼查企业数据检索上更专业，能让这个 Skill 的企业画像、行业对比和招聘分析更完整。

## 亮点

| 能力 | 说明 |
| --- | --- |
| 单企业洞察 | 输入企业名称，生成 9 个 Tab 的企业 HTML 看板 |
| 行业分析 | 输入行业名称，自动整理头部企业并生成行业洞察看板 |
| 招聘分析 | 聚合城市、学历、薪资、经验、来源、发布时间趋势和热门岗位 |
| 风险与资本 | 汇总司法风险、融资历史、股东结构、知识产权和对外投资 |
| 求职参考 | 给出企业健康度、招聘趋势、求职者友好度和综合建议 |
| 零后端部署 | 输出单文件 HTML，浏览器打开即可查看 |

## 适合谁

- 想快速了解目标公司的求职者
- 需要比较一个行业里多家公司的人
- 做企业研究、竞品分析、投资前调研的知识工作者
- 已经在 Kimi Work 中使用天眼查数据的用户

## 安装

### 通过 canghe-skills marketplace 安装

```bash
/plugin install business-intelligence-skills@canghe-skills
```

### 独立安装

```bash
mkdir -p ~/.kimi/daimon/skills
git clone https://github.com/freestylefly/canghe-skills.git /tmp/canghe-skills
cp -r /tmp/canghe-skills/skills/canghe-tianyancha ~/.kimi/daimon/skills/canghe-tianyancha
```

如果你已经下载了源码，也可以直接复制目录：

```bash
mkdir -p ~/.kimi/daimon/skills
cp -r /path/to/canghe-tianyancha ~/.kimi/daimon/skills/canghe-tianyancha
```

Windows PowerShell：

```powershell
$skillsDir = "$env:USERPROFILE\.kimi\daimon\skills"
New-Item -ItemType Directory -Force -Path $skillsDir
Copy-Item -Recurse -Force "canghe-tianyancha" "$skillsDir\canghe-tianyancha"
```

安装后重启 Kimi Work，或重新加载 Agent。

## 快速开始

在 Kimi Work 中输入：

```text
查一下月之暗面的企业情况，生成一个天眼查看板
```

或者：

```text
分析一下 AI 大模型行业的头部企业，做一个行业洞察看板
```

Skill 会完成三件事：

1. 用 `kimi_search_v2` 检索企业或行业相关的天眼查信息
2. 将工商、招聘、司法、融资、股东、知识产权等内容整理成结构化数据
3. 用 `scripts/generate_dashboard.py` 生成本地 HTML 看板

## 输出效果

### 企业洞察看板

企业看板包含 9 个 Tab：

| Tab | 内容 |
| --- | --- |
| 企业概况 | 成立时间、注册资本、法定代表人、参保人数、经营范围等 |
| 在招岗位分析 | 城市、学历、薪资、经验、来源、趋势、热门岗位图表 |
| 数据分析 | 企业健康度、招聘趋势预测、求职者友好度、薪资竞争力 |
| 司法风险 | 诉讼、开庭公告、风险等级和案件状态 |
| 融资历史 | 融资轮次、金额、日期、投资方 |
| 股东结构 | 股东名称、持股比例、认缴金额 |
| 知识产权 | 专利、商标、软件著作权 |
| 对外投资 | 被投企业、金额、比例、行业和状态 |
| 主要人员 | 高管姓名、职位、教育背景 |

### 行业洞察看板

行业看板会汇总 TOP 企业，并提供：

- 头部企业卡片
- 在招岗位对比
- 融资活跃度对比
- 成立时间分布
- 企业规模分布
- 总部城市分布
- 点击跳转到单个企业看板

## 文件结构

```text
canghe-tianyancha/
├── SKILL.md
├── README.md
└── scripts/
    └── generate_dashboard.py
```

## 本地调用

`generate_dashboard.py` 只依赖 Python 标准库。你也可以在 Kimi Work 之外直接调用它，只要自己准备好结构化企业数据。

```python
import sys

sys.path.insert(0, "/path/to/canghe-tianyancha/scripts")
from generate_dashboard import generate_dashboard

filepath = generate_dashboard(company_data, "/path/to/output")
print(f"看板已生成: {filepath}")
```

行业看板：

```python
import sys

sys.path.insert(0, "/path/to/canghe-tianyancha/scripts")
from generate_dashboard import generate_industry_dashboard

filepath = generate_industry_dashboard(industry_data, "/path/to/output")
print(f"行业看板已生成: {filepath}")
```

行业看板 + 多个企业看板：

```python
import sys

sys.path.insert(0, "/path/to/canghe-tianyancha/scripts")
from generate_dashboard import generate_industry_with_companies

result = generate_industry_with_companies(
    industry_data,
    companies_data_list,
    "/path/to/output",
)

print(result["industry_dashboard"])
print(result["company_dashboards"])
```

完整字段约定见 [SKILL.md](./SKILL.md)。

## 数据说明

- 本 Skill 不内置天眼查账号、接口密钥或私有数据源
- 数据质量取决于检索结果和可访问的数据范围
- Kimi Work 的天眼查专业数据能力会显著提升召回质量
- 招聘分析默认聚焦最近 90 天岗位，用于降低过期岗位影响
- 薪资、趋势预测、健康度评分为算法估算，仅供参考

## 免责声明

本项目生成的企业分析、风险判断、招聘趋势和求职建议仅用于信息整理与研究参考，不构成法律、投资、招聘或职业决策建议。请以天眼查、企业公告、监管披露及其他官方信息为准。

## License

未指定许可证。使用、分发或二次开发前请先确认作者授权。
