---
name: canghe-tianyancha
description: Generates Tianyancha-style company and industry insight dashboards from researched enterprise data. Use when user asks for 天眼查, company lookup, enterprise analysis, hiring analysis, legal risk, financing, shareholders, intellectual property, investments, or industry company comparison.
---

# canghe-tianyancha

天眼查企业洞察看板 Skill —— 输入企业名称，自动生成包含企业概况、在招岗位分析、数据分析、司法风险、融资历史、股东结构、知识产权、对外投资、主要人员的单文件 HTML 看板。

> **导出说明**：本 Skill 已从原 Kimi 环境导出，适配其他 Kimi Work 用户使用。`kimi_search_v2` 和 `PythonRun` 均为 Kimi Work 内置工具，无需修改。

## 触发条件

当用户提到以下关键词时触发：
- 天眼查、查企业、企业信息、企业看板、公司查询
- 招聘查询、在招岗位、岗位列表、岗位分析、招聘分析
- 司法风险、法律诉讼、开庭公告
- 融资情况、融资历史、股东信息
- 工商信息、主要人员、企业洞察
- 知识产权、专利、商标、软件著作权
- 对外投资、成立时间、参保人数
- 岗位数据分析、招聘数据分析、招聘趋势
- 企业健康度、求职建议、公司评价、企业分析
- 招聘预测、薪资分析、求职参考
- **行业分析、行业洞察、头部企业、行业排名、大厂对比**
- **AI大模型、互联网、电商、金融科技、新能源等行业名 + 看板/分析/洞察**

## Preferences (EXTEND.md)

Use Bash to check EXTEND.md existence (priority order):

```bash
# Check project-level first
test -f .canghe-skills/canghe-tianyancha/EXTEND.md && echo "project"

# Then user-level (cross-platform: $HOME works on macOS/Linux/WSL)
test -f "$HOME/.canghe-skills/canghe-tianyancha/EXTEND.md" && echo "user"
```

| Path | Location |
|------|----------|
| `.canghe-skills/canghe-tianyancha/EXTEND.md` | Project directory |
| `$HOME/.canghe-skills/canghe-tianyancha/EXTEND.md` | User home |

| Result | Action |
|--------|--------|
| Found | Read, parse, display summary |
| Not found | Ask user with AskUserQuestion (see references/config/first-time-setup.md) |

**EXTEND.md Supports**: default output directory, recent job analysis window, industry company count, preferred data sources, report language, and whether to include dashboard disclaimers.

Schema: `references/config/preferences-schema.md`

## Usage

### 执行流程

### 模式 1 — 单企业查询（输入企业名称）

1. 从用户输入中提取企业名称
2. 使用 `kimi_search_v2` 并行搜索企业数据：
   - `{企业名} 天眼查 在招岗位 招聘 岗位分析`
   - `{企业名} 天眼查 司法风险 法律诉讼`
   - `{企业名} 天眼查 融资历史 股东信息`
   - `{企业名} 天眼查 工商信息 主要人员 成立时间 参保人数`
   - `{企业名} 天眼查 知识产权 专利 商标 软件著作权`
   - `{企业名} 天眼查 对外投资`
3. 结构化提取后调用 `generate_dashboard()` 生成单企业看板

### 模式 2 — 行业查询（输入行业名称）

1. 从用户输入中提取行业名称（如"AI大模型"、"互联网"、"电商"）
2. 使用 `kimi_search_v2` 搜索该行业头部企业名单：
   - `{行业名} 头部企业 排名 大厂 天眼查`
   - `{行业名} 公司 融资 在招岗位 天眼查`
3. 提取 TOP 5-10 家头部企业的核心数据（名称、在招岗位、成立时间、注册资本、融资轮次、参保人数、总部城市、核心产品）
4. **为每个头部企业收集完整数据**（工商信息、在招岗位、司法风险、融资历史、股东结构、知识产权、对外投资、主要人员）
5. 调用 `generate_industry_with_companies()` 批量生成：
   - 每个企业的独立「企业洞察看板」
   - 行业洞察看板（企业卡片可点击跳转至对应企业看板）

## Script Directory

**Important**: All scripts are located in the `scripts/` subdirectory of this skill.

**Agent Execution Instructions**:
1. Determine this SKILL.md file's directory path as `SKILL_DIR`
2. Script path = `${SKILL_DIR}/scripts/<script-name>.py`
3. Replace all `${SKILL_DIR}` in this document with the actual path

