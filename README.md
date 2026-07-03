# ReAct Agent Demo

一个用于学习 AI Agent 工作原理的 ReAct (Reasoning + Acting) 示例项目。

## 特性

- 🤖 **ReAct 模式** - 完整的思考 → 行动 → 观察循环
- 🛠️ **内置工具** - 文件读写、Shell 命令、Python REPL
- 🔒 **安全设计** - 默认白名单 + 操作确认
- 📝 **日志保存** - 自动保存对话历史
- 🎨 **彩色输出** - 清晰的终端展示

## 快速开始

### 1. 安装依赖

使用 `uv` 安装依赖（推荐）：

```bash
uv venv
uv pip install -e .
```

或者使用 pip：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的 DOUBAO_API_KEY
```

API Key 从 [火山引擎控制台](https://console.volcengine.com/ark/) 获取。

### 3. 运行 Agent

**单次任务模式：**

```bash
python agent.py "列出当前目录的文件"
```

**交互模式：**

```bash
python agent.py
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--unsafe` | 关闭安全限制（谨慎使用） |
| `--quiet` | 简洁输出模式 |
| `--max-iter N` | 最大迭代次数（默认 10） |
| `--no-log` | 不保存对话日志 |

## 可用工具

- `read_file(file_path)` - 读取文件
- `write_file(file_path, content)` - 写入文件
- `list_dir(dir_path)` - 列出目录
- `run_shell(command)` - 执行 Shell 命令
- `python_repl(code)` - 执行 Python 代码

## 项目结构

```
dannis-agent-poc/
├── agent.py           # ReAct Agent 主程序
├── pyproject.toml     # 项目配置
├── .env.example       # 环境变量示例
├── .gitignore
├── README.md
└── logs/              # 对话日志目录（自动创建）
```

## ReAct 工作原理

```
用户问题
    ↓
Thought: 思考下一步做什么
    ↓
Action: 选择工具并执行
    ↓
Observation: 获取工具执行结果
    ↓
... (循环) ...
    ↓
Final Answer: 给出最终答案
```

## 示例

```
You: 创建一个名为 hello.txt 的文件，内容是 "Hello, ReAct Agent!"
━━━ ReAct Agent Started ━━━
User: 创建一个名为 hello.txt 的文件，内容是 "Hello, ReAct Agent!"

─── Step 1/10 ───
Thought: 我需要创建一个文件，使用 write_file 工具
Action: write_file
Params: {
  "file_path": "hello.txt",
  "content": "Hello, ReAct Agent!"
}
创建新文件 hello.txt? [y/N] y
Observation: Successfully wrote to hello.txt

─── Step 2/10 ───
Thought: 文件已创建成功，任务完成
Final Answer: 已成功创建 hello.txt 文件！
```

## 安全说明

默认模式下：
- 文件操作限制在项目目录内
- Shell 命令仅限白名单（`ls`, `cat`, `echo` 等）
- 危险操作需要确认

使用 `--unsafe` 可以关闭限制（仅在完全信任的环境中使用）。

## 学习建议

1. 先阅读 `agent.py` 代码，理解 ReAct 循环
2. 运行交互模式，观察思考过程
3. 尝试不同任务，理解工具使用
4. 修改和扩展工具，加深理解

## 许可证

MIT
