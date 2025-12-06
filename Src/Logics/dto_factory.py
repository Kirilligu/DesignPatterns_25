from Src.Dtos.nomenclature_dto import nomenclature_dto
from Src.Dtos.range_dto import range_dto
from Src.Dtos.category_dto import category_dto
from Src.Dtos.storage_dto import storage_dto
from Src.Core.validator import operation_exception

"""
Фабрика для создания DTO справочников
"""
class DtoFactory:
    __mapping = {
        "nomenclature": nomenclature_dto(),
        "range": range_dto(),
        "group": category_dto(),
        "storage": storage_dto(),
    }

    @staticmethod
    def create(reference_type: str, data: dict):
        factory = DtoFactory.__mapping.get(reference_type.lower())
        if not factory:
            raise operation_exception("Неверный тип справочника")
        return factory.create(data)