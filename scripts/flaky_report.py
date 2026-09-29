import argparse
import collections
import glob
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

FINAL_STATUSES = {"passed", "failed", "broken", "skipped"}


def load_results(results_dir):
    results = []
    pattern = os.path.join(results_dir, "*result.json")
    for path in glob.glob(pattern):
        with io.open(path, encoding="utf-8") as f:
            results.append(json.load(f))
    return results

def find_flaky(results):
    by_history = collections.defaultdict(list)
    for result in results:
        by_history[result.get("historyId") or result.get("uuid")].append(result)

    flaky = []
    for entries in by_history.values():
        statuses = {e.get("status") for e in entries}
        if len(entries) > 1 and any(s in {"failed", "broken"} for s in statuses):
            failed = [e for e in entries if e.get("status") in {"failed", "broken"}]
            flaky.append((entries[0].get("fullName", "unknown"), len(entries) - len(failed), len(failed)))
    return flaky


def main():
    parser = argparse.ArgumentParser(description="Отчёт по flaky-тестам")
    parser.add_argument("--results", default="allure-results", help="папка с результатами Allure")
    parser.add_argument("--max-flaky-percent", type=float, default=20.0, help="допустимый процент flaky")
    parser.add_argument("--allow-empty", action="store_true", help="не падать, если результатов нет")
    args = parser.parse_args()

    results = load_results(args.results)
    if not results:
        print(f"Нет результатов в {args.results}")
        if args.allow_empty:
            return 0
        print("Проверка невозможна: пустой каталог результатов. Это ошибка сборки, а не успех.")
        return 2

    unique = {r.get("historyId") or r.get("uuid") for r in results}
    flaky = find_flaky(results)
    percent = round(len(flaky) * 100 / len(unique), 1)

    print(f"Всего тестов: {len(unique)}")
    print(f"Flaky: {len(flaky)} ({percent}%)")
    for name, passed, failed in flaky:
        print(f"  - {name}: упало {failed}, прошло {passed}")

    if percent > args.max_flaky_percent:
        print(f"Порог превышен: {percent}% > {args.max_flaky_percent}%")
        return 1

    print(f"Порог в норме: {percent}% <= {args.max_flaky_percent}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
