#!/usr/bin/env python3
"""
Minimal terminal client for testing an OpenAI-compatible model relay.

It sends the fixed candy puzzle prompt to one selected model or to every
available model, then saves all replies to a txt file.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


DEFAULT_BASE_URL = "https://a6api.com/v1"
DEFAULT_PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs"

CANDY_PROMPT = """在一个不透明的黑袋子里装有三种口味的糖果：苹果味、桃子味和西瓜味。每种口味的糖果都有两种形状：圆形和五角星形。参赛者摸糖时不能分辨口味，但可以凭手感分辨形状，并据此选择摸取圆形或五角星形糖果。

袋中各类糖果数量如下：

圆形：苹果味 7 颗，桃子味 9 颗，西瓜味 8 颗；
五角星形：苹果味 7 颗，桃子味 6 颗，西瓜味 4 颗。

问：参赛者在活动前至少要决定摸出多少颗糖，才能保证手中至少有一对糖果，其中一颗是苹果味、另一颗是桃子味，且两颗糖果的形状不同？
也就是说，至少保证出现以下两种情况之一：

圆形苹果味与五角星形桃子味；
圆形桃子味与五角星形苹果味。"""

EXPECTED_ANSWER = 21
ResultTuple = tuple[str, str, str, float]
ResultCallback = Callable[[ResultTuple, int, int], None]


class ApiError(RuntimeError):
    pass


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def request_json(
    method: str,
    base_url: str,
    path: str,
    api_key: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    url = f"{normalize_base_url(base_url)}{path}"
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "CandyModelCLI/1.0",
    }
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ApiError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"Network error: {exc.reason}") from exc

    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ApiError(f"Response is not JSON: {data[:500]}") from exc
    if not isinstance(parsed, dict):
        raise ApiError(f"Unexpected response shape: {type(parsed).__name__}")
    return parsed


def list_models(base_url: str, api_key: str) -> list[str]:
    data = request_json("GET", base_url, "/models", api_key)
    models = []
    for item in data.get("data", []):
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            models.append(item["id"])
        elif isinstance(item, str):
            models.append(item)
    return sorted(set(models))


def call_model(base_url: str, api_key: str, model: str, temperature: float) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是严谨的数学推理助手。请给出清晰、简洁的中文推理。"},
            {"role": "user", "content": CANDY_PROMPT},
        ],
        "temperature": temperature,
    }
    data = request_json("POST", base_url, "/chat/completions", api_key, payload=payload)
    choices = data.get("choices")
    if not choices or not isinstance(choices, list):
        raise ApiError(f"No choices in response: {json.dumps(data, ensure_ascii=False)[:500]}")
    message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return content.strip()
    text = choices[0].get("text") if isinstance(choices[0], dict) else None
    if isinstance(text, str):
        return text.strip()
    raise ApiError(f"No text content in response: {json.dumps(data, ensure_ascii=False)[:500]}")


def default_output_file() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_DIR / f"candy_model_replies_{timestamp}.txt"


def append_result(path: Path, model: str, status: str, content: str, elapsed: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write("=" * 88 + "\n")
        f.write(f"Time: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"Model: {model}\n")
        f.write(f"Status: {status}\n")
        f.write(f"Elapsed seconds: {elapsed:.2f}\n")
        f.write("-" * 88 + "\n")
        f.write(content.strip() + "\n\n")


def choose_model(models: list[str]) -> str | None:
    if not models:
        print("没有获取到可用模型。")
        return None
    print("\n可用模型：")
    for idx, model in enumerate(models, start=1):
        print(f"{idx:>3}. {model}")
    while True:
        raw = input("\n请输入模型序号，或直接输入模型名（q 退出）：").strip()
        if raw.lower() in {"q", "quit", "exit"}:
            return None
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(models):
                return models[idx - 1]
        if raw:
            return raw
        print("输入无效，请重试。")


def run_one(base_url: str, api_key: str, model: str, output: Path, temperature: float) -> None:
    print(f"\n正在测试模型：{model}")
    start = time.time()
    try:
        reply = call_model(base_url, api_key, model, temperature)
        elapsed = time.time() - start
        append_result(output, model, "ok", reply, elapsed)
        print(f"完成：{model}，耗时 {elapsed:.2f}s，已保存到 {output}")
        print("\n模型回复预览：")
        print(reply[:1000] + ("..." if len(reply) > 1000 else ""))
    except Exception as exc:
        elapsed = time.time() - start
        append_result(output, model, "error", str(exc), elapsed)
        print(f"失败：{model}，错误已保存到 {output}")
        print(str(exc))


def call_and_capture(base_url: str, api_key: str, model: str, temperature: float) -> tuple[str, str, str, float]:
    start = time.time()
    try:
        reply = call_model(base_url, api_key, model, temperature)
        return model, "ok", reply, time.time() - start
    except Exception as exc:
        return model, "error", str(exc), time.time() - start


def extract_final_answer(content: str) -> int | None:
    """Extract a conservative final numeric answer from a model reply."""
    tail = content[-1600:]
    patterns = (
        r"(?:最终答案|最终结果|答案|至少(?:需要|要)?|合计|总计)\s*(?:是|为|：|:)?\s*[^\d]{0,12}(\d+)\s*(?:颗|个)?",
        r"(?:final answer|answer|minimum|total)\s*(?:is|:|=)?\s*[^\d]{0,12}(\d+)",
        r"\\boxed\{\s*(\d+)\s*\}",
    )
    candidates: list[tuple[int, int]] = []
    for pattern in patterns:
        for match in re.finditer(pattern, tail, flags=re.IGNORECASE):
            candidates.append((match.start(), int(match.group(1))))
    if candidates:
        return max(candidates, key=lambda item: item[0])[1]

    final_line_numbers = re.findall(r"(?m)^\s*(\d+)\s*(?:颗|个)?[。.!！]?\s*$", tail)
    return int(final_line_numbers[-1]) if final_line_numbers else None


def run_models(
    base_url: str,
    api_key: str,
    models: list[str],
    temperature: float,
    concurrency: int,
    on_result: ResultCallback | None = None,
) -> list[ResultTuple]:
    """Run selected models concurrently and report results as they complete."""
    if not models:
        return []
    workers = max(1, min(concurrency, len(models)))
    results: list[ResultTuple] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(call_and_capture, base_url, api_key, model, temperature): model
            for model in models
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            results.append(result)
            if on_result:
                on_result(result, completed, len(models))
    return results


def run_all(
    base_url: str,
    api_key: str,
    models: list[str],
    output: Path,
    temperature: float,
    concurrency: int,
) -> None:
    if not models:
        print("没有模型可测试。")
        return
    workers = max(1, min(concurrency, len(models)))
    print(f"\n将测试 {len(models)} 个模型，并发数 {workers}，结果写入：{output}")

    def report(result: ResultTuple, completed: int, total: int) -> None:
        model, status, content, elapsed = result
        append_result(output, model, status, content, elapsed)
        print(f"[{completed}/{total}] {model}: {status} ({elapsed:.2f}s)")

    run_models(base_url, api_key, models, temperature, workers, report)


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def read_api_key(args_key: str | None) -> str:
    load_dotenv(DEFAULT_PROJECT_DIR / ".env")
    api_key = args_key or os.getenv("A6API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key
    return getpass.getpass("请输入 API Key（输入时不会显示，直接回车退出）：").strip()


def interactive(args: argparse.Namespace, api_key: str) -> int:
    output = Path(args.output) if args.output else default_output_file()
    base_url = args.base_url
    models: list[str] = []

    while True:
        print("\n=== Candy Model CLI ===")
        print("1. 获取/刷新可用模型")
        print("2. 选择一个模型测试")
        print("3. 测试全部可用模型")
        print("4. 查看固定 prompt")
        print("5. 退出")
        choice = input("请选择（直接回车默认 2）：").strip() or "2"

        if choice == "1":
            try:
                models = list_models(base_url, api_key)
                print(f"获取到 {len(models)} 个模型。")
                for model in models:
                    print(f"- {model}")
            except Exception as exc:
                print(f"获取模型失败：{exc}")
        elif choice == "2":
            if not models:
                try:
                    models = list_models(base_url, api_key)
                except Exception as exc:
                    print(f"获取模型失败：{exc}")
                    continue
            model = choose_model(models)
            if model:
                run_one(base_url, api_key, model, output, args.temperature)
        elif choice == "3":
            if not models:
                try:
                    models = list_models(base_url, api_key)
                except Exception as exc:
                    print(f"获取模型失败：{exc}")
                    continue
            confirm = input(f"确认调用全部 {len(models)} 个模型？这可能产生费用。（y/N）：").strip().lower()
            if confirm == "y":
                run_all(base_url, api_key, models, output, args.temperature, args.concurrency)
        elif choice == "4":
            print("\n" + CANDY_PROMPT)
        elif choice == "5":
            print("再见。")
            return 0
        else:
            print("请输入 1-5。")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test A6API/OpenAI-compatible models with the candy puzzle.")
    parser.add_argument("--base-url", default=os.getenv("A6API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--api-key", help="API key. Prefer A6API_KEY env var instead of passing secrets in shell history.")
    parser.add_argument("--output", help="Txt output path. Defaults to outputs/candy_model_replies_<timestamp>.txt")
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--concurrency", type=int, default=10, help="Max parallel requests for --all. Default: 10.")
    parser.add_argument("--list", action="store_true", help="List available models and exit.")
    parser.add_argument("--model", help="Call one selected model and exit.")
    parser.add_argument("--all", action="store_true", help="Call every available model and exit.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    api_key = read_api_key(args.api_key)
    if not api_key:
        print("缺少 API Key。", file=sys.stderr)
        return 2

    output = Path(args.output) if args.output else default_output_file()

    try:
        if args.list:
            for model in list_models(args.base_url, api_key):
                print(model)
            return 0
        if args.model:
            run_one(args.base_url, api_key, args.model, output, args.temperature)
            return 0
        if args.all:
            models = list_models(args.base_url, api_key)
            run_all(args.base_url, api_key, models, output, args.temperature, args.concurrency)
            return 0
        return interactive(args, api_key)
    except Exception as exc:
        print(f"运行失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
