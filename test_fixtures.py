import allure
import pytest

@pytest.fixture
def browser():
    print("Браузер")
    yield

    print("Закрываем")


@pytest.fixture
def login_page(browser):
    print("Логин пейдж")


@pytest.fixture
def user():
    print("Юзер")
    return "username", "password"


@allure.title("Логин с валидными данными")
@allure.severity(allure.severity_level.CRITICAL)
@allure.epic("Авторизация")
@allure.story("Успешный вход")
@allure.tag("auth")
@allure.label("owner", "backend-team")
@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.smoke
def test_login(login_page,user):
    username, password = user
    assert username == "username"
    assert password == "password"


@allure.title("Тест-кейс в статусе failed")
@allure.description("Проверяем, что тест-кейс TC_042 помечен как упавший")
@allure.severity(allure.severity_level.NORMAL)
@allure.step("Проверяем статус")
@pytest.mark.unit
def test_case_status_is_failed(sample_test_case):
    assert sample_test_case["status"] == "failed"


@allure.title("Тест-кейс имеет корректный id")
@allure.severity(allure.severity_level.MINOR)
@pytest.mark.unit
def test_case_has_correct_id(sample_test_case):
    assert sample_test_case["id"] == "TC_042"
