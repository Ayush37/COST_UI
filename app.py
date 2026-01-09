"""
EMR Cost Optimizer - Flask Application
"""
from flask import Flask, jsonify, render_template, request
from services.emr_service import EMRService
from services.analyzer_service import AnalyzerService
import config

app = Flask(__name__)

# Initialize services
emr_service = EMRService()
analyzer_service = AnalyzerService()


@app.route('/')
def index():
    """Render the main landing page"""
    return render_template('home.html', active_service=None)


@app.route('/emr')
def emr():
    """Render the EMR cost optimizer dashboard"""
    return render_template('emr.html', active_service='emr')


@app.route('/api/config/lookback-options', methods=['GET'])
def get_lookback_options():
    """Get available lookback period options"""
    return jsonify({
        'success': True,
        'data': {
            'options': config.LOOKBACK_OPTIONS,
            'default_hours': config.DEFAULT_LOOKBACK_HOURS
        }
    })


@app.route('/api/clusters', methods=['GET'])
def get_clusters():
    """
    Get all EMR clusters including running and recently terminated.
    Returns clusters segregated by type (TRANSIENT, LONG_RUNNING) and state.

    Query params:
        include_terminated: Include clusters terminated in last 3 hours (default: true)
    """
    try:
        # Get running clusters
        running_clusters = emr_service.list_running_clusters()

        # Check if we should include terminated clusters
        include_terminated = request.args.get('include_terminated', 'true').lower() == 'true'

        terminated_clusters = []
        if include_terminated:
            terminated_clusters = emr_service.list_recently_terminated_clusters(hours=3)

        # Segregate running clusters by type
        transient_clusters = [c for c in running_clusters if c['cluster_type'] == 'TRANSIENT']
        long_running_clusters = [c for c in running_clusters if c['cluster_type'] == 'LONG_RUNNING']

        # Segregate terminated clusters by type
        terminated_transient = [c for c in terminated_clusters if c['cluster_type'] == 'TRANSIENT']
        terminated_long_running = [c for c in terminated_clusters if c['cluster_type'] == 'LONG_RUNNING']

        # Sort by runtime
        transient_clusters.sort(key=lambda x: x['runtime_hours'], reverse=True)
        long_running_clusters.sort(key=lambda x: x['runtime_hours'], reverse=True)
        terminated_transient.sort(key=lambda x: x['runtime_hours'], reverse=True)
        terminated_long_running.sort(key=lambda x: x['runtime_hours'], reverse=True)

        return jsonify({
            'success': True,
            'data': {
                'transient': transient_clusters,
                'long_running': long_running_clusters,
                'terminated': terminated_transient + terminated_long_running,
                'terminated_transient': terminated_transient,
                'terminated_long_running': terminated_long_running,
                'total_count': len(running_clusters),
                'transient_count': len(transient_clusters),
                'long_running_count': len(long_running_clusters),
                'terminated_count': len(terminated_clusters)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/clusters/<cluster_id>', methods=['GET'])
def get_cluster(cluster_id):
    """Get details for a specific cluster"""
    try:
        cluster = emr_service.get_cluster_by_id(cluster_id)
        if not cluster:
            return jsonify({
                'success': False,
                'error': f'Cluster {cluster_id} not found'
            }), 404

        return jsonify({
            'success': True,
            'data': cluster
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/clusters/<cluster_id>/analyze', methods=['POST'])
def analyze_cluster(cluster_id):
    """
    Analyze a cluster's utilization and generate recommendations.
    This endpoint triggers the full analysis pipeline.

    Query params:
        lookback_hours: Number of hours to look back for metrics (default: from config)
    """
    try:
        # Get lookback hours from request (query param or JSON body)
        lookback_hours = None
        if request.is_json and request.json:
            lookback_hours = request.json.get('lookback_hours')
        if not lookback_hours:
            lookback_hours = request.args.get('lookback_hours', type=int)
        if not lookback_hours:
            lookback_hours = config.DEFAULT_LOOKBACK_HOURS

        analysis = analyzer_service.analyze_cluster(cluster_id, lookback_hours=lookback_hours)

        if 'error' in analysis:
            return jsonify({
                'success': False,
                'error': analysis['error']
            }), 404

        return jsonify({
            'success': True,
            'data': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/clusters/<cluster_id>/analysis', methods=['GET'])
def get_cluster_analysis(cluster_id):
    """Get the latest analysis for a cluster (if available)"""
    try:
        analysis = analyzer_service.get_latest_analysis(cluster_id)

        if not analysis:
            return jsonify({
                'success': True,
                'data': None,
                'message': 'No analysis available for this cluster'
            })

        return jsonify({
            'success': True,
            'data': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analysis/history', methods=['GET'])
def get_analysis_history():
    """Get analysis history for all clusters or a specific cluster"""
    try:
        cluster_id = request.args.get('cluster_id')
        history = analyzer_service.get_analysis_history(cluster_id)

        return jsonify({
            'success': True,
            'data': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'emr-cost-optimizer'
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
