def check_password_length(password, min_length):
    if len(password) >= min_length:
        return "Пароль принят"
    return f"Пароль отклонён: длина {len(password)}, требуется минимум {min_length}"


print(check_password_length("secure123", 8))
print(check_password_length("1234", 8))
