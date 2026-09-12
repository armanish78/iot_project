from flask import Blueprint, request, jsonify
from backend.services.live_inference_service import live_inference_service
from backend.services.database_service import db_service
from backend.services.logging_service import logger_service

prediction_bp = Blueprint('predictions', __name__, url_prefix='/api/predictions')

@prediction_bp.route('/detect', methods=['POST'])
def detect_threat():
    """
    POST /api/predictions/detect
    """
    try:
        data = request.get_json()
        if not data or 'features' not in data or 'flow_meta' not in data:
            return jsonify({"error": "Invalid data. Expected 'features' and 'flow_meta'."}), 400
            
        prediction = live_inference_service.predict(
            features=data['features'], 
            flow_meta=data['flow_meta'], 
            run_id='offline_test',
            skip_correlation=True
        )
        return jsonify(prediction), 200
    except Exception as e:
        logger_service.log_error(e, {"context": "API detect_threat"})
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@prediction_bp.route('/history', methods=['GET'])
def get_prediction_history():
    """
    GET /api/predictions/history?limit=100
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        history = db_service.get_prediction_history(limit)
        return jsonify(history), 200
    except Exception as e:
        logger_service.log_error(e, {"context": "API get_prediction_history"})
        return jsonify({"error": "Internal server error"}), 500