**Script Reference**:
| Script | Purpose |
|--------|---------|
| `scripts/generate_dashboard.py` | Generates single-company, industry, and batch HTML dashboards |

## 行业看板数据结构

`industry_data` 字段：
- `industry_name`: 行业名称
- `industry_desc`: 行业简介（可选）
- `companies`: 头部企业列表，每项包含：
  - `name`: 企业名称
  - `jobs_total`: 在招岗位总数
  - `established_date`: 成立时间
  - `registered_capital`: 注册资本
  - `status`: 经营状态
  - `scale`: 企业规模
  - `funding_rounds`: 融资轮次数
  - `tianyancha_url`: 天眼查详情页链接
  - `key_products`: 核心产品/业务
  - `employees`: 员工规模/参保人数
  - `city`: 总部城市
  - `industry_segment`: 细分赛道

## 行业看板内容

行业洞察看板包含：
1. **行业概览** — 头部企业数量、在招岗位总数、参保人数汇总、融资轮次汇总
2. **头部企业卡片** — 每家企业展示：在招岗位、融资轮次、参保人数、成立年份、总部城市、注册资本、企业规模、核心产品。卡片可点击跳转至该企业独立的「企业洞察看板」，同时保留「天眼查详情」外部链接
3. **在招岗位对比** — TOP10 企业横向柱状图
4. **融资活跃度对比** — TOP10 企业融资轮次对比
5. **成立时间分布** — 按年份统计企业成立数量
6. **企业规模分布** — 饼图展示规模分布
7. **总部城市分布** — 柱状图展示城市集中度
8. **免责声明** — 数据仅供参考，不构成投资建议

## 看板生成代码

### 单企业看板

```python
import sys
sys.path.insert(0, '${SKILL_DIR}/scripts')
from generate_dashboard import generate_dashboard

# 请替换 {workspace_path} 为你的实际工作区路径，例如：
# macOS: /Users/<你的用户名>/Documents/kimi/workspace
# Windows: C:\Users\<你的用户名>\Documents\kimi\workspace
filepath = generate_dashboard(company_data, '{workspace_path}')
print(f"看板已生成: {filepath}")
```

### 行业看板

```python
import sys
sys.path.insert(0, '${SKILL_DIR}/scripts')
from generate_dashboard import generate_industry_dashboard

filepath = generate_industry_dashboard(industry_data, '{workspace_path}')
print(f"行业看板已生成: {filepath}")
```

### 批量生成（行业看板 + 企业看板）

同时生成行业洞察看板 + 所有头部企业的独立洞察看板，企业卡片可点击跳转：

```python
import sys
sys.path.insert(0, '${SKILL_DIR}/scripts')
from generate_dashboard import generate_industry_with_companies

result = generate_industry_with_companies(
    industry_data,           # 行业数据（同 generate_industry_dashboard）
    companies_data_list,     # 企业数据列表（每个元素同 generate_dashboard 的 company_data）
    '{workspace_path}'
)

print(f"行业看板: {result['industry_dashboard']}")
print(f"企业看板: {result['company_dashboards']}")
print(f"所有文件: {result['all_files']}")
```

**批量生成流程**：
1. 先为每个企业生成独立的 `企业洞察看板_{企业名}.html`
2. 再生成行业看板，企业卡片自动链接到对应的企业看板文件
3. 企业卡片提供两个入口：「企业洞察看板」（本地）和「天眼查详情」（外部）

#### 企业概况字段
- `established_date`: 成立时间 (string, e.g. "1999-09-09")
- `registered_capital`: 注册资本 (string, e.g. "10000万元")
- `paid_in_capital`: 实缴资本 (string)
- `legal_representative`: 法定代表人 (string)
- `social_credit_code`: 统一社会信用代码 (string)
- `company_type`: 企业类型 (string, e.g. "有限责任公司")
- `insured_count`: 参保人数 (int)
- `business_scope`: 经营范围 (string)

#### 在招岗位字段
- `title`: 岗位名称
- `salary`: 薪资范围
- `city`: 城市
- `education`: 学历要求
- `experience`: 经验要求
- `source`: 招聘平台来源
- `date`: 发布日期 (YYYY-MM-DD 格式)
- `url` / `webInfoPath`: 岗位链接（优先使用 webInfoPath）
- `startDate`: 时间戳（毫秒，可选）

