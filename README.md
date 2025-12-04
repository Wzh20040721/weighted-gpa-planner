# 加权平均分规划助手 V2.0

> 使用运筹学优化算法，智能分配各科目标分数

## ✨ 核心特性

- 🎯 **智能优化** - 输入分数范围和难度，自动计算最优目标
- 📊 **运筹学算法** - 使用线性规划，最小化学习成本
- 💡 **智能建议** - 目标无法达成时提供调整方案
- 🎨 **可视化** - 颜色编码、难度标识一目了然
- 💾 **自动保存** - 数据自动持久化
- 📤 **导入导出** - 支持 JSON 格式

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行应用

```bash
python main.py
```

### 构建可执行文件

**Windows:**
```bash
build_windows.bat
```

**macOS/Linux:**
```bash
chmod +x build_macos.sh
./build_macos.sh
```

**使用 GitHub Actions（推荐）:**
- 无需本地构建环境
- 自动构建 Windows、macOS、Linux 三个平台
- 查看 [GitHub自动构建说明.md](GitHub自动构建说明.md)

## 📖 使用方法

### 1. 添加已修课程
- 输入课程名、学分、分数

### 2. 添加计划课程
- 课程名：例如"数据结构"
- 学分：例如 3
- **最低分**：保守估计能考多少（例如 70）
- **最高分**：乐观估计能考多少（例如 95）
- **难度系数**：0-1 之间
  - 0-0.3：简单 📗
  - 0.3-0.7：中等 📘
  - 0.7-1.0：困难 📕

### 3. 智能优化
- 设置目标 GPA
- 点击"开始智能优化"
- 查看最优分数分配

## 📊 优化算法

**目标函数：**
```
minimize: Σ(difficulty × (score - min_score))
```

**策略：**
- 简单课程 → 高目标分数（重点提分）
- 困难课程 → 最低要求（保证及格）

## 📁 项目结构

```
windsurf-project/
├── main.py                    # 主程序
├── requirements.txt           # 依赖
├── build.spec                 # 打包配置
├── build_windows.bat          # Windows 构建脚本
├── build_macos.sh            # macOS 构建脚本
├── example_data.json          # 示例数据
├── example_data_full.json     # 完整示例（61门课程）
├── README_V2.md              # 详细文档
├── 快速使用指南_V2.md         # 快速指南
└── .github/workflows/         # GitHub Actions 配置
```

## 📚 文档

- **[README_V2.md](README_V2.md)** - 完整技术文档
- **[快速使用指南_V2.md](快速使用指南_V2.md)** - 5分钟上手
- **[V2_更新说明.md](V2_更新说明.md)** - 版本更新详情
- **[GitHub自动构建说明.md](GitHub自动构建说明.md)** - 跨平台构建指南

## 🛠️ 技术栈

- Python 3.8+
- PyQt6 - GUI 框架
- scipy - 优化算法
- numpy - 数值计算
- PyInstaller - 打包工具

## 📦 依赖

```
PyQt6==6.6.1
scipy>=1.11.0
numpy>=1.24.0
pyinstaller==6.3.0
```

## 🌟 使用示例

**输入：**
- 已修课程：130+ 学分，当前 GPA 87.0
- 计划课程：
  - 数据结构（3学分，70-95分，难度0.8）
  - Web开发（2.5学分，80-98分，难度0.3）
- 目标 GPA：87

**输出：**
- Web开发：目标 95分 📗（简单，重点提分）
- 数据结构：目标 72分 📕（困难，保证及格）

## 🎯 适用场景

- 大学生成绩规划
- GPA 目标管理
- 学习时间优化分配
- 选课决策支持

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**让成绩规划更科学、更智能！** 🎓✨
