# Candy Model CLI

一个极简终端项目：调用 `https://a6api.com/v1` 这类 OpenAI-compatible 中转站，向模型发送固定“糖果问题” prompt，并把返回结果保存到 txt 文件。

## 使用

当前目录已支持自动读取 `.env`，所以直接运行即可：

```bash
cd /Users/lizhixin/Documents/Codex/2026-08-15/https-a6api-com-sk-f5nodgcdilnw50lhwmimk8gup6v8mdtzamsjkpdtpa5xsma0/work/candy_model_cli
python3 main.py
```

默认会进入交互菜单，支持：

- 获取/刷新全部可用模型
- 选择某个模型测试
- 测试全部可用模型
- 查看固定 prompt

启动后直接回车，会默认进入“选择一个模型测试”。

结果默认保存到项目根目录的 `outputs/candy_model_replies_时间戳.txt`。

## 非交互用法

列出模型：

```bash
python3 main.py --list
```

测试单个模型：

```bash
python3 main.py --model "模型名"
```

测试全部模型：

```bash
python3 main.py --all
```

默认一次并行测试 10 个模型。需要调整并发数：

```bash
python3 main.py --all --concurrency 5
```

指定输出文件：

```bash
python3 main.py --model "模型名" --output ../../outputs/result.txt
```

如果你的中转站地址不是默认的 `https://a6api.com/v1`：

```bash
A6API_BASE_URL="https://example.com/v1" A6API_KEY="你的 API Key" python3 main.py
```

## 说明

- 不依赖第三方包，只使用 Python 标准库。
- `.env` 已在 `.gitignore` 中，不会被误提交。
- 默认 temperature 为 `0`，便于比较不同模型的稳定推理。
- `--all` 会真实调用所有可用模型，默认 10 并发，可能产生费用；交互模式下会二次确认。
