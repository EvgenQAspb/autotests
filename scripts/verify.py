"""Проверка всего окружения автотестов.

Запуск:
    python scripts/verify.py
    python scripts/verify.py --skip e2e,docker

Коды возврата: 0 — все проверки прошли (SKIP допустим), 1 — есть FAIL.
"""

import argparse
import glob
import importlib.util
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from contextlib import contextmanager

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = sys.executable
RESULTS_DIR = os.path.join(ROOT, "allure-results")
REPORT_DIR = os.path.join(ROOT, "allure-report")
BADGE_PATH = os.path.join(ROOT, "badges", "tests.svg")
API_PORT = 5000
API_URL = f"http://localhost:{API_PORT}"
EXPECTED_MARKERS = ["unit", "integration", "e2e", "smoke", "regression", "auth", "flaky", "serial"]

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

results = []


def report(status, name, detail=""):
    results.append((status, name, detail))
    color = {"PASS": GREEN, "FAIL": RED, "SKIP": YELLOW}[status]
    print(f"{color}[{status}]{RESET} {name}" + (f"\n       {detail}" if detail else ""))


def run(args, **kwargs):
    return subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        **kwargs,
    )


def pytest(args, label):
    proc = run([PYTHON, "-m", "pytest", *args])
    tail = (proc.stdout or "").strip().splitlines()
    summary = tail[-1] if tail else ""
    if proc.returncode == 0:
        report("PASS", label, summary)
    else:
        report("FAIL", label, summary or (proc.stderr or "").strip()[-500:])
    return proc.returncode == 0


def port_open(port):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("localhost", port)) == 0


