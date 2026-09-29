import allure


@allure.title("Сумма 5 и 10 равна 15")
@allure.severity(allure.severity_level.CRITICAL)
@allure.epic("Математика")
@allure.story("Сложение")
@pytest.mark.unit
@pytest.mark.smoke
def test_sum():
    a = 5
    b = 10

    with allure.step("Складываем 5 и 10"):
        result = a + b

    with allure.step(f"Проверяем результат ({result})"):
        assert result == 15
