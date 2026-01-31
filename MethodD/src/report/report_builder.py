"""
报告生成器：生成对照实验报告
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List


class ReportBuilder:
    """报告生成器"""
    
    @staticmethod
    def generate_summary_report(experiment_name: str,
                               experiment_results: Dict,
                               ablation_results: Dict = None,
                               comparison_results: Dict = None) -> str:
        """
        生成总结报告
        
        参数:
            experiment_name: 实验名称
            experiment_results: 实验结果
            ablation_results: 消融实验结果
            comparison_results: 对照实验结果
            
        返回:
            str: 报告文本
        """
        report = []
        report.append("=" * 80)
        report.append(f"IV 收敛因子策略 - {experiment_name}")
        report.append("=" * 80)
        report.append("")
        
        # 生成时间
        report.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 实验结果
        report.append("【实验结果】")
        report.append("-" * 80)
        report.append("")
        
        if experiment_results:
            report.append("基础策略性能:")
            for key, value in experiment_results.items():
                if isinstance(value, float):
                    report.append(f"  {key}: {value:.4f}")
                else:
                    report.append(f"  {key}: {value}")
            report.append("")
        
        # 消融实验结果
        if ablation_results:
            report.append("【消融实验结果】")
            report.append("-" * 80)
            report.append("")
            
            base_return = ablation_results.get('base_result', {}).get('total_return', 0)
            report.append(f"基础策略收益: {base_return:.2%}")
            report.append("")
            
            report.append("消融实验影响分析:")
            for ablation_name, ablation_data in ablation_results.get('ablation_results', {}).items():
                impact = ablation_data.get('impact', {})
                report.append(f"  {ablation_name}:")
                report.append(f"    收益变化: {impact.get('return_change', 0):.2%}")
                report.append(f"    夏普比率变化: {impact.get('sharpe_change', 0):.4f}")
                report.append(f"    最大回撤变化: {impact.get('drawdown_change', 0):.2%}")
            report.append("")
        
        # 对照实验结果
        if comparison_results:
            report.append("【对照实验结果】")
            report.append("-" * 80)
            report.append("")
            
            report.append("策略对比:")
            for strategy_name, result in comparison_results.items():
                report.append(f"  {strategy_name}:")
                report.append(f"    总收益: {result.get('total_return', 0):.2%}")
                report.append(f"    年化收益: {result.get('annual_return', 0):.2%}")
                report.append(f"    夏普比率: {result.get('sharpe_ratio', 0):.4f}")
                report.append(f"    最大回撤: {result.get('max_drawdown', 0):.2%}")
            report.append("")
        
        report.append("=" * 80)
        report.append("报告完成")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    @staticmethod
    def save_report(report_text: str, filename: str) -> None:
        """
        保存报告到文件
        
        参数:
            report_text: 报告文本
            filename: 文件名
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_text)
