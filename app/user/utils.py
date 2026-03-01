"""Утилиты для работы с паролями: хеширование и проверка через bcrypt."""

import bcrypt


class PasswordService:
    """Сервис безопасного хеширования паролей с использованием bcrypt."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Генерирует bcrypt-хеш пароля с автоматической солью."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Сравнивает открытый пароль с его bcrypt-хешем."""
        return bcrypt.checkpw(password.encode(), hashed_password.encode())
