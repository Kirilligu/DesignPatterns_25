from Src.Core.abstract_logic import abstract_logic
from Src.Core.validator import operation_exception
"""
Реализация наблюдателя
"""
class observe_service:
    handlers = []

    """
    Добавить объект под наблюденние
    """
    @staticmethod
    def add(instance):
        if instance is None: return
        if not isinstance( instance, abstract_logic ): return

        if instance not in  observe_service.handlers:
            observe_service.handlers.append( instance )

    """
    Удадлить из под наблюдения
    """
    @staticmethod
    def delete(instance):
        if instance is None: return
        if not isinstance( instance, abstract_logic ): return

        if instance in  observe_service.handlers:
            observe_service.handlers.remove( instance )

    """
    Вызвать событие
    """
    @staticmethod
    def create_event(  event: str, params ):
        for handler in observe_service.handlers[:]:
            try:
                handler.handle(event, params)
            except operation_exception:
                raise
            except Exception as e:
                pass


