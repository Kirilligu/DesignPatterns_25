from Src.Core.abstract_dto import abstract_dto
from Src.Core.log_level import log_level
from Src.Core.validator import validator

class log_event_dto(abstract_dto):
    __level: log_level
    __message: str = ""
    __context: dict = {}

    @property
    def level(self) -> log_level:
        return self.__level
    @level.setter
    def level(self, value: log_level):
        validator.validate(value, log_level)
        self.__level = value
    @property
    def message(self) -> str:
        return self.__message
    @message.setter
    def message(self, value: str):
        validator.validate(value, str)
        self.__message = value.strip()
    @property
    def context(self) -> dict:
        return self.__context
    @context.setter
    def context(self, value: dict):
        validator.validate(value, dict)
        self.__context = value
    @staticmethod
    def create(level: log_level, message: str, context: dict = None) -> "log_event_dto":
        dto = log_event_dto()
        dto.level = level
        dto.message = message
        if context:
            dto.context = context
        return dto