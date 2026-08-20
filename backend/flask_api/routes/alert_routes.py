from flask import Blueprint, request, jsonify
from backend.services.database_service import db_service
from backend.services.logging_service import logger_service

alert_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

@alert_bp.route('/', methods=['GET'])
def get_alerts():
    """
    GET /api/alerts
    """
    try:
        alerts = db_service.get_active_alerts()
        return jsonify({"alerts": alerts}), 200
    except Exception as e:
        logger_service.log_error(e, {"context": "API get_alerts"})
        return jsonify({"error": "Internal server error"}), 500

@alert_bp.route('/<alert_id>/acknowledge', methods=['PUT'])
def acknowledge_alert(alert_id: str):
    """
    PUT /api/alerts/{alert_id}/acknowledge
    """
    try:
        success = db_service.acknowledge_alert(alert_id)
        if success:
            return jsonify({"message": "Alert acknowledged"}), 200
        return jsonify({"error": "Alert not found"}), 404
    except Exception as e:
        logger_service.log_error(e, {"context": f"API acknowledge_alert {alert_id}"})
        return jsonify({"error": "Internal server error"}), 500

@alert_bp.route('/<alert_id>/resolve', methods=['PUT'])
def resolve_alert(alert_id: str):
    """
    PUT /api/alerts/{alert_id}/resolve
    """
    try:
        success = db_service.resolve_alert(alert_id)
        if success:
            return jsonify({"message": "Alert resolved"}), 200
        return jsonify({"error": "Alert not found"}), 404
    except Exception as e:
        logger_service.log_error(e, {"context": f"API resolve_alert {alert_id}"})
        return jsonify({"error": "Internal server error"}), 500
