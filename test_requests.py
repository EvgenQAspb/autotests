import os

import allure
import pytest
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
CREATE_URL = f"{API_BASE_URL}/posts"
EXPECTED_TITLE = "sunt aut facere repellat provident occaecati excepturi optio reprehenderit"


def attach_response(response, name):
    allure.attach(
        response.text,
        name=name,
        attachment_type=allure.attachment_type.JSON,
    )


@pytest.fixture
def api_response():
    with allure.step(f"GET {API_BASE_URL}/posts/1"):
        response = requests.get(f"{API_BASE_URL}/posts/1", timeout=30)
    attach_response(response, "get_post_response")
    return response


@allure.title("GET /posts/1 возвращает 200")
@allure.severity(allure.severity_level.BLOCKER)
@allure.epic("API")
@allure.story("Чтение поста")
@allure.tag("api")
@pytest.mark.integration
@pytest.mark.smoke
def test_get_post_returns_200(api_response):
    assert api_response.status_code == 200


@allure.title("GET /posts/1 возвращает ожидаемый title")
@allure.severity(allure.severity_level.NORMAL)
@allure.epic("API")
@allure.story("Чтение поста")
@allure.tag("api")
@pytest.mark.integration
def test_post_has_correct_title(api_response):
    with allure.step("Парсим JSON"):
        data = api_response.json()
    assert data["title"] == EXPECTED_TITLE


@allure.title("POST /posts создаёт пост")
@allure.severity(allure.severity_level.CRITICAL)
@allure.epic("API")
@allure.story("Создание поста")
@allure.tag("api")
@pytest.mark.integration
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_create_post():
    payload = {"title": "Мой тест", "body": "Тестовое содержимое", "userId": 1}
    with allure.step("Отправляем POST"):
        response = requests.post(CREATE_URL, json=payload, timeout=30)
    attach_response(response, "create_post_response")
    assert response.status_code == 201
    assert response.json()["title"] == "Мой тест"


@allure.title("POST /posts/500 возвращает 500")
@allure.severity(allure.severity_level.NORMAL)
@allure.epic("API")
@allure.story("Обработка ошибок")
@allure.tag("api")
@pytest.mark.integration
def test_create_post_error():
    with allure.step("Отправляем POST на ошибочный эндпоинт"):
        response = requests.post(f"{API_BASE_URL}/posts/500", json={}, timeout=30)
    attach_response(response, "create_post_error_response")
    assert response.status_code == 500
