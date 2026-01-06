# EMR Cost Optimizer

A web-based tool for analyzing AWS EMR cluster utilization and providing cost optimization recommendations.

## Overview

This tool helps identify oversized EMR clusters by analyzing CPU and memory utilization metrics from CloudWatch, then recommends appropriately-sized EC2 instances that can reduce costs while meeting workload requirements.

## Architecture

```
emr-cost-optimizer/
├── app.py                      # Flask application entry point
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── claude.md                   # This documentation file
├── data/
│   └── analysis_history.json   # Persisted analysis results
├── services/
│   ├── __init__.py
│   ├── emr_service.py          # EMR cluster operations
│   ├── cloudwatch_service.py   # CloudWatch metrics collection
│   ├── pricing_service.py      # EC2 pricing data (static)
│   └── analyzer_service.py     # Analysis and recommendation engine
├── static/
│   ├── css/
│   │   └── style.css           # Custom styles
│   └── js/
│       └── app.js              # Frontend JavaScript
└── templates/
    └── index.html              # Main UI template
```

## Key Components

### Services

#### EMRService (`services/emr_service.py`)
- Lists running EMR clusters
- Retrieves cluster details including instance groups
- Classifies clusters as TRANSIENT or LONG_RUNNING
- Gets EC2 instance IDs for each instance group

**Cluster Classification Logic:**
- TRANSIENT: Cluster name matches pattern `STRESS-\d+-(?:S|L|XL)` OR runtime < 7 hours
- LONG_RUNNING: Runtime > 7 hours (excluding pattern matches)

#### CloudWatchService (`services/cloudwatch_service.py`)
- Fetches CPU metrics from `AWS/EC2` namespace
- Fetches memory metrics from `CWAgent` namespace (`mem_used_percent`)
- Calculates average, p95 (peak), min, max for each metric
- Aggregates metrics across multiple instances in a group

**Lookback Periods:**
- TRANSIENT clusters: 4 hours
- LONG_RUNNING clusters: 3 days or since cluster start (whichever is shorter)

#### PricingService (`services/pricing_service.py`)
- Static pricing data for EC2 instances in us-east-1
- Covers instance families: m5, m5a, m6i, m7i, c5, c5a, c6i, c7i, r5, r5a, r6i, r7i, i3, d2
- Provides instance specifications (vCPUs, memory, hourly price)
- Finds suitable instances based on resource requirements

#### AnalyzerService (`services/analyzer_service.py`)
- Orchestrates the full analysis pipeline
- Determines workload profile (CPU-heavy, Memory-heavy, Balanced)
- Calculates sizing status based on utilization thresholds
- Generates recommendations with cost savings calculations
- Persists analysis results to JSON

### Recommendation Logic

#### Sizing Status Thresholds
Uses the HIGHER of CPU and Memory utilization:

| Status | Average | Peak (P95) | Action |
|--------|---------|------------|--------|
| Heavily Oversized | < 25% | < 35% | Suggest 2 sizes down |
| Moderately Oversized | < 50% | < 60% | Suggest 1 size down |
| Right-Sized | < 70% | < 80% | No change needed |
| Undersized | >= 70% | >= 80% | Consider upsizing |

#### Workload Profile Detection
- **CPU Heavy**: CPU utilization > 1.5x Memory utilization
- **Memory Heavy**: Memory utilization > 1.5x CPU utilization
- **Balanced**: Both within 1.5x of each other

#### Recommendation Types
1. **Same Family**: Smaller instance in current family (e.g., r5.2xlarge → r5.xlarge)
2. **Cross Family**: Cheapest instance meeting requirements across all families
3. **Category Optimized**: Best instance for workload profile (compute/memory/general)

#### Headroom Calculation
Required resources = (Current specs × Peak utilization) × 1.2 (20% headroom)

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main dashboard UI |
| GET | `/api/clusters` | List all running clusters |
| GET | `/api/clusters/<id>` | Get cluster details |
| POST | `/api/clusters/<id>/analyze` | Trigger cluster analysis |
| GET | `/api/clusters/<id>/analysis` | Get latest analysis |
| GET | `/api/analysis/history` | Get analysis history |
| GET | `/api/health` | Health check |

### Frontend

- Bootstrap 5 for styling
- Vanilla JavaScript (no framework)
- Real-time analysis with loading states
- Modal-based detailed analysis view
- Responsive design

## Configuration

Key settings in `config.py`:

```python
AWS_REGION = 'us-east-1'
CLOUDWATCH_PERIOD_SECONDS = 300  # 5-minute resolution
MAX_LOOKBACK_DAYS = 3
TRANSIENT_LOOKBACK_HOURS = 4
HEADROOM_PERCENT = 20

THRESHOLDS = {
    'heavily_oversized': {'avg_max': 25, 'peak_max': 35},
    'moderately_oversized': {'avg_max': 50, 'peak_max': 60},
    'right_sized': {'avg_max': 70, 'peak_max': 80}
}
```

## Running the Application

### Prerequisites
- Python 3.8+
- AWS credentials configured (`~/.aws/credentials`)
- IAM permissions for EMR, EC2, and CloudWatch read access

### Installation
```bash
cd emr-cost-optimizer
pip install -r requirements.txt
```

### Start Server
```bash
python app.py
```

Access at: http://localhost:5000

## Data Persistence

Analysis results are stored in `data/analysis_history.json`:
- Keyed by cluster ID
- Last 10 analyses kept per cluster
- Includes full metrics, recommendations, and timestamps

## Important Notes

### Task Node Metrics for Long-Running Clusters
Task nodes in long-running clusters scale up/down frequently. Since EC2 only retains 3 hours of CloudWatch metrics for terminated instances, task node metrics may be unavailable or partial. The UI shows appropriate warnings when this occurs.

### Memory Metrics Requirement
Memory metrics require CloudWatch Agent installed on EMR nodes with `mem_used_percent` metric enabled. If CWAgent is not configured, only CPU analysis will be available.

### Pricing Data
Static pricing for us-east-1 region. Update `services/pricing_service.py` if:
- Using a different region
- New instance types are needed
- Prices have changed significantly

## Extending the Tool

### Adding New Instance Types
Edit `INSTANCE_DATA` in `services/pricing_service.py`:
```python
'new.instance': {
    'vcpus': X,
    'memory_gb': Y,
    'price': Z.ZZ,
    'family': 'new',
    'generation': N,
    'category': 'general|compute|memory|storage'
}
```

### Modifying Thresholds
Edit `THRESHOLDS` in `config.py` to adjust when instances are considered oversized/undersized.

### Adding Regions
1. Update `AWS_REGION` in config
2. Update pricing data in `pricing_service.py` (prices vary by region)

## Troubleshooting

### No clusters showing
- Verify AWS credentials are configured
- Check IAM permissions for `elasticmapreduce:ListClusters`, `elasticmapreduce:DescribeCluster`
- Ensure clusters are in RUNNING or WAITING state

### No metrics available
- Verify CloudWatch permissions
- For memory: ensure CWAgent is installed and configured
- Check if instances have been running long enough to generate metrics

### Analysis taking too long
- Large clusters with many nodes require more API calls
- CloudWatch API has rate limits; analysis may queue requests

## Contributing

When modifying:
1. Follow existing code patterns
2. Update this documentation for significant changes
3. Test with both transient and long-running clusters
4. Verify recommendations make sense for edge cases
