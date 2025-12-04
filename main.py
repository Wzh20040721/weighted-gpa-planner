#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加权平均分规划助手 - 优化版本
使用线性规划算法智能分配各科目标分数
"""

import sys
import json
import numpy as np
from typing import List, Dict, Optional, Tuple
from scipy.optimize import linprog, minimize
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QFileDialog, QTabWidget, QTextEdit, QSpinBox,
    QDoubleSpinBox, QHeaderView, QDialog, QDialogButtonBox, QGroupBox,
    QFormLayout
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont, QColor


class PlannedCourse:
    """计划课程数据模型（优化版）"""
    def __init__(self, name: str, credit: float, 
                 min_score: float, max_score: float, difficulty: float,
                 course_id: Optional[str] = None):
        self.id = course_id or self._generate_id()
        self.name = name
        self.credit = credit
        self.min_score = min_score  # 最低可能分数
        self.max_score = max_score  # 最高可能分数
        self.difficulty = difficulty  # 难度系数 (0-1, 越大越难)
        self.optimized_target = None  # 优化后的目标分数
    
    @staticmethod
    def _generate_id():
        import time
        import random
        return f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'credit': self.credit,
            'min_score': self.min_score,
            'max_score': self.max_score,
            'difficulty': self.difficulty,
            'optimized_target': self.optimized_target
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PlannedCourse':
        """从字典创建课程"""
        course = cls(
            name=data.get('name', ''),
            credit=data.get('credit', 0.0),
            min_score=data.get('min_score', 0.0),
            max_score=data.get('max_score', 100.0),
            difficulty=data.get('difficulty', 0.5),
            course_id=data.get('id')
        )
        course.optimized_target = data.get('optimized_target')
        return course


class CompletedCourse:
    """已修课程数据模型"""
    def __init__(self, name: str, credit: float, score: float,
                 course_id: Optional[str] = None):
        self.id = course_id or self._generate_id()
        self.name = name
        self.credit = credit
        self.score = score
    
    @staticmethod
    def _generate_id():
        import time
        import random
        return f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'credit': self.credit,
            'score': self.score
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CompletedCourse':
        """从字典创建课程"""
        return cls(
            name=data.get('name', ''),
            credit=data.get('credit', 0.0),
            score=data.get('score', 0.0),
            course_id=data.get('id')
        )


class OptimizationEngine:
    """优化引擎 - 使用运筹学方法计算最优分数分配"""
    
    @staticmethod
    def calculate_weighted_avg(courses: List, score_attr: str = 'score') -> Tuple[float, float]:
        """计算加权平均分"""
        total_credit = 0.0
        total_score = 0.0
        
        for course in courses:
            credit = course.credit
            score = getattr(course, score_attr, 0)
            if credit <= 0 or score is None:
                continue
            total_credit += credit
            total_score += credit * score
        
        avg = total_score / total_credit if total_credit > 0 else 0.0
        return total_credit, avg
    
    @staticmethod
    def optimize_scores(completed_courses: List[CompletedCourse],
                       planned_courses: List[PlannedCourse],
                       target_gpa: float) -> Dict:
        """
        使用优化算法计算各科最优目标分数
        
        目标函数：最小化总体难度加权的努力成本
        约束条件：
        1. 每科分数在 [min_score, max_score] 范围内
        2. 加权平均分达到目标 target_gpa
        
        返回：
        {
            'feasible': bool,  # 是否可行
            'optimized_scores': List[float],  # 优化后的各科分数
            'total_gpa': float,  # 预期GPA
            'suggestions': List[str],  # 建议
            'adjustments': Dict  # 调整建议
        }
        """
        if not planned_courses:
            return {
                'feasible': False,
                'optimized_scores': [],
                'total_gpa': 0,
                'suggestions': ['没有计划课程，无法进行优化'],
                'adjustments': {}
            }
        
        # 计算已修课程的加权总分和总学分
        completed_credit, completed_avg = OptimizationEngine.calculate_weighted_avg(completed_courses)
        completed_weighted_sum = completed_avg * completed_credit
        
        # 计划课程数据
        n = len(planned_courses)
        credits = np.array([c.credit for c in planned_courses])
        min_scores = np.array([c.min_score for c in planned_courses])
        max_scores = np.array([c.max_score for c in planned_courses])
        difficulties = np.array([c.difficulty for c in planned_courses])
        
        total_credit = completed_credit + np.sum(credits)
        
        # 检查是否可行（即使全部拿最高分也无法达到目标）
        max_possible_weighted_sum = completed_weighted_sum + np.sum(credits * max_scores)
        max_possible_gpa = max_possible_weighted_sum / total_credit
        
        if max_possible_gpa < target_gpa:
            # 不可行，返回建议
            gap = target_gpa - max_possible_gpa
            return {
                'feasible': False,
                'optimized_scores': max_scores.tolist(),
                'total_gpa': max_possible_gpa,
                'suggestions': [
                    f'即使所有计划课程都拿最高分，也只能达到 {max_possible_gpa:.2f} 分',
                    f'与目标相差 {gap:.2f} 分',
                    '建议：'
                ],
                'adjustments': OptimizationEngine._generate_adjustments(
                    completed_courses, planned_courses, target_gpa, gap
                )
            }
        
        # 检查最低分是否已经超过目标
        min_possible_weighted_sum = completed_weighted_sum + np.sum(credits * min_scores)
        min_possible_gpa = min_possible_weighted_sum / total_credit
        
        if min_possible_gpa >= target_gpa:
            # 即使拿最低分也能达到目标
            return {
                'feasible': True,
                'optimized_scores': min_scores.tolist(),
                'total_gpa': min_possible_gpa,
                'suggestions': [
                    f'好消息！即使所有计划课程都拿最低分 ({min_possible_gpa:.2f})，也能达到目标',
                    '建议保持正常学习即可'
                ],
                'adjustments': {}
            }
        
        # 可行，进行优化
        # 目标函数：最小化 sum(difficulty * (score - min_score))
        # 即优先在简单的课程上拿高分，难的课程可以适当降低要求
        
        def objective(x):
            """目标函数：最小化难度加权的努力"""
            effort = difficulties * (x - min_scores)
            return np.sum(effort)
        
        def constraint_gpa(x):
            """约束：达到目标GPA"""
            planned_weighted_sum = np.sum(credits * x)
            total_weighted_sum = completed_weighted_sum + planned_weighted_sum
            gpa = total_weighted_sum / total_credit
            return gpa - target_gpa
        
        # 边界约束
        bounds = [(min_s, max_s) for min_s, max_s in zip(min_scores, max_scores)]
        
        # 等式约束
        constraints = [
            {'type': 'eq', 'fun': constraint_gpa}
        ]
        
        # 初始猜测：线性插值
        required_planned_avg = (target_gpa * total_credit - completed_weighted_sum) / np.sum(credits)
        x0 = np.full(n, required_planned_avg)
        x0 = np.clip(x0, min_scores, max_scores)
        
        # 优化
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if result.success:
            optimized_scores = result.x
            final_gpa = (completed_weighted_sum + np.sum(credits * optimized_scores)) / total_credit
            
            # 生成建议
            suggestions = OptimizationEngine._generate_suggestions(
                planned_courses, optimized_scores, difficulties
            )
            
            return {
                'feasible': True,
                'optimized_scores': optimized_scores.tolist(),
                'total_gpa': final_gpa,
                'suggestions': suggestions,
                'adjustments': {}
            }
        else:
            # 优化失败，使用均匀分配
            uniform_scores = np.full(n, required_planned_avg)
            uniform_scores = np.clip(uniform_scores, min_scores, max_scores)
            
            return {
                'feasible': True,
                'optimized_scores': uniform_scores.tolist(),
                'total_gpa': target_gpa,
                'suggestions': ['使用均匀分配策略'],
                'adjustments': {}
            }
    
    @staticmethod
    def _generate_suggestions(planned_courses: List[PlannedCourse],
                             optimized_scores: np.ndarray,
                             difficulties: np.ndarray) -> List[str]:
        """生成优化建议"""
        suggestions = ['优化结果分析：\n']
        
        # 按难度分类
        easy_courses = []
        medium_courses = []
        hard_courses = []
        
        for i, course in enumerate(planned_courses):
            score = optimized_scores[i]
            diff = difficulties[i]
            
            if diff < 0.3:
                easy_courses.append((course.name, score))
            elif diff < 0.7:
                medium_courses.append((course.name, score))
            else:
                hard_courses.append((course.name, score))
        
        if easy_courses:
            suggestions.append('\n📗 简单课程（建议重点提分）：')
            for name, score in easy_courses:
                suggestions.append(f'  • {name}: 目标 {score:.1f} 分')
        
        if medium_courses:
            suggestions.append('\n📘 中等难度课程：')
            for name, score in medium_courses:
                suggestions.append(f'  • {name}: 目标 {score:.1f} 分')
        
        if hard_courses:
            suggestions.append('\n📕 困难课程（保证及格即可）：')
            for name, score in hard_courses:
                suggestions.append(f'  • {name}: 目标 {score:.1f} 分')
        
        suggestions.append('\n💡 策略建议：')
        suggestions.append('  • 优先在简单课程上投入精力，争取高分')
        suggestions.append('  • 困难课程保证达到目标分数即可')
        suggestions.append('  • 合理分配学习时间，避免过度追求完美')
        
        return suggestions
    
    @staticmethod
    def _generate_adjustments(completed_courses: List[CompletedCourse],
                             planned_courses: List[PlannedCourse],
                             target_gpa: float,
                             gap: float) -> Dict:
        """生成调整建议"""
        adjustments = {
            'options': []
        }
        
        # 选项1：降低目标GPA
        new_target = target_gpa - gap - 0.5
        adjustments['options'].append({
            'type': 'lower_target',
            'description': f'降低目标GPA至 {new_target:.1f} 分',
            'feasibility': 'high'
        })
        
        # 选项2：增加高分课程
        total_planned_credit = sum(c.credit for c in planned_courses)
        additional_credit_needed = gap * (sum(c.credit for c in completed_courses) + total_planned_credit) / 10
        adjustments['options'].append({
            'type': 'add_courses',
            'description': f'增加约 {additional_credit_needed:.1f} 学分的高分课程（预期90分以上）',
            'feasibility': 'medium'
        })
        
        # 选项3：提高课程最高分预期
        adjustments['options'].append({
            'type': 'raise_expectations',
            'description': '重新评估各课程的最高可能分数，可能低估了自己的能力',
            'feasibility': 'medium'
        })
        
        return adjustments


class DataManager:
    """数据管理器"""
    def __init__(self):
        self.completed_courses: List[CompletedCourse] = []
        self.planned_courses: List[PlannedCourse] = []
        self.target_score: Optional[float] = None
        self.settings = QSettings('WeightedPlanner', 'GradeAppV2')
        self.load_from_settings()
    
    def load_from_settings(self):
        """从设置加载数据"""
        try:
            data_str = self.settings.value('app_data', '')
            if data_str:
                data = json.loads(data_str)
                self.completed_courses = [CompletedCourse.from_dict(c) for c in data.get('completed', [])]
                self.planned_courses = [PlannedCourse.from_dict(c) for c in data.get('planned', [])]
                self.target_score = data.get('targetScore')
        except Exception as e:
            print(f"加载数据失败: {e}")
    
    def save_to_settings(self):
        """保存数据到设置"""
        try:
            data = {
                'completed': [c.to_dict() for c in self.completed_courses],
                'planned': [c.to_dict() for c in self.planned_courses],
                'targetScore': self.target_score
            }
            self.settings.setValue('app_data', json.dumps(data, ensure_ascii=False))
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    def export_to_json(self, filepath: str, selected_courses: Optional[List[str]] = None):
        """导出为JSON文件"""
        if selected_courses:
            completed = [c.to_dict() for c in self.completed_courses if c.id in selected_courses]
            planned = [c.to_dict() for c in self.planned_courses if c.id in selected_courses]
        else:
            completed = [c.to_dict() for c in self.completed_courses]
            planned = [c.to_dict() for c in self.planned_courses]
        
        data = {
            'completed': completed,
            'planned': planned,
            'targetScore': self.target_score,
            'version': '2.0'
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def import_from_json(self, filepath: str, merge: bool = False):
        """从JSON文件导入"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not merge:
            self.completed_courses.clear()
            self.planned_courses.clear()
        
        for c_data in data.get('completed', []):
            course = CompletedCourse.from_dict(c_data)
            self.completed_courses.append(course)
        
        for p_data in data.get('planned', []):
            course = PlannedCourse.from_dict(p_data)
            self.planned_courses.append(course)
        
        if 'targetScore' in data and data['targetScore'] is not None:
            self.target_score = data['targetScore']
        
        self.save_to_settings()


