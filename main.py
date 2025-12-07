import connexion
from flask import request, jsonify
from Src.Logics.reference_service import reference_service
from Src.Dtos.nomenclature_dto import nomenclature_dto
from Src.Dtos.range_dto import range_dto
from Src.Dtos.category_dto import category_dto
from Src.Dtos.storage_dto import storage_dto
import uuid
from Src.start_manager import start_manager
from Src.Core.observe_service import observe_service
from Src.Core.event_type import event_type
from Src.Core.validator import operation_exception
from Src.Dtos.reference_event_dto import ReferenceEventDto
from Src.Logics.dto_factory import DtoFactory
from Src.Logics.log_observer import log_observer
from Src.Core.log_level import log_level
from Src.Dtos.log_event_dto import log_event_dto
class ReferenceDeletionProtector:
    """Защита от удаления используемых справочников"""
    def handle(self, event: str, params):
        if event != event_type.before_reference_delete():
            return
        if not isinstance(params, ReferenceEventDto):
            return
        item = params.item
        ref_type = params.reference_type
        if not item or not ref_type:
            return
        manager = start_manager()
        data = manager.data

        # номенклатура
        if ref_type == "nomenclature":
            # проверяем транзакции
            for tr in data.get("transaction_key", []):
                if getattr(tr, "nomenclature", None) == item:
                    block_dto = log_event_dto.create(
                        level=log_level.INFO,
                        message='Attempt to delete used nomenclature blocked',
                        context={'item_id': item.unique_code, 'item_name': item.name}
                    )
                    observe_service.create_event(event_type.log_info(), block_dto)
                    raise operation_exception(f"Нельзя удалить {item.name} - есть движения по складу")

            # проверяем рецепты
            for receipt in data.get("receipt_model", []):
                for ri in receipt.composition:
                    if getattr(ri, "nomenclature", None) == item:
                        block_dto = log_event_dto.create(
                            level=log_level.INFO,
                            message='Attempt to delete nomenclature used in recipe blocked',
                            context={'item_id': item.unique_code, 'item_name': item.name, 'recipe': receipt.name}
                        )
                        observe_service.create_event(event_type.log_info(), block_dto)
                        raise operation_exception(
                            f"Нельзя удалить {item.name} -используется в рецепте «{receipt.name}»")

        # склад
        elif ref_type == "storage":
            for tr in data.get("transaction_key", []):
                if getattr(tr, "storage", None) == item:
                    block_dto = log_event_dto.create(
                        level=log_level.INFO,
                        message='Attempt to delete used storage blocked',
                        context={'item_id': item.unique_code, 'item_name': item.name}
                    )
                    observe_service.create_event(event_type.log_info(), block_dto)
                    raise operation_exception(f"Нельзя удалить склад {item.name}")

        # группа
        elif ref_type == "group":
            for nom in data.get("nomenclature_model", []):
                if getattr(nom, "group", None) == item:
                    block_dto = log_event_dto.create(
                        level=log_level.INFO,
                        message='Attempt to delete used group blocked',
                        context={'item_id': item.unique_code, 'item_name': item.name}
                    )
                    observe_service.create_event(event_type.log_info(), block_dto)
                    raise operation_exception(f"Нельзя удалить группу {item.name}")


def __log_web_call(method: str, path: str, params: dict = None):
    """Логирование веб-вызовов"""
    context = {
        'method': method,
        'path': path,
        'params': params
    }

    web_dto = log_event_dto.create(
        level=log_level.DEBUG,
        message='Web API call',
        context=context
    )
    observe_service.create_event(event_type.web_call(), web_dto)
app = connexion.FlaskApp(__name__)

service = start_manager()
service.start()
observe_service.add(ReferenceDeletionProtector())

logger = log_observer()
observe_service.add(logger)

#логируем запуск системы
system_start_dto = log_event_dto.create(
    level=log_level.INFO,
    message='System started',
    context={'host': '0.0.0.0', 'port': 8080}
)
observe_service.create_event(event_type.log_info(), system_start_dto)
"""
Проверить доступность REST API
"""
@app.route("/api/accessibility", methods=['GET'])
def accessibility():
    __log_web_call('GET', '/api/accessibility')
    accessibility_dto = log_event_dto.create(
        level=log_level.INFO,
        message='Accessibility check',
        context={'endpoint': '/api/accessibility'}
    )
    observe_service.create_event(event_type.log_info(), accessibility_dto)
    return "SUCCESS"

@app.route("/api/<reference_type>", methods=["GET"])
def api_get_references(reference_type: str):
    __log_web_call('GET', f'/api/{reference_type}')

    try:
        if reference_type not in ["nomenclature", "range", "group", "storage"]:
            error_dto = log_event_dto.create(
                level=log_level.ERROR,
                message='Invalid reference type',
                context={'reference_type': reference_type}
            )
            observe_service.create_event(event_type.log_error(), error_dto)
            return jsonify({"error": "Неверный тип"}), 400
        items = reference_service.get_all(reference_type)
        info_dto = log_event_dto.create(
            level=log_level.INFO,
            message=f'Retrieved {reference_type} list',
            context={'count': len(items.data)}
        )
        observe_service.create_event(event_type.log_info(), info_dto)

        return jsonify([item.to_dto().__dict__ for item in items.data])
    except Exception as e:
        observe_service.create_event(event_type.log_error(), {
            'level': log_level.ERROR,
            'message': f'Error getting {reference_type} list',
            'context': {'error': str(e)}
        })
        return jsonify({"error": str(e)}), 500


