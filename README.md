# CandyBench CLI

> A clean terminal benchmark for comparing OpenAI-compatible relay models on one deceptively simple reasoning puzzle.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![No Dependencies](https://img.shields.io/badge/Dependencies-None-16A34A?style=flat-square)](#)
[![CLI](https://img.shields.io/badge/Interface-Terminal-111827?style=flat-square)](#)

CandyBench CLI is a tiny, zero-dependency command-line tool for testing every available model behind an OpenAI-compatible relay. It sends the same fixed Chinese reasoning prompt to each model, captures the response, and writes all results into a single text file for fast comparison.

The built-in prompt is the classic "candy puzzle": a small combinatorics problem that looks simple, but quickly exposes whether a model can reason carefully under constraints.

## Why This Exists

Model relays often expose dozens of models, but it is hard to know which ones are actually useful for reasoning tasks. CandyBench gives you a repeatable, low-friction way to compare them:

- same prompt
- same API route
- same temperature
- same output format
- optional 10-way parallel testing

No framework. No database. No dashboard. Just a terminal, a model list, and a clean `.txt` report.

## Highlights

- **OpenAI-compatible relay support**: works with `/v1/models` and `/v1/chat/completions`
- **Interactive terminal flow**: list models, choose one, or test all
- **Parallel model sweep**: `--all` runs 10 requests at a time by default
- **Single-file reports**: every success and failure is appended to one `.txt`
- **Zero dependencies**: built entirely on the Python standard library
- **Safe local secrets**: reads `.env`, which is ignored by git

## Quick Start

```bash
git clone https://github.com/galaxy99881/candy-model-cli.git
cd candy-model-cli
```

Create a local `.env` file:

```bash
A6API_BASE_URL=https://a6api.com/v1
A6API_KEY=your_api_key_here
```

Run the interactive CLI:

```bash
python3 main.py
```

Press `Enter` on the main menu to jump straight into model selection.

## Usage

List available models:

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

Tune parallelism:

```bash
python3 main.py --all --concurrency 5
python3 main.py --all --concurrency 20
```

Write to a custom report file:

```bash
python3 main.py --model "gpt-4o-mini" --output results.txt
```

Use another OpenAI-compatible relay:

```bash
A6API_BASE_URL="https://example.com/v1" A6API_KEY="your_key" python3 main.py --list
```

## Report Format

Each model result is appended like this:

```txt
========================================================================================
Time: 2026-08-15T17:10:44
Model: gpt-4o-mini
Status: ok
Elapsed seconds: 31.69
----------------------------------------------------------------------------------------
模型回复内容...
```

Failures are saved too, so a full sweep still produces an auditable report even when some models time out or disconnect.

## Built-In Prompt

CandyBench currently uses one fixed Chinese prompt about drawing candies from a black bag. The puzzle asks for the minimum number of candies needed to guarantee a cross-shape apple-peach pair.

That fixed prompt is intentional: it makes outputs easy to compare across models without prompt drift.

## Notes

- Default temperature is `0` for more stable comparisons.
- `--all` makes real API calls to every available model and may consume credits.
- The local `.env` file is ignored by git. Do not commit API keys.
- This project is intentionally small; it is designed to be easy to inspect, fork, and modify.

## License

No license has been added yet.
