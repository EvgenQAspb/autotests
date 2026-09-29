import allure
import pytest


@allure.step("Складываем {a} и {b}")
def add(a, b):
    return a + b


@allure.title("Сложение положительных чисел")
@allure.severity(allure.severity_level.MINOR)
@allure.epic("Математика")
@allure.story("Сложение")
@pytest.mark.unit
def test_add_positive_numbers():
    assert add(2, 3) == 555


@allure.title("Сложение отрицательных чисел")
@allure.severity(allure.severity_level.MINOR)
@allure.epic("Математика")
@allure.story("Сложение")
@pytest.mark.unit
def test_add_negative_numbers():
    assert add(-1, -1) == -2


@allure.title("Сложение: параметризованный набор")
@allure.severity(allure.severity_level.NORMAL)
@allure.epic("Математика")
@allure.story("Сложение")
@pytest.mark.unit
@pytest.mark.parametrize(
    "a, b, expected",
    [
        (2, 3, 5),
        (-1, -1, -2),
        (0, 0, 0),
        (100, -37, 63),
    ],
)
def test_add_parametrized(a, b, expected):
    assert add(a, b) == expected