@app.route("/api/<reference_type>/<item_id>", methods=["GET"])
def api_get_reference_by_id(reference_type: str, item_id: str):
    __log_web_call('GET', f'/api/{reference_type}/{item_id}')

    try:
        item = reference_service.get_by_id(reference_type, item_id)
        if not item:
            not_found_dto = log_event_dto.create(
                level=log_level.INFO,
                message=f'{reference_type} not found',
                context={'item_id': item_id}
            )
            observe_service.create_event(event_type.log_info(), not_found_dto)
            return jsonify({"error": "Не найдено"}), 404

        retrieved_dto = log_event_dto.create(
            level=log_level.INFO,
            message=f'{reference_type} retrieved',
            context={'item_id': item_id, 'name': item.name}
        )
        observe_service.create_event(event_type.log_info(), retrieved_dto)

        return jsonify(item.to_dto().__dict__)
    except Exception as e:
        error_dto = log_event_dto.create(
            level=log_level.ERROR,
            message=f'Error getting {reference_type}',
            context={'item_id': item_id, 'error': str(e)}
        )
        observe_service.create_event(event_type.log_error(), error_dto)
        return jsonify({"error": str(e)}), 500


@app.route("/api/<reference_type>", methods=["PUT"])
def api_add_reference(reference_type: str):
    __log_web_call('PUT', f'/api/{reference_type}', request.get_json())
    try:
        data = request.get_json()
        data["id"] = str(uuid.uuid4())
        debug_dto = log_event_dto.create(
            level=log_level.DEBUG,
            message=f'Creating new {reference_type}',
            context={'data': data}
        )
        observe_service.create_event(event_type.log_debug(), debug_dto)
        dto = DtoFactory.create(reference_type, data)
        item = reference_service.add(reference_type, dto)
        info_dto = log_event_dto.create(
            level=log_level.INFO,
            message=f'{reference_type} created',
            context={'id': item.unique_code, 'name': getattr(item, 'name', 'Unknown')}
        )
        observe_service.create_event(event_type.log_info(), info_dto)
        return jsonify(item.to_dto().__dict__), 201
    except Exception as e:
        error_dto = log_event_dto.create(
            level=log_level.ERROR,
            message=f'Error creating {reference_type}',
            context={'error': str(e)}
        )
        observe_service.create_event(event_type.log_error(), error_dto)
        return jsonify({"error": str(e)}), 500


@app.route("/api/<reference_type>/<item_id>", methods=["PATCH"])
def api_update_reference(reference_type: str, item_id: str):
    __log_web_call('PATCH', f'/api/{reference_type}/{item_id}', request.get_json())

    try:
        data = request.get_json()
        data["id"] = item_id
        observe_service.create_event(event_type.log_debug(), {
            'level': log_level.DEBUG,
            'message': f'Updating {reference_type}',
            'context': {'item_id': item_id, 'data': data}
        })
        dto = DtoFactory.create(reference_type, data)
        item = reference_service.update(reference_type, item_id, dto)
        observe_service.create_event(event_type.log_info(), {
            'level': log_level.INFO,
            'message': f'{reference_type} updated',
            'context': {'item_id': item_id, 'name': getattr(item, 'name', 'Unknown')}
        })

        return jsonify(item.to_dto().__dict__)
    except Exception as e:
        observe_service.create_event(event_type.log_error(), {
            'level': log_level.ERROR,
            'message': f'Error updating {reference_type}',
            'context': {'item_id': item_id, 'error': str(e)}
        })
        return jsonify({"error": str(e)}), 500


@app.route("/api/<reference_type>/<item_id>", methods=["DELETE"])
def api_delete_reference(reference_type: str, item_id: str):
    __log_web_call('DELETE', f'/api/{reference_type}/{item_id}')

    try:
        debug_dto = log_event_dto.create(
            level=log_level.DEBUG,
            message=f'Deleting {reference_type}',
            context={'reference_type': reference_type, 'item_id': item_id}
        )
        observe_service.create_event(event_type.log_debug(), debug_dto)
        reference_service.delete(reference_type, item_id)
        info_dto = log_event_dto.create(
            level=log_level.INFO,
            message=f'{reference_type} deleted',
            context={'item_id': item_id}
        )
        observe_service.create_event(event_type.log_info(), info_dto)
        return jsonify({"success": True})
    except Exception as e:
        error_dto = log_event_dto.create(
            level=log_level.ERROR,
            message=f'Error deleting {reference_type}',
            context={'item_id': item_id, 'error': str(e)}
        )
        observe_service.create_event(event_type.log_error(), error_dto)
        return jsonify({"error": str(e)}), 400
if __name__ == '__main__':
    app.run(host="0.0.0.0", port = 8080)
