import argparse
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

TREND_FILES = (
    "history-trend.json",
    "duration-trend.json",
    "retry-trend.json",
    "categories-trend.json",
)


def read_json(path):
    if not os.path.isfile(path):
        return None
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def history_file(report_dir, name):
    return os.path.join(report_dir, "history", name)


def merge_trends(previous_dir, report_dir):
    """Дописывает текущий прогон в конец трендов предыдущего отчёта."""
    merged = 0
    for name in TREND_FILES:
        old = read_json(history_file(previous_dir, name))
        new = read_json(history_file(report_dir, name))
        if not isinstance(old, list) or not isinstance(new, list):
            continue
        if not old:
            continue
        write_json(history_file(report_dir, name), old + new)
        merged += 1
    return merged


def merge_history(previous_dir, report_dir, max_runs):
    """Склеивает per-test историю, оставляя последние max_runs прогонов."""
    old = read_json(history_file(previous_dir, "history.json"))
    new = read_json(history_file(report_dir, "history.json"))
    if not isinstance(old, dict) or not isinstance(new, dict):
        return 0
    if not old:
        return 0

    combined = dict(old)
    for key, value in new.items():
        if key in combined and isinstance(value, dict) and isinstance(combined[key], dict):
            items = list(combined[key].get("items") or []) + list(value.get("items") or [])
            statistic = dict(combined[key].get("statistic") or {})
            statistic.update(value.get("statistic") or {})
            combined[key] = {"statistic": statistic, "items": items}
        else:
            combined[key] = value

    for key, value in combined.items():
        items = value.get("items") or []
        if max_runs and len(items) > max_runs:
            value["items"] = items[-max_runs:]

    write_json(history_file(report_dir, "history.json"), combined)
    return len(combined)


def main():
    parser = argparse.ArgumentParser(description="Склеивает историю Allure с прошлым отчётом")
    parser.add_argument("--previous", required=True, help="корень прошлого отчёта (с папкой history)")
    parser.add_argument("--report", required=True, help="корень свежего отчёта (с папкой history)")
    parser.add_argument("--max-runs", type=int, default=20, help="сколько прогонов хранить на тест")
    args = parser.parse_args()

    if not os.path.isdir(os.path.join(args.previous, "history")):
        print(f"Предыдущий отчёт не найден: {args.previous}. Отчёт будет без трендов.")
        return 0

    trends = merge_trends(args.previous, args.report)
    tests = merge_history(args.previous, args.report, args.max_runs)
    print(f"Трендов склеено: {trends}, тестов в истории: {tests}")
    if trends == 0:
        print("Внимание: тренды не найдены, история может остаться пустой.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