class LLMGuideDialog(QDialog):
    """LLM使用指南对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LLM生成JSON数据指南")
        self.setMinimumSize(700, 600)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("如何使用LLM生成符合规定的JSON数据（V2.0格式）")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        guide_text = QTextEdit()
        guide_text.setReadOnly(True)
        guide_text.setMarkdown(self.get_guide_content())
        layout.addWidget(guide_text)
        
        example_label = QLabel("JSON格式示例（V2.0）：")
        example_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(example_label)
        
        example_text = QTextEdit()
        example_text.setReadOnly(True)
        example_text.setPlainText(self.get_example_json())
        example_text.setMaximumHeight(250)
        layout.addWidget(example_text)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_guide_content(self) -> str:
        return """
## V2.0 新格式说明

计划课程现在需要提供：
- **min_score**: 最低可能分数（你觉得最差能考多少）
- **max_score**: 最高可能分数（你觉得最好能考多少）
- **difficulty**: 难度系数（0-1之间，0.3以下=简单，0.3-0.7=中等，0.7以上=困难）

系统会使用运筹学优化算法，自动计算最优的目标分数分配！

## 提示词模板

```
请生成课程成绩管理JSON（V2.0格式）：

已修课程格式：
- id, name, credit, score

计划课程格式（新）：
- id, name, credit, min_score（最低分）, max_score（最高分）, difficulty（0-1难度系数）

我的数据：
已修：高等数学(4.5学分，88分)
计划：数据结构(3学分，最低70最高95，难度0.7)

目标GPA：85
```
"""
    
    def get_example_json(self) -> str:
        return """{
  "completed": [
    {
      "id": "c001",
      "name": "高等数学B",
      "credit": 4.5,
      "score": 88
    }
  ],
  "planned": [
    {
      "id": "p001",
      "name": "数据结构与算法",
      "credit": 3,
      "min_score": 70,
      "max_score": 95,
      "difficulty": 0.7
    },
    {
      "id": "p002",
      "name": "Web开发",
      "credit": 2.5,
      "min_score": 80,
      "max_score": 98,
      "difficulty": 0.3
    }
  ],
  "targetScore": 85,
  "version": "2.0"
}"""


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.data_manager = DataManager()
        self.setWindowTitle("加权平均分规划助手 - 智能优化版")
        self.setMinimumSize(1200, 750)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 标题
        title = QLabel("加权平均分规划助手 - 智能优化版")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        subtitle = QLabel("使用运筹学优化算法，智能分配各科目标分数")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: gray;")
        main_layout.addWidget(subtitle)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        export_btn = QPushButton("导出JSON")
        export_btn.clicked.connect(self.export_json)
        toolbar_layout.addWidget(export_btn)
        
        import_btn = QPushButton("导入JSON")
        import_btn.clicked.connect(self.import_json)
        toolbar_layout.addWidget(import_btn)
        
        llm_guide_btn = QPushButton("LLM使用指南")
        llm_guide_btn.clicked.connect(self.show_llm_guide)
        toolbar_layout.addWidget(llm_guide_btn)
        
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)
        
        # 标签页
        tabs = QTabWidget()
        
        tabs.addTab(self.create_completed_tab(), "已修课程")
        tabs.addTab(self.create_planned_tab(), "计划课程")
        tabs.addTab(self.create_optimization_tab(), "智能优化")
        
        main_layout.addWidget(tabs)
    
    def create_completed_tab(self) -> QWidget:
        """创建已修课程标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 输入表单
        form_layout = QHBoxLayout()
        
        self.completed_name = QLineEdit()
        self.completed_name.setPlaceholderText("课程名")
        form_layout.addWidget(self.completed_name)
        
        self.completed_credit = QDoubleSpinBox()
        self.completed_credit.setRange(0, 20)
        self.completed_credit.setSingleStep(0.5)
        self.completed_credit.setDecimals(1)
        self.completed_credit.setPrefix("学分: ")
        form_layout.addWidget(self.completed_credit)
        
        self.completed_score = QDoubleSpinBox()
        self.completed_score.setRange(0, 100)
        self.completed_score.setSingleStep(1)
        self.completed_score.setDecimals(1)
        self.completed_score.setPrefix("分数: ")
        form_layout.addWidget(self.completed_score)
        
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self.add_completed_course)
        form_layout.addWidget(add_btn)
        
        layout.addLayout(form_layout)
        
        # 表格
        self.completed_table = QTableWidget()
        self.completed_table.setColumnCount(4)
        self.completed_table.setHorizontalHeaderLabels(['课程名', '学分', '分数', '操作'])
        self.completed_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.completed_table)
        
        # 统计信息
        self.completed_summary = QLabel()
        layout.addWidget(self.completed_summary)
        
        widget.setLayout(layout)
        return widget
    
    def create_planned_tab(self) -> QWidget:
        """创建计划课程标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 说明
        info_label = QLabel("💡 请填写每门课程的最低分、最高分和难度系数，系统将自动优化目标分数")
        info_label.setStyleSheet("background-color: #e3f2fd; padding: 8px; border-radius: 4px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 输入表单
        form_group = QGroupBox("添加计划课程")
        form_layout = QFormLayout()
        
        self.planned_name = QLineEdit()
        self.planned_name.setPlaceholderText("例如：数据结构与算法")
        form_layout.addRow("课程名:", self.planned_name)
        
        self.planned_credit = QDoubleSpinBox()
        self.planned_credit.setRange(0, 20)
        self.planned_credit.setSingleStep(0.5)
        self.planned_credit.setDecimals(1)
        form_layout.addRow("学分:", self.planned_credit)
        
        score_layout = QHBoxLayout()
        self.planned_min_score = QDoubleSpinBox()
        self.planned_min_score.setRange(0, 100)
        self.planned_min_score.setValue(60)
        self.planned_min_score.setPrefix("最低: ")
        score_layout.addWidget(self.planned_min_score)
        
        self.planned_max_score = QDoubleSpinBox()
        self.planned_max_score.setRange(0, 100)
        self.planned_max_score.setValue(95)
        self.planned_max_score.setPrefix("最高: ")
        score_layout.addWidget(self.planned_max_score)
        form_layout.addRow("分数范围:", score_layout)
        
        self.planned_difficulty = QDoubleSpinBox()
        self.planned_difficulty.setRange(0, 1)
        self.planned_difficulty.setSingleStep(0.1)
        self.planned_difficulty.setDecimals(1)
        self.planned_difficulty.setValue(0.5)
        self.planned_difficulty.setSuffix(" (0=简单, 1=困难)")
        form_layout.addRow("难度系数:", self.planned_difficulty)
        
        add_btn = QPushButton("添加计划课程")
        add_btn.clicked.connect(self.add_planned_course)
        form_layout.addRow("", add_btn)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # 表格
        self.planned_table = QTableWidget()
        self.planned_table.setColumnCount(6)
        self.planned_table.setHorizontalHeaderLabels([
            '课程名', '学分', '最低分', '最高分', '难度', '操作'
        ])
        self.planned_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.planned_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_optimization_tab(self) -> QWidget:
        """创建优化结果标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 目标设置
        target_group = QGroupBox("目标设置")
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("目标加权平均分:"))
        
        self.target_score_input = QDoubleSpinBox()
        self.target_score_input.setRange(0, 100)
        self.target_score_input.setSingleStep(0.5)
        self.target_score_input.setDecimals(2)
        target_layout.addWidget(self.target_score_input)
        
        calc_btn = QPushButton("🚀 开始智能优化")
        calc_btn.clicked.connect(self.run_optimization)
        calc_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        target_layout.addWidget(calc_btn)
        
        target_layout.addStretch()
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        # 优化结果摘要
        self.optimization_summary = QLabel()
        self.optimization_summary.setWordWrap(True)
        self.optimization_summary.setStyleSheet(
            "padding: 15px; background-color: #f5f5f5; border-radius: 8px; font-size: 13px;"
        )
        layout.addWidget(self.optimization_summary)
        
        # 详细结果表格
        result_label = QLabel("📊 优化后的各科目标分数：")
        result_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(result_label)
        
        self.optimization_table = QTableWidget()
        self.optimization_table.setColumnCount(6)
        self.optimization_table.setHorizontalHeaderLabels([
            '课程名', '学分', '分数范围', '难度', '优化目标', '说明'
        ])
        self.optimization_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.optimization_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.optimization_table)
        
        # 建议和调整
        self.suggestions_text = QTextEdit()
        self.suggestions_text.setReadOnly(True)
        self.suggestions_text.setMaximumHeight(200)
        layout.addWidget(self.suggestions_text)
        
        widget.setLayout(layout)
        return widget
    
    def add_completed_course(self):
        """添加已修课程"""
        name = self.completed_name.text().strip()
        credit = self.completed_credit.value()
        score = self.completed_score.value()
        
        if not name:
            QMessageBox.warning(self, "警告", "请输入课程名")
            return
        
        if credit <= 0:
            QMessageBox.warning(self, "警告", "学分必须大于0")
            return
        
        course = CompletedCourse(name, credit, score)
        self.data_manager.completed_courses.append(course)
        self.data_manager.save_to_settings()
        
        self.completed_name.clear()
        self.completed_credit.setValue(0)
        self.completed_score.setValue(0)
        
        self.refresh_completed_table()
    
    def add_planned_course(self):
        """添加计划课程"""
        name = self.planned_name.text().strip()
        credit = self.planned_credit.value()
        min_score = self.planned_min_score.value()
        max_score = self.planned_max_score.value()
        difficulty = self.planned_difficulty.value()
        
        if not name:
            QMessageBox.warning(self, "警告", "请输入课程名")
            return
        
        if credit <= 0:
            QMessageBox.warning(self, "警告", "学分必须大于0")
            return
        
        if min_score >= max_score:
            QMessageBox.warning(self, "警告", "最低分必须小于最高分")
            return
        
        course = PlannedCourse(name, credit, min_score, max_score, difficulty)
        self.data_manager.planned_courses.append(course)
        self.data_manager.save_to_settings()
        
        self.planned_name.clear()
        self.planned_credit.setValue(0)
        self.planned_min_score.setValue(60)
        self.planned_max_score.setValue(95)
        self.planned_difficulty.setValue(0.5)
        
        self.refresh_planned_table()
    
    def delete_completed_course(self, course_id: str):
        """删除已修课程"""
        self.data_manager.completed_courses = [
            c for c in self.data_manager.completed_courses if c.id != course_id
        ]
        self.data_manager.save_to_settings()
        self.refresh_completed_table()
    
    def delete_planned_course(self, course_id: str):
        """删除计划课程"""
        self.data_manager.planned_courses = [
            c for c in self.data_manager.planned_courses if c.id != course_id
        ]
        self.data_manager.save_to_settings()
        self.refresh_planned_table()
    
    def refresh_completed_table(self):
        """刷新已修课程表格"""
        self.completed_table.setRowCount(len(self.data_manager.completed_courses))
        
        for i, course in enumerate(self.data_manager.completed_courses):
            self.completed_table.setItem(i, 0, QTableWidgetItem(course.name))
            self.completed_table.setItem(i, 1, QTableWidgetItem(str(course.credit)))
            self.completed_table.setItem(i, 2, QTableWidgetItem(str(course.score)))
            
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda checked, cid=course.id: self.delete_completed_course(cid))
            self.completed_table.setCellWidget(i, 3, delete_btn)
        
        # 更新统计
        total_credit, avg = OptimizationEngine.calculate_weighted_avg(self.data_manager.completed_courses)
        if total_credit == 0:
            self.completed_summary.setText("目前还没有已修课程记录。")
        else:
            self.completed_summary.setText(
                f"已修总学分：<b>{total_credit:.2f}</b>，当前加权平均分：<b>{avg:.2f}</b>"
            )
    
    def refresh_planned_table(self):
        """刷新计划课程表格"""
        self.planned_table.setRowCount(len(self.data_manager.planned_courses))
        
        for i, course in enumerate(self.data_manager.planned_courses):
            self.planned_table.setItem(i, 0, QTableWidgetItem(course.name))
            self.planned_table.setItem(i, 1, QTableWidgetItem(str(course.credit)))
            self.planned_table.setItem(i, 2, QTableWidgetItem(str(course.min_score)))
            self.planned_table.setItem(i, 3, QTableWidgetItem(str(course.max_score)))
            self.planned_table.setItem(i, 4, QTableWidgetItem(f"{course.difficulty:.1f}"))
            
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda checked, cid=course.id: self.delete_planned_course(cid))
            self.planned_table.setCellWidget(i, 5, delete_btn)
    
    def run_optimization(self):
        """运行优化算法"""
        target = self.target_score_input.value()
        
        if target <= 0:
            QMessageBox.warning(self, "警告", "请设置目标平均分")
            return
        
        if not self.data_manager.planned_courses:
            QMessageBox.warning(self, "警告", "请先添加计划课程")
            return
        
        self.data_manager.target_score = target
        self.data_manager.save_to_settings()
        
        # 运行优化
        result = OptimizationEngine.optimize_scores(
            self.data_manager.completed_courses,
            self.data_manager.planned_courses,
            target
        )
        
        # 更新优化目标到课程
        if result['feasible'] and result['optimized_scores']:
            for i, course in enumerate(self.data_manager.planned_courses):
                course.optimized_target = result['optimized_scores'][i]
            self.data_manager.save_to_settings()
        
        # 显示结果
        self.display_optimization_result(result)
    
    def display_optimization_result(self, result: Dict):
        """显示优化结果"""
        # 摘要
        if result['feasible']:
            color = "green"
            status = "✅ 目标可达成"
        else:
            color = "red"
            status = "❌ 目标无法达成"
        
        summary_html = f"""
        <div style='font-size: 14px;'>
            <p style='color: {color}; font-weight: bold; font-size: 16px;'>{status}</p>
            <p><b>目标GPA:</b> {self.data_manager.target_score:.2f}</p>
            <p><b>预期GPA:</b> {result['total_gpa']:.2f}</p>
        </div>
        """
        self.optimization_summary.setText(summary_html)
        
        # 表格
        self.optimization_table.setRowCount(len(self.data_manager.planned_courses))
        
        for i, course in enumerate(self.data_manager.planned_courses):
            self.optimization_table.setItem(i, 0, QTableWidgetItem(course.name))
            self.optimization_table.setItem(i, 1, QTableWidgetItem(str(course.credit)))
            self.optimization_table.setItem(i, 2, QTableWidgetItem(
                f"{course.min_score:.0f} - {course.max_score:.0f}"
            ))
            
            # 难度显示
            if course.difficulty < 0.3:
                diff_text = "简单 📗"
            elif course.difficulty < 0.7:
                diff_text = "中等 📘"
            else:
                diff_text = "困难 📕"
            self.optimization_table.setItem(i, 3, QTableWidgetItem(diff_text))
            
            # 优化目标
            if result['optimized_scores'] and i < len(result['optimized_scores']):
                target_score = result['optimized_scores'][i]
                target_item = QTableWidgetItem(f"{target_score:.1f}")
                
                # 根据难度和目标分数设置颜色
                if target_score >= course.max_score * 0.9:
                    target_item.setBackground(QColor(255, 200, 200))  # 红色 - 需要高分
                elif target_score <= course.min_score * 1.1:
                    target_item.setBackground(QColor(200, 255, 200))  # 绿色 - 要求低
                else:
                    target_item.setBackground(QColor(255, 255, 200))  # 黄色 - 中等
                
                self.optimization_table.setItem(i, 4, target_item)
                
                # 说明
                if target_score >= course.max_score * 0.9:
                    note = "需要全力以赴"
                elif target_score <= course.min_score * 1.1:
                    note = "保持正常水平即可"
                else:
                    note = "需要认真准备"
                self.optimization_table.setItem(i, 5, QTableWidgetItem(note))
        
        # 建议
        suggestions_text = "\n".join(result['suggestions'])
        
        if not result['feasible'] and result.get('adjustments'):
            suggestions_text += "\n\n" + "="*50 + "\n"
            suggestions_text += "💡 调整建议：\n\n"
            for i, option in enumerate(result['adjustments']['options'], 1):
                suggestions_text += f"{i}. {option['description']}\n"
                suggestions_text += f"   可行性: {option['feasibility']}\n\n"
        
        self.suggestions_text.setPlainText(suggestions_text)
    
    def export_json(self):
        """导出JSON"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出JSON", "", "JSON Files (*.json)"
        )
        if filepath:
            try:
                self.data_manager.export_to_json(filepath)
                QMessageBox.information(self, "成功", "数据已成功导出！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")
    
    def import_json(self):
        """导入JSON"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "导入JSON", "", "JSON Files (*.json)"
        )
        if filepath:
            reply = QMessageBox.question(
                self, "导入模式",
                "是否合并到现有数据？\n\n"
                "点击 Yes 合并数据（保留现有数据）\n"
                "点击 No 替换数据（清空现有数据）",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Cancel:
                return
            
            merge = (reply == QMessageBox.StandardButton.Yes)
            
            try:
                self.data_manager.import_from_json(filepath, merge)
                self.load_data()
                QMessageBox.information(self, "成功", "数据已成功导入！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败：{str(e)}\n\n请确保JSON格式正确。")
    
    def show_llm_guide(self):
        """显示LLM使用指南"""
        dialog = LLMGuideDialog(self)
        dialog.exec()
    
    def load_data(self):
        """加载数据到界面"""
        self.refresh_completed_table()
        self.refresh_planned_table()
        
        if self.data_manager.target_score:
            self.target_score_input.setValue(self.data_manager.target_score)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
