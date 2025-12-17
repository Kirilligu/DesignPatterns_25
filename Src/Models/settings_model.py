from Src.Models.company_model import company_model
from Src.Core.validator import validator, argument_exception
from Src.Core.response_formats import response_formats
from datetime import datetime
from Src.Core.observe_service import observe_service
from Src.Core.event_type import event_type
from Src.Core.log_level import log_level
from Src.Dtos.log_event_dto import log_event_dto

######################################
# Модель настроек приложения
class settings_model:
    __company: company_model = None
    __default_response_format: str = response_formats.csv()
    __block_period: datetime

    # Дата блокировки
    @property
    def block_period(self) -> datetime:
        return self.__block_period

    @block_period.setter
    def block_period(self, value: datetime):
        validator.validate(value, datetime)

        #получаем старое значение если оно существует
        old = None
        if hasattr(self, '_settings_model__block_period'):
            old = self.__block_period

        self.__block_period = value

        #логирование изменения только если значение изменилось
        if old != value:
            #событие смены даты блокировки
            block_dto = log_event_dto.create(
                level=log_level.INFO,
                message='Block period changed',
                context={'new_date': value.strftime("%Y-%m-%d")}
            )
            observe_service.create_event(event_type.change_block_period(), block_dto)

            #логирование INFO уровня
            info_dto = log_event_dto.create(
                level=log_level.INFO,
                message='Block period changed',
                context={
                    'old': old.strftime("%Y-%m-%d") if old else None,
                    'new': value.strftime("%Y-%m-%d")
                }
            )
            observe_service.create_event(event_type.log_info(), info_dto)

            #событие изменения настроек
            settings_dto = log_event_dto.create(
                level=log_level.INFO,
                message='Settings updated: block_period',
                context={'new': value.strftime("%Y-%m-%d")}
            )
            observe_service.create_event(event_type.settings_change(), settings_dto)

    #текущая организация
    @property
    def company(self) -> company_model:
        return self.__company

    @company.setter
    def company(self, value: company_model):
        validator.validate(value, company_model)
        old = None
        if hasattr(self, '_settings_model__company'):
            old = self.__company

        self.__company = value

        # логирование изменения только если значение изменилось
        if old != value:
            #логирование INFO уровня
            info_dto = log_event_dto.create(
                level=log_level.INFO,
                message='Company changed',
                context={
                    'old_name': old.name if old else None,
                    'new_name': value.name
                }
            )
            observe_service.create_event(event_type.log_info(), info_dto)

            #событие изменения настроек
            settings_dto = log_event_dto.create(
                level=log_level.INFO,
                message='Settings updated: company',
                context={'new_company': value.name}
            )
            observe_service.create_event(event_type.settings_change(), settings_dto)

    @property
    def default_response_format(self) -> str:
        return self.__default_response_format

    @default_response_format.setter
    def default_response_format(self, value: str):
        validator.validate(value, str)
        if value not in response_formats.list_all_formats():
            raise argument_exception("Некорректно указан тип формата!")

        #получаем старое значение если оно существует
        old = None
        if hasattr(self, '_settings_model__default_response_format'):
            old = self.__default_response_format

        self.__default_response_format = value

        #логирование изменения только если значение изменилось
        if old != value:
            #логирование INFO уровня
            info_dto = log_event_dto.create(
                level=log_level.INFO,
                message='Default response format changed',
                context={'old': old, 'new': value}
            )
            observe_service.create_event(event_type.log_info(), info_dto)
            #изменения настроек
            settings_dto = log_event_dto.create(
                level=log_level.INFO,
                message='Settings updated: default_response_format',
                context={'new': value}
            )
            observe_service.create_event(event_type.settings_change(), settings_dto)

    #настройки логирования
    __log_min_level: log_level = log_level.INFO
    __log_output: str = "console"
    __log_file_name: str = "system.log"

    @property
    def log_min_level(self) -> log_level:
        return self.__log_min_level

    @log_min_level.setter
    def log_min_level(self, value: log_level):
        if not isinstance(value, log_level):
            raise argument_exception("log_min_level должен быть типом log_level (DEBUG, INFO, ERROR)")

        old = self.__log_min_level if hasattr(self, '_settings_model__log_min_level') else None

        self.__log_min_level = value

        if old != value:
            # логируем изменение
            info_dto = log_event_dto.create(
                level=log_level.INFO,
                message='Log min level changed',
                context={'old': old.name if old else None, 'new': value.name}
            )
            observe_service.create_event(event_type.log_info(), info_dto)

            # генерируем событие изменения настроек
            settings_dto = log_event_dto.create(
                level=log_level.INFO,
                message='Settings updated: log_min_level',
                context={'new': value.name}
            )
            observe_service.create_event(event_type.settings_change(), settings_dto)

    @property
    def log_output(self) -> str:
        return self.__log_output

    @log_output.setter
    def log_output(self, value: str):
        validator.validate(value, str)
        if value not in ["console", "file"]:
            raise argument_exception("Некорректный тип вывода логирования!")
        old = self.__log_output
        self.__log_output = value

        if old != value:
            info_dto = log_event_dto.create(
                level=log_level.INFO,
                message='Log output changed',
                context={'old': old, 'new': value}
            )
            observe_service.create_event(event_type.log_info(), info_dto)
            settings_dto = log_event_dto.create(
                level=log_level.INFO,
                message='Settings updated: log_output',
                context={'new': value}
            )
            observe_service.create_event(event_type.settings_change(), settings_dto)

    @property
    def log_file_name(self) -> str:
        return self.__log_file_name

    @log_file_name.setter
    def log_file_name(self, value: str):
        validator.validate(value, str)
        old = self.__log_file_name
        self.__log_file_name = value
        if old != value:
            info_dto = log_event_dto.create(
                level=log_level.INFO,
                message='Log file name changed',
                context={'old': old, 'new': value}
            )
            observe_service.create_event(event_type.log_info(), info_dto)
            settings_dto = log_event_dto.create(
                level=log_level.INFO,
                message='Settings updated: log_file_name',
                context={'new': value}
            )
            observe_service.create_event(event_type.settings_change(), settings_dto)