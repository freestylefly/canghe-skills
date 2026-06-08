# canghe-tianyancha Preferences Schema

Use this file to document optional `EXTEND.md` settings for `canghe-tianyancha`.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `output_dir` | string | Workspace directory | Directory for generated HTML dashboards. |
| `recent_job_days` | number | `90` | Time window used for recent hiring analysis. |
| `industry_company_count` | number | `5-10` | Target number of companies for industry dashboards. |
| `preferred_sources` | string[] | `["天眼查"]` | Preferred sources for enterprise facts and risk data. |
| `report_language` | string | `zh` | Output language for dashboard labels and summaries. |
| `include_disclaimer` | boolean | `true` | Whether generated dashboards include data and decision disclaimers. |

Example:

```markdown
# canghe-tianyancha preferences

output_dir: ~/Desktop/company-dashboards
recent_job_days: 90
industry_company_count: 8
preferred_sources:
  - 天眼查
  - 企业官网
report_language: zh
include_disclaimer: true
```
