import datetime
import os
import sys
from Src.Core.abstract_logic import abstract_logic
from Src.Core.validator import validator, argument_exception
from Src.Core.log_level import log_level
from Src.Core.event_type import event_type
from Src.settings_manager import settings_manager
from Src.Dtos.log_event_dto import log_event_dto

class log_observer(abstract_logic):
    __min_level = log_level.INFO
    __output = "console"
    __file_name = "system.log"

    def __init__(self):
        super().__init__()
        self.__load_logging_settings()

    def __load_logging_settings(self):
        """Загружаем настройки логирования из settings_manager"""
        try:
            manager = settings_manager()

            #если настройки загружены,получаем параметры логирования
            if manager.settings:
                level_str = manager.settings.log_min_level.upper()
                if level_str == "DEBUG":
                    self.__min_level = log_level.DEBUG
                elif level_str == "INFO":
                    self.__min_level = log_level.INFO
                elif level_str == "ERROR":
                    self.__min_level = log_level.ERROR

                self.__output = manager.settings.log_output
                self.__file_name = manager.settings.log_file_name
                self.__log_internal(
                    f"Logging settings loaded from manager: min_level={self.__min_level.name}, output={self.__output}, file_name={self.__file_name}")
            else:
                self.__log_internal("Settings not loaded, using defaults")

        except AttributeError:
            self.__log_internal("Logging properties not found in settings, using defaults")
        except Exception as ex:
            self.set_exception(ex)
            self.__log_internal(f"Error loading logging settings: {str(ex)}")

    def __log_internal(self, message: str):
        """Внутреннее логирование для самого логгера"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(f"[{timestamp}] LOGGER_INIT: {message}\n")

    def handle(self, event: str, params):
        super().handle(event, params)

        #обрабатываем только события логирования
        if event not in [event_type.log_debug(), event_type.log_info(), event_type.log_error(),
                         event_type.web_call(), event_type.crud_operation(),
                         event_type.settings_change(), event_type.storage_operation()]:
            return

        if isinstance(params, log_event_dto):
            level = params.level
            message = params.message
            context = params.context
        elif isinstance(params, dict):
            level = params.get("level", log_level.INFO)
            message = params.get("message", "")
            context = params.get("context", {})
        else:
            return
        if level is None:
            level = log_level.INFO
            if event == event_type.log_debug():
                level = log_level.DEBUG
            elif event == event_type.log_error():
                level = log_level.ERROR

        #проверяем минимальный уровень
        if level.value < self.__min_level.value:
            return
        if not message:
            if event == event_type.web_call():
                message = "Web API call"
            elif event == event_type.crud_operation():
                message = "CRUD operation"
            elif event == event_type.settings_change():
                message = "Settings changed"
            elif event == event_type.storage_operation():
                message = "Storage operation"

        #формируем запись лога
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        event_name = event.upper().replace("_", " ")
        log_entry = f"[{timestamp}] {event_name}: {level.name}: {message}"
        if isinstance(context, dict) and len(context) > 0:
            try:
                ctx_parts = []
                for key, value in context.items():
                    if value is None:
                        ctx_parts.append(f"{key}=None")
                    elif hasattr(value, '__dict__'):
                        ctx_parts.append(f"{key}={type(value).__name__}")
                    else:
                        ctx_parts.append(f"{key}={str(value)}")
                ctx_str = " | ".join(ctx_parts)
                log_entry += f" | {ctx_str}"
            except Exception:
                pass

        #консоль или файл
        if self.__output == "console":
            sys.stdout.write(log_entry + "\n")
        else:
            try:
                directory = os.path.dirname(self.__file_name)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)
                with open(self.__file_name, "a", encoding="utf-8") as f:
                    f.write(log_entry + "\n")
            except Exception as ex:
                self.set_exception(ex)
                sys.stderr.write(f"ERROR writing to log file: {str(ex)}\n")
                sys.stderr.write(log_entry + "\n")