import unittest
from datetime import datetime
from Src.Logics.log_observer import log_observer
from Src.Core.log_level import log_level
from Src.Core.event_type import event_type
import sys

class TestLogObserver(unittest.TestCase):
    """Набор тестов для проверки работы log_observer"""
    def setUp(self):
        """Настройка перед каждым тестом"""
        #подготовка
        self.observer = log_observer()

    # Тесты форматирования записей лога
    def test_notThrow_format_log_entry_simple(self):
        """Проверить форматирование лога без контекста"""
        #подготовка
        event = "test_event"
        level = log_level.INFO
        message = "Test message"
        context = {}
        #действие
        result = self.observer._log_observer__format_log_entry(
            event=event,
            level=level,
            message=message,
            context=context
        )

        #проверка
        self.assertIn("TEST EVENT", result)
        self.assertIn("INFO", result)
        self.assertIn("Test message", result)
        self.assertIn(":", result)
        self.assertIn("[", result)
        self.assertIn("]", result)

    def test_true_format_log_entry_with_context(self):
        """Проверить форматирование лога с контекстом"""
        #подготовка
        event = "user_action"
        level = log_level.DEBUG
        message = "User performed action"
        context = {
            "user_id": 123,
            "username": "test_user",
            "action": "login",
            "success": True
        }
        #действие
        result = self.observer._log_observer__format_log_entry(
            event=event,
            level=level,
            message=message,
            context=context
        )
        #проверка
        self.assertIn("user_id=123", result)
        self.assertIn("username=test_user", result)
        self.assertIn("action=login", result)
        self.assertIn("success=True", result)
        self.assertIn(" | ", result)

    def test_notThrow_format_log_entry_with_none_context(self):
        """Проверить форматирование лога с None значениями в контексте"""
        #подготовка
        event = "test"
        level = log_level.ERROR
        message = "Error occurred"
        context = {
            "user_id": None,
            "username": "test",
            "data": None
        }
        #действие
        result = self.observer._log_observer__format_log_entry(
            event=event,
            level=level,
            message=message,
            context=context
        )

        #проверка
        self.assertIn("user_id=None", result)
        self.assertIn("username=test", result)
        self.assertIn("data=None", result)

    def test_notThrow_format_log_entry_with_object_context(self):
        #подготовка
        class MockObject:
            def __init__(self, name):
                self.name = name

        obj = MockObject("test_object")
        event = "object_test"
        level = log_level.INFO
        message = "Processing object"
        context = {
            "object": obj,
            "description": "Test object"
        }
        #действие
        result = self.observer._log_observer__format_log_entry(
            event=event,
            level=level,
            message=message,
            context=context
        )
        #проверка
        self.assertIn("object=MockObject", result)
        self.assertIn("description=Test object", result)

    def test_true_format_log_entry_event_name_conversion(self):
        """Проверить преобразование имени события"""
        #подготовка
        event = "web_api_call"
        level = log_level.DEBUG
        message = "API request"
        context = {}
        #действие
        result = self.observer._log_observer__format_log_entry(
            event=event,
            level=level,
            message=message,
            context=context
        )
        #проверка
        self.assertIn("WEB API CALL", result)
        self.assertNotIn("_", result)

    def test_true_format_log_entry_timestamp_format(self):
        """Проверить формат временной метки"""
        #подготовка
        event = "test"
        level = log_level.INFO
        message = "Test"
        context = {}
        #действие
        result = self.observer._log_observer__format_log_entry(
            event=event,
            level=level,
            message=message,
            context=context
        )

        #проверка
        # Проверяем формат timestamp
        timestamp_pattern = r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]'
        self.assertRegex(result, timestamp_pattern)

    def test_true_format_log_entry_empty_context(self):
        """Проверить форматирование лога с пустым словарем контекста"""
        #подготовка
        event = "empty_test"
        level = log_level.ERROR
        message = "Warning message"
        context = {}
        #действие
        result = self.observer._log_observer__format_log_entry(
            event=event,
            level=level,
            message=message,
            context=context
        )
        #проверка
        self.assertNotIn(" | ", result)
    def test_skip_format_log_entry_warning_level(self):
        """Проверить обработку уровня WARNING """
        #подготовка
        try:
            warning_level = log_level.WARNING
            event = "warning_test"
            message = "This is a warning"
            context = {}
            #действие
            result = self.observer._log_observer__format_log_entry(
                event=event,
                level=warning_level,
                message=message,
                context=context
            )
            #проверка
            self.assertIn("WARNING", result)
            self.assertIn("This is a warning", result)
        except AttributeError:
            self.skipTest("log_level.WARNING не определен в системе")

    def test_notThrow_format_log_entry_special_characters(self):
        """Проверить форматирование лога со специальными символами"""
        #подготовка
        event = "special_chars"
        level = log_level.INFO
        message = "Test with: colons, commas, and other ()[]{} symbols"
        context = {"key": "value with spaces"}
        #действие
        result = self.observer._log_observer__format_log_entry(
            event=event,
            level=level,
            message=message,
            context=context
        )
        #проверка
        self.assertIn("Test with: colons", result)
        self.assertIn("key=value with spaces", result)
    def test_true_all_log_levels_handled(self):
        """Проверить что все уровни логирования корректно обрабатываются"""
        #подготовка
        for level in log_level:
            event = f"test_{level.name.lower()}"
            message = f"Test message for {level.name}"
            context = {"level": level.name}
            #действие
            result = self.observer._log_observer__format_log_entry(
                event=event,
                level=level,
                message=message,
                context=context
            )
            #проверка
            self.assertIn(level.name, result)
            self.assertIn(f"Test message for {level.name}", result)

    def test_any_available_log_levels(self):
        """Проверить какие уровни логирования доступны в системе"""
        #действие
        available_levels = [level.name for level in log_level]
        #проверка
        sys.stdout.write(f"Доступные уровни логирования: {available_levels}\n")
        assert len(available_levels) > 0
        #проверяем что основные уровни присутствуют
        assert "DEBUG" in available_levels
        assert "INFO" in available_levels
        assert "ERROR" in available_levels
if __name__ == '__main__':
    unittest.main()