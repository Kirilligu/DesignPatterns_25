from Src.start_manager import start_manager
from Src.reposity_manager import reposity_manager
from Src.Core.prototype import prototype
from Src.Core.observe_service import observe_service
from Src.Core.validator import validator, operation_exception
from Src.Dtos.reference_event_dto import ReferenceEventDto
from Src.Core.event_type import event_type
from Src.Core.log_level import log_level
import os
import json
from Src.Dtos.log_event_dto import log_event_dto

class reference_service:
    __manager = start_manager()

    @staticmethod
    def __log_crud_operation(operation: str, reference_type: str, item_id: str = None, success: bool = True,
                             error: str = None):
        """Логирование CRUD операций"""
        context = {
            'operation': operation,
            'reference_type': reference_type,
            'item_id': item_id,
            'success': success
        }

        if error:
            context['error'] = error

        level = log_level.INFO if success else log_level.ERROR
        message = f"{operation} {reference_type}"
        if not success:
            message += " failed"

        crud_dto = log_event_dto.create(
            level=level,
            message=message,
            context=context
        )
        observe_service.create_event(event_type.crud_operation(), crud_dto)

    @staticmethod
    def get_all(reference_type: str):
        try:
            debug_dto = log_event_dto.create(
                level=log_level.DEBUG,
                message=f'Getting all {reference_type}',
                context={'reference_type': reference_type}
            )
            observe_service.create_event(event_type.log_debug(), debug_dto)
            key_map = {
                "nomenclature": reposity_manager.nomenclature_key(),
                "range": reposity_manager.range_key(),
                "group": reposity_manager.group_key(),
                "storage": reposity_manager.storage_key(),
            }
            key = key_map.get(reference_type.lower())
            if not key:
                raise operation_exception("Неверный тип справочника")
            items = prototype(reference_service.__manager.data.get(key, []))
            info_dto = log_event_dto.create(
                level=log_level.INFO,
                message=f'Retrieved all {reference_type}',
                context={'count': len(items.data)}
            )
            observe_service.create_event(event_type.log_info(), info_dto)
            reference_service.__log_crud_operation("GET_ALL", reference_type, success=True)
            return items
        except Exception as e:
            reference_service.__log_crud_operation("GET_ALL", reference_type, success=False, error=str(e))
            raise

    @staticmethod
    def get_by_id(reference_type: str, item_id: str):
        try:
            debug_dto = log_event_dto.create(
                level=log_level.DEBUG,
                message=f'Getting {reference_type} by ID',
                context={'reference_type': reference_type, 'item_id': item_id}
            )
            observe_service.create_event(event_type.log_debug(), debug_dto)
            items = reference_service.get_all(reference_type)
            for item in items.data:
                if item.unique_code == item_id:
                    info_dto = log_event_dto.create(
                        level=log_level.INFO,
                        message=f'{reference_type} found',
                        context={'item_id': item_id, 'name': item.name}
                    )
                    observe_service.create_event(event_type.log_info(), info_dto)
                    reference_service.__log_crud_operation("GET", reference_type, item_id, success=True)
                    return item
            not_found_dto = log_event_dto.create(
                level=log_level.INFO,
                message=f'{reference_type} not found',
                context={'item_id': item_id}
            )
            observe_service.create_event(event_type.log_info(), not_found_dto)
            reference_service.__log_crud_operation("GET", reference_type, item_id, success=False, error="Not found")
            return None

        except Exception as e:
            reference_service.__log_crud_operation("GET", reference_type, item_id, success=False, error=str(e))
            raise
    @staticmethod
    def add(reference_type: str, item):
        try:
            debug_dto = log_event_dto.create(
                level=log_level.DEBUG,
                message=f'Adding new {reference_type}',
                context={'reference_type': reference_type, 'item_name': getattr(item, 'name', 'Unknown')}
            )
            observe_service.create_event(event_type.log_debug(), debug_dto)
            key = {
                "nomenclature": reposity_manager.nomenclature_key(),
                "range": reposity_manager.range_key(),
                "group": reposity_manager.group_key(),
                "storage": reposity_manager.storage_key(),
            }[reference_type]
            reference_service.__manager.data[key].append(item)
            reference_service.__manager._start_manager__cache[item.unique_code] = item

            # Уведомляем наблюдателей
            observe_service.create_event(event_type.reference_added(), ReferenceEventDto(reference_type, item))
            reference_service.__save_to_file()
            info_dto = log_event_dto.create(
                level=log_level.INFO,
                message=f'{reference_type} added successfully',
                context={'id': item.unique_code, 'name': item.name}
            )
            observe_service.create_event(event_type.log_info(), info_dto)
            reference_service.__log_crud_operation("ADD", reference_type, item.unique_code, success=True)
            return item
        except Exception as e:
            reference_service.__log_crud_operation("ADD", reference_type, success=False, error=str(e))
            raise

    @staticmethod
    def update(reference_type: str, item_id: str, new_data):
        try:
            debug_dto = log_event_dto.create(
                level=log_level.DEBUG,
                message=f'Updating {reference_type}',
                context={'reference_type': reference_type, 'item_id': item_id}
            )
            observe_service.create_event(event_type.log_debug(), debug_dto)
            item = reference_service.get_by_id(reference_type, item_id)
            if not item:
                raise operation_exception("Элемент не найден")
            old_name = getattr(item, 'name', 'Unknown')

            # Обновляем поля
            for key, value in new_data.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            new_name = getattr(item, 'name', old_name)
            observe_service.create_event(
                event_type.reference_updated(),
                ReferenceEventDto(reference_type, item)
            )
            reference_service.__save_to_file()
            info_dto = log_event_dto.create(
                level=log_level.INFO,
                message=f'{reference_type} updated successfully',
                context={'item_id': item_id, 'old_name': old_name, 'new_name': new_name}
            )
            observe_service.create_event(event_type.log_info(), info_dto)
            reference_service.__log_crud_operation("UPDATE", reference_type, item_id, success=True)
            return item
        except Exception as e:
            reference_service.__log_crud_operation("UPDATE", reference_type, item_id, success=False, error=str(e))
            raise

    @staticmethod
    def delete(reference_type: str, item_id: str):
        try:
            debug_dto = log_event_dto.create(
                level=log_level.DEBUG,
                message=f'Deleting {reference_type}',
                context={'reference_type': reference_type, 'item_id': item_id}
            )
            observe_service.create_event(event_type.log_debug(), debug_dto)

            item = reference_service.get_by_id(reference_type, item_id)
            if not item:
                raise operation_exception("Элемент не найден")

            item_name = getattr(item, 'name', 'Unknown')

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
            info_dto = log_event_dto.create(
                level=log_level.INFO,
                message=f'{reference_type} deleted successfully',
                context={'item_id': item_id, 'name': item_name}
            )
            observe_service.create_event(event_type.log_info(), info_dto)
            reference_service.__log_crud_operation("DELETE", reference_type, item_id, success=True)
        except Exception as e:
            reference_service.__log_crud_operation("DELETE", reference_type, item_id, success=False, error=str(e))
            raise

    @staticmethod
    def __save_to_file():
        pass