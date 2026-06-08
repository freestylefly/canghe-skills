#!/usr/bin/env python3
"""
天眼查企业洞察看板 HTML 生成器
默认只显示最近一个季度（90天）的在招岗位
支持：企业概况、在招岗位（数据分析）、数据分析、司法风险、融资历史、股东结构、知识产权、对外投资、主要人员
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter


def parse_job_date(job: dict) -> Optional[datetime]:
    """解析岗位日期，支持多种格式"""
    start_date = job.get('startDate')
    if start_date and str(start_date).isdigit():
        try:
            return datetime.fromtimestamp(int(start_date) / 1000)
        except (ValueError, OSError):
            pass
    
    date_str = job.get('date')
    if date_str:
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d', '%m-%d']:
            try:
                if fmt == '%m-%d':
                    parsed = datetime.strptime(date_str, fmt)
                    return parsed.replace(year=datetime.now().year)
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
    
    return None


def get_time_label(job_date: datetime) -> str:
    """获取时间标签：今天/昨天/X天前/X周前/X个月前/长期"""
    now = datetime.now()
    delta = now - job_date
    days = delta.days
    
    if days < 0:
        return "未来"
    if days == 0:
        return "今天"
    if days == 1:
        return "昨天"
    if days < 7:
        return f"{days}天前"
    if days < 30:
        weeks = days // 7
        return f"{weeks}周前"
    if days < 90:
        months = days // 30
        return f"{months}个月前"
    return "长期"


def filter_jobs_by_time(jobs: List[dict], days: int = 90) -> List[dict]:
    """按时间过滤岗位，默认最近90天"""
    cutoff = datetime.now() - timedelta(days=days)
    filtered = []
    for job in jobs:
        job_date = parse_job_date(job)
        if job_date and job_date >= cutoff:
            job['_parsed_date'] = job_date
            job['_time_label'] = get_time_label(job_date)
            filtered.append(job)
    filtered.sort(key=lambda x: x['_parsed_date'], reverse=True)
    return filtered


def get_job_url(job: dict) -> str:
    """获取有效的岗位链接"""
    for key in ['webInfoPath', 'url', 'jobUrl', 'link']:
        url = job.get(key)
        if url and isinstance(url, str) and url.startswith('http'):
            return url
    return '#'


def analyze_jobs(jobs: List[dict]) -> dict:
    """对岗位列表进行多维度数据分析"""
    if not jobs:
        return {
            'city': [],
            'education': {'categories': [], 'values': []},
            'salary': [],
            'avg_salary': 0,
            'experience': {'categories': [], 'values': []},
            'source': [],
            'date_trend': {'categories': [], 'values': []},
            'top_titles': [],
            'job_types': {'categories': [], 'values': []},
        }
    
    # 城市分布
    city_counter = Counter()
    for job in jobs:
        city = job.get('city', '未知')
        if city:
            city_counter[city] += 1
    city_dist = [{'name': k, 'value': v} for k, v in city_counter.most_common()]
    
    # 学历分布
    edu_counter = Counter()
    for job in jobs:
        edu = job.get('education', '未知')
        if edu:
            edu_counter[edu] += 1
    edu_categories = [k for k, _ in edu_counter.most_common()]
    edu_values = [v for _, v in edu_counter.most_common()]
    
    # 薪资分布
    salary_ranges = {'10K以下': 0, '10-20K': 0, '20-30K': 0, '30-50K': 0, '50K+': 0, '薪资面议': 0}
    salary_sum = 0
    salary_count = 0
    for job in jobs:
        salary = job.get('salary', '薪资面议')
        if not salary or salary == '薪资面议':
            salary_ranges['薪资面议'] += 1
            continue
        try:
            s = salary.replace('K', '').replace('k', '').replace('+', '')
            if '-' in s:
                parts = s.split('-')
                low = float(parts[0])
                high = float(parts[1]) if parts[1] else low
                avg = (low + high) / 2
            else:
                avg = float(s)
            
            salary_sum += avg
            salary_count += 1
            
            if avg < 10:
                salary_ranges['10K以下'] += 1
            elif avg < 20:
                salary_ranges['10-20K'] += 1
            elif avg < 30:
                salary_ranges['20-30K'] += 1
            elif avg < 50:
                salary_ranges['30-50K'] += 1
            else:
                salary_ranges['50K+'] += 1
        except (ValueError, IndexError):
            salary_ranges['薪资面议'] += 1
    
    salary_dist = [{'range': k, 'count': v} for k, v in salary_ranges.items() if v > 0]
    avg_salary = round(salary_sum / salary_count, 1) if salary_count > 0 else 0
    
    # 经验要求分布
    exp_counter = Counter()
    for job in jobs:
        exp = job.get('experience', '未知')
        if exp:
            exp_counter[exp] += 1
    exp_categories = [k for k, _ in exp_counter.most_common()]
    exp_values = [v for _, v in exp_counter.most_common()]
    
    # 招聘平台来源分布
    source_counter = Counter()
    for job in jobs:
        src = job.get('source', '未知')
        if src:
            source_counter[src] += 1
    source_dist = [{'name': k, 'value': v} for k, v in source_counter.most_common()]
    
    # 岗位发布时间趋势（按周）
    now = datetime.now()
    week_labels = []
    week_counts = []
    for i in range(12, -1, -1):
        week_start = now - timedelta(weeks=i+1)
        week_end = now - timedelta(weeks=i)
        label = f"{week_start.month}/{week_start.day}"
        count = sum(1 for job in jobs if parse_job_date(job) and week_start <= parse_job_date(job) < week_end)
        week_labels.append(label)
        week_counts.append(count)
    
    # TOP热门岗位
    title_counter = Counter()
    for job in jobs:
        title = job.get('title', '')
        if title:
            core = title.split('-')[0].split('（')[0].split('(')[0].strip()
            title_counter[core] += 1
    top_titles = [{'name': k, 'value': v} for k, v in title_counter.most_common(10)]
    
    # 岗位类型分布（技术/产品/运营/销售/职能/其他）
    type_keywords = {
        '技术类': ['开发', '工程师', '算法', '架构', '测试', '运维', '前端', '后端', 'Java', 'Python', '数据'],
        '产品类': ['产品', '项目经理', '项目'],
        '运营类': ['运营', '内容', '活动', '用户', '社群', '新媒体'],
        '销售类': ['销售', '商务', 'BD', '客户经理', '渠道'],
        '职能类': ['HR', '人力', '财务', '法务', '行政', '采购', '助理'],
        '设计类': ['设计', 'UI', 'UX', '视觉', '交互'],
    }
    type_counter = Counter()
    for job in jobs:
        title = job.get('title', '')
        matched = False
        for ttype, keywords in type_keywords.items():
            if any(kw in title for kw in keywords):
                type_counter[ttype] += 1
                matched = True
                break
        if not matched:
            type_counter['其他'] += 1
    job_types = {'categories': [k for k, _ in type_counter.most_common()], 'values': [v for _, v in type_counter.most_common()]}
    
    return {
        'city': city_dist,
        'education': {'categories': edu_categories, 'values': edu_values},
        'salary': salary_dist,
        'avg_salary': avg_salary,
        'experience': {'categories': exp_categories, 'values': exp_values},
        'source': source_dist,
        'date_trend': {'categories': week_labels, 'values': week_counts},
        'top_titles': top_titles,
        'job_types': job_types,
    }


def analyze_company(company_data: dict, recent_jobs: List[dict], all_jobs: List[dict], risks: List[dict], 
                    funding: List[dict], ip_list: List[dict], investments: List[dict]) -> dict:
    """
    对企业进行深度数据分析和预测
    返回包含分析结果和预测的字典
    """
    result = {
        'health_score': 0,
        'health_level': '',
        'health_details': [],
        'recruit_trend': '',
        'recruit_prediction': [],
        'recruit_suggestion': '',
        'job_seeker_friendly': 0,
        'friendly_details': [],
        'salary_competitive': '',
        'salary_details': [],
        'risk_warning': '',
        'risk_details': [],
        'city_expansion': '',
        'city_details': [],
        'overall_suggestion': '',
        'suggestion_points': [],
    }
    
    # ===== 企业健康度评分 =====
    score = 0
    details = []
    
    # 招聘活跃度 (0-30分)
    jobs_total = company_data.get('jobs_total', len(all_jobs))
    if jobs_total >= 500:
        score += 30
        details.append({'label': '招聘活跃度', 'score': 30, 'max': 30, 'desc': '招聘非常活跃', 'status': 'excellent'})
    elif jobs_total >= 200:
        score += 25
        details.append({'label': '招聘活跃度', 'score': 25, 'max': 30, 'desc': '招聘较活跃', 'status': 'good'})
    elif jobs_total >= 50:
        score += 18
        details.append({'label': '招聘活跃度', 'score': 18, 'max': 30, 'desc': '招聘一般', 'status': 'normal'})
    elif jobs_total > 0:
        score += 10
        details.append({'label': '招聘活跃度', 'score': 10, 'max': 30, 'desc': '招聘较少', 'status': 'warning'})
    else:
        details.append({'label': '招聘活跃度', 'score': 0, 'max': 30, 'desc': '暂无招聘信息', 'status': 'danger'})
    
    # 企业稳定性 (0-30分)
    established_date = company_data.get('established_date', '')
    company_age_years = 0
    if established_date:
        try:
            est_year = int(established_date.split('-')[0])
            company_age_years = datetime.now().year - est_year
        except:
            pass
    
    insured_count = company_data.get('insured_count', 0)
    status = company_data.get('status', '')
    
    stability_score = 0
    if company_age_years >= 10:
        stability_score += 12
    elif company_age_years >= 5:
        stability_score += 10
    elif company_age_years >= 3:
        stability_score += 7
    elif company_age_years > 0:
        stability_score += 4
    
    if insured_count >= 1000:
        stability_score += 12
    elif insured_count >= 500:
        stability_score += 10
    elif insured_count >= 100:
        stability_score += 7
    elif insured_count > 0:
        stability_score += 4
    
    if status == '存续':
        stability_score += 6
    elif status == '在业':
        stability_score += 6
    else:
        stability_score += 3
    
    score += stability_score
    if stability_score >= 25:
        details.append({'label': '企业稳定性', 'score': stability_score, 'max': 30, 'desc': '非常稳定', 'status': 'excellent'})
    elif stability_score >= 20:
        details.append({'label': '企业稳定性', 'score': stability_score, 'max': 30, 'desc': '较为稳定', 'status': 'good'})
    elif stability_score >= 12:
        details.append({'label': '企业稳定性', 'score': stability_score, 'max': 30, 'desc': '稳定性一般', 'status': 'normal'})
    else:
        details.append({'label': '企业稳定性', 'score': stability_score, 'max': 30, 'desc': '稳定性较弱', 'status': 'warning'})
    
    # 发展潜力 (0-20分)
    potential_score = 0
    if len(funding) >= 3:
        potential_score += 10
    elif len(funding) >= 1:
        potential_score += 7
    
    if len(ip_list) >= 50:
        potential_score += 10
    elif len(ip_list) >= 20:
        potential_score += 8
    elif len(ip_list) >= 5:
        potential_score += 5
    elif len(ip_list) > 0:
        potential_score += 3
    
    score += potential_score
    if potential_score >= 15:
        details.append({'label': '发展潜力', 'score': potential_score, 'max': 20, 'desc': '发展潜力大', 'status': 'excellent'})
    elif potential_score >= 10:
        details.append({'label': '发展潜力', 'score': potential_score, 'max': 20, 'desc': '有一定潜力', 'status': 'good'})
    elif potential_score >= 5:
        details.append({'label': '发展潜力', 'score': potential_score, 'max': 20, 'desc': '潜力一般', 'status': 'normal'})
    else:
        details.append({'label': '发展潜力', 'score': potential_score, 'max': 20, 'desc': '潜力待观察', 'status': 'warning'})
    
    # 风险等级 (0-20分，风险越低分越高)
    risk_score = 20
    high_risks = sum(1 for r in risks if r.get('type') == '高风险')
    medium_risks = sum(1 for r in risks if r.get('type') == '中风险')
    
    risk_score -= high_risks * 8
    risk_score -= medium_risks * 4
    risk_score = max(0, risk_score)
    score += risk_score
    
    if risk_score >= 16:
        details.append({'label': '风险等级', 'score': risk_score, 'max': 20, 'desc': '风险较低', 'status': 'excellent'})
    elif risk_score >= 10:
        details.append({'label': '风险等级', 'score': risk_score, 'max': 20, 'desc': '风险中等', 'status': 'normal'})
    elif risk_score >= 5:
        details.append({'label': '风险等级', 'score': risk_score, 'max': 20, 'desc': '风险较高', 'status': 'warning'})
    else:
        details.append({'label': '风险等级', 'score': risk_score, 'max': 20, 'desc': '风险很高', 'status': 'danger'})
    
    result['health_score'] = score
    if score >= 85:
        result['health_level'] = '优秀'
    elif score >= 70:
        result['health_level'] = '良好'
    elif score >= 50:
        result['health_level'] = '一般'
    elif score >= 30:
        result['health_level'] = '较弱'
    else:
        result['health_level'] = '差'
    result['health_details'] = details
    
    # ===== 招聘趋势预测 =====
    recent_analysis = analyze_jobs(recent_jobs)
    trend_values = recent_analysis['date_trend']['values']
    
    if len(trend_values) >= 3 and sum(trend_values) > 0:
        # 简单线性回归预测未来4周
        n = len(trend_values)
        x_mean = sum(range(n)) / n
        y_mean = sum(trend_values) / n
        
        numerator = sum((i - x_mean) * (trend_values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator != 0:
            slope = numerator / denominator
            intercept = y_mean - slope * x_mean
            
            predictions = []
            for i in range(4):
                pred = max(0, round(slope * (n + i) + intercept))
                predictions.append(pred)
            
            result['recruit_prediction'] = predictions
            
            if slope > 0.5:
                result['recruit_trend'] = '上升'
                result['recruit_suggestion'] = '招聘需求呈上升趋势，建议尽快投递'
            elif slope < -0.5:
                result['recruit_trend'] = '下降'
                result['recruit_suggestion'] = '招聘需求在放缓，建议抓紧机会'
            else:
                result['recruit_trend'] = '稳定'
                result['recruit_suggestion'] = '招聘需求保持稳定，可正常投递'
        else:
            result['recruit_prediction'] = [round(y_mean)] * 4
            result['recruit_trend'] = '稳定'
            result['recruit_suggestion'] = '招聘需求保持稳定，可正常投递'
    else:
        result['recruit_prediction'] = [0, 0, 0, 0]
        result['recruit_trend'] = '未知'
        result['recruit_suggestion'] = '数据不足，无法判断趋势'
    
    # ===== 求职者友好度 =====
    friendly_score = 0
    friendly_details = []
    
    # 学历门槛
    edu_data = recent_analysis['education']
    total_edu = sum(edu_data['values']) if edu_data['values'] else 0
    if total_edu > 0:
        low_edu_idx = [i for i, c in enumerate(edu_data['categories']) if c in ['大专', '不限', '高中']]
        low_edu_count = sum(edu_data['values'][i] for i in low_edu_idx if i < len(edu_data['values']))
        low_edu_ratio = low_edu_count / total_edu
        
        if low_edu_ratio >= 0.3:
            friendly_score += 25
            friendly_details.append({'label': '学历门槛', 'score': 25, 'max': 25, 'desc': '门槛较低，大专/不限岗位占比高', 'status': 'excellent'})
        elif low_edu_ratio >= 0.15:
            friendly_score += 18
            friendly_details.append({'label': '学历门槛', 'score': 18, 'max': 25, 'desc': '门槛适中', 'status': 'good'})
        else:
            friendly_score += 10
            friendly_details.append({'label': '学历门槛', 'score': 10, 'max': 25, 'desc': '门槛较高，以本科及以上为主', 'status': 'normal'})
    else:
        friendly_details.append({'label': '学历门槛', 'score': 0, 'max': 25, 'desc': '数据不足', 'status': 'normal'})
    
    # 经验要求
    exp_data = recent_analysis['experience']
    total_exp = sum(exp_data['values']) if exp_data['values'] else 0
    if total_exp > 0:
        low_exp_idx = [i for i, c in enumerate(exp_data['categories']) if c in ['不限', '应届生', '1年以下', '1-3年']]
        low_exp_count = sum(exp_data['values'][i] for i in low_exp_idx if i < len(exp_data['values']))
        low_exp_ratio = low_exp_count / total_exp
        
        if low_exp_ratio >= 0.4:
            friendly_score += 25
            friendly_details.append({'label': '经验要求', 'score': 25, 'max': 25, 'desc': '对新人友好，不限/低经验岗位多', 'status': 'excellent'})
        elif low_exp_ratio >= 0.2:
            friendly_score += 18
            friendly_details.append({'label': '经验要求', 'score': 18, 'max': 25, 'desc': '有一定新人岗位', 'status': 'good'})
        else:
            friendly_score += 10
            friendly_details.append({'label': '经验要求', 'score': 10, 'max': 25, 'desc': '偏向有经验者', 'status': 'normal'})
    else:
        friendly_details.append({'label': '经验要求', 'score': 0, 'max': 25, 'desc': '数据不足', 'status': 'normal'})
    
    # 岗位多样性
    job_types = recent_analysis['job_types']
    type_count = len(job_types['categories']) if job_types['categories'] else 0
    if type_count >= 5:
        friendly_score += 25
        friendly_details.append({'label': '岗位多样性', 'score': 25, 'max': 25, 'desc': '岗位类型丰富，选择面广', 'status': 'excellent'})
    elif type_count >= 3:
        friendly_score += 18
        friendly_details.append({'label': '岗位多样性', 'score': 18, 'max': 25, 'desc': '岗位类型较丰富', 'status': 'good'})
    elif type_count >= 2:
        friendly_score += 12
        friendly_details.append({'label': '岗位多样性', 'score': 12, 'max': 25, 'desc': '岗位类型一般', 'status': 'normal'})
    else:
        friendly_score += 5
        friendly_details.append({'label': '岗位多样性', 'score': 5, 'max': 25, 'desc': '岗位类型较单一', 'status': 'warning'})
    
    # 薪资竞争力
    avg_salary = recent_analysis['avg_salary']
    if avg_salary >= 35:
        friendly_score += 25
        friendly_details.append({'label': '薪资竞争力', 'score': 25, 'max': 25, 'desc': f'平均薪资{avg_salary}K，竞争力强', 'status': 'excellent'})
    elif avg_salary >= 25:
        friendly_score += 20
        friendly_details.append({'label': '薪资竞争力', 'score': 20, 'max': 25, 'desc': f'平均薪资{avg_salary}K，竞争力较好', 'status': 'good'})
    elif avg_salary >= 15:
        friendly_score += 15
        friendly_details.append({'label': '薪资竞争力', 'score': 15, 'max': 25, 'desc': f'平均薪资{avg_salary}K，中等水平', 'status': 'normal'})
    elif avg_salary > 0:
        friendly_score += 8
        friendly_details.append({'label': '薪资竞争力', 'score': 8, 'max': 25, 'desc': f'平均薪资{avg_salary}K，偏低', 'status': 'warning'})
    else:
        friendly_details.append({'label': '薪资竞争力', 'score': 0, 'max': 25, 'desc': '薪资数据不足', 'status': 'normal'})
    
    result['job_seeker_friendly'] = friendly_score
    result['friendly_details'] = friendly_details
    
    # ===== 薪资竞争力分析 =====
    salary_data = recent_analysis['salary']
    if salary_data:
        high_salary = sum(d['count'] for d in salary_data if d['range'] in ['30-50K', '50K+'])
        total_salary = sum(d['count'] for d in salary_data)
        if total_salary > 0:
            high_ratio = high_salary / total_salary
            if high_ratio >= 0.4:
                result['salary_competitive'] = '强'
                result['salary_details'] = [
                    f'高薪岗位（30K+）占比 {high_ratio*100:.1f}%',
                    '薪资水平在行业中处于领先地位',
                    '适合追求高收入的求职者'
                ]
            elif high_ratio >= 0.2:
                result['salary_competitive'] = '较强'
                result['salary_details'] = [
                    f'高薪岗位（30K+）占比 {high_ratio*100:.1f}%',
                    '薪资水平在行业中处于中上位置',
                    '有一定的高薪机会'
                ]
            else:
                result['salary_competitive'] = '一般'
                result['salary_details'] = [
                    f'高薪岗位（30K+）占比 {high_ratio*100:.1f}%',
                    '薪资水平在行业中处于中等位置',
                    '建议综合考虑其他因素'
                ]
    
    # ===== 风险预警 =====
    if high_risks > 0:
        result['risk_warning'] = '高风险'
        result['risk_details'] = [
            f'存在 {high_risks} 条高风险司法记录',
            '建议仔细了解相关案件详情',
            '可通过天眼查详情页查看具体信息'
        ]
    elif medium_risks > 0:
        result['risk_warning'] = '中风险'
        result['risk_details'] = [
            f'存在 {medium_risks} 条中风险司法记录',
            '建议关注企业法律纠纷情况',
            '总体风险可控，但需留意'
        ]
    elif len(risks) > 0:
        result['risk_warning'] = '低风险'
        result['risk_details'] = [
            f'存在 {len(risks)} 条低风险记录',
            '企业法律风险较低',
            '可放心投递'
        ]
    else:
        result['risk_warning'] = '无风险'
        result['risk_details'] = [
            '暂无司法风险记录',
            '企业法律状况良好',
            '可放心投递'
        ]
    
    # ===== 城市扩张分析 =====
    city_data = recent_analysis['city']
    if city_data:
        top_city = city_data[0]
        top_ratio = top_city['value'] / sum(d['value'] for d in city_data)
        city_count = len(city_data)
        
        if city_count >= 5 and top_ratio < 0.6:
            result['city_expansion'] = '多城市扩张'
            result['city_details'] = [
                f'招聘覆盖 {city_count} 个城市',
                f'最大招聘城市占比 {top_ratio*100:.1f}%',
                '企业处于多城市扩张阶段',
                '跨城市求职机会较多'
            ]
        elif city_count >= 3:
            result['city_expansion'] = '区域扩张'
            result['city_details'] = [
                f'招聘覆盖 {city_count} 个城市',
                f'主要招聘城市占比 {top_ratio*100:.1f}%',
                '企业在重点区域布局',
                '可选择主要城市投递'
            ]
        else:
            result['city_expansion'] = '集中发展'
            result['city_details'] = [
                f'招聘集中在 {city_count} 个城市',
                f'主要城市占比 {top_ratio*100:.1f}%',
                '企业招聘较为集中',
                '建议关注主要招聘城市'
            ]
    
    # ===== 综合求职建议 =====
    suggestions = []
    
    if score >= 70:
        suggestions.append('企业整体状况良好，值得投递')
    elif score >= 50:
        suggestions.append('企业整体状况一般，可综合考虑后投递')
    else:
        suggestions.append('企业整体状况较弱，建议谨慎考虑')
    
    if result['recruit_trend'] == '上升':
        suggestions.append('招聘需求上升，是投递的好时机')
    elif result['recruit_trend'] == '下降':
        suggestions.append('招聘需求在下降，建议尽快行动')
    
    if friendly_score >= 80:
        suggestions.append('对求职者非常友好，门槛较低')
    elif friendly_score >= 60:
        suggestions.append('对求职者较为友好')
    
    if result['salary_competitive'] in ['强', '较强']:
        suggestions.append('薪资竞争力强，适合追求高收入')
    
    if result['risk_warning'] == '高风险':
        suggestions.append('⚠️ 存在司法风险，建议深入了解后再决定')
    
    if len(investments) >= 5:
        suggestions.append('对外投资活跃，企业生态较完善')
    
    if len(ip_list) >= 20:
        suggestions.append('知识产权丰富，技术实力较强')
    
    result['overall_suggestion'] = '；'.join(suggestions[:3]) if suggestions else '建议综合评估后决定'
    result['suggestion_points'] = suggestions
    
    return result


def generate_dashboard(company_data: dict, output_dir: str) -> str:
    """生成企业洞察看板 HTML 文件"""
    
    # ===== 数据准备 =====
    name = company_data.get('name', '未知企业')
    status = company_data.get('status', '存续')
    industry = company_data.get('industry', '未知行业')
    scale = company_data.get('scale', '未知规模')
    address = company_data.get('address', '')
    tianyancha_url = company_data.get('tianyancha_url', '')
    
    # 企业概况
    established_date = company_data.get('established_date', '')
    registered_capital = company_data.get('registered_capital', '')
    paid_in_capital = company_data.get('paid_in_capital', '')
    legal_representative = company_data.get('legal_representative', '')
    social_credit_code = company_data.get('social_credit_code', '')
    company_type = company_data.get('company_type', '')
    insured_count = company_data.get('insured_count', 0)
    business_scope = company_data.get('business_scope', '')
    
    company_age = ''
    if established_date:
        try:
            est_year = int(established_date.split('-')[0])
            company_age = f"{datetime.now().year - est_year}年"
        except (ValueError, IndexError):
            pass
    
    # 岗位数据
    all_jobs = company_data.get('jobs', [])
    jobs_total = company_data.get('jobs_total', len(all_jobs))
    recent_jobs = filter_jobs_by_time(all_jobs, days=90)
    
    all_jobs_with_labels = []
    for job in all_jobs:
        job_copy = dict(job)
        job_date = parse_job_date(job)
        if job_date:
            job_copy['_parsed_date'] = job_date
            job_copy['_time_label'] = get_time_label(job_date)
        else:
            job_copy['_time_label'] = '未知'
        job_copy['_url'] = get_job_url(job)
        all_jobs_with_labels.append(job_copy)
    all_jobs_with_labels.sort(key=lambda x: x.get('_parsed_date', datetime.min), reverse=True)
    
    for job in recent_jobs:
        job['_url'] = get_job_url(job)
    
    # 岗位数据分析
    recent_analysis = analyze_jobs(recent_jobs)
    all_analysis = analyze_jobs(all_jobs_with_labels)
    
    # 风险数据
    risks = company_data.get('risk', [])
    
    # 融资数据
    funding = company_data.get('funding', [])
    
    # 股东数据
    shareholders = company_data.get('shareholders', [])
    
    # 知识产权
    ip_list = company_data.get('intellectual_property', [])
    ip_patents = [ip for ip in ip_list if ip.get('type') == '专利']
    ip_trademarks = [ip for ip in ip_list if ip.get('type') == '商标']
    ip_copyrights = [ip for ip in ip_list if ip.get('type') == '软件著作权']
    
    # 对外投资
    investments = company_data.get('investments', [])
    
    # 人员数据
    staff = company_data.get('staff', [])
    
    # 企业深度分析
    company_analysis = analyze_company(company_data, recent_jobs, all_jobs_with_labels, risks, funding, ip_list, investments)
    
    query_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # ===== 序列化数据为 JSON =====
    recent_analysis_json = json.dumps(recent_analysis, ensure_ascii=False)
    all_analysis_json = json.dumps(all_analysis, ensure_ascii=False)
    company_analysis_json = json.dumps(company_analysis, ensure_ascii=False)
    
    # ===== HTML 模板 =====
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>企业洞察看板 · {name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        * {{ font-family: 'Inter', -apple-system, sans-serif; }}
        .glass {{ background: rgba(255,255,255,0.95); backdrop-filter: blur(12px); border: 1px solid rgba(226,232,240,0.8); }}
        .card {{ transition: all 0.3s ease; }}
        .card:hover {{ transform: translateY(-3px); box-shadow: 0 12px 40px -12px rgba(0,0,0,0.12); }}
        .tab-active {{ border-bottom: 2px solid #1e3a5f; color: #1e3a5f; font-weight: 600; }}
        .risk-high {{ border-left: 4px solid #dc2626; }}
        .risk-medium {{ border-left: 4px solid #f59e0b; }}
        .risk-low {{ border-left: 4px solid #16a34a; }}
        .animate-in {{ animation: fadeIn 0.5s ease-out; }}
        @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(10px); }} to {{ opacity:1; transform:translateY(0); }} }}
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 3px; }}
        .page-btn {{ transition: all 0.2s; }}
        .page-btn:hover:not(:disabled) {{ background: #1e3a5f; color: white; }}
        .page-btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}
        .page-btn.active {{ background: #1e3a5f; color: white; }}
        .time-recent {{ background: #dcfce7; color: #166534; }}
        .time-medium {{ background: #fef3c7; color: #92400e; }}
        .time-old {{ background: #f1f5f9; color: #64748b; }}
        .filter-btn {{ transition: all 0.2s; }}
        .filter-btn.active {{ background: #1e3a5f; color: white; border-color: #1e3a5f; }}
        .info-card {{ background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); }}
        .ip-patent {{ border-left: 3px solid #3b82f6; }}
        .ip-trademark {{ border-left: 3px solid #f59e0b; }}
        .ip-copyright {{ border-left: 3px solid #10b981; }}
        .investment-card {{ border-left: 3px solid #8b5cf6; }}
        .chart-container {{ min-height: 280px; }}
        .score-ring {{ position: relative; width: 120px; height: 120px; }}
        .score-ring svg {{ transform: rotate(-90deg); }}
        .score-text {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }}
        .status-excellent {{ color: #16a34a; background: #dcfce7; }}
        .status-good {{ color: #2563eb; background: #dbeafe; }}
        .status-normal {{ color: #d97706; background: #fef3c7; }}
        .status-warning {{ color: #ea580c; background: #ffedd5; }}
        .status-danger {{ color: #dc2626; background: #fee2e2; }}
        .prediction-line {{ border-top: 2px dashed #94a3b8; }}
    </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen">
    <header class="bg-slate-900 text-white sticky top-0 z-50 shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center gap-3">
                    <div class="w-9 h-9 bg-amber-400 rounded-lg flex items-center justify-center">
                        <i class="fas fa-building text-slate-900 text-lg"></i>
                    </div>
                    <div>
                        <h1 class="text-lg font-bold">企业洞察看板</h1>
                        <p class="text-xs text-slate-400">数据来源：天眼查企业数据库 · 实时查询</p>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    <span class="text-xs bg-green-900 text-green-300 px-3 py-1 rounded-full">
                        <i class="fas fa-check-circle mr-1"></i>真实数据
                    </span>
                    <span class="text-xs text-slate-400">查询时间：{query_time}</span>
                </div>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        <!-- 企业概览 -->
        <div class="glass rounded-2xl p-6 animate-in">
            <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                <div class="flex items-start gap-4">
                    <div class="w-16 h-16 bg-orange-50 rounded-xl flex items-center justify-center flex-shrink-0">
                        <i class="fas fa-building text-2xl text-orange-600"></i>
                    </div>
                    <div>
                        <h2 class="text-2xl font-bold text-slate-800">{name}</h2>
                        <div class="flex flex-wrap items-center gap-2 mt-2">
                            <span class="px-2.5 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">{status}</span>
                            <span class="px-2.5 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">{industry}</span>
                            <span class="px-2.5 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">{scale}</span>
                            {f'<span class="px-2.5 py-0.5 bg-amber-100 text-amber-700 rounded-full text-xs font-medium">成立{company_age}</span>' if company_age else ''}
                        </div>
                        <p class="text-sm text-slate-500 mt-2"><i class="fas fa-map-marker-alt mr-1"></i>{address}</p>
                    </div>
                </div>
                {f'<a href="{tianyancha_url}" target="_blank" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"><i class="fas fa-external-link-alt"></i>天眼查详情页</a>' if tianyancha_url else ''}
            </div>
        </div>

        <!-- 核心指标 -->
        <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <div class="card glass rounded-xl p-5">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-sm text-slate-500">在招岗位</span>
                    <div class="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center"><i class="fas fa-briefcase text-blue-500 text-sm"></i></div>
                </div>
                <p class="text-2xl font-bold text-slate-800">{jobs_total:,}</p>
                <p class="text-xs text-slate-400 mt-1">活跃招聘中</p>
            </div>
            <div class="card glass rounded-xl p-5">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-sm text-slate-500">司法案件</span>
                    <div class="w-8 h-8 bg-red-50 rounded-lg flex items-center justify-center"><i class="fas fa-gavel text-red-500 text-sm"></i></div>
                </div>
                <p class="text-2xl font-bold text-slate-800">{len(risks)}</p>
                <p class="text-xs text-slate-400 mt-1">历史记录</p>
            </div>
            <div class="card glass rounded-xl p-5">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-sm text-slate-500">知识产权</span>
                    <div class="w-8 h-8 bg-indigo-50 rounded-lg flex items-center justify-center"><i class="fas fa-lightbulb text-indigo-500 text-sm"></i></div>
                </div>
                <p class="text-2xl font-bold text-slate-800">{len(ip_list)}</p>
                <p class="text-xs text-slate-400 mt-1">专利/商标/著作权</p>
            </div>
            <div class="card glass rounded-xl p-5">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-sm text-slate-500">对外投资</span>
                    <div class="w-8 h-8 bg-purple-50 rounded-lg flex items-center justify-center"><i class="fas fa-project-diagram text-purple-500 text-sm"></i></div>
                </div>
                <p class="text-2xl font-bold text-slate-800">{len(investments)}</p>
                <p class="text-xs text-slate-400 mt-1">投资企业数</p>
            </div>
            <div class="card glass rounded-xl p-5">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-sm text-slate-500">成立时间</span>
                    <div class="w-8 h-8 bg-amber-50 rounded-lg flex items-center justify-center"><i class="fas fa-calendar-alt text-amber-500 text-sm"></i></div>
                </div>
                <p class="text-2xl font-bold text-slate-800">{established_date[:4] if established_date else '-'}</p>
                <p class="text-xs text-slate-400 mt-1">{company_age if company_age else '成立时间未知'}</p>
            </div>
        </div>

        <!-- Tab 导航 -->
        <div class="glass rounded-xl px-6 py-3">
            <div class="flex gap-6 overflow-x-auto">
                <button id="tab-overview" onclick="switchTab('overview')" class="tab-btn tab-active pb-2 text-sm whitespace-nowrap">
                    <i class="fas fa-info-circle mr-1.5"></i>企业概况
                </button>
                <button id="tab-analysis" onclick="switchTab('analysis')" class="tab-btn text-slate-500 pb-2 text-sm whitespace-nowrap">
                    <i class="fas fa-brain mr-1.5"></i>数据分析
                </button>
                <button id="tab-risk" onclick="switchTab('risk')" class="tab-btn text-slate-500 pb-2 text-sm whitespace-nowrap">
                    <i class="fas fa-gavel mr-1.5"></i>司法风险
                </button>
                <button id="tab-funding" onclick="switchTab('funding')" class="tab-btn text-slate-500 pb-2 text-sm whitespace-nowrap">
                    <i class="fas fa-coins mr-1.5"></i>融资历史
                </button>
                <button id="tab-shareholders" onclick="switchTab('shareholders')" class="tab-btn text-slate-500 pb-2 text-sm whitespace-nowrap">
                    <i class="fas fa-users mr-1.5"></i>股东结构
                </button>
                <button id="tab-ip" onclick="switchTab('ip')" class="tab-btn text-slate-500 pb-2 text-sm whitespace-nowrap">
                    <i class="fas fa-lightbulb mr-1.5"></i>知识产权
                </button>
                <button id="tab-investments" onclick="switchTab('investments')" class="tab-btn text-slate-500 pb-2 text-sm whitespace-nowrap">
                    <i class="fas fa-project-diagram mr-1.5"></i>对外投资
                </button>
                <button id="tab-staff" onclick="switchTab('staff')" class="tab-btn text-slate-500 pb-2 text-sm whitespace-nowrap">
                    <i class="fas fa-id-card mr-1.5"></i>主要人员
                </button>
            </div>
        </div>

        <!-- 企业概况 Tab -->
        <div id="panel-overview" class="tab-panel space-y-4">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2 space-y-4">
                    <div class="glass rounded-xl p-6">
                        <h3 class="font-semibold text-slate-800 mb-4">工商基本信息</h3>
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div class="info-card rounded-lg p-4">
                                <p class="text-xs text-slate-500 mb-1">成立时间</p>
                                <p class="font-semibold text-slate-800">{established_date if established_date else '未披露'}</p>
                            </div>
                            <div class="info-card rounded-lg p-4">
                                <p class="text-xs text-slate-500 mb-1">经营状态</p>
                                <p class="font-semibold text-green-700">{status}</p>
                            </div>
                            <div class="info-card rounded-lg p-4">
                                <p class="text-xs text-slate-500 mb-1">注册资本</p>
                                <p class="font-semibold text-slate-800">{registered_capital if registered_capital else '未披露'}</p>
                            </div>
                            <div class="info-card rounded-lg p-4">
                                <p class="text-xs text-slate-500 mb-1">实缴资本</p>
                                <p class="font-semibold text-slate-800">{paid_in_capital if paid_in_capital else '未披露'}</p>
                            </div>
                            <div class="info-card rounded-lg p-4">
                                <p class="text-xs text-slate-500 mb-1">法定代表人</p>
                                <p class="font-semibold text-slate-800">{legal_representative if legal_representative else '未披露'}</p>
                            </div>
                            <div class="info-card rounded-lg p-4">
                                <p class="text-xs text-slate-500 mb-1">参保人数</p>
                                <p class="font-semibold text-slate-800">{f"{insured_count:,}人" if insured_count else '未披露'}</p>
                            </div>
                            <div class="info-card rounded-lg p-4">
                                <p class="text-xs text-slate-500 mb-1">企业类型</p>
                                <p class="font-semibold text-slate-800">{company_type if company_type else '未披露'}</p>
                            </div>
                            <div class="info-card rounded-lg p-4">
                                <p class="text-xs text-slate-500 mb-1">统一社会信用代码</p>
                                <p class="font-semibold text-slate-800 text-sm">{social_credit_code if social_credit_code else '未披露'}</p>
                            </div>
                        </div>
                    </div>
                    <div class="glass rounded-xl p-6">
                        <h3 class="font-semibold text-slate-800 mb-4">核心数据汇总</h3>
                        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            <div class="text-center p-4 bg-blue-50 rounded-xl">
                                <p class="text-2xl font-bold text-blue-700">{jobs_total:,}</p>
                                <p class="text-xs text-blue-600 mt-1">在招岗位</p>
                            </div>
                            <div class="text-center p-4 bg-red-50 rounded-xl">
                                <p class="text-2xl font-bold text-red-700">{len(risks)}</p>
                                <p class="text-xs text-red-600 mt-1">司法案件</p>
                            </div>
                            <div class="text-center p-4 bg-indigo-50 rounded-xl">
                                <p class="text-2xl font-bold text-indigo-700">{len(ip_list)}</p>
                                <p class="text-xs text-indigo-600 mt-1">知识产权</p>
                            </div>
                            <div class="text-center p-4 bg-purple-50 rounded-xl">
                                <p class="text-2xl font-bold text-purple-700">{len(investments)}</p>
                                <p class="text-xs text-purple-600 mt-1">对外投资</p>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="space-y-4">
                    <div class="glass rounded-xl p-6">
                        <h3 class="font-semibold text-slate-800 mb-4">经营范围</h3>
                        <div class="bg-slate-50 rounded-lg p-4 max-h-[400px] overflow-y-auto">
                            <p class="text-sm text-slate-600 leading-relaxed">{business_scope if business_scope else '暂无经营范围数据'}</p>
                        </div>
                    </div>
                    <div class="glass rounded-xl p-6">
                        <h3 class="font-semibold text-slate-800 mb-4">企业标签</h3>
                        <div class="flex flex-wrap gap-2">
                            <span class="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">{industry}</span>
                            <span class="px-3 py-1.5 bg-green-50 text-green-700 rounded-full text-xs font-medium">{status}</span>
                            <span class="px-3 py-1.5 bg-purple-50 text-purple-700 rounded-full text-xs font-medium">{scale}</span>
                            {f'<span class="px-3 py-1.5 bg-amber-50 text-amber-700 rounded-full text-xs font-medium">成立{company_age}</span>' if company_age else ''}
                            {f'<span class="px-3 py-1.5 bg-pink-50 text-pink-700 rounded-full text-xs font-medium">{company_type}</span>' if company_type else ''}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 数据分析 Tab -->
        <div id="panel-analysis" class="tab-panel hidden space-y-4">
            <!-- 企业健康度评分 -->
            <div class="glass rounded-xl p-6">
                <h3 class="font-semibold text-slate-800 mb-4"><i class="fas fa-heartbeat mr-2 text-red-500"></i>企业健康度评估</h3>
                <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    <!-- 总评分 -->
                    <div class="flex flex-col items-center justify-center">
                        <div class="score-ring mb-2">
                            <svg width="120" height="120" viewBox="0 0 120 120">
                                <circle cx="60" cy="60" r="54" fill="none" stroke="#e2e8f0" stroke-width="8"/>
                                <circle cx="60" cy="60" r="54" fill="none" stroke="{('#16a34a' if company_analysis['health_score'] >= 70 else '#2563eb' if company_analysis['health_score'] >= 50 else '#d97706' if company_analysis['health_score'] >= 30 else '#dc2626')}" stroke-width="8"
                                    stroke-dasharray="{company_analysis['health_score'] * 3.39} 339.292"
                                    stroke-linecap="round"/>
                            </svg>
                            <div class="score-text">
                                <p class="text-3xl font-bold text-slate-800">{company_analysis['health_score']}</p>
                                <p class="text-xs text-slate-500">{company_analysis['health_level']}</p>
                            </div>
                        </div>
                        <p class="text-sm text-slate-600 text-center">综合评分（满分100）</p>
                    </div>
                    <!-- 分项评分 -->
                    <div class="lg:col-span-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {''.join([
                            f'<div class="flex items-center gap-3 p-3 rounded-lg {"status-excellent" if d["status"] == "excellent" else "status-good" if d["status"] == "good" else "status-normal" if d["status"] == "normal" else "status-warning" if d["status"] == "warning" else "status-danger"}">'
                            f'<div class="flex-1">'
                            f'<p class="text-sm font-medium">{d["label"]}</p>'
                            f'<p class="text-xs opacity-80">{d["desc"]}</p></div>'
                            f'<p class="text-lg font-bold">{d["score"]}/{d["max"]}</p></div>'
                            for d in company_analysis['health_details']
                        ])}
                    </div>
                </div>
            </div>

            <!-- 招聘趋势预测 -->
            <div class="glass rounded-xl p-6">
                <h3 class="font-semibold text-slate-800 mb-4"><i class="fas fa-chart-line mr-2 text-blue-500"></i>招聘趋势预测</h3>
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div class="lg:col-span-2">
                        <div id="predictionChart" style="height: 300px;"></div>
                    </div>
                    <div class="space-y-3">
                        <div class="p-4 bg-blue-50 rounded-xl">
                            <p class="text-xs text-blue-600 mb-1">趋势判断</p>
                            <p class="text-lg font-bold text-blue-800">{company_analysis['recruit_trend']}</p>
                        </div>
                        <div class="p-4 bg-green-50 rounded-xl">
                            <p class="text-xs text-green-600 mb-1">预测建议</p>
                            <p class="text-sm text-green-800">{company_analysis['recruit_suggestion']}</p>
                        </div>
                        <div class="p-4 bg-slate-50 rounded-xl">
                            <p class="text-xs text-slate-500 mb-1">未来4周预测岗位数</p>
                            <div class="flex gap-2">
                                {''.join([f'<span class="px-2 py-1 bg-white rounded text-sm font-medium">{p}</span>' for p in company_analysis['recruit_prediction']])}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- 求职者友好度 -->
                <div class="glass rounded-xl p-6">
                    <h3 class="font-semibold text-slate-800 mb-4"><i class="fas fa-smile mr-2 text-green-500"></i>求职者友好度（{company_analysis['job_seeker_friendly']}/100）</h3>
                    <div class="space-y-3">
                        {''.join([
                            f'<div class="flex items-center gap-3">'
                            f'<div class="flex-1">'
                            f'<div class="flex items-center justify-between mb-1">'
                            f'<span class="text-sm text-slate-700">{d["label"]}</span>'
                            f'<span class="text-xs font-medium {"text-green-600" if d["status"] == "excellent" else "text-blue-600" if d["status"] == "good" else "text-amber-600"}">{d["score"]}/{d["max"]}</span></div>'
                            f'<div class="w-full bg-slate-100 rounded-full h-2">'
                            f'<div class="h-2 rounded-full {"bg-green-500" if d["status"] == "excellent" else "bg-blue-500" if d["status"] == "good" else "bg-amber-500"}" style="width: {(d["score"]/d["max"]*100) if d["max"] > 0 else 0}%"></div></div>'
                            f'<p class="text-xs text-slate-500 mt-1">{d["desc"]}</p></div></div>'
                            for d in company_analysis['friendly_details']
                        ])}
                    </div>
                </div>

                <!-- 薪资竞争力 -->
                <div class="glass rounded-xl p-6">
                    <h3 class="font-semibold text-slate-800 mb-4"><i class="fas fa-coins mr-2 text-amber-500"></i>薪资竞争力</h3>
                    <div class="flex items-center gap-4 mb-4">
                        <div class="w-16 h-16 bg-amber-50 rounded-full flex items-center justify-center">
                            <span class="text-xl font-bold text-amber-600">{company_analysis['salary_competitive']}</span>
                        </div>
                        <div>
                            <p class="text-sm text-slate-600">竞争力评级</p>
                            <p class="text-xs text-slate-400">基于岗位薪资分布分析</p>
                        </div>
                    </div>
                    <div class="space-y-2">
                        {''.join([f'<div class="flex items-center gap-2 text-sm text-slate-600"><i class="fas fa-check-circle text-green-500 text-xs"></i>{d}</div>' for d in company_analysis['salary_details']])}
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- 风险预警 -->
                <div class="glass rounded-xl p-6">
                    <h3 class="font-semibold text-slate-800 mb-4"><i class="fas fa-exclamation-triangle mr-2 text-red-500"></i>风险预警</h3>
                    <div class="flex items-center gap-4 mb-4">
                        <div class="w-16 h-16 {"bg-green-50" if company_analysis["risk_warning"] == "无风险" else "bg-red-50" if company_analysis["risk_warning"] == "高风险" else "bg-amber-50"} rounded-full flex items-center justify-center">
                            <span class="text-sm font-bold {"text-green-600" if company_analysis["risk_warning"] == "无风险" else "text-red-600" if company_analysis["risk_warning"] == "高风险" else "text-amber-600"}">{company_analysis['risk_warning']}</span>
                        </div>
                        <div>
                            <p class="text-sm text-slate-600">风险等级</p>
                            <p class="text-xs text-slate-400">基于司法风险数据分析</p>
                        </div>
                    </div>
                    <div class="space-y-2">
                        {''.join([f'<div class="flex items-center gap-2 text-sm text-slate-600"><i class="fas {"fa-check-circle text-green-500" if company_analysis["risk_warning"] == "无风险" else "fa-exclamation-circle text-red-500"} text-xs"></i>{d}</div>' for d in company_analysis['risk_details']])}
                    </div>
                </div>

                <!-- 城市扩张 -->
                <div class="glass rounded-xl p-6">
                    <h3 class="font-semibold text-slate-800 mb-4"><i class="fas fa-map-marked-alt mr-2 text-purple-500"></i>城市扩张分析</h3>
                    <div class="flex items-center gap-4 mb-4">
                        <div class="w-16 h-16 bg-purple-50 rounded-full flex items-center justify-center">
                            <span class="text-sm font-bold text-purple-600">{company_analysis['city_expansion']}</span>
                        </div>
                        <div>
                            <p class="text-sm text-slate-600">扩张阶段</p>
                            <p class="text-xs text-slate-400">基于招聘城市分布</p>
                        </div>
                    </div>
                    <div class="space-y-2">
                        {''.join([f'<div class="flex items-center gap-2 text-sm text-slate-600"><i class="fas fa-dot-circle text-purple-500 text-xs"></i>{d}</div>' for d in company_analysis['city_details']])}
                    </div>
                </div>
            </div>

            <!-- 岗位类型分布 -->
            <div class="glass rounded-xl p-6">
                <h3 class="font-semibold text-slate-800 mb-4"><i class="fas fa-sitemap mr-2 text-indigo-500"></i>岗位类型分布</h3>
                <div id="jobTypeChart" style="height: 300px;"></div>
            </div>

            <!-- 综合求职建议 -->
            <div class="glass rounded-xl p-6">
                <h3 class="font-semibold text-slate-800 mb-4"><i class="fas fa-lightbulb mr-2 text-amber-500"></i>综合求职建议</h3>
                <div class="p-4 bg-amber-50 border border-amber-100 rounded-xl mb-4">
                    <p class="text-sm text-amber-800 font-medium">{company_analysis['overall_suggestion']}</p>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {''.join([
                        f'<div class="flex items-start gap-2 p-3 bg-slate-50 rounded-lg">'
                        f'<i class="fas fa-check text-green-500 mt-0.5 text-xs"></i>'
                        f'<p class="text-sm text-slate-700">{s}</p></div>'
                        for s in company_analysis['suggestion_points']
                    ]) if company_analysis['suggestion_points'] else '<div class="text-center py-4 text-slate-400">暂无建议数据</div>'}
                </div>
            </div>
        </div>

        <!-- 司法风险 Tab -->
        <div id="panel-risk" class="tab-panel hidden space-y-4">
            <div class="glass rounded-xl p-6">
                <h3 class="font-semibold text-slate-800 mb-4">司法风险 ({len(risks)} 条)</h3>
                {''.join([
                    f'<div class="glass rounded-xl p-4 mb-3 {"risk-high" if r.get("type") == "高风险" else "risk-medium" if r.get("type") == "中风险" else "risk-low"}">'
                    f'<div class="flex items-start justify-between"><div><h4 class="font-medium text-slate-800">{r.get("title", "未知")}</h4>'
                    f'<p class="text-xs text-slate-500 mt-1">{r.get("date", "")}</p></div>'
                    f'<span class="px-2 py-1 rounded text-xs font-medium {"bg-red-100 text-red-700" if r.get("type") == "高风险" else "bg-amber-100 text-amber-700" if r.get("type") == "中风险" else "bg-green-100 text-green-700"}">{r.get("type", "低风险")}</span></div>'
                    f'<p class="text-sm text-slate-600 mt-2">{r.get("status", "")}</p></div>'
                    for r in risks
                ]) if risks else '<div class="text-center py-8 text-slate-400">暂无司法风险数据</div>'}
            </div>
        </div>

        <!-- 融资历史 Tab -->
        <div id="panel-funding" class="tab-panel hidden space-y-4">
            <div class="glass rounded-xl p-6">
                <h3 class="font-semibold text-slate-800 mb-4">融资历史 ({len(funding)} 轮)</h3>
                <div class="space-y-3">
                    {''.join([
                        f'<div class="glass rounded-xl p-4 flex items-center justify-between">'
                        f'<div><span class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">{f.get("round", "未知轮次")}</span>'
                        f'<p class="font-medium text-slate-800 mt-1">{f.get("amount", "金额未披露")}</p>'
                        f'<p class="text-xs text-slate-500">{f.get("date", "")}</p></div>'
                        f'<div class="text-right"><p class="text-sm text-slate-600">投资方</p>'
                        f'<p class="text-xs text-slate-500">{f.get("investor", "未披露")}</p></div></div>'
                        for f in funding
                    ]) if funding else '<div class="text-center py-8 text-slate-400">暂无融资数据</div>'}
                </div>
            </div>
        </div>

        <!-- 股东结构 Tab -->
        <div id="panel-shareholders" class="tab-panel hidden space-y-4">
            <div class="glass rounded-xl p-6">
                <h3 class="font-semibold text-slate-800 mb-4">股东结构 ({len(shareholders)} 位)</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {''.join([
                        f'<div class="glass rounded-xl p-4">'
                        f'<div class="flex items-center justify-between"><h4 class="font-medium text-slate-800">{s.get("name", "未知")}</h4>'
                        f'<span class="text-lg font-bold text-blue-600">{s.get("ratio", "")}</span></div>'
                        f'<p class="text-xs text-slate-500 mt-1">认缴金额：{s.get("amount", "未披露")}</p></div>'
                        for s in shareholders
                    ]) if shareholders else '<div class="text-center py-8 text-slate-400">暂无股东数据</div>'}
                </div>
            </div>
        </div>

        <!-- 知识产权 Tab -->
        <div id="panel-ip" class="tab-panel hidden space-y-4">
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="card glass rounded-xl p-5 text-center">
                    <div class="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center mx-auto mb-2"><i class="fas fa-certificate text-blue-500"></i></div>
                    <p class="text-2xl font-bold text-slate-800">{len(ip_patents)}</p>
                    <p class="text-xs text-slate-500">专利</p>
                </div>
                <div class="card glass rounded-xl p-5 text-center">
                    <div class="w-10 h-10 bg-amber-50 rounded-lg flex items-center justify-center mx-auto mb-2"><i class="fas fa-trademark text-amber-500"></i></div>
                    <p class="text-2xl font-bold text-slate-800">{len(ip_trademarks)}</p>
                    <p class="text-xs text-slate-500">商标</p>
                </div>
                <div class="card glass rounded-xl p-5 text-center">
                    <div class="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center mx-auto mb-2"><i class="fas fa-copyright text-green-500"></i></div>
                    <p class="text-2xl font-bold text-slate-800">{len(ip_copyrights)}</p>
                    <p class="text-xs text-slate-500">软件著作权</p>
                </div>
                <div class="card glass rounded-xl p-5 text-center">
                    <div class="w-10 h-10 bg-indigo-50 rounded-lg flex items-center justify-center mx-auto mb-2"><i class="fas fa-lightbulb text-indigo-500"></i></div>
                    <p class="text-2xl font-bold text-slate-800">{len(ip_list)}</p>
                    <p class="text-xs text-slate-500">知识产权总数</p>
                </div>
            </div>
            <div class="glass rounded-xl p-6">
                <h3 class="font-semibold text-slate-800 mb-4">知识产权明细 ({len(ip_list)} 条)</h3>
                <div class="space-y-3 max-h-[600px] overflow-y-auto pr-1">
                    {''.join([
                        f'<div class="glass rounded-xl p-4 {"ip-patent" if ip.get("type") == "专利" else "ip-trademark" if ip.get("type") == "商标" else "ip-copyright"}">'
                        f'<div class="flex items-start justify-between">'
                        f'<div class="flex-1">'
                        f'<div class="flex items-center gap-2 mb-1">'
                        f'<span class="px-2 py-0.5 {"bg-blue-100 text-blue-700" if ip.get("type") == "专利" else "bg-amber-100 text-amber-700" if ip.get("type") == "商标" else "bg-green-100 text-green-700"} rounded text-xs font-medium">{ip.get("type", "其他")}</span>'
                        f'<h4 class="font-medium text-slate-800">{ip.get("name", "未知")}</h4></div>'
                        f'<div class="flex flex-wrap items-center gap-3 text-xs text-slate-500 mt-1">'
                        f'<span><i class="fas fa-calendar mr-1"></i>{ip.get("date", "日期未知")}</span>'
                        f'<span><i class="fas fa-tag mr-1"></i>{ip.get("category", "分类未知")}</span>'
                        f'<span><i class="fas fa-check-circle mr-1"></i>{ip.get("status", "状态未知")}</span></div></div></div></div>'
                        for ip in ip_list
                    ]) if ip_list else '<div class="text-center py-8 text-slate-400">暂无知识产权数据</div>'}
                </div>
            </div>
        </div>

        <!-- 对外投资 Tab -->
        <div id="panel-investments" class="tab-panel hidden space-y-4">
            <div class="grid grid-cols-2 lg:grid-cols-3 gap-4">
                <div class="card glass rounded-xl p-5">
                    <div class="flex items-center justify-between mb-3">
                        <span class="text-sm text-slate-500">投资企业数</span>
                        <div class="w-8 h-8 bg-purple-50 rounded-lg flex items-center justify-center"><i class="fas fa-building text-purple-500 text-sm"></i></div>
                    </div>
                    <p class="text-2xl font-bold text-slate-800">{len(investments)}</p>
                    <p class="text-xs text-slate-400 mt-1">对外投资企业</p>
                </div>
                <div class="card glass rounded-xl p-5">
                    <div class="flex items-center justify-between mb-3">
                        <span class="text-sm text-slate-500">控股企业</span>
                        <div class="w-8 h-8 bg-red-50 rounded-lg flex items-center justify-center"><i class="fas fa-hand-holding-heart text-red-500 text-sm"></i></div>
                    </div>
                    <p class="text-2xl font-bold text-slate-800">{len([i for i in investments if i.get("ratio", "").replace("%", "").isdigit() and float(i.get("ratio", "0").replace("%", "")) > 50])}</p>
                    <p class="text-xs text-slate-400 mt-1">持股比例>50%</p>
                </div>
                <div class="card glass rounded-xl p-5">
                    <div class="flex items-center justify-between mb-3">
                        <span class="text-sm text-slate-500">参股企业</span>
                        <div class="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center"><i class="fas fa-handshake text-blue-500 text-sm"></i></div>
                    </div>
                    <p class="text-2xl font-bold text-slate-800">{len([i for i in investments if i.get("ratio", "").replace("%", "").isdigit() and float(i.get("ratio", "0").replace("%", "")) <= 50])}</p>
                    <p class="text-xs text-slate-400 mt-1">持股比例≤50%</p>
                </div>
            </div>
            <div class="glass rounded-xl p-6">
                <h3 class="font-semibold text-slate-800 mb-4">对外投资明细 ({len(investments)} 条)</h3>
                <div class="space-y-3 max-h-[600px] overflow-y-auto pr-1">
                    {''.join([
                        f'<div class="glass rounded-xl p-4 investment-card">'
                        f'<div class="flex items-start justify-between">'
                        f'<div class="flex-1">'
                        f'<div class="flex items-center gap-2 mb-1">'
                        f'<h4 class="font-medium text-slate-800">{inv.get("company", "未知企业")}</h4>'
                        f'<span class="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">{inv.get("industry", "未知行业")}</span></div>'
                        f'<div class="flex flex-wrap items-center gap-3 text-xs text-slate-500 mt-1">'
                        f'<span><i class="fas fa-coins mr-1"></i>投资金额：{inv.get("amount", "未披露")}</span>'
                        f'<span><i class="fas fa-percentage mr-1"></i>持股比例：{inv.get("ratio", "未披露")}</span>'
                        f'<span><i class="fas fa-calendar mr-1"></i>{inv.get("date", "日期未知")}</span>'
                        f'<span><i class="fas fa-info-circle mr-1"></i>{inv.get("status", "状态未知")}</span></div></div></div></div>'
                        for inv in investments
                    ]) if investments else '<div class="text-center py-8 text-slate-400">暂无对外投资数据</div>'}
                </div>
            </div>
        </div>

        <!-- 主要人员 Tab -->
        <div id="panel-staff" class="tab-panel hidden space-y-4">
            <div class="glass rounded-xl p-6">
                <h3 class="font-semibold text-slate-800 mb-4">主要人员 ({len(staff)} 位)</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {''.join([
                        f'<div class="glass rounded-xl p-4 flex items-center gap-3">'
                        f'<div class="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center"><i class="fas fa-user text-slate-500"></i></div>'
                        f'<div><p class="font-medium text-sm text-slate-700">{s.get("name", "未知")}</p>'
                        f'<p class="text-xs text-slate-500">{s.get("position", "")} · {s.get("education", "")}</p></div></div>'
                        for s in staff
                    ]) if staff else '<div class="text-center py-8 text-slate-400">暂无人员数据</div>'}
                </div>
            </div>
        </div>

        <!-- 页脚 -->
        <div class="glass rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-sm">
            <div class="flex items-center gap-2">
                <i class="fas fa-database text-blue-500"></i>
                <span class="text-slate-600">数据来源：<span class="font-semibold">天眼查企业数据库</span></span>
            </div>
            <div class="flex items-center gap-4 text-xs text-slate-400">
                <span>查询时间：{query_time}</span>
                <span>数据仅供参考，以官方公示为准</span>
            </div>
        </div>
    </main>

    <script>
        // ==================== Job Data & Analysis ====================
        const RECENT_ANALYSIS = {recent_analysis_json};
        const COMPANY_ANALYSIS = {company_analysis_json};
        
        let analysisCharts = {{}};
        
        // ==================== Analysis Tab Charts ====================
        function renderAnalysisCharts() {{
            // 招聘趋势预测图
            if (analysisCharts.prediction) analysisCharts.prediction.dispose();
            const ca = COMPANY_ANALYSIS;
            if (ca.recruit_prediction && ca.recruit_prediction.length > 0) {{
                const recentAnalysis = RECENT_ANALYSIS;
                const trendData = recentAnalysis.date_trend;
                const historical = trendData.values;
                const labels = trendData.categories;
                
                // 生成预测标签
                const lastDate = labels[labels.length - 1];
                const predLabels = ['+1周', '+2周', '+3周', '+4周'];
                const allLabels = [...labels, ...predLabels];
                const allValues = [...historical, ...ca.recruit_prediction];
                
                // 标记预测部分
                const historicalData = historical.map(v => v);
                const predictionData = [...Array(historical.length).fill(null), ...ca.recruit_prediction];
                
                analysisCharts.prediction = echarts.init(document.getElementById('predictionChart'));
                analysisCharts.prediction.setOption({{
                    tooltip: {{ trigger: 'axis' }},
                    legend: {{ data: ['历史数据', '预测数据'], top: 5 }},
                    grid: {{ left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true }},
                    xAxis: {{ type: 'category', data: allLabels, axisLabel: {{ fontSize: 10, rotate: 30 }} }},
                    yAxis: {{ type: 'value', axisLabel: {{ fontSize: 11 }}, minInterval: 1 }},
                    series: [
                        {{
                            name: '历史数据',
                            type: 'line',
                            data: historicalData,
                            smooth: true,
                            symbol: 'circle',
                            symbolSize: 5,
                            lineStyle: {{ color: '#3b82f6', width: 2 }},
                            itemStyle: {{ color: '#3b82f6' }},
                            areaStyle: {{ color: {{ type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
                                {{ offset: 0, color: 'rgba(59,130,246,0.2)' }},
                                {{ offset: 1, color: 'rgba(59,130,246,0.02)' }}
                            ]}} }}
                        }},
                        {{
                            name: '预测数据',
                            type: 'line',
                            data: predictionData,
                            smooth: true,
                            symbol: 'diamond',
                            symbolSize: 6,
                            lineStyle: {{ color: '#10b981', width: 2, type: 'dashed' }},
                            itemStyle: {{ color: '#10b981' }},
                            label: {{ show: true, fontSize: 10 }}
                        }}
                    ]
                }});
            }} else {{
                document.getElementById('predictionChart').innerHTML = '<div class="flex items-center justify-center h-full text-slate-400 text-sm">数据不足，无法生成预测</div>';
            }}
            
            // 岗位类型分布图
            if (analysisCharts.jobType) analysisCharts.jobType.dispose();
            const recentAnalysis = RECENT_ANALYSIS;
            if (recentAnalysis.job_types && recentAnalysis.job_types.categories.length > 0) {{
                analysisCharts.jobType = echarts.init(document.getElementById('jobTypeChart'));
                analysisCharts.jobType.setOption({{
                    tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
                    grid: {{ left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true }},
                    xAxis: {{ type: 'category', data: recentAnalysis.job_types.categories, axisLabel: {{ fontSize: 12 }} }},
                    yAxis: {{ type: 'value', axisLabel: {{ fontSize: 11 }} }},
                    series: [{{
                        type: 'bar',
                        data: recentAnalysis.job_types.values,
                        itemStyle: {{ borderRadius: [4, 4, 0, 0], color: {{ type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
                            {{ offset: 0, color: '#6366f1' }},
                            {{ offset: 1, color: '#818cf8' }}
                        ]}} }},
                        label: {{ show: true, position: 'top', fontSize: 11 }}
                    }}]
                }});
            }} else {{
                document.getElementById('jobTypeChart').innerHTML = '<div class="flex items-center justify-center h-full text-slate-400 text-sm">暂无岗位类型数据</div>';
            }}
        }}

        // ==================== Tab Switching ====================
        function switchTab(tab) {{
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.classList.remove('tab-active');
                btn.classList.add('text-slate-500');
            }});
            document.getElementById('tab-' + tab).classList.add('tab-active');
            document.getElementById('tab-' + tab).classList.remove('text-slate-500');
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
            document.getElementById('panel-' + tab).classList.remove('hidden');
            
            if (tab === 'analysis') {{
                setTimeout(() => renderAnalysisCharts(), 50);
            }}
            
            setTimeout(() => {{
                Object.values(analysisCharts).forEach(c => c && c.resize());
            }}, 50);
        }}

        window.addEventListener('resize', () => {{
            Object.values(analysisCharts).forEach(c => c && c.resize());
        }});
        
        document.addEventListener('DOMContentLoaded', () => {{
            const totalRecent = RECENT_JOBS.length;
            document.getElementById('jobsCountLabel').textContent = `(本季度 ${{totalRecent}} 个)`;
        }});
    </script>
</body>
</html>'''
    
    safe_name = name.replace('/', '_').replace('\\', '_').replace(' ', '_')
    filename = f"企业洞察看板_{safe_name}.html"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return filepath


if __name__ == '__main__':
    from datetime import datetime, timedelta
    
    demo_data = {
        'name': '示例科技有限公司',
        'status': '存续',
        'industry': '软件和信息技术服务业',
        'scale': '大型企业',
        'address': '北京市海淀区',
        'tianyancha_url': 'https://www.tianyancha.com',
        
        'established_date': '2015-06-18',
        'registered_capital': '5000万元',
        'paid_in_capital': '3000万元',
        'legal_representative': '张三',
        'social_credit_code': '91110108MA0012345X',
        'company_type': '有限责任公司',
        'insured_count': 328,
        'business_scope': '技术开发、技术咨询、技术服务、技术转让；计算机系统服务；基础软件服务；应用软件服务；软件开发；软件咨询；产品设计；模型设计；包装装潢设计；教育咨询（中介服务除外）；经济贸易咨询；文化咨询；体育咨询；公共关系服务；会议服务；工艺美术设计；电脑动画设计；企业策划、设计；设计、制作、代理、发布国内广告；市场调查；企业管理咨询；组织文化艺术交流活动（不含营业性演出）；文艺创作；承办展览展示活动；影视策划；翻译服务；自然科学研究与试验发展；工程和技术研究与试验发展；农业科学研究与试验发展；医学研究与试验发展；数据处理（数据处理中的银行卡中心、PUE值在1.5以上的云计算数据中心除外）。',
        
        'jobs_total': 150,
        'jobs': [
            {'title': 'Java开发工程师', 'salary': '20K-35K', 'city': '北京', 'education': '本科', 'experience': '3-5年', 'source': 'BOSS直聘', 'date': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'), 'url': 'https://www.zhipin.com'},
            {'title': 'Java开发工程师-中间件', 'salary': '25K-40K', 'city': '北京', 'education': '本科', 'experience': '3-5年', 'source': 'BOSS直聘', 'date': (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d'), 'url': 'https://www.zhipin.com'},
            {'title': '产品经理', 'salary': '25K-40K', 'city': '北京', 'education': '本科', 'experience': '3-5年', 'source': '拉勾网', 'date': (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'), 'url': 'https://www.lagou.com'},
            {'title': '算法工程师', 'salary': '30K-50K', 'city': '上海', 'education': '硕士', 'experience': '3-5年', 'source': 'BOSS直聘', 'date': (datetime.now() - timedelta(days=25)).strftime('%Y-%m-%d'), 'url': 'https://www.zhipin.com'},
            {'title': '前端开发工程师', 'salary': '18K-30K', 'city': '深圳', 'education': '本科', 'experience': '1-3年', 'source': '拉勾网', 'date': (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d'), 'url': 'https://www.lagou.com'},
            {'title': '测试工程师', 'salary': '15K-25K', 'city': '北京', 'education': '本科', 'experience': '1-3年', 'source': '智联招聘', 'date': (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d'), 'url': 'https://www.zhaopin.com'},
            {'title': '运维工程师', 'salary': '15K-25K', 'city': '杭州', 'education': '本科', 'experience': '1-3年', 'source': 'BOSS直聘', 'date': (datetime.now() - timedelta(days=50)).strftime('%Y-%m-%d'), 'url': 'https://www.zhipin.com'},
            {'title': '数据分析师', 'salary': '18K-30K', 'city': '北京', 'education': '本科', 'experience': '1-3年', 'source': '猎聘网', 'date': (datetime.now() - timedelta(days=55)).strftime('%Y-%m-%d'), 'url': 'https://www.liepin.com'},
            {'title': 'UI设计师', 'salary': '15K-25K', 'city': '上海', 'education': '本科', 'experience': '1-3年', 'source': 'BOSS直聘', 'date': (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'), 'url': 'https://www.zhipin.com'},
            {'title': '运营专员', 'salary': '10K-18K', 'city': '广州', 'education': '大专', 'experience': '不限', 'source': '智联招聘', 'date': (datetime.now() - timedelta(days=70)).strftime('%Y-%m-%d'), 'url': 'https://www.zhaopin.com'},
            {'title': '销售经理', 'salary': '12K-20K', 'city': '成都', 'education': '大专', 'experience': '不限', 'source': 'BOSS直聘', 'date': (datetime.now() - timedelta(days=80)).strftime('%Y-%m-%d'), 'url': 'https://www.zhipin.com'},
            {'title': 'HRBP', 'salary': '15K-25K', 'city': '北京', 'education': '本科', 'experience': '3-5年', 'source': '猎聘网', 'date': (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d'), 'url': 'https://www.liepin.com'},
        ],
        'risk': [
            {'title': '合同纠纷', 'date': '2025-01-15', 'type': '中风险', 'status': '已结案'},
            {'title': '劳动争议', 'date': '2024-11-20', 'type': '低风险', 'status': '已调解'},
        ],
        'funding': [
            {'round': 'A轮', 'amount': '1亿元', 'date': '2020-03-15', 'investor': '红杉资本'},
            {'round': 'B轮', 'amount': '3亿元', 'date': '2021-09-10', 'investor': '高瓴资本'},
        ],
        'shareholders': [
            {'name': '张三', 'ratio': '60%', 'amount': '3000万'},
            {'name': '李四', 'ratio': '30%', 'amount': '1500万'},
            {'name': '王五', 'ratio': '10%', 'amount': '500万'},
        ],
        'intellectual_property': [
            {'type': '专利', 'name': '一种分布式数据处理方法', 'date': '2023-05-12', 'status': '授权', 'category': '发明专利'},
            {'type': '商标', 'name': '示例科技', 'date': '2020-03-20', 'status': '注册', 'category': '第9类'},
            {'type': '软件著作权', 'name': '示例数据分析平台V1.0', 'date': '2022-01-10', 'status': '登记', 'category': '软件'},
        ],
        'investments': [
            {'company': '子公司A科技有限公司', 'amount': '1000万元', 'ratio': '100%', 'status': '存续', 'date': '2018-05-20', 'industry': '软件开发'},
            {'company': '参股B网络科技', 'amount': '500万元', 'ratio': '30%', 'status': '存续', 'date': '2019-11-10', 'industry': '互联网'},
        ],
        'staff': [
            {'name': '张三', 'position': '执行董事兼总经理', 'education': '硕士'},
            {'name': '李四', 'position': '财务负责人', 'education': '本科'},
            {'name': '王五', 'position': '监事', 'education': '本科'},
        ],
    }
    
    output = generate_dashboard(demo_data, '.')
    print(f"看板已生成: {output}")


def generate_industry_dashboard(industry_data: dict, output_dir: str) -> str:
    """
    生成行业头部企业洞察看板 HTML 文件
    
    industry_data 字段:
    - industry_name: 行业名称
    - industry_desc: 行业简介（可选）
    - companies: 头部企业列表，每项包含:
        - name: 企业名称
        - jobs_total: 在招岗位总数
        - established_date: 成立时间 (YYYY-MM-DD)
        - registered_capital: 注册资本
        - status: 经营状态
        - scale: 企业规模
        - funding_rounds: 融资轮次数 (int)
        - tianyancha_url: 天眼查详情页链接
        - key_products: 核心产品/业务 (string)
        - employees: 员工规模/参保人数 (int)
        - city: 总部城市
        - industry_segment: 细分赛道
    """
    
    industry_name = industry_data.get('industry_name', '未知行业')
    industry_desc = industry_data.get('industry_desc', '')
    companies = industry_data.get('companies', [])
    
    query_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 数据预处理
    for c in companies:
        # 计算成立年限
        est_date = c.get('established_date', '')
        c['_age'] = ''
        if est_date:
            try:
                est_year = int(est_date.split('-')[0])
                c['_age'] = f"{datetime.now().year - est_year}年"
            except:
                pass
        # 确保数值字段
        c['_employees'] = c.get('employees', 0) or 0
        c['_jobs'] = c.get('jobs_total', 0) or 0
        c['_funding'] = c.get('funding_rounds', 0) or 0
    
    # 排序：按在招岗位数降序
    companies.sort(key=lambda x: x['_jobs'], reverse=True)
    
    # 序列化图表数据
    # 在招岗位对比
    jobs_chart_data = json.dumps([
        {'name': c['name'], 'value': c['_jobs']} 
        for c in companies[:10]
    ], ensure_ascii=False)
    
    # 成立时间分布（按年份）
    year_counter = Counter()
    for c in companies:
        est = c.get('established_date', '')
        if est:
            try:
                year = int(est.split('-')[0])
                year_counter[year] += 1
            except:
                pass
    year_dist = [{'year': str(y), 'count': c} for y, c in sorted(year_counter.items())]
    year_chart_data = json.dumps(year_dist, ensure_ascii=False)
    
    # 融资活跃度对比
    funding_chart_data = json.dumps([
        {'name': c['name'], 'value': c['_funding']}
        for c in companies[:10]
    ], ensure_ascii=False)
    
    # 企业规模分布
    scale_counter = Counter()
    for c in companies:
        scale = c.get('scale', '未知')
        if scale:
            scale_counter[scale] += 1
    scale_dist = [{'name': k, 'value': v} for k, v in scale_counter.most_common()]
    scale_chart_data = json.dumps(scale_dist, ensure_ascii=False)
    
    # 城市分布
    city_counter = Counter()
    for c in companies:
        city = c.get('city', '未知')
        if city:
            city_counter[city] += 1
    city_dist = [{'name': k, 'value': v} for k, v in city_counter.most_common()]
    city_chart_data = json.dumps(city_dist, ensure_ascii=False)
    
    # 统计汇总
    total_jobs = sum(c['_jobs'] for c in companies)
    total_employees = sum(c['_employees'] for c in companies)
    total_funding_rounds = sum(c['_funding'] for c in companies)
    avg_age = sum((datetime.now().year - int(c['established_date'].split('-')[0])) for c in companies if c.get('established_date')) / len([c for c in companies if c.get('established_date')]) if any(c.get('established_date') for c in companies) else 0
    
    # 企业卡片 HTML
    company_cards = []
    for c in companies:
        # 生成企业看板文件名
        safe_name = c.get('name', '未知').replace('/', '_').replace('\\', '_').replace(' ', '_').replace('（', '_').replace('）', '_')
        dashboard_filename = f"企业洞察看板_{safe_name}.html"
        dashboard_url = f"./{dashboard_filename}"
        
        card = f'''
        <div class="glass rounded-xl p-5 card hover:border-blue-300 relative">
            <a href="{dashboard_url}" class="absolute inset-0 z-0" title="点击查看企业洞察看板"></a>
            <div class="relative z-10">
                <div class="flex items-start justify-between mb-3">
                    <div>
                        <h4 class="font-semibold text-slate-800 text-lg">{c.get('name', '未知')}</h4>
                        <p class="text-xs text-slate-500 mt-1">{c.get('industry_segment', '')}</p>
                    </div>
                    <span class="px-2.5 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">{c.get('status', '存续')}</span>
                </div>
                <div class="grid grid-cols-2 gap-3 mb-3">
                    <div class="bg-slate-50 rounded-lg p-2.5 text-center">
                        <p class="text-xl font-bold text-blue-600">{c['_jobs']:,}</p>
                        <p class="text-xs text-slate-500">在招岗位</p>
                    </div>
                    <div class="bg-slate-50 rounded-lg p-2.5 text-center">
                        <p class="text-xl font-bold text-purple-600">{c['_funding']}</p>
                        <p class="text-xs text-slate-500">融资轮次</p>
                    </div>
                    <div class="bg-slate-50 rounded-lg p-2.5 text-center">
                        <p class="text-xl font-bold text-amber-600">{c['_employees']:,}</p>
                        <p class="text-xs text-slate-500">参保人数</p>
                    </div>
                    <div class="bg-slate-50 rounded-lg p-2.5 text-center">
                        <p class="text-xl font-bold text-slate-700">{c.get('established_date', '')[:4] if c.get('established_date') else '-'}</p>
                        <p class="text-xs text-slate-500">成立年份</p>
                    </div>
                </div>
                <div class="space-y-1.5 text-xs text-slate-600 mb-3">
                    <div class="flex items-center gap-1.5"><i class="fas fa-map-marker-alt text-slate-400 w-3"></i>{c.get('city', '未知')}</div>
                    <div class="flex items-center gap-1.5"><i class="fas fa-coins text-slate-400 w-3"></i>注册资本：{c.get('registered_capital', '未披露')}</div>
                    <div class="flex items-center gap-1.5"><i class="fas fa-briefcase text-slate-400 w-3"></i>规模：{c.get('scale', '未知')}</div>
                    <div class="flex items-center gap-1.5"><i class="fas fa-rocket text-slate-400 w-3"></i>{c.get('key_products', '')}</div>
                </div>
                <div class="flex gap-2">
                    <a href="{dashboard_url}" class="flex-1 text-center px-3 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-sm font-medium transition-colors relative z-10"><i class="fas fa-chart-bar mr-1"></i>企业洞察看板</a>
                    {f'<a href="{c.get("tianyancha_url", "")}" target="_blank" class="flex-1 text-center px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition-colors relative z-10"><i class="fas fa-external-link-alt mr-1"></i>天眼查详情</a>' if c.get('tianyancha_url') else ''}
                </div>
            </div>
        </div>
        '''
        company_cards.append(card)
    
    cards_html = '\n'.join(company_cards)
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>行业洞察看板 · {industry_name}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        * {{ font-family: 'Inter', -apple-system, sans-serif; }}
        .glass {{ background: rgba(255,255,255,0.95); backdrop-filter: blur(12px); border: 1px solid rgba(226,232,240,0.8); }}
        .card {{ transition: all 0.3s ease; border: 1px solid transparent; }}
        .card:hover {{ transform: translateY(-3px); box-shadow: 0 12px 40px -12px rgba(0,0,0,0.12); border-color: rgba(59,130,246,0.2); }}
        .animate-in {{ animation: fadeIn 0.5s ease-out; }}
        @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(10px); }} to {{ opacity:1; transform:translateY(0); }} }}
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 3px; }}
        .chart-container {{ min-height: 300px; }}
    </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen">
    <header class="bg-slate-900 text-white sticky top-0 z-50 shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center gap-3">
                    <div class="w-9 h-9 bg-amber-400 rounded-lg flex items-center justify-center">
                        <i class="fas fa-industry text-slate-900 text-lg"></i>
                    </div>
                    <div>
                        <h1 class="text-lg font-bold">行业洞察看板</h1>
                        <p class="text-xs text-slate-400">数据来源：天眼查企业数据库 · 实时查询</p>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    <span class="text-xs bg-green-900 text-green-300 px-3 py-1 rounded-full">
                        <i class="fas fa-check-circle mr-1"></i>真实数据
                    </span>
                    <span class="text-xs text-slate-400">查询时间：{query_time}</span>
                </div>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        <!-- 行业概览 -->
        <div class="glass rounded-2xl p-6 animate-in">
            <div class="flex items-start gap-4">
                <div class="w-16 h-16 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
                    <i class="fas fa-industry text-2xl text-blue-600"></i>
                </div>
                <div class="flex-1">
                    <h2 class="text-2xl font-bold text-slate-800">{industry_name}</h2>
                    {f'<p class="text-sm text-slate-500 mt-1">{industry_desc}</p>' if industry_desc else ''}
                    <div class="flex flex-wrap items-center gap-3 mt-3">
                        <span class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                            <i class="fas fa-building mr-1"></i>头部企业 {len(companies)} 家
                        </span>
                        <span class="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                            <i class="fas fa-briefcase mr-1"></i>在招岗位 {total_jobs:,} 个
                        </span>
                        <span class="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                            <i class="fas fa-users mr-1"></i>参保人数 {total_employees:,} 人
                        </span>
                        <span class="px-3 py-1 bg-amber-100 text-amber-700 rounded-full text-xs font-medium">
                            <i class="fas fa-chart-line mr-1"></i>融资轮次 {total_funding_rounds} 轮
                        </span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 头部企业卡片 -->
        <div class="glass rounded-xl p-6">
            <h3 class="font-semibold text-slate-800 mb-4"><i class="fas fa-crown mr-2 text-amber-500"></i>头部企业概览</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {cards_html}
            </div>
        </div>

        <!-- 数据分析图表 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 在招岗位对比 -->
            <div class="glass rounded-xl p-4">
                <h3 class="font-semibold text-slate-800 text-sm mb-3"><i class="fas fa-briefcase mr-1.5 text-blue-500"></i>在招岗位对比（TOP10）</h3>
                <div id="jobsChart" class="chart-container" style="height: 320px;"></div>
            </div>
            <!-- 融资活跃度 -->
            <div class="glass rounded-xl p-4">
                <h3 class="font-semibold text-slate-800 text-sm mb-3"><i class="fas fa-coins mr-1.5 text-amber-500"></i>融资轮次对比（TOP10）</h3>
                <div id="fundingChart" class="chart-container" style="height: 320px;"></div>
            </div>
            <!-- 成立时间分布 -->
            <div class="glass rounded-xl p-4">
                <h3 class="font-semibold text-slate-800 text-sm mb-3"><i class="fas fa-calendar-alt mr-1.5 text-green-500"></i>成立时间分布</h3>
                <div id="yearChart" class="chart-container" style="height: 320px;"></div>
            </div>
            <!-- 企业规模分布 -->
            <div class="glass rounded-xl p-4">
                <h3 class="font-semibold text-slate-800 text-sm mb-3"><i class="fas fa-chart-pie mr-1.5 text-purple-500"></i>企业规模分布</h3>
                <div id="scaleChart" class="chart-container" style="height: 320px;"></div>
            </div>
            <!-- 总部城市分布 -->
            <div class="glass rounded-xl p-4 lg:col-span-2">
                <h3 class="font-semibold text-slate-800 text-sm mb-3"><i class="fas fa-map-marker-alt mr-1.5 text-red-500"></i>总部城市分布</h3>
                <div id="cityChart" class="chart-container" style="height: 320px;"></div>
            </div>
        </div>

        <!-- 免责声明 -->
        <div class="glass rounded-xl p-4 flex items-center gap-3 text-sm">
            <i class="fas fa-exclamation-circle text-amber-500"></i>
            <span class="text-slate-600">数据仅供参考，以天眼查官方公示为准。企业排名基于公开数据，不构成投资建议。</span>
        </div>

        <!-- 页脚 -->
        <div class="glass rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-sm">
            <div class="flex items-center gap-2">
                <i class="fas fa-database text-blue-500"></i>
                <span class="text-slate-600">数据来源：<span class="font-semibold">天眼查企业数据库</span></span>
            </div>
            <div class="flex items-center gap-4 text-xs text-slate-400">
                <span>查询时间：{query_time}</span>
                <span>数据仅供参考，以官方公示为准</span>
            </div>
        </div>
    </main>

    <script>
        // 图表数据
        const jobsData = {jobs_chart_data};
        const fundingData = {funding_chart_data};
        const yearData = {year_chart_data};
        const scaleData = {scale_chart_data};
        const cityData = {city_chart_data};
        
        let charts = {{}};
        
        function initCharts() {{
            // 在招岗位对比 - 横向柱状图
            if (jobsData.length > 0) {{
                charts.jobs = echarts.init(document.getElementById('jobsChart'));
                const jobsSorted = [...jobsData].sort((a, b) => a.value - b.value);
                charts.jobs.setOption({{
                    tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
                    grid: {{ left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true }},
                    xAxis: {{ type: 'value', axisLabel: {{ fontSize: 11 }} }},
                    yAxis: {{ type: 'category', data: jobsSorted.map(d => d.name), axisLabel: {{ fontSize: 11 }} }},
                    series: [{{
                        type: 'bar', data: jobsSorted.map(d => d.value),
                        itemStyle: {{ borderRadius: [0, 4, 4, 0], color: '#3b82f6' }},
                        label: {{ show: true, position: 'right', fontSize: 11 }}
                    }}]
                }});
            }} else {{
                document.getElementById('jobsChart').innerHTML = '<div class="flex items-center justify-center h-full text-slate-400 text-sm">暂无数据</div>';
            }}
            
            // 融资轮次对比 - 横向柱状图
            if (fundingData.length > 0) {{
                charts.funding = echarts.init(document.getElementById('fundingChart'));
                const fundingSorted = [...fundingData].sort((a, b) => a.value - b.value);
                charts.funding.setOption({{
                    tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'shadow' }} }},
                    grid: {{ left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true }},
                    xAxis: {{ type: 'value', axisLabel: {{ fontSize: 11 }}, minInterval: 1 }},
                    yAxis: {{ type: 'category', data: fundingSorted.map(d => d.name), axisLabel: {{ fontSize: 11 }} }},
                    series: [{{
                        type: 'bar', data: fundingSorted.map(d => d.value),
                        itemStyle: {{ borderRadius: [0, 4, 4, 0], color: '#f59e0b' }},
                        label: {{ show: true, position: 'right', fontSize: 11 }}
                    }}]
                }});
            }} else {{
                document.getElementById('fundingChart').innerHTML = '<div class="flex items-center justify-center h-full text-slate-400 text-sm">暂无数据</div>';
            }}
            
            // 成立时间分布 - 柱状图
            if (yearData.length > 0) {{
                charts.year = echarts.init(document.getElementById('yearChart'));
                charts.year.setOption({{
                    tooltip: {{ trigger: 'axis' }},
                    grid: {{ left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true }},
                    xAxis: {{ type: 'category', data: yearData.map(d => d.year), axisLabel: {{ fontSize: 11 }} }},
                    yAxis: {{ type: 'value', axisLabel: {{ fontSize: 11 }}, minInterval: 1 }},
                    series: [{{
                        type: 'bar', data: yearData.map(d => d.count),
                        itemStyle: {{ borderRadius: [4, 4, 0, 0], color: '#10b981' }},
                        label: {{ show: true, position: 'top', fontSize: 11 }}
                    }}]
                }});
            }} else {{
                document.getElementById('yearChart').innerHTML = '<div class="flex items-center justify-center h-full text-slate-400 text-sm">暂无数据</div>';
            }}
            
            // 企业规模分布 - 饼图
            if (scaleData.length > 0) {{
                charts.scale = echarts.init(document.getElementById('scaleChart'));
                charts.scale.setOption({{
                    tooltip: {{ trigger: 'item', formatter: '{{b}}: {{c}} 家 ({{d}}%)' }},
                    legend: {{ type: 'scroll', orient: 'vertical', right: 10, top: 20, bottom: 20, textStyle: {{ fontSize: 11 }} }},
                    series: [{{
                        type: 'pie', radius: ['35%', '65%'], center: ['40%', '50%'],
                        avoidLabelOverlap: false,
                        itemStyle: {{ borderRadius: 6, borderColor: '#fff', borderWidth: 2 }},
                        label: {{ show: false }},
                        emphasis: {{ label: {{ show: true, fontSize: 12, fontWeight: 'bold' }} }},
                        data: scaleData
                    }}],
                    color: ['#1e3a5f', '#2d5a87', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe']
                }});
            }} else {{
                document.getElementById('scaleChart').innerHTML = '<div class="flex items-center justify-center h-full text-slate-400 text-sm">暂无数据</div>';
            }}
            
            // 城市分布 - 柱状图
            if (cityData.length > 0) {{
                charts.city = echarts.init(document.getElementById('cityChart'));
                charts.city.setOption({{
                    tooltip: {{ trigger: 'axis' }},
                    grid: {{ left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true }},
                    xAxis: {{ type: 'category', data: cityData.map(d => d.name), axisLabel: {{ fontSize: 11 }} }},
                    yAxis: {{ type: 'value', axisLabel: {{ fontSize: 11 }}, minInterval: 1 }},
                    series: [{{
                        type: 'bar', data: cityData.map(d => d.value),
                        itemStyle: {{ borderRadius: [4, 4, 0, 0], color: {{ type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
                            {{ offset: 0, color: '#ef4444' }},
                            {{ offset: 1, color: '#f87171' }}
                        ]}} }},
                        label: {{ show: true, position: 'top', fontSize: 11 }}
                    }}]
                }});
            }} else {{
                document.getElementById('cityChart').innerHTML = '<div class="flex items-center justify-center h-full text-slate-400 text-sm">暂无数据</div>';
            }}
        }}
        
        window.addEventListener('resize', () => Object.values(charts).forEach(c => c && c.resize()));
        document.addEventListener('DOMContentLoaded', initCharts);
    </script>
</body>
</html>'''
    
    safe_name = industry_name.replace('/', '_').replace('\\', '_').replace(' ', '_')
    filename = f"行业洞察看板_{safe_name}.html"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return filepath


def generate_industry_with_companies(industry_data, companies_data_list, output_dir):
    """
    批量生成行业洞察看板 + 所有企业的独立洞察看板
    
    Args:
        industry_data: 行业数据字典（同 generate_industry_dashboard）
        companies_data_list: 企业数据字典列表（每个元素同 generate_dashboard 的 company_data）
        output_dir: 输出目录
    
    Returns:
        dict: {
            'industry_dashboard': 行业看板文件路径,
            'company_dashboards': [企业看板文件路径列表],
            'all_files': [所有生成文件路径列表]
        }
    """
    import os
    
    generated_files = []
    company_dashboard_paths = []
    
    # 第一步：生成所有企业的独立洞察看板
    print(f"[批量生成] 开始生成 {len(companies_data_list)} 个企业洞察看板...")
    for idx, company_data in enumerate(companies_data_list, 1):
        company_name = company_data.get('name', f'企业_{idx}')
        print(f"  [{idx}/{len(companies_data_list)}] 生成企业看板: {company_name}")
        try:
            path = generate_dashboard(company_data, output_dir)
            company_dashboard_paths.append(path)
            generated_files.append(path)
        except Exception as e:
            print(f"  ⚠️ 生成 {company_name} 看板失败: {e}")
    
    # 第二步：生成行业洞察看板
    # 确保行业数据中的企业列表包含正确的名称，以便卡片能链接到对应的企业看板
    print(f"[批量生成] 生成行业洞察看板: {industry_data.get('industry_name', '未知行业')}...")
    try:
        industry_path = generate_industry_dashboard(industry_data, output_dir)
        generated_files.append(industry_path)
    except Exception as e:
        print(f"  ⚠️ 生成行业看板失败: {e}")
        industry_path = None
    
    print(f"[批量生成] 完成！共生成 {len(generated_files)} 个文件")
    print(f"  - 行业看板: {industry_path}")
    print(f"  - 企业看板: {len(company_dashboard_paths)} 个")
    
    return {
        'industry_dashboard': industry_path,
        'company_dashboards': company_dashboard_paths,
        'all_files': generated_files
    }
