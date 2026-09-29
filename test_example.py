import allure
import pytest


@allure.title("Заголовок страницы Example Domains")
@allure.severity(allure.severity_level.MINOR)
@allure.epic("Смоук")
@pytest.mark.e2e
@pytest.mark.smoke
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_example_domain_title(page):
    with allure.step("Открываем страницу"):
        page.goto("https://www.iana.org/help/example-domains")

    with allure.step("Проверяем h1"):
        assert page.locator("h1").inner_text() == "Example Domains"
