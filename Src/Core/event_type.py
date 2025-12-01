

"""
Типы событий
"""
class event_type:

    """
    Событие - смена даты блокировки
    """
    @staticmethod
    def change_block_period() -> str:
        return "change_block_period"
    
    """
    Событие - сформирован Json
    """
    @staticmethod
    def convert_to_json() -> str:
        return "convert_to_json"

    """
    Получить список всех событий
    """
    @staticmethod
    def events() -> list:
        result = []
        methods = [method for method in dir(event_type) if
                    callable(getattr(event_type, method)) and not method.startswith('__') and method != "events"]
        for method in methods:
            key = getattr(event_type, method)()
            result.append(key)

        return result

    @staticmethod
    def before_reference_delete() -> str:
        return "before_reference_delete"

    @staticmethod
    def reference_deleted() -> str:
        return "reference_deleted"

    @staticmethod
    def reference_added() -> str:
        return "reference_added"

    @staticmethod
    def reference_updated() -> str:
        return "reference_updated"