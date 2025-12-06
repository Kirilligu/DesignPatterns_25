from Src.start_manager import start_manager
from Src.reposity_manager import reposity_manager
from Src.Core.prototype import prototype
from Src.Core.observe_service import observe_service
from Src.Core.validator import validator, operation_exception
from Src.Dtos.reference_event_dto import ReferenceEventDto
from Src.Core.event_type import event_type
import os
import json


class reference_service:
    __manager = start_manager()

    @staticmethod
    def get_all(reference_type: str):
        key_map = {
            "nomenclature": reposity_manager.nomenclature_key(),
            "range": reposity_manager.range_key(),
            "group": reposity_manager.group_key(),
            "storage": reposity_manager.storage_key(),
        }
        key = key_map.get(reference_type.lower())
        if not key:
            raise operation_exception("Неверный тип справочника")
        return prototype(reference_service.__manager.data.get(key, []))

    @staticmethod
    def get_by_id(reference_type: str, item_id: str):
        items = reference_service.get_all(reference_type)
        for item in items.data:
            if item.unique_code == item_id:
                return item
        return None

    @staticmethod
    def add(reference_type: str, item):
        key = {
            "nomenclature": reposity_manager.nomenclature_key(),
            "range": reposity_manager.range_key(),
            "group": reposity_manager.group_key(),
            "storage": reposity_manager.storage_key(),
        }[reference_type]

        reference_service.__manager.data[key].append(item)
        reference_service.__manager._start_manager__cache[item.unique_code] = item

        #уведомляем наблюдателей
        observe_service.create_event(event_type.reference_added(),ReferenceEventDto(reference_type, item))

        reference_service.__save_to_file()
        return item

    @staticmethod
    def update(reference_type: str, item_id: str, new_data):
        item = reference_service.get_by_id(reference_type, item_id)
        if not item:
            raise operation_exception("Элемент не найден")

        #обновляем поля
        for key, value in new_data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        observe_service.create_event(
            event_type.reference_updated(),
            ReferenceEventDto(reference_type, item)
        )
        reference_service.__save_to_file()
        return item

    @staticmethod
    def delete(reference_type: str, item_id: str):
        item = reference_service.get_by_id(reference_type, item_id)
        if not item:
            raise operation_exception("Элемент не найден")
        try:
            observe_service.create_event(
                event_type.before_reference_delete(),
                ReferenceEventDto(reference_type, item)
            )
        except operation_exception:
            raise
        except Exception as e:
            raise operation_exception(f"Удаление запрещено: {str(e)}")
        key = {
            "nomenclature": reposity_manager.nomenclature_key(),
            "range": reposity_manager.range_key(),
            "group": reposity_manager.group_key(),
            "storage": reposity_manager.storage_key(),
        }[reference_type]

        reference_service.__manager.data[key].remove(item)
        reference_service.__manager._start_manager__cache.pop(item_id, None)
        observe_service.create_event(
            event_type.reference_deleted(),
            ReferenceEventDto(reference_type, item)
        )
        reference_service.__save_to_file()

    @staticmethod
    def __save_to_file():
        pass