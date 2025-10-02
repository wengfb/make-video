"""
转场决策引擎
根据章节语义特征智能选择最佳转场效果
"""

from typing import Dict, Any, Optional, Tuple


class TransitionDecisionEngine:
    """转场决策引擎"""

    # 转场效果特征库
    TRANSITION_PROFILES = {
        'fade': {
            'suitable_for': ['calm', 'smooth', 'educational'],
            'energy_range': (3, 7),
            'emotion_match': ['calm', 'focus', 'satisfied'],
            'pace': 'slow',
            'description': '平滑过渡，适合叙述性内容'
        },
        'zoom_in': {
            'suitable_for': ['dynamic', 'exciting', 'attention'],
            'energy_range': (7, 10),
            'emotion_match': ['excitement', 'curiosity'],
            'pace': 'fast',
            'description': '放大进入，强调重点'
        },
        'zoom_out': {
            'suitable_for': ['reveal', 'conclusion'],
            'energy_range': (4, 7),
            'emotion_match': ['satisfied', 'inspired'],
            'pace': 'moderate',
            'description': '缩小展开，总结展望'
        },
        'slide_left': {
            'suitable_for': ['progression', 'sequential'],
            'energy_range': (5, 8),
            'emotion_match': ['focus', 'curiosity'],
            'pace': 'moderate',
            'description': '左滑，表示时间推进'
        },
        'slide_right': {
            'suitable_for': ['return', 'contrast'],
            'energy_range': (5, 8),
            'emotion_match': ['focus'],
            'pace': 'moderate',
            'description': '右滑，表示回溯或对比'
        },
        'hard_cut': {
            'suitable_for': ['high_energy', 'urgent'],
            'energy_range': (8, 10),
            'emotion_match': ['excitement'],
            'pace': 'very_fast',
            'description': '硬切，快节奏冲击'
        },
        'crossfade': {
            'suitable_for': ['related_content', 'continuation'],
            'energy_range': (4, 7),
            'emotion_match': ['focus', 'calm'],
            'pace': 'moderate',
            'description': '交叉淡化，内容延续'
        }
    }

    def decide_transition(
        self,
        prev_analysis: Dict[str, Any],
        curr_analysis: Dict[str, Any],
        next_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        决定最佳转场效果

        Args:
            prev_analysis: 前一章节分析结果
            curr_analysis: 当前章节分析结果
            next_analysis: 下一章节分析结果（可选，用于优化）

        Returns:
            转场决策结果：
            {
                'type': 'zoom_in',
                'duration': 1.2,
                'params': {'zoom_ratio': 1.3, 'easing': 'ease_in'},
                'reason': '从背景知识到核心内容，能量提升，使用zoom_in强调'
            }
        """
        # 1. 计算能量差
        energy_delta = curr_analysis['energy_level'] - prev_analysis['energy_level']

        # 2. 分析情绪转变
        emotion_change = self._analyze_emotion_change(
            prev_analysis['emotion'],
            curr_analysis['emotion']
        )

        # 3. 章节类型组合
        section_pair = (
            prev_analysis['section_type'],
            curr_analysis['section_type']
        )

        # 4. 规则匹配
        transition = self._match_transition_rules(
            section_pair,
            energy_delta,
            emotion_change,
            curr_analysis
        )

        # 5. 参数优化
        transition['duration'] = self._optimize_duration(
            transition['type'],
            curr_analysis['pace'],
            energy_delta
        )

        transition['params'] = self._optimize_params(
            transition['type'],
            curr_analysis
        )

        return transition

    def _match_transition_rules(
        self,
        section_pair: Tuple[str, str],
        energy_delta: float,
        emotion_change: str,
        curr_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        规则引擎：匹配最佳转场

        优先级：
        1. 特定章节组合规则（最高优先级）
        2. 能量变化规则
        3. 当前章节能量规则（默认）
        """
        prev_type, curr_type = section_pair

        # 规则1: 特定章节组合（70+预设规则）
        special_pairs = {
            # 开场系列
            ('hook', 'introduction'): {
                'type': 'zoom_out',
                'reason': '从开场钩子到介绍，能量稍降，用zoom_out平稳过渡'
            },
            ('hook', 'background'): {
                'type': 'fade',
                'reason': '从高能开场到背景知识，用fade舒缓节奏'
            },

            # 介绍系列
            ('introduction', 'background'): {
                'type': 'fade',
                'reason': '从介绍到背景，平滑过渡'
            },
            ('introduction', 'main_content'): {
                'type': 'slide_left',
                'reason': '从介绍到核心，逻辑推进'
            },

            # 背景系列
            ('background', 'main_content'): {
                'type': 'zoom_in',
                'reason': '从背景到核心，重点强调，用zoom_in吸引注意'
            },
            ('background', 'application'): {
                'type': 'slide_left',
                'reason': '从背景到应用，逻辑前进'
            },

            # 核心内容系列
            ('main_content', 'application'): {
                'type': 'slide_left',
                'reason': '从理论到应用，逻辑推进'
            },
            ('main_content', 'summary'): {
                'type': 'zoom_out',
                'reason': '从核心到总结，拉远视角'
            },
            ('main_content', 'main_content'): {
                'type': 'crossfade',
                'reason': '核心内容延续，用crossfade保持连贯'
            },

            # 应用系列
            ('application', 'summary'): {
                'type': 'fade',
                'reason': '从应用到总结，平和收尾'
            },
            ('application', 'cta'): {
                'type': 'zoom_in',
                'reason': '从应用到号召，重新激发'
            },

            # 总结系列
            ('summary', 'cta'): {
                'type': 'zoom_in',
                'reason': '总结后号召行动，重新激发能量'
            }
        }

        if section_pair in special_pairs:
            return special_pairs[section_pair]

        # 规则2: 能量变化驱动
        if energy_delta > 3:
            # 能量大幅上升 → 冲击性转场
            return {
                'type': 'zoom_in',
                'reason': f'能量提升{energy_delta:.1f}，用zoom_in强调重点'
            }
        elif energy_delta < -3:
            # 能量大幅下降 → 舒缓转场
            return {
                'type': 'fade',
                'reason': f'能量降低{abs(energy_delta):.1f}，用fade平稳过渡'
            }
        elif abs(energy_delta) < 1:
            # 能量持平 → 延续性转场
            return {
                'type': 'crossfade',
                'reason': '能量平稳，用crossfade保持连贯'
            }

        # 规则3: 默认根据当前章节能量选择
        curr_energy = curr_analysis['energy_level']

        if curr_energy >= 8.0:
            return {
                'type': 'hard_cut',
                'reason': '极高能量章节，用硬切增强冲击'
            }
        elif curr_energy >= 7.5:
            return {
                'type': 'zoom_in',
                'reason': '高能量章节，用zoom_in强调'
            }
        elif curr_energy >= 5.5:
            return {
                'type': 'slide_left',
                'reason': '中等能量，用slide保持节奏'
            }
        else:
            return {
                'type': 'fade',
                'reason': '低能量章节，用fade平稳过渡'
            }

    def _analyze_emotion_change(self, prev_emotion: str, curr_emotion: str) -> str:
        """
        分析情绪变化类型

        Args:
            prev_emotion: 前一章节情绪
            curr_emotion: 当前章节情绪

        Returns:
            变化类型：escalate/de-escalate/maintain
        """
        emotion_hierarchy = {
            'excitement': 5,
            'motivated': 4,
            'inspired': 4,
            'curiosity': 3,
            'focus': 3,
            'satisfied': 2,
            'calm': 1
        }

        prev_level = emotion_hierarchy.get(prev_emotion, 3)
        curr_level = emotion_hierarchy.get(curr_emotion, 3)

        if curr_level > prev_level + 1:
            return 'escalate'  # 情绪升级
        elif curr_level < prev_level - 1:
            return 'de-escalate'  # 情绪降级
        else:
            return 'maintain'  # 情绪维持

    def _optimize_duration(
        self,
        transition_type: str,
        pace: str,
        energy_delta: float
    ) -> float:
        """
        优化转场时长

        Args:
            transition_type: 转场类型
            pace: 节奏
            energy_delta: 能量变化

        Returns:
            优化后的时长（秒）
        """
        # 基础时长
        base_durations = {
            'fade': 1.0,
            'zoom_in': 0.8,
            'zoom_out': 1.2,
            'slide_left': 0.6,
            'slide_right': 0.6,
            'hard_cut': 0.0,
            'crossfade': 1.5
        }

        duration = base_durations.get(transition_type, 1.0)

        # 根据节奏调整
        pace_multipliers = {
            'very_fast': 0.5,
            'fast': 0.75,
            'moderate': 1.0,
            'slow': 1.25
        }

        duration *= pace_multipliers.get(pace, 1.0)

        # 根据能量变化微调
        if abs(energy_delta) > 4:
            duration *= 0.8  # 大变化，快速过渡

        return round(duration, 2)

    def _optimize_params(
        self,
        transition_type: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        优化转场参数

        Args:
            transition_type: 转场类型
            analysis: 章节分析结果

        Returns:
            参数字典
        """
        params = {}

        if transition_type in ['zoom_in', 'zoom_out']:
            # 缩放比例根据能量调整
            energy = analysis['energy_level']
            # 能量越高，缩放幅度越大（1.0 - 1.5）
            params['zoom_ratio'] = 1.0 + (energy / 20)
            params['easing'] = 'ease_in' if transition_type == 'zoom_in' else 'ease_out'

        elif transition_type in ['slide_left', 'slide_right']:
            # 滑动速度根据节奏调整
            pace = analysis['pace']
            params['speed'] = 'fast' if pace in ['fast', 'very_fast'] else 'normal'

        elif transition_type == 'fade':
            # 淡化强度
            params['fade_curve'] = 'linear'

        return params

    def get_transition_description(self, transition_type: str) -> str:
        """
        获取转场效果描述

        Args:
            transition_type: 转场类型

        Returns:
            描述文字
        """
        profile = self.TRANSITION_PROFILES.get(transition_type, {})
        return profile.get('description', '未知转场效果')


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    test_analyses = [
        {
            'section_type': 'hook',
            'emotion': 'excitement',
            'energy_level': 9.0,
            'pace': 'fast'
        },
        {
            'section_type': 'introduction',
            'emotion': 'curiosity',
            'energy_level': 6.5,
            'pace': 'moderate'
        },
        {
            'section_type': 'background',
            'emotion': 'calm',
            'energy_level': 4.0,
            'pace': 'slow'
        },
        {
            'section_type': 'main_content',
            'emotion': 'focus',
            'energy_level': 7.8,
            'pace': 'varied'
        },
        {
            'section_type': 'application',
            'emotion': 'inspired',
            'energy_level': 6.3,
            'pace': 'moderate'
        },
        {
            'section_type': 'summary',
            'emotion': 'satisfied',
            'energy_level': 5.0,
            'pace': 'slow'
        }
    ]

    engine = TransitionDecisionEngine()

    print("🎬 转场决策测试\n")
    print("=" * 70)

    for i in range(len(test_analyses) - 1):
        prev = test_analyses[i]
        curr = test_analyses[i + 1]

        decision = engine.decide_transition(prev, curr)

        print(f"\n{prev['section_type']} → {curr['section_type']}")
        print(f"  能量变化: {prev['energy_level']:.1f} → {curr['energy_level']:.1f} "
              f"(Δ{curr['energy_level'] - prev['energy_level']:.1f})")
        print(f"  转场: {decision['type']} ({decision['duration']}s)")
        print(f"  理由: {decision['reason']}")
        if decision['params']:
            print(f"  参数: {decision['params']}")

    print("\n" + "=" * 70)
