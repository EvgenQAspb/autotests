import allure
import pytest

from pages.login_page import LoginPage


@allure.title("Успешный логин")
@allure.severity(allure.severity_level.CRITICAL)
@allure.epic("Авторизация")
@allure.story("Успешный вход")
@allure.tag("auth")
@allure.label("owner", "qa-team")
@pytest.mark.e2e
@pytest.mark.auth
@pytest.mark.smoke
def test_successful_login(page):
    login_page = LoginPage(page)

    with allure.step("Открываем страницу логина"):
        login_page.open()

    with allure.step("Вводим валидные логин и пароль"):
        login_page.login("tomsmith", "SuperSecretPassword!")

    with allure.step("Проверяем текст успешного входа"):
        assert "You logged into a secure area!" in login_page.get_flash_text()


@allure.title("Логин с неверным паролем")
@allure.severity(allure.severity_level.NORMAL)
@allure.epic("Авторизация")
@allure.story("Негативные сценарии")
@allure.tag("auth")
@pytest.mark.e2e
@pytest.mark.auth
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_failed_login_wrong_password(page):
    login_page = LoginPage(page)

    with allure.step("Открываем страницу логина"):
        login_page.open()

    with allure.step("Вводим неверный пароль"):
        login_page.login("tomsmith", "wrongpassword")

    with allure.step("Проверяем текст ошибки"):
        assert "Your password is invalid!" in login_page.get_error_text()
