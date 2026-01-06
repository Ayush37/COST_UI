"""
EMR Cost Optimizer - Flask Application
"""
from flask import Flask, jsonify, render_template, request
from services.emr_service import EMRService
from services.analyzer_service import AnalyzerService

app = Flask(__name__)

# Initialize services
emr_service = EMRService()
analyzer_service = AnalyzerService()


@app.route('/')
def index():
    """Render the main dashboard"""
    return render_template('index.html')


@app.route('/api/clusters', methods=['GET'])
def get_clusters():
    """
    Get all running EMR clusters.
    Returns clusters segregated by type (TRANSIENT, LONG_RUNNING).
    """
    try:
        clusters = emr_service.list_running_clusters()

        # Segregate by type
        transient_clusters = [c for c in clusters if c['cluster_type'] == 'TRANSIENT']
        long_running_clusters = [c for c in clusters if c['cluster_type'] == 'LONG_RUNNING']

        # Sort by runtime
        transient_clusters.sort(key=lambda x: x['runtime_hours'], reverse=True)
        long_running_clusters.sort(key=lambda x: x['runtime_hours'], reverse=True)

        return jsonify({
            'success': True,
            'data': {
                'transient': transient_clusters,
                'long_running': long_running_clusters,
                'total_count': len(clusters),
                'transient_count': len(transient_clusters),
                'long_running_count': len(long_running_clusters)
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
    """
    try:
        analysis = analyzer_service.analyze_cluster(cluster_id)

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
