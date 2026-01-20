# Cost Recommendation Engine - Technical Documentation

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [EMR Cost Optimizer (Implemented)](#emr-cost-optimizer-implemented)
   - [Architecture Overview](#architecture-overview)
   - [Tech Stack](#tech-stack)
   - [UI Design Principles](#ui-design-principles)
   - [Metrics Collection](#metrics-collection)
   - [Analysis Logic](#analysis-logic)
   - [Recommendation Engine](#recommendation-engine)
   - [API Endpoints](#api-endpoints)
   - [Data Persistence](#data-persistence)
   - [IAM Permissions](#iam-permissions)
3. [ECS Cost Optimizer (Proposed)](#ecs-cost-optimizer-proposed)
4. [EKS Cost Optimizer (Proposed)](#eks-cost-optimizer-proposed)
5. [DynamoDB Cost Optimizer (Proposed)](#dynamodb-cost-optimizer-proposed)
6. [Glue Cost Optimizer (Proposed)](#glue-cost-optimizer-proposed)
7. [Production Recommendations](#production-recommendations)
8. [Appendix](#appendix)

---

## Executive Summary

The **Cost Recommendation Engine** is a web-based platform designed to analyze AWS resource utilization across multiple services and provide actionable cost optimization recommendations. The platform identifies over-provisioned resources, calculates potential savings, and suggests right-sized alternatives.

### Current Status

| Service | Status | Savings Potential |
|---------|--------|-------------------|
| EMR | Implemented | High - Instance right-sizing |
| ECS | Planned | High - Task/Service optimization |
| EKS | Planned | High - Node & Pod optimization |
| DynamoDB | Planned | Medium - Capacity mode optimization |
| Glue | Planned | Medium - DPU right-sizing |

### Key Capabilities

- **Utilization Analysis**: Collect and analyze CPU/Memory metrics from CloudWatch
- **Intelligent Classification**: Categorize resources as oversized, right-sized, or undersized
- **Smart Recommendations**: Provide same-family, cross-family, and workload-optimized alternatives
- **Savings Calculator**: Quantify potential monthly cost savings
- **Multi-Service Dashboard**: Unified portal for all AWS cost optimization needs

---

## EMR Cost Optimizer (Implemented)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER BROWSER                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Frontend (Bootstrap 5)                        │   │
│  │  - Landing Page (Savings Overview)                                   │   │
│  │  - EMR Dashboard (Cluster List, Analysis Modal)                      │   │
│  │  - Sidebar Navigation                                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP/REST
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLASK APPLICATION                                  │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   app.py     │  │ emr_service  │  │ cloudwatch_  │  │  analyzer_   │   │
│  │   (Routes)   │  │    .py       │  │  service.py  │  │  service.py  │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│         │                 │                 │                 │            │
│         │                 │                 │                 │            │
│  ┌──────────────┐  ┌──────────────┐                   ┌──────────────┐   │
│  │   config.py  │  │   pricing_   │                   │    data/     │   │
│  │ (Thresholds) │  │  service.py  │                   │ history.json │   │
│  └──────────────┘  └──────────────┘                   └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ AWS SDK (boto3)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS SERVICES                                    │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │     EMR      │  │  CloudWatch  │  │     EC2      │                      │
│  │              │  │              │  │              │                      │
│  │ - Clusters   │  │ - CPU Metrics│  │ - Instance   │                      │
│  │ - Instance   │  │   (AWS/EC2)  │  │   Details    │                      │
│  │   Groups     │  │ - Memory     │  │              │                      │
│  │              │  │   (CWAgent)  │  │              │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

#### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Runtime** | Python 3.8+ | Core application runtime |
| **Web Framework** | Flask 2.x | REST API and template rendering |
| **AWS SDK** | boto3 | AWS service integration |
| **Configuration** | Python module (config.py) | Centralized settings |

#### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **CSS Framework** | Bootstrap 5.3.2 | Responsive layout, components |
| **Icons** | Bootstrap Icons 1.11.1 | UI iconography |
| **JavaScript** | Vanilla JS (ES6+) | Dynamic interactions, API calls |
| **Templating** | Jinja2 | Server-side HTML rendering |

#### Project Structure

```
emr-cost-optimizer/
├── app.py                      # Flask application entry point
├── config.py                   # Configuration settings & thresholds
├── requirements.txt            # Python dependencies
│
├── services/
│   ├── __init__.py
│   ├── emr_service.py          # EMR cluster operations
│   ├── cloudwatch_service.py   # CloudWatch metrics collection
│   ├── pricing_service.py      # EC2 pricing data (static)
│   └── analyzer_service.py     # Analysis and recommendation engine
│
├── data/
│   └── analysis_history.json   # Persisted analysis results
│
├── static/
│   ├── css/
│   │   └── style.css           # Custom styles (800+ lines)
│   └── js/
│       └── app.js              # Frontend JavaScript (900+ lines)
│
└── templates/
    ├── base.html               # Base template with sidebar
    ├── home.html               # Landing page
    └── emr.html                # EMR dashboard
```

### UI Design Principles

The UI follows these core principles to ensure a professional, consistent experience:

#### 1. Color Palette

```css
:root {
    --primary-color: #0d6efd;    /* Actions, active states */
    --success-color: #198754;    /* Savings, positive indicators */
    --warning-color: #ffc107;    /* Caution, moderate issues */
    --danger-color: #dc3545;     /* Critical, heavily oversized */
    --info-color: #0dcaf0;       /* Information, transient items */
    --dark-bg: #1a1d21;          /* Headers, navbar */
    --card-bg: #ffffff;          /* Card backgrounds */
    --border-color: #e9ecef;     /* Subtle borders */
    --text-muted: #6c757d;       /* Secondary text */
    --body-bg: #f5f7fa;          /* Page background */
}
```

#### 2. Component Styling

| Component | Style Guidelines |
|-----------|------------------|
| **Cards** | 12px border-radius, subtle shadow (`0 2px 8px rgba(0,0,0,0.08)`), no border |
| **Buttons** | 8px border-radius, 500 font-weight, subtle hover elevation |
| **Badges** | 6px border-radius, uppercase text, 0.75rem font-size |
| **Icons** | Bootstrap Icons, consistent sizing within context |
| **Spacing** | 8px base unit (0.5rem increments) |

#### 3. Layout Structure

- **Sidebar**: Fixed 220px width, always visible on desktop
- **Main Content**: Fluid width with 2rem horizontal padding
- **Cards**: Full-width within content area, 1rem gap between
- **Responsive**: Sidebar collapses to icons at 991px, bottom nav at 576px

#### 4. Status Indicators

| Status | Background | Text Color | Use Case |
|--------|------------|------------|----------|
| Heavily Oversized | `#f8d7da` | `#721c24` | <25% avg, <35% peak utilization |
| Moderately Oversized | `#fff3cd` | `#856404` | <50% avg, <60% peak utilization |
| Right-Sized | `#d1e7dd` | `#0f5132` | <70% avg, <80% peak utilization |
| Undersized | `#cff4fc` | `#055160` | ≥70% avg, ≥80% peak utilization |

#### 5. Typography

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;

/* Hierarchy */
Page Title: 1.5rem, 600 weight
Section Title: 1rem, 600 weight
Body Text: 0.875rem, 400 weight
Meta/Labels: 0.75rem, 500-600 weight, uppercase, letter-spacing: 0.05em
Code/IDs: 'SFMono-Regular', Consolas, monospace
```

### Metrics Collection

#### Data Sources

| Metric | CloudWatch Namespace | Metric Name | Dimension |
|--------|---------------------|-------------|-----------|
| CPU Utilization | `AWS/EC2` | `CPUUtilization` | InstanceId |
| Memory Utilization | `CWAgent` | `mem_used_percent` | InstanceId |

#### Collection Process

```python
# Pseudocode for metrics collection

def collect_metrics(instance_ids, lookback_hours):
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=lookback_hours)

    for instance_id in instance_ids:
        # Fetch CPU metrics
        cpu_data = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,  # 5-minute intervals
            Statistics=['Average', 'Maximum']
        )

        # Fetch Memory metrics (requires CWAgent)
        memory_data = cloudwatch.get_metric_statistics(
            Namespace='CWAgent',
            MetricName='mem_used_percent',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Average', 'Maximum']
        )

    # Aggregate across all instances in group
    return {
        'cpu': {
            'average': mean(all_cpu_averages),
            'p95': percentile(all_cpu_max, 95),
            'min': min(all_cpu_values),
            'max': max(all_cpu_values)
        },
        'memory': {
            'average': mean(all_memory_averages),
            'p95': percentile(all_memory_max, 95),
            'min': min(all_memory_values),
            'max': max(all_memory_values)
        }
    }
```

#### Lookback Periods

| Cluster Type | Default Lookback | Rationale |
|--------------|------------------|-----------|
| Transient | 4 hours | Short-lived, recent data most relevant |
| Long-Running | 72 hours (3 days) | Need sufficient data for patterns |
| Terminated | Full runtime or 72 hours | Historical analysis |

#### Sustained Peak Analysis

The system differentiates between momentary spikes and sustained peaks:

```python
def analyze_peak(metrics_data):
    p95 = percentile(data, 95)
    p90 = percentile(data, 90)
    p75 = percentile(data, 75)

    # Calculate duration at P95 level
    duration_at_p95 = count(data >= p95 * 0.95) * period_minutes

    if duration_at_p95 >= 30:  # Sustained for 30+ minutes
        return {'type': 'sustained', 'effective_peak': p95}
    elif duration_at_p95 >= 10:  # Moderate duration
        return {'type': 'moderate', 'effective_peak': p90}
    else:  # Momentary spike
        return {'type': 'momentary', 'effective_peak': p75}
```

### Analysis Logic

#### Cluster Classification

```python
def classify_cluster(cluster):
    # Pattern-based classification
    if re.match(r'STRESS-\d+-(?:S|L|XL)', cluster['name']):
        return 'TRANSIENT'

    # Runtime-based classification
    if cluster['runtime_hours'] < 7:
        return 'TRANSIENT'
    else:
        return 'LONG_RUNNING'
```

#### Sizing Status Determination

The system uses the **higher** of CPU and Memory utilization to determine sizing status:

```python
THRESHOLDS = {
    'heavily_oversized': {'avg_max': 25, 'peak_max': 35},
    'moderately_oversized': {'avg_max': 50, 'peak_max': 60},
    'right_sized': {'avg_max': 70, 'peak_max': 80}
}

def determine_sizing_status(cpu_metrics, memory_metrics):
    # Use higher of CPU and Memory
    avg_utilization = max(cpu_metrics['average'], memory_metrics['average'])
    peak_utilization = max(cpu_metrics['p95'], memory_metrics['p95'])

    if avg_utilization < 25 and peak_utilization < 35:
        return 'HEAVILY_OVERSIZED'
    elif avg_utilization < 50 and peak_utilization < 60:
        return 'MODERATELY_OVERSIZED'
    elif avg_utilization < 70 and peak_utilization < 80:
        return 'RIGHT_SIZED'
    else:
        return 'UNDERSIZED'
```

#### Workload Profile Detection

```python
def detect_workload_profile(cpu_avg, memory_avg):
    if cpu_avg > memory_avg * 1.5:
        return 'CPU_HEAVY'
    elif memory_avg > cpu_avg * 1.5:
        return 'MEMORY_HEAVY'
    else:
        return 'BALANCED'
```

### Recommendation Engine

#### Recommendation Types

| Type | Description | Selection Criteria |
|------|-------------|-------------------|
| **Same Family** | Smaller instance in current family | Maintains compatibility, lowest risk |
| **Cross Family** | Cheapest instance meeting requirements | Maximum savings potential |
| **Category Optimized** | Best for workload profile | Matches CPU-heavy/Memory-heavy pattern |
| **Cheaper Alternative** | Same size, cheaper family | e.g., r6i vs r7i for same specs |

#### Resource Requirements Calculation

```python
HEADROOM_PERCENT = 20  # 20% buffer

def calculate_required_resources(current_specs, peak_utilization):
    required_vcpus = (current_specs['vcpus'] * (peak_utilization['cpu'] / 100)) * (1 + HEADROOM_PERCENT / 100)
    required_memory = (current_specs['memory_gb'] * (peak_utilization['memory'] / 100)) * (1 + HEADROOM_PERCENT / 100)

    return {
        'vcpus': math.ceil(required_vcpus),
        'memory_gb': math.ceil(required_memory)
    }
```

#### Instance Selection Logic

```python
def find_recommendations(current_instance, required_resources, workload_profile):
    recommendations = {}

    # 1. Same Family - find smaller in same family
    same_family_options = [i for i in INSTANCES
                          if i['family'] == current_instance['family']
                          and i['vcpus'] >= required_resources['vcpus']
                          and i['memory_gb'] >= required_resources['memory_gb']
                          and i['price'] < current_instance['price']]
    if same_family_options:
        recommendations['same_family'] = min(same_family_options, key=lambda x: x['price'])

    # 2. Cross Family - cheapest across all families
    all_options = [i for i in INSTANCES
                   if i['vcpus'] >= required_resources['vcpus']
                   and i['memory_gb'] >= required_resources['memory_gb']
                   and i['price'] < current_instance['price']]
    if all_options:
        recommendations['cross_family'] = min(all_options, key=lambda x: x['price'])

    # 3. Category Optimized - based on workload profile
    category_map = {
        'CPU_HEAVY': 'compute',
        'MEMORY_HEAVY': 'memory',
        'BALANCED': 'general'
    }
    category = category_map.get(workload_profile, 'general')
    category_options = [i for i in all_options if i['category'] == category]
    if category_options:
        recommendations['category_optimized'] = min(category_options, key=lambda x: x['price'])

    return recommendations
```

#### Savings Calculation

```python
def calculate_savings(current_instance, recommended_instance, instance_count):
    hourly_savings = (current_instance['price'] - recommended_instance['price']) * instance_count
    monthly_savings = hourly_savings * 24 * 30  # 720 hours/month
    savings_percent = ((current_instance['price'] - recommended_instance['price']) / current_instance['price']) * 100

    return {
        'hourly_savings': hourly_savings,
        'monthly_savings': monthly_savings,
        'savings_percent': round(savings_percent, 1)
    }
```

### API Endpoints

#### Routes Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Landing page with savings overview |
| GET | `/emr` | EMR dashboard |
| GET | `/api/clusters` | List all EMR clusters |
| GET | `/api/clusters/<id>` | Get cluster details |
| POST | `/api/clusters/<id>/analyze` | Trigger cluster analysis |
| GET | `/api/clusters/<id>/analysis` | Get latest analysis |
| GET | `/api/analysis/history` | Get analysis history |
| GET | `/api/config/lookback-options` | Get lookback period options |
| GET | `/api/health` | Health check |

#### Detailed API Specifications

##### GET /api/clusters

**Response:**
```json
{
    "success": true,
    "data": {
        "transient": [
            {
                "id": "j-XXXXXXXXXXXXX",
                "name": "cluster-name",
                "state": "RUNNING",
                "cluster_type": "TRANSIENT",
                "runtime_hours": 2.5,
                "release_label": "emr-6.10.0",
                "applications": ["Spark", "Hadoop"],
                "instance_groups": [
                    {
                        "type": "CORE",
                        "instance_type": "r5.2xlarge",
                        "running_count": 4,
                        "requested_count": 4
                    }
                ]
            }
        ],
        "long_running": [...],
        "terminated": [...],
        "total_count": 10,
        "transient_count": 3,
        "long_running_count": 5,
        "terminated_count": 2
    }
}
```

##### POST /api/clusters/{cluster_id}/analyze

**Request:**
```json
{
    "lookback_hours": 72
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "cluster_id": "j-XXXXXXXXXXXXX",
        "cluster_name": "cluster-name",
        "cluster_type": "LONG_RUNNING",
        "runtime_hours": 168.5,
        "analysis_period": {
            "start": "2024-01-15T00:00:00Z",
            "end": "2024-01-18T00:00:00Z"
        },
        "node_analyses": {
            "CORE": {
                "instance_type": "r5.2xlarge",
                "instance_count": 4,
                "instance_specs": {
                    "vcpus": 8,
                    "memory_gb": 64,
                    "price_per_hour": 0.504
                },
                "current_hourly_cost": 2.016,
                "metrics_available": true,
                "metrics": {
                    "cpu": {
                        "average": 23.5,
                        "p95": 45.2,
                        "min": 5.1,
                        "max": 78.3,
                        "effective_peak": 45.2,
                        "peak_type": "sustained"
                    },
                    "memory": {
                        "available": true,
                        "average": 35.2,
                        "p95": 52.1,
                        "min": 20.3,
                        "max": 65.8,
                        "effective_peak": 52.1,
                        "peak_type": "sustained"
                    }
                },
                "sizing_status": {
                    "status": "moderately_oversized",
                    "label": "Moderately Oversized",
                    "description": "Resources are larger than needed..."
                },
                "workload_profile": "memory_heavy",
                "recommendations": {
                    "action": "downsize",
                    "required_vcpus": 5,
                    "required_memory_gb": 40,
                    "same_family": {
                        "instance_type": "r5.xlarge",
                        "vcpus": 4,
                        "memory_gb": 32,
                        "price_per_hour": 0.252,
                        "savings": {
                            "hourly_savings": 1.008,
                            "monthly_savings": 726,
                            "savings_percent": 50.0
                        }
                    },
                    "cross_family": {...},
                    "best_recommendation": {...}
                },
                "confidence": {
                    "level": "high",
                    "reasons": ["Sufficient data points", "Stable utilization pattern"]
                }
            },
            "TASK": {...}
        },
        "total_potential_hourly_savings": 1.512,
        "total_potential_monthly_savings": 1089,
        "analyzed_at": "2024-01-18T12:30:00Z"
    }
}
```

### Data Persistence

#### Current Implementation (File-based)

```
data/
└── analysis_history.json
```

**Structure:**
```json
{
    "j-XXXXXXXXXXXXX": [
        {
            "analyzed_at": "2024-01-18T12:30:00Z",
            "cluster_name": "...",
            "total_potential_monthly_savings": 1089,
            "node_analyses": {...}
        }
    ]
}
```

- Keyed by cluster ID
- Last 10 analyses kept per cluster
- Oldest analyses automatically pruned

### IAM Permissions

#### Required IAM Policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "EMRReadAccess",
            "Effect": "Allow",
            "Action": [
                "elasticmapreduce:ListClusters",
                "elasticmapreduce:DescribeCluster",
                "elasticmapreduce:ListInstanceGroups",
                "elasticmapreduce:ListInstances",
                "elasticmapreduce:ListInstanceFleets"
            ],
            "Resource": "*"
        },
        {
            "Sid": "EC2ReadAccess",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances"
            ],
            "Resource": "*"
        },
        {
            "Sid": "CloudWatchReadAccess",
            "Effect": "Allow",
            "Action": [
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:GetMetricData",
                "cloudwatch:ListMetrics"
            ],
            "Resource": "*"
        }
    ]
}
```

---

## ECS Cost Optimizer (Proposed)

### Overview

Analyze ECS services and tasks to identify over-provisioned CPU and memory allocations, and recommend right-sized task definitions.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ECS COST OPTIMIZER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ ecs_service  │────▶│ cloudwatch_  │────▶│  analyzer_   │                │
│  │    .py       │     │  service.py  │     │  service.py  │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
│         │                    │                    │                         │
│         ▼                    ▼                    ▼                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │  ECS API     │     │  CloudWatch  │     │   Pricing    │                │
│  │  - Clusters  │     │  - CPU %     │     │   Service    │                │
│  │  - Services  │     │  - Memory %  │     │              │                │
│  │  - Tasks     │     │              │     │              │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Metrics Collection

#### Data Sources

| Metric | CloudWatch Namespace | Metric Name | Dimensions |
|--------|---------------------|-------------|------------|
| CPU Utilization | `AWS/ECS` | `CPUUtilization` | ClusterName, ServiceName |
| Memory Utilization | `AWS/ECS` | `MemoryUtilization` | ClusterName, ServiceName |
| Running Task Count | `AWS/ECS` | `RunningTaskCount` | ClusterName, ServiceName |

#### Key Data Points to Collect

```python
def collect_ecs_metrics(cluster_name, service_name, lookback_hours):
    return {
        'service_info': {
            'cluster': cluster_name,
            'service': service_name,
            'launch_type': 'FARGATE' | 'EC2',
            'desired_count': int,
            'running_count': int,
            'task_definition': {
                'cpu': 1024,  # CPU units (1024 = 1 vCPU)
                'memory': 2048,  # Memory in MB
                'containers': [
                    {
                        'name': 'container-name',
                        'cpu': 512,
                        'memory': 1024,
                        'memory_reservation': 512
                    }
                ]
            }
        },
        'metrics': {
            'cpu': {
                'average': float,
                'p95': float,
                'max': float
            },
            'memory': {
                'average': float,
                'p95': float,
                'max': float
            }
        }
    }
```

### Analysis Logic

#### Sizing Status Thresholds

Use same thresholds as EMR for consistency:

| Status | Avg Utilization | Peak (P95) Utilization |
|--------|-----------------|------------------------|
| Heavily Oversized | < 25% | < 35% |
| Moderately Oversized | < 50% | < 60% |
| Right-Sized | < 70% | < 80% |
| Undersized | ≥ 70% | ≥ 80% |

#### Resource Requirements Calculation

```python
def calculate_ecs_requirements(current_config, peak_utilization):
    HEADROOM = 1.2  # 20% buffer

    # Current allocation in units
    current_cpu = current_config['cpu']  # e.g., 1024 (1 vCPU)
    current_memory = current_config['memory']  # e.g., 2048 MB

    # Required based on peak utilization
    required_cpu = math.ceil((current_cpu * (peak_utilization['cpu'] / 100)) * HEADROOM)
    required_memory = math.ceil((current_memory * (peak_utilization['memory'] / 100)) * HEADROOM)

    # Round to valid Fargate configurations
    valid_cpu_values = [256, 512, 1024, 2048, 4096, 8192, 16384]
    valid_memory_for_cpu = {
        256: [512, 1024, 2048],
        512: [1024, 2048, 3072, 4096],
        1024: [2048, 3072, 4096, 5120, 6144, 7168, 8192],
        2048: [4096, 5120, 6144, 7168, 8192, 9216, 10240, 11264, 12288, 13312, 14336, 15360, 16384],
        4096: list(range(8192, 30721, 1024)),
        8192: list(range(16384, 61441, 4096)),
        16384: list(range(32768, 122881, 8192))
    }

    return snap_to_valid_fargate_config(required_cpu, required_memory)
```

### Recommendations

#### Recommendation Types

| Type | Description |
|------|-------------|
| **Task CPU/Memory Reduction** | Reduce task definition CPU/Memory units |
| **Container-level Optimization** | Adjust individual container allocations |
| **Launch Type Switch** | Switch between Fargate and EC2 based on cost |
| **Service Consolidation** | Combine underutilized services |

#### Savings Calculation

**Fargate Pricing Model:**
```python
def calculate_fargate_cost(cpu_units, memory_mb, hours):
    CPU_PRICE_PER_VCPU_HOUR = 0.04048  # us-east-1
    MEMORY_PRICE_PER_GB_HOUR = 0.004445

    vcpu = cpu_units / 1024
    memory_gb = memory_mb / 1024

    hourly_cost = (vcpu * CPU_PRICE_PER_VCPU_HOUR) + (memory_gb * MEMORY_PRICE_PER_GB_HOUR)
    return hourly_cost * hours
```

### Proposed API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ecs/clusters` | List all ECS clusters |
| GET | `/api/ecs/clusters/<name>/services` | List services in cluster |
| POST | `/api/ecs/services/<arn>/analyze` | Trigger service analysis |
| GET | `/api/ecs/services/<arn>/analysis` | Get latest analysis |
| GET | `/api/ecs/analysis/history` | Get analysis history |

#### POST /api/ecs/services/{service_arn}/analyze

**Request:**
```json
{
    "lookback_hours": 72
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "service_arn": "arn:aws:ecs:us-east-1:123456789:service/cluster/service",
        "service_name": "my-service",
        "cluster_name": "my-cluster",
        "launch_type": "FARGATE",
        "current_config": {
            "cpu": 1024,
            "memory": 2048,
            "desired_count": 3
        },
        "metrics": {
            "cpu": {"average": 15.3, "p95": 28.7},
            "memory": {"average": 22.1, "p95": 35.4}
        },
        "sizing_status": "heavily_oversized",
        "recommendations": {
            "action": "downsize",
            "recommended_config": {
                "cpu": 512,
                "memory": 1024
            },
            "savings": {
                "current_monthly_cost": 87.65,
                "recommended_monthly_cost": 43.82,
                "monthly_savings": 43.83,
                "savings_percent": 50.0
            }
        }
    }
}
```

### IAM Permissions

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ECSReadAccess",
            "Effect": "Allow",
            "Action": [
                "ecs:ListClusters",
                "ecs:ListServices",
                "ecs:DescribeServices",
                "ecs:DescribeTaskDefinition",
                "ecs:ListTasks",
                "ecs:DescribeTasks"
            ],
            "Resource": "*"
        },
        {
            "Sid": "CloudWatchReadAccess",
            "Effect": "Allow",
            "Action": [
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:GetMetricData"
            ],
            "Resource": "*"
        }
    ]
}
```

### Implementation Steps

1. **Create `services/ecs_service.py`**
   - Implement `list_clusters()`, `list_services()`, `get_service_details()`
   - Fetch task definitions and container configurations

2. **Extend `services/cloudwatch_service.py`**
   - Add ECS-specific metric collection methods
   - Handle both Fargate and EC2 launch types

3. **Create `services/ecs_analyzer_service.py`**
   - Implement sizing status logic
   - Generate recommendations with valid Fargate configurations
   - Calculate Fargate/EC2 cost comparisons

4. **Add API routes in `app.py`**
   - `/api/ecs/*` endpoints as specified above

5. **Create `templates/ecs.html`**
   - Service list view similar to EMR cluster list
   - Analysis modal with container-level breakdown

6. **Update sidebar navigation**
   - Change ECS status from "Coming Soon" to "Active"

---

## EKS Cost Optimizer (Proposed)

### Overview

Analyze EKS node groups AND pod resource allocations to identify over-provisioned Kubernetes resources at both infrastructure and application levels.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EKS COST OPTIMIZER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      TWO-LEVEL ANALYSIS                               │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │                                                                       │  │
│  │  LEVEL 1: NODE GROUPS                 LEVEL 2: POD RESOURCES         │  │
│  │  ┌─────────────────────┐             ┌─────────────────────┐        │  │
│  │  │ Instance Type       │             │ Pod Requests vs     │        │  │
│  │  │ Node Count          │             │ Actual Usage        │        │  │
│  │  │ Node Utilization    │             │                     │        │  │
│  │  │                     │             │ Per-namespace       │        │  │
│  │  │ Similar to EMR      │             │ Per-deployment      │        │  │
│  │  └─────────────────────┘             └─────────────────────┘        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ eks_service  │     │ cloudwatch_  │     │  analyzer_   │                │
│  │    .py       │     │  service.py  │     │  service.py  │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Metrics Collection

#### Data Sources

| Level | Metric | Source | Dimension |
|-------|--------|--------|-----------|
| Node | CPU Utilization | CloudWatch `AWS/EC2` | InstanceId |
| Node | Memory Utilization | CloudWatch `CWAgent` | InstanceId |
| Pod | CPU Usage | Container Insights `ContainerInsights` | PodName, Namespace |
| Pod | Memory Usage | Container Insights `ContainerInsights` | PodName, Namespace |
| Pod | CPU Request | Kubernetes API | PodName |
| Pod | Memory Request | Kubernetes API | PodName |

**Important:** Container Insights must be enabled on the EKS cluster for pod-level metrics.

#### Pod-Level Data Structure

```python
def collect_pod_metrics(cluster_name, namespace, lookback_hours):
    return {
        'namespace': namespace,
        'pods': [
            {
                'name': 'pod-name',
                'deployment': 'deployment-name',
                'node': 'node-name',
                'resources': {
                    'requests': {
                        'cpu': '500m',      # millicores
                        'memory': '512Mi'   # mebibytes
                    },
                    'limits': {
                        'cpu': '1000m',
                        'memory': '1Gi'
                    }
                },
                'actual_usage': {
                    'cpu': {
                        'average_millicores': 125,
                        'p95_millicores': 280,
                        'average_percent_of_request': 25.0,
                        'p95_percent_of_request': 56.0
                    },
                    'memory': {
                        'average_bytes': 268435456,
                        'p95_bytes': 402653184,
                        'average_percent_of_request': 50.0,
                        'p95_percent_of_request': 75.0
                    }
                }
            }
        ]
    }
```

### Analysis Logic

#### Level 1: Node Group Analysis

Same approach as EMR:

```python
def analyze_node_group(node_group):
    # Collect EC2-level metrics for all nodes in group
    # Determine sizing status based on utilization
    # Recommend smaller instance types or fewer nodes
    # Calculate savings
```

#### Level 2: Pod Resource Analysis

```python
def analyze_pod_resources(pod_data):
    request_cpu = parse_cpu(pod_data['resources']['requests']['cpu'])  # Convert to millicores
    request_memory = parse_memory(pod_data['resources']['requests']['memory'])  # Convert to bytes

    actual_cpu_p95 = pod_data['actual_usage']['cpu']['p95_millicores']
    actual_memory_p95 = pod_data['actual_usage']['memory']['p95_bytes']

    # Calculate utilization percentage
    cpu_utilization = (actual_cpu_p95 / request_cpu) * 100
    memory_utilization = (actual_memory_p95 / request_memory) * 100

    # Apply same thresholds
    return determine_sizing_status(cpu_utilization, memory_utilization)
```

#### Aggregated Deployment Analysis

```python
def analyze_deployment(deployment_name, namespace, pods):
    # Aggregate all pods in deployment
    total_requested_cpu = sum(pod['requests']['cpu'] for pod in pods)
    total_requested_memory = sum(pod['requests']['memory'] for pod in pods)

    total_actual_cpu = sum(pod['actual_usage']['cpu']['p95'] for pod in pods)
    total_actual_memory = sum(pod['actual_usage']['memory']['p95'] for pod in pods)

    # Calculate wasted resources
    wasted_cpu = total_requested_cpu - total_actual_cpu
    wasted_memory = total_requested_memory - total_actual_memory

    return {
        'deployment': deployment_name,
        'namespace': namespace,
        'pod_count': len(pods),
        'total_requested': {'cpu': total_requested_cpu, 'memory': total_requested_memory},
        'total_actual_p95': {'cpu': total_actual_cpu, 'memory': total_actual_memory},
        'wasted_resources': {'cpu': wasted_cpu, 'memory': wasted_memory},
        'sizing_status': determine_sizing_status(...)
    }
```

### Recommendations

#### Node-Level Recommendations

| Type | Description |
|------|-------------|
| **Instance Right-sizing** | Smaller instance type for node group |
| **Node Count Reduction** | Reduce min/desired nodes if over-provisioned |
| **Spot Instance Mix** | Add Spot instances for fault-tolerant workloads |
| **Graviton Migration** | Move to ARM-based instances for cost savings |

#### Pod-Level Recommendations

| Type | Description |
|------|-------------|
| **Request Reduction** | Lower CPU/Memory requests in deployment spec |
| **Limit Adjustment** | Set appropriate limits based on actual usage |
| **HPA Configuration** | Recommend Horizontal Pod Autoscaler settings |
| **VPA Suggestion** | Suggest Vertical Pod Autoscaler installation |

### Savings Calculation

```python
def calculate_eks_savings(current_state, recommended_state):
    # Node-level savings (EC2 cost reduction)
    node_savings = calculate_ec2_savings(
        current_instance=current_state['instance_type'],
        recommended_instance=recommended_state['instance_type'],
        node_count=current_state['node_count']
    )

    # Pod-level savings (improved bin-packing = fewer nodes needed)
    freed_resources = calculate_freed_resources(pod_recommendations)
    potential_node_reduction = estimate_node_reduction(freed_resources)
    pod_efficiency_savings = potential_node_reduction * instance_hourly_cost * 720

    return {
        'node_level_monthly_savings': node_savings,
        'pod_efficiency_monthly_savings': pod_efficiency_savings,
        'total_monthly_savings': node_savings + pod_efficiency_savings
    }
```

### Proposed API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/eks/clusters` | List all EKS clusters |
| GET | `/api/eks/clusters/<name>/nodegroups` | List node groups |
| GET | `/api/eks/clusters/<name>/namespaces` | List namespaces with pod counts |
| POST | `/api/eks/nodegroups/<name>/analyze` | Analyze node group |
| POST | `/api/eks/namespaces/<name>/analyze` | Analyze namespace pods |
| GET | `/api/eks/analysis/summary/<cluster>` | Get cluster-wide summary |

#### POST /api/eks/namespaces/{namespace}/analyze

**Response:**
```json
{
    "success": true,
    "data": {
        "cluster_name": "my-cluster",
        "namespace": "production",
        "analysis_period": {"start": "...", "end": "..."},
        "summary": {
            "total_pods": 45,
            "oversized_pods": 28,
            "right_sized_pods": 12,
            "undersized_pods": 5
        },
        "deployments": [
            {
                "name": "api-service",
                "replicas": 5,
                "sizing_status": "heavily_oversized",
                "current_resources": {
                    "cpu_request": "1000m",
                    "memory_request": "2Gi"
                },
                "recommended_resources": {
                    "cpu_request": "250m",
                    "memory_request": "512Mi"
                },
                "savings_per_pod": {
                    "cpu_freed": "750m",
                    "memory_freed": "1.5Gi"
                }
            }
        ],
        "estimated_node_reduction": 2,
        "estimated_monthly_savings": 292.32
    }
}
```

### IAM Permissions

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "EKSReadAccess",
            "Effect": "Allow",
            "Action": [
                "eks:ListClusters",
                "eks:DescribeCluster",
                "eks:ListNodegroups",
                "eks:DescribeNodegroup"
            ],
            "Resource": "*"
        },
        {
            "Sid": "EC2ReadAccess",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances"
            ],
            "Resource": "*"
        },
        {
            "Sid": "CloudWatchReadAccess",
            "Effect": "Allow",
            "Action": [
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:GetMetricData"
            ],
            "Resource": "*"
        }
    ]
}
```

**Note:** For pod-level metrics, Container Insights uses CloudWatch Logs Insights. Additional permissions may be needed:
```json
{
    "Sid": "CloudWatchLogsAccess",
    "Effect": "Allow",
    "Action": [
        "logs:StartQuery",
        "logs:GetQueryResults",
        "logs:DescribeLogGroups"
    ],
    "Resource": "arn:aws:logs:*:*:log-group:/aws/containerinsights/*"
}
```

### Implementation Steps

1. **Create `services/eks_service.py`**
   - List clusters and node groups via EKS API
   - Integrate with Container Insights for pod metrics
   - Parse Kubernetes resource specifications

2. **Extend `services/cloudwatch_service.py`**
   - Add Container Insights query methods
   - Handle both node-level (EC2) and pod-level metrics

3. **Create `services/eks_analyzer_service.py`**
   - Two-tier analysis (node + pod)
   - Deployment-level aggregation
   - Node reduction estimation

4. **Add API routes in `app.py`**

5. **Create `templates/eks.html`**
   - Cluster overview with node group cards
   - Namespace/Deployment drill-down view
   - Pod-level resource visualization

---

## DynamoDB Cost Optimizer (Proposed)

### Overview

Analyze DynamoDB table capacity utilization to recommend optimal capacity mode (Provisioned vs On-Demand) and storage class (Standard vs Infrequent Access).

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DYNAMODB COST OPTIMIZER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      TWO OPTIMIZATION AREAS                           │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │                                                                       │  │
│  │  CAPACITY MODE                          STORAGE CLASS                 │  │
│  │  ┌─────────────────────┐               ┌─────────────────────┐       │  │
│  │  │ Provisioned vs      │               │ Standard vs         │       │  │
│  │  │ On-Demand           │               │ Infrequent Access   │       │  │
│  │  │                     │               │                     │       │  │
│  │  │ Based on RCU/WCU    │               │ Based on access     │       │  │
│  │  │ utilization patterns│               │ patterns per item   │       │  │
│  │  └─────────────────────┘               └─────────────────────┘       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ dynamodb_    │     │ cloudwatch_  │     │  analyzer_   │                │
│  │ service.py   │     │  service.py  │     │  service.py  │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Metrics Collection

#### Data Sources

| Metric | CloudWatch Namespace | Metric Name | Purpose |
|--------|---------------------|-------------|---------|
| Read Utilization | `AWS/DynamoDB` | `ConsumedReadCapacityUnits` | Actual RCU consumed |
| Write Utilization | `AWS/DynamoDB` | `ConsumedWriteCapacityUnits` | Actual WCU consumed |
| Provisioned RCU | `AWS/DynamoDB` | `ProvisionedReadCapacityUnits` | Provisioned read capacity |
| Provisioned WCU | `AWS/DynamoDB` | `ProvisionedWriteCapacityUnits` | Provisioned write capacity |
| Throttled Requests | `AWS/DynamoDB` | `ReadThrottledRequests`, `WriteThrottledRequests` | Under-provisioning indicator |
| Table Size | DynamoDB API | `TableSizeBytes` | For storage class analysis |
| Item Count | DynamoDB API | `ItemCount` | For storage class analysis |

#### Data Structure

```python
def collect_dynamodb_metrics(table_name, lookback_hours):
    return {
        'table_info': {
            'name': table_name,
            'billing_mode': 'PROVISIONED' | 'PAY_PER_REQUEST',
            'provisioned_rcu': int | None,
            'provisioned_wcu': int | None,
            'table_size_bytes': int,
            'item_count': int,
            'table_class': 'STANDARD' | 'STANDARD_INFREQUENT_ACCESS',
            'gsi_count': int,
            'lsi_count': int
        },
        'capacity_metrics': {
            'read': {
                'consumed_avg': float,
                'consumed_p95': float,
                'consumed_max': float,
                'provisioned': int,
                'utilization_avg': float,
                'utilization_p95': float,
                'throttled_requests': int
            },
            'write': {
                'consumed_avg': float,
                'consumed_p95': float,
                'consumed_max': float,
                'provisioned': int,
                'utilization_avg': float,
                'utilization_p95': float,
                'throttled_requests': int
            }
        },
        'access_patterns': {
            'reads_per_day_avg': float,
            'writes_per_day_avg': float,
            'read_write_ratio': float
        }
    }
```

### Analysis Logic

#### Capacity Mode Analysis

```python
def analyze_capacity_mode(table_metrics):
    # For PROVISIONED tables
    if table_metrics['billing_mode'] == 'PROVISIONED':
        read_util = table_metrics['capacity_metrics']['read']['utilization_avg']
        write_util = table_metrics['capacity_metrics']['write']['utilization_avg']

        # Low utilization suggests On-Demand might be cheaper
        if read_util < 20 and write_util < 20:
            return {
                'recommendation': 'SWITCH_TO_ON_DEMAND',
                'reason': 'Consistent low utilization (<20%) indicates On-Demand would be more cost-effective'
            }

        # Check for high throttling (under-provisioned)
        if table_metrics['capacity_metrics']['read']['throttled_requests'] > 100:
            return {
                'recommendation': 'INCREASE_PROVISIONED_OR_ON_DEMAND',
                'reason': 'High throttling detected. Consider increasing provisioned capacity or switching to On-Demand'
            }

        return {'recommendation': 'KEEP_PROVISIONED', 'reason': 'Current capacity is appropriately utilized'}

    # For ON_DEMAND tables
    else:
        # Calculate what provisioned cost would be
        avg_rcu = table_metrics['capacity_metrics']['read']['consumed_avg']
        avg_wcu = table_metrics['capacity_metrics']['write']['consumed_avg']

        # If usage is consistent and high, Provisioned might be cheaper
        if is_consistent_usage(table_metrics) and (avg_rcu > 100 or avg_wcu > 100):
            return {
                'recommendation': 'CONSIDER_PROVISIONED',
                'reason': 'Consistent high usage pattern detected. Provisioned capacity could save costs'
            }

        return {'recommendation': 'KEEP_ON_DEMAND', 'reason': 'Variable workload suits On-Demand pricing'}
```

#### Storage Class Analysis

```python
def analyze_storage_class(table_metrics):
    # Standard IA is cheaper for storage but more expensive for reads
    # Break-even: tables accessed less than ~2.5 times per month per GB

    table_size_gb = table_metrics['table_info']['table_size_bytes'] / (1024**3)

    if table_size_gb < 1:
        return {
            'recommendation': 'STANDARD',
            'reason': 'Table too small for IA to provide meaningful savings'
        }

    # Calculate access frequency
    reads_per_gb = table_metrics['access_patterns']['reads_per_day_avg'] / table_size_gb

    # IA pricing: Storage is ~60% cheaper, but reads cost more
    # Break-even roughly at tables accessed <20% of Standard threshold
    if reads_per_gb < 0.5:  # Less than 0.5 reads per GB per day
        return {
            'recommendation': 'STANDARD_INFREQUENT_ACCESS',
            'reason': f'Low access frequency ({reads_per_gb:.2f} reads/GB/day) makes IA more cost-effective'
        }

    return {
        'recommendation': 'STANDARD',
        'reason': 'Access pattern suits Standard storage class'
    }
```

### Savings Calculation

```python
# DynamoDB Pricing (us-east-1)
PRICING = {
    'provisioned': {
        'rcu_per_hour': 0.00013,  # per RCU
        'wcu_per_hour': 0.00065,  # per WCU
    },
    'on_demand': {
        'rru_per_million': 0.25,   # Read Request Units
        'wru_per_million': 1.25,   # Write Request Units
    },
    'storage': {
        'standard_per_gb': 0.25,   # per month
        'ia_per_gb': 0.10,         # per month (60% cheaper)
    }
}

def calculate_cost_comparison(table_metrics):
    # Current cost
    if table_metrics['billing_mode'] == 'PROVISIONED':
        current_cost = calculate_provisioned_cost(
            table_metrics['provisioned_rcu'],
            table_metrics['provisioned_wcu']
        )
        alternative_cost = calculate_on_demand_cost(
            table_metrics['capacity_metrics']['read']['consumed_avg'],
            table_metrics['capacity_metrics']['write']['consumed_avg']
        )
    else:
        current_cost = calculate_on_demand_cost(...)
        alternative_cost = calculate_provisioned_cost(...)

    return {
        'current_monthly_cost': current_cost,
        'alternative_monthly_cost': alternative_cost,
        'potential_savings': max(0, current_cost - alternative_cost)
    }
```

### Proposed API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dynamodb/tables` | List all DynamoDB tables |
| GET | `/api/dynamodb/tables/<name>` | Get table details |
| POST | `/api/dynamodb/tables/<name>/analyze` | Trigger table analysis |
| GET | `/api/dynamodb/tables/<name>/analysis` | Get latest analysis |
| GET | `/api/dynamodb/analysis/summary` | Get summary across all tables |

#### POST /api/dynamodb/tables/{table_name}/analyze

**Response:**
```json
{
    "success": true,
    "data": {
        "table_name": "users-table",
        "current_config": {
            "billing_mode": "PROVISIONED",
            "provisioned_rcu": 100,
            "provisioned_wcu": 50,
            "table_class": "STANDARD",
            "table_size_gb": 25.6
        },
        "capacity_analysis": {
            "read_utilization": {
                "average": 12.5,
                "p95": 28.3,
                "status": "heavily_oversized"
            },
            "write_utilization": {
                "average": 18.2,
                "p95": 35.1,
                "status": "heavily_oversized"
            },
            "throttled_requests": 0
        },
        "recommendations": {
            "capacity_mode": {
                "current": "PROVISIONED",
                "recommended": "ON_DEMAND",
                "reason": "Low utilization (<20%) suggests On-Demand would be more cost-effective"
            },
            "storage_class": {
                "current": "STANDARD",
                "recommended": "STANDARD",
                "reason": "Access pattern suits Standard storage class"
            }
        },
        "cost_comparison": {
            "current_monthly_cost": 142.56,
            "recommended_monthly_cost": 48.25,
            "potential_monthly_savings": 94.31,
            "savings_percent": 66.2
        }
    }
}
```

### IAM Permissions

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DynamoDBReadAccess",
            "Effect": "Allow",
            "Action": [
                "dynamodb:ListTables",
                "dynamodb:DescribeTable",
                "dynamodb:DescribeContinuousBackups",
                "dynamodb:DescribeTimeToLive"
            ],
            "Resource": "*"
        },
        {
            "Sid": "CloudWatchReadAccess",
            "Effect": "Allow",
            "Action": [
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:GetMetricData"
            ],
            "Resource": "*"
        }
    ]
}
```

### Implementation Steps

1. **Create `services/dynamodb_service.py`**
   - List tables and describe configuration
   - Fetch billing mode, provisioned capacity, table class

2. **Extend `services/cloudwatch_service.py`**
   - Add DynamoDB-specific metric collection
   - Calculate utilization percentages

3. **Create `services/dynamodb_analyzer_service.py`**
   - Capacity mode recommendation logic
   - Storage class analysis
   - Cost comparison calculations

4. **Add API routes in `app.py`**

5. **Create `templates/dynamodb.html`**
   - Table list with current config
   - Capacity utilization visualization
   - Before/after cost comparison

---

## Glue Cost Optimizer (Proposed)

### Overview

Analyze AWS Glue job configurations to identify over-allocated DPU (Data Processing Units) and recommend right-sized configurations.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GLUE COST OPTIMIZER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      JOB-LEVEL ANALYSIS                               │  │
│  ├──────────────────────────────────────────────────────────────────────┤  │
│  │                                                                       │  │
│  │  ┌─────────────────────┐    ┌─────────────────────┐                  │  │
│  │  │ DPU Allocation      │    │ Execution Time      │                  │  │
│  │  │ vs Actual Usage     │    │ Optimization        │                  │  │
│  │  │                     │    │                     │                  │  │
│  │  │ - Worker count      │    │ - Job duration      │                  │  │
│  │  │ - Worker type       │    │ - Data volume       │                  │  │
│  │  │ - Memory usage      │    │ - Glue version      │                  │  │
│  │  └─────────────────────┘    └─────────────────────┘                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ glue_service │     │ cloudwatch_  │     │  analyzer_   │                │
│  │    .py       │     │  service.py  │     │  service.py  │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Metrics Collection

#### Data Sources

| Metric | Source | Purpose |
|--------|--------|---------|
| Job Configuration | Glue API | DPU allocation, worker type, Glue version |
| Job Runs | Glue API | Execution history, duration, status |
| Bytes Read/Written | CloudWatch `Glue` | Data volume processed |
| Elapsed Time | CloudWatch `Glue` | Actual execution time |
| Memory Usage | CloudWatch `Glue` | Memory utilization per executor |

#### Data Structure

```python
def collect_glue_job_metrics(job_name, lookback_days=30):
    return {
        'job_config': {
            'name': job_name,
            'glue_version': '3.0',
            'worker_type': 'G.1X',  # Standard, G.1X, G.2X, G.025X
            'number_of_workers': 10,
            'max_capacity': 10.0,  # DPUs
            'execution_class': 'STANDARD' | 'FLEX',
            'timeout_minutes': 2880
        },
        'recent_runs': [
            {
                'run_id': 'jr_xxxxx',
                'started_on': datetime,
                'completed_on': datetime,
                'execution_time_seconds': 1800,
                'dpu_seconds': 18000,
                'status': 'SUCCEEDED',
                'bytes_read': 10737418240,
                'bytes_written': 5368709120,
                'metrics': {
                    'memory_used_percent': 45.2,
                    'executor_memory_used_gb': 28.8,
                    'executor_cpu_percent': 35.5
                }
            }
        ],
        'aggregated_metrics': {
            'avg_execution_time_minutes': 30,
            'avg_dpu_usage': 4.5,
            'avg_memory_percent': 42.3,
            'runs_per_week': 21,
            'success_rate': 98.5
        }
    }
```

### Analysis Logic

#### DPU Utilization Analysis

```python
def analyze_dpu_utilization(job_metrics):
    allocated_dpu = job_metrics['job_config']['number_of_workers']

    # Calculate effective DPU usage from memory utilization
    avg_memory_percent = job_metrics['aggregated_metrics']['avg_memory_percent']

    # Sizing status based on memory utilization (similar thresholds)
    if avg_memory_percent < 25:
        return {
            'status': 'heavily_oversized',
            'recommendation': 'reduce_workers',
            'recommended_workers': max(2, int(allocated_dpu * 0.4)),
            'reason': 'Memory utilization consistently below 25%'
        }
    elif avg_memory_percent < 50:
        return {
            'status': 'moderately_oversized',
            'recommendation': 'reduce_workers',
            'recommended_workers': max(2, int(allocated_dpu * 0.6)),
            'reason': 'Memory utilization below 50%'
        }
    elif avg_memory_percent < 70:
        return {
            'status': 'right_sized',
            'recommendation': 'keep_current',
            'reason': 'DPU allocation is appropriate'
        }
    else:
        return {
            'status': 'undersized',
            'recommendation': 'increase_workers',
            'recommended_workers': int(allocated_dpu * 1.3),
            'reason': 'High memory utilization may cause failures'
        }
```

#### Execution Class Analysis

```python
def analyze_execution_class(job_metrics):
    # FLEX execution class is 34% cheaper but has startup latency
    current_class = job_metrics['job_config']['execution_class']
    avg_execution_minutes = job_metrics['aggregated_metrics']['avg_execution_time_minutes']

    if current_class == 'STANDARD' and avg_execution_minutes > 10:
        # Jobs running >10 min won't be significantly impacted by FLEX startup delay
        return {
            'recommendation': 'SWITCH_TO_FLEX',
            'reason': 'Jobs >10 minutes can benefit from FLEX pricing (34% savings)',
            'savings_percent': 34
        }

    return {'recommendation': 'KEEP_CURRENT', 'reason': 'Current execution class is appropriate'}
```

### Savings Calculation

```python
# Glue Pricing (us-east-1)
GLUE_PRICING = {
    'standard': {
        'dpu_hour': 0.44
    },
    'flex': {
        'dpu_hour': 0.29  # 34% cheaper
    },
    'worker_types': {
        'Standard': {'dpu': 1, 'memory_gb': 16},
        'G.1X': {'dpu': 1, 'memory_gb': 16},
        'G.2X': {'dpu': 2, 'memory_gb': 32},
        'G.025X': {'dpu': 0.25, 'memory_gb': 2}
    }
}

def calculate_glue_savings(job_metrics, recommendation):
    current_config = job_metrics['job_config']
    runs_per_month = job_metrics['aggregated_metrics']['runs_per_week'] * 4
    avg_duration_hours = job_metrics['aggregated_metrics']['avg_execution_time_minutes'] / 60

    # Current cost
    current_dpu_hours = current_config['number_of_workers'] * avg_duration_hours * runs_per_month
    current_rate = GLUE_PRICING['standard' if current_config['execution_class'] == 'STANDARD' else 'flex']['dpu_hour']
    current_monthly_cost = current_dpu_hours * current_rate

    # Recommended cost
    recommended_workers = recommendation.get('recommended_workers', current_config['number_of_workers'])
    recommended_dpu_hours = recommended_workers * avg_duration_hours * runs_per_month
    recommended_rate = GLUE_PRICING['flex']['dpu_hour'] if recommendation.get('execution_class') == 'FLEX' else current_rate
    recommended_monthly_cost = recommended_dpu_hours * recommended_rate

    return {
        'current_monthly_cost': round(current_monthly_cost, 2),
        'recommended_monthly_cost': round(recommended_monthly_cost, 2),
        'monthly_savings': round(current_monthly_cost - recommended_monthly_cost, 2),
        'savings_percent': round(((current_monthly_cost - recommended_monthly_cost) / current_monthly_cost) * 100, 1)
    }
```

### Proposed API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/glue/jobs` | List all Glue jobs |
| GET | `/api/glue/jobs/<name>` | Get job details and recent runs |
| POST | `/api/glue/jobs/<name>/analyze` | Trigger job analysis |
| GET | `/api/glue/jobs/<name>/analysis` | Get latest analysis |
| GET | `/api/glue/analysis/summary` | Get summary across all jobs |

#### POST /api/glue/jobs/{job_name}/analyze

**Response:**
```json
{
    "success": true,
    "data": {
        "job_name": "etl-daily-transform",
        "current_config": {
            "glue_version": "3.0",
            "worker_type": "G.2X",
            "number_of_workers": 20,
            "execution_class": "STANDARD"
        },
        "recent_runs_analyzed": 30,
        "metrics": {
            "avg_execution_minutes": 45,
            "avg_memory_utilization": 32.5,
            "avg_cpu_utilization": 28.3,
            "success_rate": 100
        },
        "analysis": {
            "dpu_sizing": {
                "status": "moderately_oversized",
                "reason": "Memory utilization averaging 32.5%"
            },
            "execution_class": {
                "current": "STANDARD",
                "recommended": "FLEX",
                "reason": "Jobs >10 minutes benefit from FLEX pricing"
            }
        },
        "recommendations": {
            "worker_type": "G.2X",
            "number_of_workers": 12,
            "execution_class": "FLEX"
        },
        "cost_comparison": {
            "current_monthly_cost": 1188.00,
            "recommended_monthly_cost": 468.72,
            "monthly_savings": 719.28,
            "savings_percent": 60.5
        }
    }
}
```

### IAM Permissions

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "GlueReadAccess",
            "Effect": "Allow",
            "Action": [
                "glue:GetJobs",
                "glue:GetJob",
                "glue:GetJobRuns",
                "glue:GetJobRun",
                "glue:BatchGetJobs"
            ],
            "Resource": "*"
        },
        {
            "Sid": "CloudWatchReadAccess",
            "Effect": "Allow",
            "Action": [
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:GetMetricData"
            ],
            "Resource": "*"
        }
    ]
}
```

### Implementation Steps

1. **Create `services/glue_service.py`**
   - List jobs and get configurations
   - Fetch job run history
   - Parse execution metrics

2. **Extend `services/cloudwatch_service.py`**
   - Add Glue-specific metric collection
   - Memory and execution time metrics

3. **Create `services/glue_analyzer_service.py`**
   - DPU utilization analysis
   - Execution class recommendation
   - Cost comparison calculations

4. **Add API routes in `app.py`**

5. **Create `templates/glue.html`**
   - Job list with current config
   - Run history with utilization charts
   - Before/after cost comparison

---

## Production Recommendations

### Database Migration

**Current:** File-based (`analysis_history.json`)

**Recommended:** Amazon RDS PostgreSQL

#### Schema Design

```sql
-- Tables
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    service_type VARCHAR(20) NOT NULL,  -- EMR, ECS, EKS, DYNAMODB, GLUE
    resource_id VARCHAR(255) NOT NULL,
    resource_name VARCHAR(255),
    analyzed_at TIMESTAMP DEFAULT NOW(),
    lookback_hours INTEGER,
    total_potential_monthly_savings DECIMAL(10,2),
    analysis_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_service_resource ON analysis_results(service_type, resource_id);
CREATE INDEX idx_analyzed_at ON analysis_results(analyzed_at DESC);

-- Cleanup old analyses (keep last 10 per resource)
CREATE OR REPLACE FUNCTION cleanup_old_analyses()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM analysis_results
    WHERE id IN (
        SELECT id FROM (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY service_type, resource_id
                ORDER BY analyzed_at DESC
            ) as rn
            FROM analysis_results
        ) ranked
        WHERE rn > 10
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_cleanup_analyses
AFTER INSERT ON analysis_results
EXECUTE FUNCTION cleanup_old_analyses();
```

### Authentication (Future)

Recommended options:
1. **AWS Cognito** - For user authentication
2. **AWS SSO** - For enterprise single sign-on
3. **IAM Roles** - For service-to-service authentication

### Deployment Options

| Option | Pros | Cons |
|--------|------|------|
| **EC2** | Simple, full control | Manual scaling, maintenance |
| **ECS Fargate** | Serverless, auto-scaling | Container knowledge required |
| **Lambda + API Gateway** | Fully serverless | Cold starts, 15-min timeout |

**Recommended:** ECS Fargate for production deployment.

### Monitoring & Alerting

1. **CloudWatch Dashboards** - Track analysis counts, error rates
2. **CloudWatch Alarms** - Alert on service errors
3. **X-Ray Tracing** - Debug slow analyses

---

## Appendix

### A. Supported EC2 Instance Types (EMR)

```python
INSTANCE_FAMILIES = {
    'general': ['m5', 'm5a', 'm6i', 'm7i'],
    'compute': ['c5', 'c5a', 'c6i', 'c7i'],
    'memory': ['r5', 'r5a', 'r6i', 'r7i'],
    'storage': ['i3', 'd2']
}
```

### B. Threshold Configuration

```python
THRESHOLDS = {
    'heavily_oversized': {
        'avg_max': 25,
        'peak_max': 35,
        'action': 'downsize_aggressive'
    },
    'moderately_oversized': {
        'avg_max': 50,
        'peak_max': 60,
        'action': 'downsize_moderate'
    },
    'right_sized': {
        'avg_max': 70,
        'peak_max': 80,
        'action': 'none'
    },
    'undersized': {
        'avg_min': 70,
        'peak_min': 80,
        'action': 'upsize'
    }
}
```

### C. API Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 404 | Resource not found |
| 500 | Internal server error |

### D. Glossary

| Term | Definition |
|------|------------|
| **DPU** | Data Processing Unit (Glue) - 4 vCPUs + 16GB RAM |
| **RCU** | Read Capacity Unit (DynamoDB) - 1 strongly consistent read/sec for 4KB |
| **WCU** | Write Capacity Unit (DynamoDB) - 1 write/sec for 1KB |
| **P95** | 95th percentile - value below which 95% of data points fall |
| **Headroom** | Buffer added to requirements (default 20%) |

---

*Document Version: 1.0*
*Last Updated: January 2025*
*Maintained by: Cloud Infrastructure Team*
