"""
Configuration settings for EMR Cost Optimizer
"""
import os

# AWS Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_PROFILE = os.environ.get('AWS_PROFILE', None)  # Uses default credentials chain if None

# Cluster Classification
# Transient cluster pattern: STRESS-XXXXXX-{S,L,XL}
TRANSIENT_CLUSTER_PATTERN = r'^STRESS-\d+-(?:S|L|XL)$'
LONG_RUNNING_THRESHOLD_HOURS = 7  # Clusters running longer than this are considered long-running

# Metrics Configuration
CLOUDWATCH_PERIOD_SECONDS = 300  # 5-minute resolution
MAX_LOOKBACK_DAYS = 3  # Maximum lookback for long-running clusters
TRANSIENT_LOOKBACK_HOURS = 4  # Lookback for transient clusters

# CloudWatch Namespaces and Metrics
EC2_NAMESPACE = 'AWS/EC2'
CWAGENT_NAMESPACE = 'CWAgent'
CPU_METRIC_NAME = 'CPUUtilization'
MEMORY_METRIC_NAME = 'mem_used_percent'

# Analysis Thresholds
THRESHOLDS = {
    'heavily_oversized': {
        'avg_max': 25,
        'peak_max': 35
    },
    'moderately_oversized': {
        'avg_max': 50,
        'peak_max': 60
    },
    'right_sized': {
        'avg_max': 70,
        'peak_max': 80
    }
    # Above right_sized thresholds = undersized
}

# Headroom buffer for recommendations
HEADROOM_PERCENT = 20

# Data persistence
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
ANALYSIS_HISTORY_FILE = os.path.join(DATA_DIR, 'analysis_history.json')
