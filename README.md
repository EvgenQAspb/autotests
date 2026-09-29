# Автотесты с Allure Report

![tests](badges/tests.svg)

Отчёт последнего прогона: <https://evgenqaspb.github.io/autotests/>

## Быстрый старт

```powershell
pip install -r requirements-dev.txt

# mock-api для интеграционных тестов
python -m mock_api.app

# в другом терминале
pytest
allure serve allure-results
```

## Слои тестов

| Слой | Маркер | Команда | Зависимости |
|------|--------|---------|-------------|
| unit | `unit` | `pytest -m unit` | нет |
| integration | `integration` | `pytest -m integration` | mock-api на `localhost:5000` |
| e2e | `e2e` | `pytest -m e2e` | Playwright + Chromium |

Дополнительно: `smoke`, `regression`, `auth`, `flaky`, `serial`.

## Локальный запуск

```powershell
pytest                        # всё, параллельно через xdist
pytest -m smoke               # только быстрые
pytest -m "smoke and not e2e" # смоук без браузера
pytest -n 0                   # без параллелизма, для отладки
pytest --reruns 5             # больше ретраев
pytest -m e2e --headed        # браузер виден
```

## Отчёт Allure

```powershell
allure serve allure-results                          # локально с автообновлением
allure generate allure-results -o allure-report --clean
python make_badge.py                                 # бейдж для README
python scripts/flaky_report.py --max-flaky-percent 20  # контроль флаки
```

`conftest.py` прикладывает скриншот страницы в отчёт при падении e2e-теста.

## Проверка, что всё работает

```powershell
python scripts/verify.py            # 21 проверка: зависимости, слои, Allure, CI, Docker
python scripts/verify.py --skip e2e # без браузерных тестов (быстрее)
```

Скрипт сам поднимает mock-api, гоняет каждый слой, генерирует отчёт и бейдж,
поднимает контейнер mock-api и проверяет e2e через Playwright Server.
Код возврата: `0` — всё здорово, `1` — есть провалы.

## Docker

```powershell
docker compose up -d --build mock-api   # только API
docker compose up -d playwright-server  # удалённые браузеры
docker compose down -v
```

Чтобы гонять e2e через удалённый Playwright Server вместо локального Chromium:

```powershell
$env:PW_TEST_CONNECT_WS = "ws://localhost:3000/"
pytest -m e2e
```

Grid (`run-pw-grid.sh`) из образов Playwright удалён, официальная замена —
`playwright run-server`, он и поднят в `docker-compose.yml`.

## Проверка, что CI собирается

Три уровня — от быстрого к полному.

**1. Статика (секунды)** — ловит опечатки в YAML и shell-скриптах:

```powershell
docker run --rm -v "${PWD}:/repo" -w /repo rhysd/actionlint:latest
```

**2. Локальный прогон джобы** — реально выполняет шаги в контейнере:

```powershell
# act скачивается один раз
Invoke-WebRequest -Uri https://github.com/nektos/act/releases/latest/download/act_Windows_x86_64.zip -OutFile $env:TEMP\act.zip
Expand-Archive $env:TEMP\act.zip $env:TEMP\actbin -Force

& $env:TEMP\actbin\act.exe -W .github/workflows/tests.yml -j unit `
  -P ubuntu-latest=catthehacker/ubuntu:act-latest --pull=false
```

`unit` — самая быстрая джоба и она покрывает установку Allure, зависимостей и генерацию отчёта.
Поддерживается `-j integration`, `-j e2e`. Шаг `upload-artifact` в act всегда падает с
`Unable to get the ACTIONS_RUNTIME_TOKEN` — это особенность act, на реальном CI он работает.

**3. На GitHub** — `git push` в ветку `main` или `develop`, дальше вкладка **Actions**.
Или без пуша: `gh workflow run tests.yml`.

Что стоит помнить про локальный запуск: `integration` и `e2e` внутри act не повторяют
поведение GitHub-раннера — сервисы там поднимаются на самом раннере, поэтому `localhost:5000`
внутри контейнера act недостижим. Эти джобы проверяйте пунктом 3 или через `python scripts/verify.py`.

## CI

`.github/workflows/tests.yml` — пайплайн с джобами:

- `unit` — быстрые тесты на каждом PR
- `integration` — mock-api поднимается через `docker compose` внутри джобы
- `e2e` — матрица из 2 шардов, `--dist=loadfile`
- `smoke` — только на PR, после `unit`
- `history` — собирает один Allure-отчёт из всех артефактов
- `quality-gate` — валит сборку, если флаки больше порога

Артефакты `allure-report` хранятся 30 дней, промежуточные результаты — 14.

## Структура

```
mock_api/app.py            mock API для интеграционных тестов
scripts/verify.py          полная проверка окружения (23 шага)
scripts/flaky_report.py    отчёт и контроль флаки
scripts/install_allure.sh  установка Allure CLI локально
make_badge.py              генератор SVG-бейджа
.github/actions/setup-allure  composite action: Java + кэш + Allure CLI
Dockerfile                 образ с Playwright для прогонов
Dockerfile.mock            лёгкий образ mock-api
docker-compose.yml         mock-api + Playwright Server
conftest.py                фикстуры, скриншоты при падении
pytest.ini                 маркеры, xdist, ретраи, alluredir
```
