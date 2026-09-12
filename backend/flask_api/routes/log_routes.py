from flask import Blueprint, jsonify
import os

log_bp = Blueprint('logs', __name__, url_prefix='/api/logs')

@log_bp.route('/', methods=['GET'])
def get_logs():
    """
    GET /api/logs
    """
    log_file_path = 'backend/logs/predictions.log'
    logs = []
    try:
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as f:
                # Read last 100 lines for simplicity
                lines = f.readlines()[-100:]
                logs = [line.strip() for line in lines]
                
        return jsonify({"logs": logs}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
