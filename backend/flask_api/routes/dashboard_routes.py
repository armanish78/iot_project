from flask import Blueprint, jsonify, request
from backend.database.db_models import db, Prediction
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/stats', methods=['GET'])
def get_statistics():
    """
    GET /api/dashboard/stats
    """
    try:
        total = Prediction.query.count()
        threats = Prediction.query.filter_by(threat=True).count()
        
        rate = 0
        if total > 0:
            rate = threats / total
            
        return jsonify({
            "stats": {
                "total_connections": total,
                "threats_detected": threats,
                "threat_rate": round(rate, 4),
                "timestamp": datetime.utcnow().isoformat()
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/activity', methods=['GET'])
def get_live_activity():
    """
    GET /api/dashboard/activity?limit=50
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        recent = Prediction.query.order_by(Prediction.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            "activity": [{
                "id": p.id,
                "source_ip": p.source_ip,
                "dest_ip": p.dest_ip,
                "threat": p.threat,
                "timestamp": p.timestamp.isoformat()
            } for p in recent]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@dashboard_bp.route('/threat-timeline', methods=['GET'])
def get_threat_timeline():
    """
    GET /api/dashboard/threat-timeline?hours=24
    """
    try:
        hours = request.args.get('hours', 24, type=int)
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # In a real scenario, this would aggregate by hour.
        # Here we just fetch recent threats.
        threats = Prediction.query.filter(Prediction.threat == True, Prediction.timestamp >= cutoff).all()
        
        return jsonify({
            "timeline": [{
                "timestamp": t.timestamp.isoformat(),
                "type": t.threat_type
            } for t in threats]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
