from Src.Models.settings_model import settings_model
from Src.Core.validator import operation_exception
from Src.Core.validator import validator
from Src.Models.company_model import company_model
from Src.Core.common import common
from Src.Core.response_formats import response_formats
import json
from datetime import datetime
from Src.Core.abstract_manager import abstract_manager
from Src.Core.observe_service import observe_service
from Src.Core.event_type import event_type
from Src.Core.log_level import log_level
from Src.Dtos.log_event_dto import log_event_dto
####################################################3
# Менеджер настроек. 
# Предназначен для управления настройками и хранения параметров приложения
class settings_manager(abstract_manager):

    # Настройки
    __settings:settings_model = None

    # Singletone
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(settings_manager, cls).__new__(cls)
        return cls.instance 
    
    def __init__(self):
        self.__set_default()

    # Текущие настройки
    @property
    def settings(self) -> settings_model:
        return self.__settings
    def load(self) -> bool:
        if self.file_name == "":
            raise operation_exception("Не найден файл настроек!")

        try:
            #логирование начала загрузки
            log_dto = log_event_dto.create(
                level=log_level.DEBUG,
                message='Loading settings from file',
                context={'file': self.file_name}
            )
            observe_service.create_event(event_type.log_debug(), log_dto)
            with open(self.file_name, 'r', encoding='utf-8') as file_instance:
                settings = json.load(file_instance)

                result = True

                # Реквизиты организации
                if "company" in settings.keys():
                    data = settings["company"]
                    result = self.__deserialize(data)

                # Формат по умолчанию
                if "default_format" in settings.keys() and result == True:
                    data = settings["default_format"]
                    if data in response_formats.list_all_formats():
                        self.settings.default_response_format = data

                # Дата блокировки
                if "block_period" in settings.keys() and result == True:
                    data = settings["block_period"]
                    date_format = "%Y-%m-%d"
                    date = datetime.strptime(data, date_format)
                    self.__settings.block_period = date
                if "logging" in settings.keys() and result == True:
                    logging_settings = settings["logging"]
                    if "min_level" in logging_settings:
                        min_level = logging_settings["min_level"]
                        if min_level.upper() == "DEBUG":
                            self.settings.log_min_level = log_level.DEBUG
                        elif min_level.upper() == "INFO":
                            self.settings.log_min_level = log_level.INFO
                        elif min_level.upper() == "ERROR":
                            self.settings.log_min_level = log_level.ERROR
                        else:
                            self.settings.log_min_level = log_level.INFO
                    if "output" in logging_settings:
                        output = logging_settings["output"]
                        if hasattr(self.settings, 'log_output'):
                            self.settings.log_output = output
                    if "file_name" in logging_settings:
                        file_name = logging_settings["file_name"]
                        if hasattr(self.settings, 'log_file_name'):
                            self.settings.log_file_name = file_name
                    settings_dto = log_event_dto.create(
                        level=log_level.INFO,
                        message='Logging settings loaded',
                        context={
                            'min_level': logging_settings.get('min_level', 'INFO'),
                            'output': logging_settings.get('output', 'console'),
                            'file_name': logging_settings.get('file_name', 'system.log')
                        }
                    )

                #логирование результата загрузки
                if result:
                    success_dto = log_event_dto.create(
                        level=log_level.INFO,
                        message='Settings loaded successfully',
                        context={'file': self.file_name}
                    )
                    observe_service.create_event(event_type.log_info(), success_dto)
                else:
                    error_dto = log_event_dto.create(
                        level=log_level.ERROR,
                        message='Settings load failed',
                        context={'file': self.file_name, 'error': 'Deserialization failed'}
                    )
                    observe_service.create_event(event_type.log_error(), error_dto)

                return result
            observe_service.create_event(event_type.settings_change(), settings_dto)

        except Exception as ex:
            #логирование ошибки
            error_dto = log_event_dto.create(
                level=log_level.ERROR,
                message='Settings load failed',
                context={'file': self.file_name, 'error': str(ex)}

            )
            observe_service.create_event(event_type.log_error(), error_dto)

            return False
    def save(self) -> bool:
        if self.file_name == "":
            raise operation_exception("Не найден файл настроек!")
        try:
            debug_dto = log_event_dto.create(
                level=log_level.DEBUG,
                message='Saving settings to file',
                context={'file': self.file_name}
            )
            observe_service.create_event(event_type.log_debug(), debug_dto)
            data = {}
            if self.__settings.company:
                data["company"] = {
                    "name": self.__settings.company.name,
                    "inn": self.__settings.company.inn
                }

            # Формат по умолчанию
            if hasattr(self.__settings, 'default_response_format'):
                data["default_format"] = self.__settings.default_response_format

            # Дата блокировки
            if hasattr(self.__settings, '_settings_model__block_period') and self.__settings.block_period:
                data["block_period"] = self.__settings.block_period.strftime("%Y-%m-%d")
            if hasattr(self.__settings, 'log_min_level') and hasattr(self.__settings, 'log_output') and hasattr(
                    self.__settings, 'log_file_name'):
                data["logging"] = {
                    "min_level": self.__settings.log_min_level,
                    "output": self.__settings.log_output,
                    "file_name": self.__settings.log_file_name
                }
            with open(self.file_name, 'w', encoding='utf-8') as file_instance:
                json.dump(data, file_instance, ensure_ascii=False, indent=4)

            #логирование успешного сохранения
            success_dto = log_event_dto.create(
                level=log_level.INFO,
                message='Settings saved successfully',
                context={'file': self.file_name}
            )
            observe_service.create_event(event_type.log_info(), success_dto)

            return True

        except Exception as ex:
            error_dto = log_event_dto.create(
                level=log_level.ERROR,
                message='Settings save failed',
                context={'file': self.file_name, 'error': str(ex)}
            )
            observe_service.create_event(event_type.log_error(), error_dto)
            return False
    # Обработать полученный словарь    
    def __deserialize(self, data: dict) -> bool:
        validator.validate(data, dict)
        fields = common.get_fields(self.__settings.company)
        matching_keys = list(filter(lambda key: key in fields, data.keys()))

        try:
            for key in matching_keys:
                setattr(self.__settings.company, key, data[key])
        except Exception as ex:
            error_dto = log_event_dto.create(
                level=log_level.ERROR,
                message='Failed to deserialize company data',
                context={'error': str(ex)}
            )
            observe_service.create_event(event_type.log_error(), error_dto)
            return False

        return True

    # Параметры настроек по умолчанию
    def __set_default(self):
        company = company_model()
        company.name = "Рога и копыта"
        company.inn = -1
        self.__settings = settings_model()
        self.__settings.company = company
        self.__settings.log_min_level = log_level.INFO
        self.__settings.log_output = "console"
        self.__settings.log_file_name = "system.log"
        



