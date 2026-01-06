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

# Configurable lookback options (in hours) for the UI
LOOKBACK_OPTIONS = [
    {'label': 'Last 1 hour', 'hours': 1},
    {'label': 'Last 3 hours', 'hours': 3},
    {'label': 'Last 6 hours', 'hours': 6},
    {'label': 'Last 12 hours', 'hours': 12},
    {'label': 'Last 24 hours', 'hours': 24},
    {'label': 'Last 3 days', 'hours': 72},
    {'label': 'Last 7 days', 'hours': 168},
    {'label': 'Last 14 days', 'hours': 336},
]
DEFAULT_LOOKBACK_HOURS = 72  # Default to 3 days

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

# Sustained Peak Analysis Settings
SUSTAINED_PEAK_THRESHOLD_MINUTES = 10  # Peak must be sustained for this long to be used for sizing
SPIKE_DETECTION_GAP_PERCENT = 15  # If gap between P90 and P95 > this, it's likely a spike
UTILIZATION_THRESHOLDS = [70, 80, 90]  # Thresholds for duration tracking

# Headroom buffer for recommendations
HEADROOM_PERCENT = 20

# Data persistence
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
ANALYSIS_HISTORY_FILE = os.path.join(DATA_DIR, 'analysis_history.json')
