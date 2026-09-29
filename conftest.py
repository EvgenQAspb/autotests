import os

import allure
import pytest

PW_TEST_CONNECT_WS = os.getenv("PW_TEST_CONNECT_WS")


@pytest.fixture
def sample_test_case():
    return {"id": "TC_042", "title": "Проверка логина", "status": "failed"}


@pytest.fixture(scope="session")
def connect_options():
    if not PW_TEST_CONNECT_WS:
        return None
    return {"endpoint": PW_TEST_CONNECT_WS}


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, "rep_" + report.when, report)


@pytest.fixture
def page(page):
    yield page
    if getattr(page, "rep_call", None) and page.rep_call.failed:
        allure.attach(
            page.screenshot(),
            name="screenshot",
            attachment_type=allure.attachment_type.PNG,
        )