#### 司法风险字段
- `title`: 案件名称
- `date`: 日期
- `type`: 风险等级（高风险/中风险/低风险）
- `status`: 案件状态

#### 融资历史字段
- `round`: 融资轮次
- `amount`: 融资金额
- `date`: 融资日期
- `investor`: 投资方

#### 股东结构字段
- `name`: 股东名称
- `ratio`: 持股比例
- `amount`: 认缴金额

#### 知识产权字段
- `type`: 类型（专利/商标/软件著作权）
- `name`: 名称
- `date`: 申请/注册日期
- `status`: 状态
- `category`: 分类

#### 对外投资字段
- `company`: 被投企业名称
- `amount`: 投资金额
- `ratio`: 持股比例
- `status`: 投资状态
- `date`: 投资日期
- `industry`: 被投企业行业

#### 主要人员字段
- `name`: 姓名
- `position`: 职位
- `education`: 学历

### Stage 3 — 看板生成

使用 `PythonRun` 调用 `generate_dashboard.py` 生成 HTML 看板：

```python
import sys
sys.path.insert(0, '${SKILL_DIR}/scripts')
from generate_dashboard import generate_dashboard

filepath = generate_dashboard(company_data, '{workspace_path}')
print(f"看板已生成: {filepath}")
```

## 看板 Tab 结构

看板包含 9 个 Tab，默认显示"企业概况"：

1. **企业概况** — 工商基本信息（成立时间、注册资本、实缴资本、法定代表人、参保人数、企业类型、统一社会信用代码）、经营范围、核心数据汇总
2. **在招岗位分析** — 多维度数据分析视图（不展示岗位列表，纯图表分析）
3. **数据分析** — 企业健康度评估、招聘趋势预测、求职者友好度、薪资竞争力、风险预警、城市扩张分析、岗位类型分布、综合求职建议
4. **司法风险** — 法律诉讼、开庭公告等
5. **融资历史** — 融资轮次、金额、投资方
6. **股东结构** — 股东名称、持股比例、认缴金额
7. **知识产权** — 专利、商标、软件著作权统计与明细
8. **对外投资** — 投资企业、金额、持股比例、行业
9. **主要人员** — 高管列表

## 在招岗位分析维度

"在招岗位分析"Tab 不展示岗位列表卡片，改为纯数据分析视图，包含 7 个 ECharts 图表：

| 图表 | 类型 | 维度 |
|------|------|------|
| 城市分布 | 环形饼图 | 岗位按城市统计 |
| 学历要求 | 横向柱状图 | 本科/硕士/大专/不限 |
| 薪资分布 | 柱状图 | 10K以下/10-20K/20-30K/30-50K/50K+ |
| 经验要求 | 柱状图 | 不限/1-3年/3-5年/5-10年/10年+ |
| 招聘平台来源 | 环形饼图 | BOSS直聘/拉勾网/智联招聘/猎聘网等 |
| 发布时间趋势 | 面积折线图 | 近13周岗位发布数量趋势 |
| TOP热门岗位 | 横向柱状图 | 按岗位名称关键词统计TOP10 |

支持"本季度"（默认，90天）和"全部"两种数据范围切换，切换后所有图表联动刷新。

## 岗位数据分析时效性规范

**核心规则：只显示最近一个季度（90天）的岗位数据分析。**

1. **固定筛选**：所有图表固定基于最近 90 天内的岗位数据进行分析，不提供"全部"历史数据切换
2. **数量显示**：标题显示 `(本季度 X 个)`
3. **提示条**：蓝色提示条说明"当前显示最近90天（一个季度）的岗位数据分析"
4. **免责声明**：在提示条下方显示灰色标注"数据仅供参考，以实际情况为准"
5. **图表维度**：城市分布、学历要求、薪资分布、经验要求、招聘平台来源、发布时间趋势、TOP热门岗位

## 岗位数据交互规范

1. **筛选切换**："本季度"/"全部"按钮切换数据范围，7个图表联动刷新
2. **图表响应式**：所有图表随窗口大小自适应
3. **图表提示**：鼠标悬停显示详细数据 tooltip
4. **数据为空处理**：当某维度无数据时，图表区域显示"暂无XX数据"提示

## 数据分析维度

Python 端 `analyze_jobs()` 函数从岗位列表提取以下分析维度：

