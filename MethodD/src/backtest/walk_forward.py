"""
Walk-Forward 样本外验证框架
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class WalkForwardValidator:
    """Walk-Forward 样本外验证"""

    @staticmethod
    def split_walk_forward(
        data: pd.DataFrame,
        train_size: int = 60,
        test_size: int = 20,
        step_size: int = 10,
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        生成 Walk-Forward 分割

        参数:
            data: 完整数据集
            train_size: 训练集大小（天数）
            test_size: 测试集大小（天数）
            step_size: 步长（天数）

        返回:
            List: (训练集, 测试集) 元组列表
        """
        splits = []
        total_size = len(data)

        for i in range(0, total_size - train_size - test_size, step_size):
            train_end = i + train_size
            test_end = train_end + test_size

            if test_end > total_size:
                break

            train_data = data.iloc[i:train_end]
            test_data = data.iloc[train_end:test_end]

            splits.append((train_data, test_data))

        return splits

    @staticmethod
    def evaluate_walk_forward(
        splits: List[Tuple[pd.DataFrame, pd.DataFrame]], strategy_func
    ) -> Dict:
        """
        评估 Walk-Forward 结果

        参数:
            splits: Walk-Forward 分割列表
            strategy_func: 策略函数

        返回:
            Dict: 评估结果
        """
        results = {
            "train_results": [],
            "test_results": [],
            "out_of_sample_performance": [],
        }

        for i, (train_data, test_data) in enumerate(splits):
            # 在训练集上训练
            train_result = strategy_func(train_data)
            results["train_results"].append(train_result)

            # 在测试集上验证
            test_result = strategy_func(test_data)
            results["test_results"].append(test_result)

            # 计算样本外性能
            oos_performance = {
                "fold": i + 1,
                "train_return": train_result.get("total_return", 0),
                "test_return": test_result.get("total_return", 0),
                "degradation": train_result.get("total_return", 0)
                - test_result.get("total_return", 0),
                "train_sharpe": train_result.get("sharpe_ratio", 0),
                "test_sharpe": test_result.get("sharpe_ratio", 0),
            }
            results["out_of_sample_performance"].append(oos_performance)

        return results


class AblationStudy:
    """消融实验"""

    @staticmethod
    def run_ablation_study(
        data: pd.DataFrame, base_strategy_func, ablation_configs: Dict
    ) -> Dict:
        """
        运行消融实验

        参数:
            data: 数据集
            base_strategy_func: 基础策略函数
            ablation_configs: 消融配置字典

        返回:
            Dict: 消融实验结果
        """
        results = {"base_result": None, "ablation_results": {}}

        # 运行基础策略
        base_result = base_strategy_func(data)
        results["base_result"] = base_result

        # 运行消融实验
        for ablation_name, ablation_func in ablation_configs.items():
            ablation_result = ablation_func(data)
            results["ablation_results"][ablation_name] = {
                "result": ablation_result,
                "impact": {
                    "return_change": ablation_result.get("total_return", 0)
                    - base_result.get("total_return", 0),
                    "sharpe_change": ablation_result.get("sharpe_ratio", 0)
                    - base_result.get("sharpe_ratio", 0),
                    "drawdown_change": ablation_result.get("max_drawdown", 0)
                    - base_result.get("max_drawdown", 0),
                },
            }

        return results


class ComparisonExperiment:
    """对照实验"""

    @staticmethod
    def run_comparison(data: pd.DataFrame, strategies: Dict) -> Dict:
        """
        运行对照实验

        参数:
            data: 数据集
            strategies: 策略字典 {策略名: 策略函数}

        返回:
            Dict: 对照实验结果
        """
        results = {}

        for strategy_name, strategy_func in strategies.items():
            result = strategy_func(data)
            results[strategy_name] = result

        return results

    @staticmethod
    def compare_strategies(comparison_results: Dict) -> pd.DataFrame:
        """
        比较策略结果

        参数:
            comparison_results: 对照实验结果

        返回:
            DataFrame: 比较表格
        """
        comparison_data = []

        for strategy_name, result in comparison_results.items():
            comparison_data.append(
                {
                    "Strategy": strategy_name,
                    "Total Return": f"{result.get('total_return', 0):.2%}",
                    "Annual Return": f"{result.get('annual_return', 0):.2%}",
                    "Sharpe Ratio": f"{result.get('sharpe_ratio', 0):.4f}",
                    "Max Drawdown": f"{result.get('max_drawdown', 0):.2%}",
                    "Num Trades": result.get("num_trades", 0),
                }
            )

        return pd.DataFrame(comparison_data)
