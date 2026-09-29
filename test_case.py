test_case = {
    "id": "TC_042",
    "title": "Проверка логина",
    "status": "failed",
}

print(test_case["title"])

test_case["priority"] = "high"

if test_case["status"] == "failed":
    print(f"Требуется перепроверка: {test_case['title']}")