- **城市分布**：按 `city` 字段统计，返回 `[{name, value}]`
- **学历分布**：按 `education` 字段统计，返回 `{categories, values}`
- **薪资分布**：解析 `salary` 字段（如 "25K-40K"），按区间统计
- **经验分布**：按 `experience` 字段统计
- **来源分布**：按 `source` 字段统计招聘平台
- **时间趋势**：按周统计近13周岗位发布数量
- **TOP岗位**：提取岗位名称核心词（去掉修饰后缀），统计TOP10

## 数据分析模块

"数据分析"Tab 基于企业全量数据进行深度分析和预测，帮助求职者全面了解企业状况。

### 企业健康度评估

综合评分（满分100分），从四个维度评估：

| 维度 | 权重 | 评分依据 |
|------|------|----------|
| 招聘活跃度 | 30分 | 在招岗位总数：≥500(30)/≥200(25)/≥50(18)/>0(10) |
| 企业稳定性 | 30分 | 成立年限 + 参保人数 + 经营状态 |
| 发展潜力 | 20分 | 融资轮次 + 知识产权数量 |
| 风险等级 | 20分 | 司法风险数量：高风险(-8)/中风险(-4) |

评分等级：≥85优秀 / ≥70良好 / ≥50一般 / ≥30较弱 / <30差

### 招聘趋势预测

基于近13周岗位发布数据，使用简单线性回归预测未来4周招聘量：
- **趋势判断**：上升（斜率>0.5）/ 下降（斜率<-0.5）/ 稳定
- **预测图表**：历史数据（实线）+ 预测数据（虚线）
- **投递建议**：根据趋势给出投递时机建议

### 求职者友好度（满分100分）

| 维度 | 权重 | 评分依据 |
|------|------|----------|
| 学历门槛 | 25分 | 大专/不限岗位占比：≥30%(25)/≥15%(18)/<15%(10) |
| 经验要求 | 25分 | 不限/低经验岗位占比：≥40%(25)/≥20%(18)/<20%(10) |
| 岗位多样性 | 25分 | 岗位类型数：≥5(25)/≥3(18)/≥2(12)/1(5) |
| 薪资竞争力 | 25分 | 平均薪资：≥35K(25)/≥25K(20)/≥15K(15)/<15K(8) |

### 薪资竞争力评级

基于高薪岗位（30K+）占比：
- **强**：≥40% 高薪岗位
- **较强**：≥20% 高薪岗位
- **一般**：<20% 高薪岗位

### 风险预警

基于司法风险数据：
- **无风险**：无司法记录
- **低风险**：仅有低风险记录
- **中风险**：存在中风险记录
- **高风险**：存在高风险记录

### 城市扩张分析

基于招聘城市分布：
- **多城市扩张**：≥5个城市，最大城市占比<60%
- **区域扩张**：≥3个城市
- **集中发展**：<3个城市

### 岗位类型分布

自动分类岗位为：技术类/产品类/运营类/销售类/职能类/设计类/其他

### 综合求职建议

基于以上分析自动生成 3-6 条求职建议，包括：
- 企业整体状况评价
- 投递时机建议
- 求职者友好度评价
- 薪资竞争力评价
- 风险提示
- 其他特色建议（对外投资、知识产权等）

## 输出

- 单企业看板：`{workspace_path}/企业洞察看板_{企业名}.html`
- 行业看板：`{workspace_path}/行业洞察看板_{行业名}.html`
- **批量生成**：同时输出行业看板 + N 个企业看板，企业卡片支持点击跳转
- 单文件 HTML，零后端依赖，浏览器直接打开
- 使用 Tailwind CSS + ECharts，响应式布局

## 注意事项

- 天眼查 API 单次返回岗位数量有限，通常只返回前 20 条，分析结果基于可用数据
- 岗位总数 `jobs_total` 与分析样本量可能不一致，已通过数量标签说明
- 已下线职位仍可能出现在 API 数据中，通过"本季度"默认筛选缓解
- 天眼查企业数据库无法被代码直接程序化调用，实际通过 `kimi_search_v2` 获取公开数据
- 知识产权和对外投资数据可能不完整，以天眼查公示为准
- 薪资分布通过解析 `salary` 字符串（如 "25K-40K"）计算平均值后归类，可能存在误差
- **招聘趋势预测**基于简单线性回归，仅供参考，不构成投资建议
- **企业健康度评分**为综合评估模型，各维度权重可根据实际情况调整
- **求职建议**由算法自动生成，建议结合个人情况综合判断

## Extension Support

Custom configurations via EXTEND.md. See **Preferences** section for paths and supported options.
