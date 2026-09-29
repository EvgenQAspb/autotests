import glob
import io
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")

RESULTS_DIR = "allure-results"
BADGE_PATH = "badges/tests.svg"

COLORS = {
    "passed": "#4c1",
    "failed": "#e05d44",
    "broken": "#fe7d37",
    "skipped": "#9f9f9f",
}


def count_statuses():
    counts = {}
    for path in glob.glob(f"{RESULTS_DIR}/*result.json"):
        data = json.load(io.open(path, encoding="utf-8"))
        status = data.get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def make_svg(label, message, color):
    label_w = 7 * len(label) + 10
    message_w = 7 * len(message) + 10
    total_w = label_w + message_w
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="20">'
        f'<rect width="{label_w}" height="20" fill="#555"/>'
        f'<rect x="{label_w}" width="{message_w}" height="20" fill="{color}"/>'
        f'<g fill="#fff" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">'
        f'<text x="{label_w / 2}" y="14" text-anchor="middle">{label}</text>'
        f'<text x="{label_w + message_w / 2}" y="14" text-anchor="middle">{message}</text>'
        f"</g></svg>"
    )


def main():
    counts = count_statuses()
    if not counts:
        print("Нет результатов в allure-results, сначала запустите pytest")
        return

    total = sum(counts.values())
    passed = counts.get("passed", 0)
    percent = round(passed * 100 / total)
    color = COLORS["passed"] if percent == 100 else COLORS["failed"]

    pathlib.Path(BADGE_PATH).parent.mkdir(parents=True, exist_ok=True)
    badge = make_svg("tests", f"{percent}% passed", color)
    pathlib.Path(BADGE_PATH).write_text(badge, encoding="utf-8")

    print(f"{RESULTS_DIR}: {counts}")
    print(f"Бейдж записан в {BADGE_PATH}")


if __name__ == "__main__":
    main()