def wait_for_api(timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{API_URL}/health", timeout=1) as r:
                if r.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    return False


@contextmanager
def mock_api():
    if port_open(API_PORT):
        report("SKIP", "mock-api поднимается", f"порт {API_PORT} уже занят, используем существующий")
        yield False
        return
    proc = subprocess.Popen(
        [PYTHON, "-m", "mock_api.app"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        yield True
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def run_pytest_with_api(args, label):
    env = os.environ.copy()
    env["API_BASE_URL"] = API_URL
    proc = subprocess.run(
        [PYTHON, "-m", "pytest", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    tail = [l for l in (proc.stdout or "").strip().splitlines() if l.strip()]
    summary = tail[-1] if tail else ""
    report("PASS" if proc.returncode == 0 else "FAIL", label, summary or (proc.stderr or "").strip()[-300:])
    return proc.returncode == 0


def check_deps():
    missing = []
    for module, package in [
        ("pytest", "pytest"),
        ("allure_commons", "allure-pytest"),
        ("xdist", "pytest-xdist"),
        ("pytest_rerunfailures", "pytest-rerunfailures"),
        ("pytest_playwright", "pytest-playwright"),
        ("requests", "requests"),
        ("flask", "flask"),
    ]:
        if importlib.util.find_spec(module) is None:
            missing.append(package)
    if missing:
        report("FAIL", "Зависимости установлены", "нет: " + ", ".join(missing))
    else:
        report("PASS", "Зависимости установлены")


def check_allure_cli():
    exe = shutil.which("allure") or shutil.which("allure.bat")
    if not exe:
        report("FAIL", "Allure CLI доступен", "не найден в PATH, нужен Java 17+")
        return
    proc = run([exe, "--version"])
    report("PASS" if proc.returncode == 0 else "FAIL", "Allure CLI доступен", proc.stdout.strip())


def check_java():
    proc = run(["java", "-version"])
    report("PASS" if proc.returncode == 0 else "SKIP", "Java 17+", proc.stderr.strip().splitlines()[0] if proc.stderr else "")


def check_markers():
    proc = run([PYTHON, "-m", "pytest", "--markers"])
    registered = {
        line.split(":", 1)[0].replace("@pytest.mark.", "").strip()
        for line in proc.stdout.splitlines()
        if line.startswith("@")
    }
    missing = [m for m in EXPECTED_MARKERS if m not in registered]
    if missing:
        report("FAIL", "Маркеры зарегистрированы", "нет: " + ", ".join("@" + m for m in missing))
    else:
        report("PASS", "Маркеры зарегистрированы", ", ".join("@" + m for m in EXPECTED_MARKERS))


def check_collect():
    proc = run([PYTHON, "-m", "pytest", "--collect-only", "-q"])
    if proc.returncode != 0:
        report("FAIL", "Тесты собираются", (proc.stdout or proc.stderr).strip()[-400:])
        return
    lines = [l for l in (proc.stdout or "").splitlines() if "test" in l and "::" in l]
    report("PASS", "Тесты собираются", f"собрано {len(lines)}")


def check_unit():
    pytest(["-m", "unit", "-q", "-n", "auto"], "unit-слой проходит")


def check_integration():
    with mock_api():
        if not wait_for_api():
            report("FAIL", "mock-api отвечает на /health", "сервис не поднялся за 20с")
            return
        report("PASS", "mock-api отвечает на /health", API_URL)
        run_pytest_with_api(["-m", "integration", "-q", "-n", "auto"], "integration-слой проходит")


def check_e2e():
    proc = pytest(["-m", "e2e", "-q", "-n", "2"], "e2e-слой проходит (Playwright)")


def check_allure_artifacts():
    shutil.rmtree(RESULTS_DIR, ignore_errors=True)
    with mock_api():
        wait_for_api()
        ok = run_pytest_with_api(
            ["-q", "--alluredir=allure-results"],
            "Полный прогон с --alluredir",
        )
    if not ok:
        return

    files = glob.glob(os.path.join(RESULTS_DIR, "*result.json"))
    statuses = {}
    for path in files:
        with io.open(path, encoding="utf-8") as f:
            status = json.load(f).get("status", "unknown")
            statuses[status] = statuses.get(status, 0) + 1
    if not files:
        report("FAIL", "Allure-результаты собраны", "нет *result.json")
    else:
        report("PASS", "Allure-результаты собраны", f"{len(files)} шт., статусы: {statuses}")

    steps = 0
    labels = 0
    for path in files:
        with io.open(path, encoding="utf-8") as f:
            data = json.load(f)
        steps += len(data.get("steps", []))
        labels += len({label["name"] for label in data.get("labels", [])})
    report("PASS" if steps else "SKIP", "Шаги и лейблы в отчёте", f"steps={steps}, уникальных лейблов={labels}")


def check_report():
    exe = shutil.which("allure") or shutil.which("allure.bat")
    if not exe:
        report("SKIP", "Allure-отчёт генерируется", "нет CLI")
        return
    proc = run([exe, "generate", RESULTS_DIR, "-o", REPORT_DIR, "--clean"])
    index = os.path.join(REPORT_DIR, "index.html")
    if proc.returncode == 0 and os.path.isfile(index):
        report("PASS", "Allure-отчёт генерируется", f"{REPORT_DIR}/index.html")
    else:
        report("FAIL", "Allure-отчёт генерируется", (proc.stderr or "").strip()[-300:])


def check_badge():
    proc = run([PYTHON, "make_badge.py"])
    if proc.returncode == 0 and os.path.isfile(BADGE_PATH):
        report("PASS", "Бейдж генерируется", os.path.relpath(BADGE_PATH, ROOT))
        return
    report("FAIL", "Бейдж генерируется", (proc.stderr or "").strip()[-300:])


def check_flaky():
    proc = run([PYTHON, "scripts/flaky_report.py", "--results", RESULTS_DIR, "--max-flaky-percent", "20"])
    tail = [l for l in (proc.stdout or "").splitlines() if l.strip()]
    report("PASS" if proc.returncode == 0 else "FAIL", "Отчёт по флаки", " / ".join(tail[:3]))


def check_docker():
    proc = run(["docker", "version", "--format", "{{.Server.Version}}"])
    if proc.returncode != 0:
        report("SKIP", "Docker-демон доступен", "демон не запущен — compose-проверки пропущены")
        return
    report("PASS", "Docker-демон доступен", f"server {proc.stdout.strip()}")
    proc = run(["docker", "compose", "config", "--quiet"])
    if proc.returncode == 0:
        report("PASS", "docker-compose.yml валиден")
    else:
        report("FAIL", "docker-compose.yml валиден", (proc.stderr or "").strip()[-300:])
    if "server" in os.environ.get("VERIFY_FLAGS", ""):
        report("SKIP", "docker compose up mock-api (server-режим)")
        return
    proc = run(["docker", "compose", "up", "-d", "--build", "mock-api"])
    if proc.returncode != 0:
        report("FAIL", "docker compose up mock-api", (proc.stderr or proc.stdout).strip()[-300:])
        return
    report("PASS", "docker compose up mock-api", "контейнер поднят")
    ok = run_pytest_with_api(["-m", "integration", "-q", "-n", "0"], "integration против контейнера")
    run(["docker", "compose", "down", "-v"])
    if not ok:
        return
    check_playwright_server()


def check_playwright_server():
    proc = run(["docker", "compose", "up", "-d", "playwright-server"])
    if proc.returncode != 0:
        report("FAIL", "Playwright Server поднимается", (proc.stderr or proc.stdout).strip()[-300:])
        return
    report("PASS", "Playwright Server поднимается", "первый запуск тянет образ, может занять пару минут")

    endpoint = os.getenv("PW_TEST_CONNECT_WS", "ws://localhost:3000/")
    deadline = time.time() + 300
    ready = False
    while time.time() < deadline:
        status = run(["docker", "compose", "ps", "--status", "running", "playwright-server"])
        if "playwright-server" in status.stdout:
            ready = True
            break
        time.sleep(5)

    if not ready:
        report("FAIL", "Playwright Server живой", "сервис не поднялся за 5 минут")
        run(["docker", "compose", "logs", "--tail", "30", "playwright-server"])
        run(["docker", "compose", "down", "-v"])
        return

    env = os.environ.copy()
    env["PW_TEST_CONNECT_WS"] = endpoint
    result = subprocess.run(
        [PYTHON, "-m", "pytest", "-m", "e2e", "-q", "-n", "0"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    tail = [l for l in (result.stdout or "").strip().splitlines() if l.strip()]
    report(
        "PASS" if result.returncode == 0 else "FAIL",
        "e2e через удалённый сервер",
        tail[-1] if tail else (result.stderr or "").strip()[-300:],
    )
    if result.returncode != 0:
        run(["docker", "compose", "logs", "--tail", "30", "playwright-server"])
    run(["docker", "compose", "down", "-v"])


def check_workflow():
    spec = importlib.util.find_spec("yaml")
    path = os.path.join(ROOT, ".github", "workflows", "tests.yml")
    if not os.path.isfile(path):
        report("FAIL", "CI-пайплайн существует", "нет .github/workflows/tests.yml")
        return
    if spec is None:
        report("SKIP", "CI-пайплайн валиден", "не хватает pyyaml для проверки синтаксиса")
        return
    import yaml

    with io.open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    jobs = list((data or {}).get("jobs", {}))
    expected = ["unit", "integration", "e2e", "history", "quality-gate"]
    missing = [j for j in expected if j not in jobs]
    if missing:
        report("FAIL", "CI-пайплайн валиден", f"нет джобов: {missing}")
    else:
        report("PASS", "CI-пайплайн валиден", f"джобы: {', '.join(jobs)}")


def check_actionlint():
    if run(["docker", "version", "--format", "{{.Server.Version}}"]).returncode != 0:
        report("SKIP", "actionlint", "нужен Docker-демон")
        return
    image = "rhysd/actionlint:latest"
    if run(["docker", "image", "inspect", image]).returncode != 0:
        report("SKIP", "actionlint", f"образ {image} не локально, нужен интернет для pull")
        return
    proc = subprocess.run(
        ["docker", "run", "--rm", "-v", f"{ROOT}:/repo", "-w", "/repo", image],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode == 0:
        report("PASS", "actionlint", "ошибок и предупреждений нет")
    else:
        report("FAIL", "actionlint", (proc.stdout or proc.stderr).strip()[-600:])


CHECKS = [
    ("deps", check_deps),
    ("allure", check_allure_cli),
    ("java", check_java),
    ("markers", check_markers),
    ("collect", check_collect),
    ("unit", check_unit),
    ("integration", check_integration),
    ("e2e", check_e2e),
    ("allure_artifacts", check_allure_artifacts),
    ("report", check_report),
    ("badge", check_badge),
    ("flaky", check_flaky),
    ("workflow", check_workflow),
    ("actionlint", check_actionlint),
    ("docker", check_docker),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip", default="", help="список проверок через запятую, например: e2e,docker")
    args = parser.parse_args()
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}

    print("=" * 60)
    print("Проверка окружения автотестов")
    print("=" * 60)

    for name, func in CHECKS:
        if name in skip:
            report("SKIP", f"{name}: пропущено пользователем")
            continue
        try:
            func()
        except Exception as exc:
            report("FAIL", name, f"{type(exc).__name__}: {exc}")

    print("=" * 60)
    passed = sum(1 for s, _, _ in results if s == "PASS")
    failed = [n for s, n, _ in results if s == "FAIL"]
    skipped = sum(1 for s, _, _ in results if s == "SKIP")
    print(f"PASS: {passed} | FAIL: {len(failed)} | SKIP: {skipped}")
    if failed:
        print("Провалено: " + ", ".join(failed))
        return 1
    print("Всё работает.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
