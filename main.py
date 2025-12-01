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


class ReferenceDeletionProtector:
    """Защита от удаления используемых справочников"""
    def handle(self, event: str, params: dict):
        if event != event_type.before_reference_delete():
            return
        item = params.get("item")
        ref_type = params.get("type")
        if not item or not ref_type:
            return
        manager = start_manager()
        data = manager.data

        #номенклатура
        if ref_type == "nomenclature":
            #проверяем транзакции
            for tr in data.get("transaction_key", []):
                if getattr(tr, "nomenclature", None) == item:
                    raise operation_exception(f"Нельзя удалить {item.name} - есть движения по складу")

            #проверяем рецепты
            for receipt in data.get("receipt_model", []):
                for ri in receipt.composition:
                    if getattr(ri, "nomenclature", None) == item:
                        raise operation_exception(
                            f"Нельзя удалить {item.name} -используется в рецепте «{receipt.name}»")

        #склад
        elif ref_type == "storage":
            for tr in data.get("transaction_key", []):
                if getattr(tr, "storage", None) == item:
                    raise operation_exception(f"Нельзя удалить склад {item.name}")

        #группа
        elif ref_type == "group":
            for nom in data.get("nomenclature_model", []):
                if getattr(nom, "group", None) == item:
                    raise operation_exception(f"Нельзя удалить группу {item.name}")
app = connexion.FlaskApp(__name__)

service = start_manager()
service.start()
observe_service.add(ReferenceDeletionProtector())
"""
Проверить доступность REST API
"""
@app.route("/api/accessibility", methods=['GET'])
def accessibility():
    return "SUCCESS"

@app.route("/api/<reference_type>", methods=["GET"])
def api_get_references(reference_type: str):
    try:
        if reference_type not in ["nomenclature", "range", "group", "storage"]:
            return jsonify({"error": "Неверный тип"}), 400
        items = reference_service.get_all(reference_type)
        return jsonify([item.to_dto().__dict__ for item in items.data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/<reference_type>/<item_id>", methods=["GET"])
def api_get_reference_by_id(reference_type: str, item_id: str):
    try:
        item = reference_service.get_by_id(reference_type, item_id)
        if not item:
            return jsonify({"error": "Не найдено"}), 404
        return jsonify(item.to_dto().__dict__)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/<reference_type>", methods=["PUT"])
def api_add_reference(reference_type: str):
    try:
        data = request.get_json()
        data["id"] = str(uuid.uuid4())
        if reference_type == "nomenclature":
            dto = nomenclature_dto().create(data)
        elif reference_type == "range":
            dto = range_dto().create(data)
        elif reference_type == "group":
            dto = category_dto().create(data)
        elif reference_type == "storage":
            dto = storage_dto().create(data)
        else:
            return jsonify({"error": "Неверный тип"}), 400
        item = reference_service.add(reference_type, dto)
        return jsonify(item.to_dto().__dict__), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/<reference_type>/<item_id>", methods=["PATCH"])
def api_update_reference(reference_type: str, item_id: str):
    try:
        data = request.get_json()
        data["id"] = item_id
        if reference_type == "nomenclature":
            dto = nomenclature_dto().create(data)
        elif reference_type == "range":
            dto = range_dto().create(data)
        elif reference_type == "group":
            dto = category_dto().create(data)
        elif reference_type == "storage":
            dto = storage_dto().create(data)
        else:
            return jsonify({"error": "Неверный тип"}), 400
        item = reference_service.update(reference_type, item_id, dto)
        return jsonify(item.to_dto().__dict__)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/<reference_type>/<item_id>", methods=["DELETE"])
def api_delete_reference(reference_type: str, item_id: str):
    try:
        reference_service.delete(reference_type, item_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
if __name__ == '__main__':
    app.run(host="0.0.0.0", port = 8080)
