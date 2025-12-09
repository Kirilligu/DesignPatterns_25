import datetime
import os
import sys
from Src.Core.abstract_logic import abstract_logic
from Src.Core.validator import validator, argument_exception
from Src.Core.log_level import log_level
from Src.Core.event_type import event_type
from Src.settings_manager import settings_manager
from Src.Dtos.log_event_dto import log_event_dto
from Src.Dtos.reference_event_dto import ReferenceEventDto
from Src.Core.observe_service import observe_service
class log_observer(abstract_logic):
    __min_level = log_level.INFO
    __output = "console"
    __file_name = "system.log"

    def __init__(self):
        super().__init__()
        observe_service.add(self)
        self.apply_current_settings()

    def apply_current_settings(self):
        """
        вызывается один раз при старте и каждый раз при событии settings_change
        """
        try:
            settings = settings_manager().settings
            self.__min_level = settings.log_min_level
            self.__output = settings.log_output
            self.__file_name = settings.log_file_name
            self.__log_internal(
                f"Logging settings applied: level={self.__min_level.name}, "
                f"output={self.__output}, file={self.__file_name}"
            )
        except Exception as ex:
            self.__log_internal(f"Failed to apply logging settings: {ex}")
    def __log_internal(self, message: str):
        """Внутреннее логирование для самого логгера"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(f"[{timestamp}] LOGGER_INIT: {message}\n")

    def handle(self, event: str, params):
        super().handle(event, params)
        if event == event_type.settings_change():
            self.apply_current_settings()
            return
        level = None
        message = ""
        context = {}
        if event == event_type.reference_added():
            if not isinstance(params, ReferenceEventDto):
                return

            level = log_level.INFO
            message = "Reference added"
            item = params.item
            context = {
                'reference_type': params.reference_type,
                'item_id': item.unique_code if item else None,
                'item_name': getattr(item, 'name', 'Unknown') if item else 'Unknown'
            }

        elif event == event_type.reference_updated():
            if not isinstance(params, ReferenceEventDto):
                return
            level = log_level.INFO
            message = "Reference updated"
            item = params.item
            context = {
                'reference_type': params.reference_type,
                'item_id': item.unique_code if item else None,
                'item_name': getattr(item, 'name', 'Unknown') if item else 'Unknown'
            }

        elif event == event_type.reference_deleted():
            if not isinstance(params, ReferenceEventDto):
                return
            level = log_level.INFO
            message = "Reference deleted"
            item = params.item
            context = {
                'reference_type': params.reference_type,
                'item_id': item.unique_code if item else None,
                'item_name': getattr(item, 'name', 'Unknown') if item else 'Unknown'
            }

        elif event == event_type.before_reference_delete():
            if not isinstance(params, ReferenceEventDto):
                return
            level = log_level.INFO
            message = "Reference delete check"
            item = params.item
            context = {
                'reference_type': params.reference_type,
                'item_id': item.unique_code if item else None,
                'item_name': getattr(item, 'name', 'Unknown') if item else 'Unknown'
            }
        elif event in (event_type.log_debug(),
                           event_type.log_info(),
                           event_type.log_error(),
                           event_type.web_call(),
                           event_type.crud_operation(),
                           event_type.storage_operation()):
            if not isinstance(params, log_event_dto):
                return
            level = params.level
            message = params.message
            context = params.context or {}
        if level is None:
            return

        #проверяем минимальный уровень
        if level.value < self.__min_level.value:
            return

        #формируем запись лога с помощью отдельного метода
        log_entry = self.__format_log_entry(event, level, message, context)

        #выводим в консоль или файл
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
                sys.stderr.write(f"ERROR writing to log file: {str(ex)}\n")
                sys.stdout.write(log_entry + "\n")

    def __format_log_entry(self, event: str, level: log_level, message: str, context: dict) -> str:
        """
        Форматирует запись лога
        Args:
            event: Имя события
            level: Уровень логирования
            message: Сообщение
            context: Контекст
        """
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

        return log_entry