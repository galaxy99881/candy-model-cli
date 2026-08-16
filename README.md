# CandyBench Notebook: Visual Multi-Model Reasoning Probe

> 中文名：糖果智测 · Jupyter 可视化模型评测<br>
> Select relay models visually, run them in parallel, and keep every raw reply.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/UI-Jupyter-F37626?style=flat-square&logo=jupyter&logoColor=white)](CandyBench.ipynb)
[![Parallel](https://img.shields.io/badge/Parallel-10x_Default-7C3AED?style=flat-square)](#)
[![Relay](https://img.shields.io/badge/API-OpenAI_Compatible-111827?style=flat-square)](#)

## The Point

**Unwatered does not mean intelligent.**  
**不掺水，不等于智商高。**

CandyBench was built after a Veridrop relay test where the models looked "unwatered": responses were fluent, complete, and not obviously degraded. But the same models still failed a small reasoning puzzle in many different ways.

This project turns that observation into a repeatable Jupyter and terminal test.

It sends one fixed Chinese combinatorics prompt, collects every model reply, and saves the full sweep into a `.txt` report. No dashboard. No hidden scoring. Just raw model behavior.

## 核心发现

在一次 Veridrop 中转站模型测试中，模型整体看起来并没有被明显“掺水”：能正常输出、推理链条很长、格式也像样。

但这不代表它们真的会推理。

同一个糖果题下，模型给出的答案非常分散，出现过 `21`、`23`、`25`、`26`、`28`、`29`、`36`、`42` 等不同结论。很多回答文字很自信，过程也很长，但关键约束理解错了。

这就是 CandyBench 想展示的东西：

- 中转站可用，不等于模型可靠
- 输出流畅，不等于推理正确
- 没有明显降智，不等于智力测试能过
- 模型评测必须看可复现任务，而不是只看回答气质

## What The Test Checks

The built-in prompt is a candy puzzle:

- There are apple, peach, and watermelon candies.
- Each flavor has round and star-shaped candies.
- The player cannot feel flavor, but can choose shape by touch.
- The goal is to guarantee a cross-shape apple-peach pair.

Under the shape-selectable interpretation, the correct strategy is:

- draw `9` round candies
- draw `12` star-shaped candies
- total: `21`

Why this works:

- `9` round candies force at least one non-watermelon round candy, because there are only `8` round watermelon candies.
- `12` star candies force both a star apple and a star peach:
  - non-apple stars are `6 + 4 = 10`
  - non-peach stars are `7 + 4 = 11`
- If the round non-watermelon candy is apple, pair it with star peach.
- If it is peach, pair it with star apple.

So the expected answer is:

```txt
21 candies = 9 round + 12 star-shaped
```

## 中文答案基准

这个题不是简单地“最多拿多少颗还不出现组合”，因为参赛者可以凭手感选择形状。

正确保证方案是：

```txt
摸 9 颗圆形糖 + 12 颗五角星形糖 = 21 颗
```

证明很短：

- 圆形西瓜只有 8 颗，所以摸 9 颗圆形，必有苹果或桃子。
- 五角星非苹果最多 `6 + 4 = 10` 颗，所以摸 12 颗五角星，必有五角星苹果。
- 五角星非桃子最多 `7 + 4 = 11` 颗，所以摸 12 颗五角星，必有五角星桃子。
- 如果圆形里有苹果，就配五角星桃子。
- 如果圆形里有桃子，就配五角星苹果。

因此至少 `21` 颗可以保证成功。

## Why It Is Useful

CandyBench is not a full benchmark suite. It is a sharp little probe.

It helps answer a practical question:

> If a relay exposes dozens of models, which ones can actually follow a constrained reasoning problem?

The answer cannot be inferred from brand name, response length, or whether the relay feels "full power." You have to test.

## Features

- OpenAI-compatible relay support: `/v1/models` and `/v1/chat/completions`
- Jupyter model picker with search and checkboxes
- Select-all and clear controls for visible models
- Live progress for parallel runs
- Result table with parsed final-answer signal
- Response-time chart and expandable full replies
- Interactive terminal UI remains available
- One-model testing
- Full model sweep
- Default `10` parallel requests for `--all`
- Raw `.txt` report output
- Zero third-party dependencies for CLI; optional Notebook dependencies
- Local `.env` support for API keys

## Jupyter Quick Start

```bash
git clone https://github.com/galaxy99881/candy-model-cli.git
cd candy-model-cli
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-notebook.txt
```

Create a local `.env` file:

```bash
A6API_BASE_URL=https://a6api.com/v1
A6API_KEY=your_api_key_here
```

Start Jupyter Lab:

```bash
jupyter lab CandyBench.ipynb
```

Run the notebook cells from top to bottom. All configuration, API, concurrency, parsing, and widget code lives directly in `CandyBench.ipynb`, so it can be edited in place. When `.env` is present, CandyBench loads the model list automatically. Select models with checkboxes and click **运行测试**. The default concurrency is `10`.

The table classifies replies as `PASS`, `FAIL`, `UNKNOWN`, or `ERROR`. This is a conservative text parser, not a substitute for reviewing the full reply. Every response is still preserved in the TXT report.

## Terminal Quick Start

The original dependency-free terminal interface is still supported:

```bash
python3 main.py
```

Press `Enter` on the main menu to jump directly into model selection.

## Usage

List all available models:

```bash
python3 main.py --list
```

Test one model:

```bash
python3 main.py --model "gpt-4o-mini"
```

Test every available model:

```bash
python3 main.py --all
```

Change parallelism:

```bash
python3 main.py --all --concurrency 5
python3 main.py --all --concurrency 20
```

Write to a custom report:

```bash
python3 main.py --model "gpt-4o-mini" --output results.txt
```

Use another relay:

```bash
A6API_BASE_URL="https://example.com/v1" A6API_KEY="your_key" python3 main.py --list
```

## Report Format

```txt
========================================================================================
Time: 2026-08-15T17:10:44
Model: gpt-4o-mini
Status: ok
Elapsed seconds: 31.69
----------------------------------------------------------------------------------------
model reply...
```

Errors are saved too. A full sweep remains useful even when some relay channels time out, disconnect, or return `no_available_channel`.

## Design Philosophy

CandyBench intentionally stays small.

It does not rank models with a synthetic score. It does not hide the raw output. It does not pretend one puzzle is a universal IQ test.

It simply makes one thing hard to ignore:

> A model can be fluent, available, and apparently unwatered, while still failing a basic reasoning test.

## Notes

- Default temperature is `0`.
- `--all` makes real API calls to every available model and may consume credits.
- `.env` is ignored by git. Do not commit API keys.
- The built-in prompt is fixed on purpose, so runs are easier to compare.

## License

No license has been added yet.
