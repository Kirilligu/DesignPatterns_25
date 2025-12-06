class ReferenceEventDto:
    """
    DTO для передачи события о справочнике
    вместо анонимных словарей
    """
    def __init__(self, reference_type: str, item):
        self.reference_type = reference_type
        self.item = item