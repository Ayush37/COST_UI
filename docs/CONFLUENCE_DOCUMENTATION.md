# Cost Recommendation Engine - Technical Documentation

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [EMR Cost Optimizer (Implemented)](#emr-cost-optimizer-implemented)
3. [ECS Cost Optimizer (Proposed)](#ecs-cost-optimizer-proposed)
4. [EKS Cost Optimizer (Proposed)](#eks-cost-optimizer-proposed)
5. [DynamoDB Cost Optimizer (Proposed)](#dynamodb-cost-optimizer-proposed)
6. [Glue Cost Optimizer (Proposed)](#glue-cost-optimizer-proposed)
7. [Unified Architecture](#unified-architecture)
8. [Production Recommendations](#production-recommendations)

---

## Executive Summary

The **Cost Recommendation Engine** is a web-based platform designed to analyze AWS resource utilization across multiple services and provide actionable cost optimization recommendations. The platform identifies over-provisioned resources, calculates potential savings, and suggests right-sized alternatives.

### Current Status

| Service | Status | Optimization Focus |
|---------|--------|-------------------|
| EMR | Implemented | Instance right-sizing for cluster nodes |
| ECS | Planned | Task CPU/Memory optimization |
| EKS | Planned | Node group + Pod resource optimization |
| DynamoDB | Planned | Capacity mode + Storage class |
| Glue | Planned | DPU right-sizing |

### Core Capabilities

- **Utilization Analysis**: Collect and analyze resource metrics from CloudWatch
- **Intelligent Classification**: Categorize resources as oversized, right-sized, or undersized
- **Smart Recommendations**: Provide actionable alternatives with cost comparisons
- **Savings Calculator**: Quantify potential monthly cost savings
- **Multi-Service Dashboard**: Unified portal for all AWS cost optimization

### Universal Sizing Thresholds

All services use consistent thresholds for classification:

| Status | Average Utilization | Peak (P95) Utilization | Action |
|--------|---------------------|------------------------|--------|
| Heavily Oversized | < 25% | < 35% | Aggressive downsizing |
| Moderately Oversized | < 50% | < 60% | Moderate downsizing |
| Right-Sized | < 70% | < 80% | No change needed |
| Undersized | ≥ 70% | ≥ 80% | Consider upsizing |

---

## EMR Cost Optimizer (Implemented)

### Overview

The EMR Cost Optimizer analyzes CPU and memory utilization of EMR cluster nodes (Core and Task) to identify over-provisioned instances and recommend cost-effective alternatives.

### Analysis Approach

#### What We Analyze

| Data Point | Source | Purpose |
|------------|--------|---------|
| Cluster configuration | EMR API | Instance types, counts, runtime |
| CPU utilization | CloudWatch (AWS/EC2) | Compute usage patterns |
| Memory utilization | CloudWatch (CWAgent) | Memory usage patterns |
| Instance specifications | Static pricing data | vCPUs, RAM, hourly cost |

#### How Analysis Works

1. **Cluster Discovery**: Fetch all running and recently terminated EMR clusters
2. **Classification**: Categorize as TRANSIENT (< 7 hours) or LONG_RUNNING (≥ 7 hours)
3. **Metrics Collection**: Gather CPU/Memory metrics for configurable lookback period
4. **Utilization Calculation**: Compute average and P95 (peak) utilization
5. **Sizing Assessment**: Compare utilization against thresholds
6. **Recommendation Generation**: Find smaller instances that meet actual workload needs
7. **Savings Calculation**: Compute hourly and monthly cost differences

#### Lookback Periods

| Cluster Type | Default Lookback | Rationale |
|--------------|------------------|-----------|
| Transient | 4 hours | Short-lived, recent data most relevant |
| Long-Running | 72 hours (3 days) | Sufficient data for usage patterns |

#### Recommendation Types

| Type | Description | Selection Criteria |
|------|-------------|-------------------|
| Same Family | Smaller instance in current family (e.g., r5.2xlarge → r5.xlarge) | Lowest risk, maintains compatibility |
| Cross Family | Cheapest instance meeting requirements across all families | Maximum savings potential |
| Category Optimized | Best instance for workload profile (compute/memory/general) | Matches CPU-heavy or Memory-heavy patterns |

#### Headroom Calculation

All recommendations include a **20% headroom buffer** to ensure recommended instances can handle peak loads:

```
Required Resources = (Current Specs × Peak Utilization) × 1.2
```

### Architecture

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
│  │   Routes     │  │ EMR Service  │  │ CloudWatch   │  │  Analyzer    │   │
│  │   (app.py)   │  │              │  │  Service     │  │  Service     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐                   ┌──────────────┐    │
│  │   Config     │  │   Pricing    │                   │    Data      │    │
│  │ (Thresholds) │  │   Service    │                   │   Storage    │    │
│  └──────────────┘  └──────────────┘                   └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ AWS SDK (boto3)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS SERVICES                                    │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │     EMR      │  │  CloudWatch  │  │     EC2      │                      │
│  │  - Clusters  │  │  - CPU (EC2) │  │  - Instance  │                      │
│  │  - Instance  │  │  - Memory    │  │    Details   │                      │
│  │    Groups    │  │    (CWAgent) │  │              │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

#### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Runtime | Python 3.8+ | Core application |
| Web Framework | Flask 2.x | REST API and templates |
| AWS SDK | boto3 | AWS service integration |

#### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| CSS Framework | Bootstrap 5.3.2 | Responsive layout |
| Icons | Bootstrap Icons 1.11.1 | UI iconography |
| JavaScript | Vanilla JS (ES6+) | Dynamic interactions |
| Templating | Jinja2 | Server-side rendering |

### UI Design Principles

| Principle | Implementation |
|-----------|----------------|
| Color Palette | Primary (#0d6efd), Success/Savings (#198754), Warning (#ffc107), Danger (#dc3545) |
| Cards | 12px border-radius, subtle shadow, no border |
| Typography | System fonts, clear hierarchy (title → body → meta) |
| Status Colors | Red (heavily oversized), Yellow (moderate), Green (right-sized), Blue (undersized) |
| Layout | Fixed 220px sidebar, fluid main content, responsive breakpoints |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Landing page with savings overview |
| GET | `/emr` | EMR dashboard |
| GET | `/api/clusters` | List all EMR clusters (transient, long-running, terminated) |
| GET | `/api/clusters/<id>` | Get specific cluster details |
| POST | `/api/clusters/<id>/analyze` | Trigger cluster analysis |
| GET | `/api/clusters/<id>/analysis` | Get latest analysis results |
| GET | `/api/analysis/history` | Get historical analyses |
| GET | `/api/config/lookback-options` | Get available lookback periods |
| GET | `/api/health` | Health check |

### Data Storage

**Current**: File-based (`data/analysis_history.json`)
- Keyed by cluster ID
- Last 10 analyses retained per cluster
- Automatic pruning of older analyses

### IAM Permissions Required

| Permission | Purpose |
|------------|---------|
| `elasticmapreduce:ListClusters` | List EMR clusters |
| `elasticmapreduce:DescribeCluster` | Get cluster details |
| `elasticmapreduce:ListInstanceGroups` | Get instance group configuration |
| `elasticmapreduce:ListInstances` | Get EC2 instance IDs |
| `ec2:DescribeInstances` | Get instance details |
| `cloudwatch:GetMetricStatistics` | Fetch CPU/Memory metrics |

---

## ECS Cost Optimizer (Proposed)

### Overview

Analyze ECS services and tasks to identify over-provisioned CPU and memory allocations in task definitions, and recommend right-sized configurations for both Fargate and EC2 launch types.

### Analysis Approach

#### What to Analyze

| Data Point | Source | Purpose |
|------------|--------|---------|
| Service configuration | ECS API | Task definitions, desired count, launch type |
| Task CPU/Memory allocation | ECS API | Provisioned resources per task |
| CPU utilization | CloudWatch (AWS/ECS) | Actual CPU consumption |
| Memory utilization | CloudWatch (AWS/ECS) | Actual memory consumption |
| Running task count | CloudWatch (AWS/ECS) | Scaling patterns |

#### How Analysis Will Work

1. **Service Discovery**: List all ECS clusters and services
2. **Configuration Extraction**: Get task definitions with CPU/Memory allocations
3. **Metrics Collection**: Gather service-level CPU and Memory utilization
4. **Utilization Comparison**: Compare allocated vs actual consumption
5. **Sizing Assessment**: Apply standard thresholds to determine status
6. **Recommendation Generation**: Suggest reduced task definitions or launch type changes
7. **Savings Calculation**: Compute Fargate (vCPU-hours + GB-hours) or EC2 cost differences

#### Key Differences from EMR

| Aspect | EMR | ECS |
|--------|-----|-----|
| Unit of Analysis | Instance groups | Services/Tasks |
| Resource Model | EC2 instance types | CPU units (1024 = 1 vCPU) + Memory MB |
| Pricing | EC2 hourly rates | Fargate: vCPU + Memory; EC2: instance hours |
| Constraints | Instance family sizes | Valid Fargate CPU/Memory combinations |

#### Recommendation Types

| Type | Description |
|------|-------------|
| Task CPU/Memory Reduction | Reduce CPU units and/or memory in task definition |
| Container-level Optimization | Adjust individual container allocations within task |
| Launch Type Switch | Recommend Fargate vs EC2 based on usage patterns and cost |

#### Fargate Configuration Constraints

Recommendations must respect valid Fargate combinations:
- 256 CPU (.25 vCPU): 512MB - 2GB memory
- 512 CPU (.5 vCPU): 1GB - 4GB memory
- 1024 CPU (1 vCPU): 2GB - 8GB memory
- 2048 CPU (2 vCPU): 4GB - 16GB memory
- 4096 CPU (4 vCPU): 8GB - 30GB memory

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ECS COST OPTIMIZER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ ECS Service  │────▶│ CloudWatch   │────▶│  Analyzer    │                │
│  │              │     │  Service     │     │  Service     │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
│         │                    │                    │                         │
│         ▼                    ▼                    ▼                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │  ECS API     │     │  CloudWatch  │     │   Fargate    │                │
│  │  - Clusters  │     │  - CPU %     │     │   Pricing    │                │
│  │  - Services  │     │  - Memory %  │     │   Service    │                │
│  │  - Tasks     │     │  - Task count│     │              │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Proposed API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ecs/clusters` | List all ECS clusters |
| GET | `/api/ecs/clusters/<name>/services` | List services in a cluster |
| GET | `/api/ecs/services/<arn>` | Get service details |
| POST | `/api/ecs/services/<arn>/analyze` | Trigger service analysis |
| GET | `/api/ecs/services/<arn>/analysis` | Get latest analysis |
| GET | `/api/ecs/analysis/summary` | Get summary across all services |

### IAM Permissions Required

| Permission | Purpose |
|------------|---------|
| `ecs:ListClusters` | List ECS clusters |
| `ecs:ListServices` | List services in cluster |
| `ecs:DescribeServices` | Get service configuration |
| `ecs:DescribeTaskDefinition` | Get task CPU/Memory allocation |
| `ecs:ListTasks` | List running tasks |
| `cloudwatch:GetMetricStatistics` | Fetch utilization metrics |

### Implementation Steps

1. Create `services/ecs_service.py` - ECS API interactions
2. Extend `services/cloudwatch_service.py` - ECS metric collection
3. Create `services/ecs_analyzer_service.py` - Analysis and recommendations
4. Add ECS routes to `app.py`
5. Create `templates/ecs.html` - Service list and analysis view
6. Update sidebar to show ECS as active

---

## EKS Cost Optimizer (Proposed)

### Overview

Analyze EKS clusters at **two levels**: node group instance sizing (infrastructure) and pod resource requests vs actual usage (application). This dual approach identifies waste at both the infrastructure and workload layers.

### Analysis Approach

#### Two-Level Analysis Model

| Level | What We Analyze | Optimization Goal |
|-------|-----------------|-------------------|
| **Node Level** | EC2 instances in node groups | Right-size instance types, reduce node count |
| **Pod Level** | CPU/Memory requests vs actual usage | Reduce over-requested resources, improve bin-packing |

#### What to Analyze

| Level | Data Point | Source | Purpose |
|-------|------------|--------|---------|
| Node | Instance type, count | EKS API | Current infrastructure |
| Node | CPU/Memory utilization | CloudWatch (AWS/EC2) | Node efficiency |
| Pod | CPU/Memory requests | Kubernetes API / Container Insights | Allocated resources |
| Pod | Actual CPU/Memory usage | Container Insights | Real consumption |

**Prerequisite**: Container Insights must be enabled on the EKS cluster for pod-level metrics.

#### How Analysis Will Work

**Node Level (Similar to EMR):**
1. List node groups and their instance configurations
2. Collect EC2-level CPU and Memory metrics
3. Apply sizing thresholds
4. Recommend smaller instance types or fewer nodes

**Pod Level (New approach):**
1. Query Container Insights for pod resource metrics
2. Compare requests vs actual usage per pod
3. Aggregate by deployment/namespace
4. Identify over-requesting deployments
5. Calculate freed resources if right-sized
6. Estimate potential node reduction from better bin-packing

#### Key Differences from EMR

| Aspect | EMR | EKS |
|--------|-----|-----|
| Unit of Analysis | Instance groups | Node groups + Pods |
| Metrics Source | EC2 + CWAgent | EC2 + Container Insights |
| Resource Model | Instance specs | Instance specs + Pod requests/limits |
| Optimization Layers | Single (infrastructure) | Dual (infrastructure + application) |

#### Recommendation Types

**Node-Level:**
| Type | Description |
|------|-------------|
| Instance Right-sizing | Smaller instance type for node group |
| Node Count Reduction | Reduce min/desired/max nodes |
| Spot Instance Mix | Add Spot instances for fault-tolerant workloads |
| Graviton Migration | Move to ARM-based instances (cost savings) |

**Pod-Level:**
| Type | Description |
|------|-------------|
| Request Reduction | Lower CPU/Memory requests in deployment spec |
| Limit Adjustment | Set appropriate limits based on actual usage |
| HPA Recommendation | Suggest Horizontal Pod Autoscaler configuration |

#### Savings Calculation

Pod-level optimization indirectly reduces costs by improving bin-packing:
- Reduced resource requests = more pods per node
- More pods per node = fewer nodes needed
- Fewer nodes = direct EC2 cost savings

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EKS COST OPTIMIZER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      TWO-LEVEL ANALYSIS                               │  │
│  ├───────────────────────────────┬──────────────────────────────────────┤  │
│  │  LEVEL 1: NODE GROUPS         │  LEVEL 2: POD RESOURCES              │  │
│  │  ┌─────────────────────┐      │  ┌─────────────────────┐             │  │
│  │  │ • Instance Type     │      │  │ • Requests vs Usage │             │  │
│  │  │ • Node Count        │      │  │ • Per Namespace     │             │  │
│  │  │ • Node Utilization  │      │  │ • Per Deployment    │             │  │
│  │  │                     │      │  │                     │             │  │
│  │  │ (Same as EMR)       │      │  │ (Container Insights)│             │  │
│  │  └─────────────────────┘      │  └─────────────────────┘             │  │
│  └───────────────────────────────┴──────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ EKS Service  │     │ CloudWatch   │     │  Analyzer    │                │
│  │              │     │  Service     │     │  Service     │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
│         │                    │                                              │
│         ▼                    ▼                                              │
│  ┌──────────────┐     ┌──────────────┐                                     │
│  │  EKS API     │     │  Container   │                                     │
│  │  EC2 API     │     │  Insights    │                                     │
│  └──────────────┘     └──────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Proposed API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/eks/clusters` | List all EKS clusters |
| GET | `/api/eks/clusters/<name>/nodegroups` | List node groups in cluster |
| GET | `/api/eks/clusters/<name>/namespaces` | List namespaces with pod counts |
| POST | `/api/eks/nodegroups/<arn>/analyze` | Analyze node group (infrastructure) |
| POST | `/api/eks/namespaces/<name>/analyze` | Analyze namespace pods (application) |
| GET | `/api/eks/analysis/summary/<cluster>` | Get cluster-wide summary |

### IAM Permissions Required

| Permission | Purpose |
|------------|---------|
| `eks:ListClusters` | List EKS clusters |
| `eks:DescribeCluster` | Get cluster details |
| `eks:ListNodegroups` | List node groups |
| `eks:DescribeNodegroup` | Get node group configuration |
| `ec2:DescribeInstances` | Get node instance details |
| `cloudwatch:GetMetricStatistics` | Fetch EC2 metrics |
| `cloudwatch:GetMetricData` | Fetch Container Insights metrics |
| `logs:StartQuery` | Query Container Insights logs |
| `logs:GetQueryResults` | Get query results |

### Implementation Steps

1. Create `services/eks_service.py` - EKS and EC2 API interactions
2. Extend `services/cloudwatch_service.py` - Container Insights queries
3. Create `services/eks_analyzer_service.py` - Two-tier analysis
4. Add EKS routes to `app.py`
5. Create `templates/eks.html` - Node group + namespace views
6. Update sidebar to show EKS as active

---

## DynamoDB Cost Optimizer (Proposed)

### Overview

Analyze DynamoDB tables to recommend optimal **capacity mode** (Provisioned vs On-Demand) and **storage class** (Standard vs Infrequent Access) based on actual usage patterns.

### Analysis Approach

#### Two Optimization Areas

| Area | What We Optimize | Potential Savings |
|------|------------------|-------------------|
| **Capacity Mode** | Provisioned vs On-Demand billing | 20-70% depending on usage pattern |
| **Storage Class** | Standard vs Infrequent Access | Up to 60% on storage costs |

#### What to Analyze

| Data Point | Source | Purpose |
|------------|--------|---------|
| Table configuration | DynamoDB API | Billing mode, provisioned RCU/WCU, table class |
| Consumed RCU/WCU | CloudWatch | Actual read/write consumption |
| Provisioned RCU/WCU | CloudWatch | Provisioned capacity (if applicable) |
| Throttled requests | CloudWatch | Under-provisioning indicator |
| Table size | DynamoDB API | Storage class analysis |
| Item count | DynamoDB API | Access pattern analysis |

#### How Analysis Will Work

**Capacity Mode Analysis:**
1. Fetch current billing mode and provisioned capacity
2. Collect consumed RCU/WCU metrics over lookback period
3. Calculate utilization percentage (consumed / provisioned)
4. Check for throttling (indicates under-provisioning)
5. Compare cost: Provisioned vs On-Demand for actual usage
6. Recommend optimal mode based on usage consistency and cost

**Storage Class Analysis:**
1. Get table size and access patterns
2. Calculate reads per GB per day
3. Compare Standard vs IA cost for the access pattern
4. Recommend IA for low-access tables (< 20% of Standard threshold)

#### Capacity Mode Decision Logic

| Current Mode | Usage Pattern | Recommendation |
|--------------|---------------|----------------|
| Provisioned | Utilization < 20% | Switch to On-Demand |
| Provisioned | Utilization 20-70% | Adjust provisioned capacity |
| Provisioned | Utilization > 70% + Throttling | Increase capacity or On-Demand |
| On-Demand | Consistent high usage | Consider Provisioned with Auto Scaling |
| On-Demand | Variable/bursty | Keep On-Demand |

#### Storage Class Decision Logic

| Table Size | Access Frequency | Recommendation |
|------------|------------------|----------------|
| < 1 GB | Any | Standard (IA not cost-effective) |
| ≥ 1 GB | < 0.5 reads/GB/day | Infrequent Access |
| ≥ 1 GB | ≥ 0.5 reads/GB/day | Standard |

#### Key Differences from EMR

| Aspect | EMR | DynamoDB |
|--------|-----|----------|
| Unit of Analysis | Clusters/Instances | Tables |
| Resource Model | Instance types | Capacity units (RCU/WCU) |
| Optimization Type | Right-sizing | Mode selection |
| Metrics | CPU/Memory % | Consumed vs Provisioned units |

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DYNAMODB COST OPTIMIZER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      TWO OPTIMIZATION AREAS                           │  │
│  ├───────────────────────────────┬──────────────────────────────────────┤  │
│  │  CAPACITY MODE                │  STORAGE CLASS                       │  │
│  │  ┌─────────────────────┐      │  ┌─────────────────────┐             │  │
│  │  │ Provisioned vs      │      │  │ Standard vs         │             │  │
│  │  │ On-Demand           │      │  │ Infrequent Access   │             │  │
│  │  │                     │      │  │                     │             │  │
│  │  │ Based on RCU/WCU    │      │  │ Based on access     │             │  │
│  │  │ utilization         │      │  │ frequency           │             │  │
│  │  └─────────────────────┘      │  └─────────────────────┘             │  │
│  └───────────────────────────────┴──────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ DynamoDB     │     │ CloudWatch   │     │  Analyzer    │                │
│  │ Service      │     │  Service     │     │  Service     │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
│         │                    │                    │                         │
│         ▼                    ▼                    ▼                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ DynamoDB API │     │  CloudWatch  │     │  Pricing     │                │
│  │ - Tables     │     │  - RCU/WCU   │     │  Calculator  │                │
│  │ - Config     │     │  - Throttles │     │              │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Proposed API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dynamodb/tables` | List all DynamoDB tables |
| GET | `/api/dynamodb/tables/<name>` | Get table details and configuration |
| POST | `/api/dynamodb/tables/<name>/analyze` | Trigger table analysis |
| GET | `/api/dynamodb/tables/<name>/analysis` | Get latest analysis |
| GET | `/api/dynamodb/analysis/summary` | Get summary across all tables |

### IAM Permissions Required

| Permission | Purpose |
|------------|---------|
| `dynamodb:ListTables` | List all tables |
| `dynamodb:DescribeTable` | Get table configuration |
| `dynamodb:DescribeContinuousBackups` | Check backup configuration |
| `cloudwatch:GetMetricStatistics` | Fetch RCU/WCU metrics |

### Implementation Steps

1. Create `services/dynamodb_service.py` - DynamoDB API interactions
2. Extend `services/cloudwatch_service.py` - DynamoDB metric collection
3. Create `services/dynamodb_analyzer_service.py` - Mode and class analysis
4. Add DynamoDB routes to `app.py`
5. Create `templates/dynamodb.html` - Table list and analysis view
6. Update sidebar to show DynamoDB as active

---

## Glue Cost Optimizer (Proposed)

### Overview

Analyze AWS Glue job configurations to identify over-allocated DPU (Data Processing Units) and recommend right-sized configurations, including execution class optimization.

### Analysis Approach

#### What to Analyze

| Data Point | Source | Purpose |
|------------|--------|---------|
| Job configuration | Glue API | Worker type, count, Glue version, execution class |
| Job run history | Glue API | Execution duration, status, DPU-seconds |
| Memory utilization | CloudWatch | Actual memory consumption per job |
| Bytes processed | CloudWatch | Data volume handled |

#### How Analysis Will Work

1. **Job Discovery**: List all Glue jobs and their configurations
2. **Run History Collection**: Fetch recent job runs (last 30 days)
3. **Metrics Aggregation**: Calculate average execution time, memory usage, success rate
4. **DPU Utilization Assessment**: Compare allocated DPUs vs actual usage
5. **Execution Class Analysis**: Determine if FLEX would be more cost-effective
6. **Recommendation Generation**: Suggest optimal worker count and execution class
7. **Savings Calculation**: Compute DPU-hour cost differences

#### DPU Sizing Thresholds

Apply same utilization thresholds based on memory usage:

| Memory Utilization | Status | Recommendation |
|--------------------|--------|----------------|
| < 25% | Heavily Oversized | Reduce workers to 40% of current |
| 25-50% | Moderately Oversized | Reduce workers to 60% of current |
| 50-70% | Right-Sized | Keep current configuration |
| > 70% | Potentially Undersized | Consider increasing workers |

#### Execution Class Optimization

| Current Class | Job Duration | Recommendation |
|---------------|--------------|----------------|
| STANDARD | > 10 minutes | Consider FLEX (34% savings) |
| STANDARD | < 10 minutes | Keep STANDARD (startup time matters) |
| FLEX | Any | Already optimized for cost |

**FLEX Execution Class:**
- 34% cheaper than STANDARD
- Has startup latency (not ideal for short jobs)
- Best for jobs running > 10 minutes

#### Key Differences from EMR

| Aspect | EMR | Glue |
|--------|-----|------|
| Unit of Analysis | Clusters | Jobs |
| Resource Model | Instance types | DPUs (1 DPU = 4 vCPU + 16GB) |
| Pricing | Per instance-hour | Per DPU-hour ($0.44 Standard, $0.29 FLEX) |
| Runtime | Continuous | Job-based (per execution) |

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GLUE COST OPTIMIZER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      JOB-LEVEL ANALYSIS                               │  │
│  ├───────────────────────────────┬──────────────────────────────────────┤  │
│  │  DPU SIZING                   │  EXECUTION CLASS                     │  │
│  │  ┌─────────────────────┐      │  ┌─────────────────────┐             │  │
│  │  │ Worker count vs     │      │  │ STANDARD vs FLEX    │             │  │
│  │  │ actual usage        │      │  │                     │             │  │
│  │  │                     │      │  │ Based on job        │             │  │
│  │  │ Based on memory     │      │  │ duration            │             │  │
│  │  │ utilization         │      │  │                     │             │  │
│  │  └─────────────────────┘      │  └─────────────────────┘             │  │
│  └───────────────────────────────┴──────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ Glue Service │     │ CloudWatch   │     │  Analyzer    │                │
│  │              │     │  Service     │     │  Service     │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
│         │                    │                    │                         │
│         ▼                    ▼                    ▼                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │  Glue API    │     │  CloudWatch  │     │   Pricing    │                │
│  │  - Jobs      │     │  - Memory %  │     │  Calculator  │                │
│  │  - Job Runs  │     │  - Runtime   │     │              │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Proposed API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/glue/jobs` | List all Glue jobs |
| GET | `/api/glue/jobs/<name>` | Get job details and recent runs |
| POST | `/api/glue/jobs/<name>/analyze` | Trigger job analysis |
| GET | `/api/glue/jobs/<name>/analysis` | Get latest analysis |
| GET | `/api/glue/analysis/summary` | Get summary across all jobs |

### IAM Permissions Required

| Permission | Purpose |
|------------|---------|
| `glue:GetJobs` | List all Glue jobs |
| `glue:GetJob` | Get job configuration |
| `glue:GetJobRuns` | Get job execution history |
| `glue:BatchGetJobs` | Batch job retrieval |
| `cloudwatch:GetMetricStatistics` | Fetch job metrics |

### Implementation Steps

1. Create `services/glue_service.py` - Glue API interactions
2. Extend `services/cloudwatch_service.py` - Glue metric collection
3. Create `services/glue_analyzer_service.py` - DPU and execution class analysis
4. Add Glue routes to `app.py`
5. Create `templates/glue.html` - Job list and analysis view
6. Update sidebar to show Glue as active

---

## Unified Architecture

### Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COST RECOMMENDATION ENGINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           FRONTEND                                   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │  Home    │ │   EMR    │ │   ECS    │ │   EKS    │ │ DynamoDB │  │   │
│  │  │ (Savings)│ │Dashboard │ │Dashboard │ │Dashboard │ │Dashboard │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  │                                                      ┌──────────┐  │   │
│  │                      SIDEBAR NAVIGATION              │   Glue   │  │   │
│  │                                                      │Dashboard │  │   │
│  │                                                      └──────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      │ REST API                             │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           BACKEND (Flask)                            │   │
│  │                                                                      │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │                      SERVICE LAYER                              │ │   │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │ │   │
│  │  │  │   EMR   │ │   ECS   │ │   EKS   │ │DynamoDB │ │  Glue   │  │ │   │
│  │  │  │ Service │ │ Service │ │ Service │ │ Service │ │ Service │  │ │   │
│  │  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                      │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │                      SHARED SERVICES                            │ │   │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │ │   │
│  │  │  │   CloudWatch    │  │    Analyzer     │  │    Pricing     │  │ │   │
│  │  │  │    Service      │  │    Engine       │  │    Service     │  │ │   │
│  │  │  └─────────────────┘  └─────────────────┘  └────────────────┘  │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                                      │ boto3                                │
│                                      ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           AWS SERVICES                               │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐ ┌──────┐ ┌───────────┐    │   │
│  │  │ EMR  │ │ ECS  │ │ EKS  │ │ DynamoDB │ │ Glue │ │CloudWatch │    │   │
│  │  └──────┘ └──────┘ └──────┘ └──────────┘ └──────┘ └───────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Service Comparison Matrix

| Aspect | EMR | ECS | EKS | DynamoDB | Glue |
|--------|-----|-----|-----|----------|------|
| **Analysis Unit** | Cluster nodes | Services/Tasks | Nodes + Pods | Tables | Jobs |
| **Primary Metrics** | CPU, Memory % | CPU, Memory % | CPU, Memory % | RCU/WCU | Memory, Duration |
| **Resource Model** | EC2 instances | CPU units + MB | Instances + Requests | Capacity units | DPUs |
| **Recommendation Type** | Instance right-sizing | Task right-sizing | Instance + Request right-sizing | Mode selection | DPU right-sizing |
| **Pricing Model** | $/instance-hour | $/vCPU-hour + $/GB-hour | $/instance-hour | $/request or $/capacity | $/DPU-hour |

---

## Production Recommendations

### Database Migration

**Current:** File-based storage (`data/analysis_history.json`)

**Recommended:** Amazon RDS PostgreSQL

#### Benefits of RDS

| Benefit | Description |
|---------|-------------|
| Durability | Automated backups, point-in-time recovery |
| Scalability | Easy vertical scaling, read replicas |
| Concurrency | Multiple users without file locking issues |
| Querying | SQL for complex analysis history queries |
| Multi-service | Single database for all service analyses |

#### Recommended Schema

| Table | Purpose |
|-------|---------|
| `analysis_results` | Store all analysis results (partitioned by service type) |
| `analysis_metadata` | Track analysis runs, duration, status |
| `recommendations_applied` | Track which recommendations were implemented |

#### Key Indexes

- Service type + Resource ID (for quick lookups)
- Analyzed timestamp (for history queries)
- Savings amount (for reporting)

### Authentication (Future Enhancement)

| Option | Use Case |
|--------|----------|
| AWS Cognito | User pools for application authentication |
| AWS SSO | Enterprise single sign-on integration |
| IAM Roles | Service-to-service authentication |

### Deployment Options

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| EC2 | Simple, full control | Manual scaling | Development/Testing |
| ECS Fargate | Serverless, auto-scaling | Container knowledge | **Production** |
| Lambda + API Gateway | Fully serverless | 15-min timeout, cold starts | Not recommended |

### Monitoring & Alerting

| Component | Tool | Purpose |
|-----------|------|---------|
| Application metrics | CloudWatch Dashboards | Track analysis counts, error rates |
| Error alerting | CloudWatch Alarms | Alert on failures |
| Request tracing | AWS X-Ray | Debug slow analyses |
| Cost monitoring | AWS Cost Explorer | Track tool's own AWS costs |

---

## Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| **DPU** | Data Processing Unit (Glue) - 4 vCPUs + 16GB RAM |
| **RCU** | Read Capacity Unit (DynamoDB) - 1 strongly consistent read/sec for 4KB |
| **WCU** | Write Capacity Unit (DynamoDB) - 1 write/sec for 1KB |
| **P95** | 95th percentile - value below which 95% of data points fall |
| **Headroom** | Buffer added to requirements (default 20%) |
| **Bin-packing** | Efficient placement of pods on nodes to minimize waste |

### B. Pricing Reference (us-east-1)

| Service | Resource | Price |
|---------|----------|-------|
| EC2 | r5.xlarge | $0.252/hour |
| EC2 | r5.2xlarge | $0.504/hour |
| Fargate | vCPU | $0.04048/hour |
| Fargate | Memory | $0.004445/GB-hour |
| DynamoDB | RCU (Provisioned) | $0.00013/hour |
| DynamoDB | WCU (Provisioned) | $0.00065/hour |
| DynamoDB | RRU (On-Demand) | $0.25/million |
| DynamoDB | WRU (On-Demand) | $1.25/million |
| Glue | DPU (Standard) | $0.44/hour |
| Glue | DPU (Flex) | $0.29/hour |

### C. Implementation Priority

| Priority | Service | Rationale |
|----------|---------|-----------|
| 1 (Done) | EMR | Foundation established |
| 2 | ECS | Most similar to EMR, high adoption |
| 3 | EKS | Similar to EMR but with pod-level complexity |
| 4 | DynamoDB | Different model, high savings potential |
| 5 | Glue | Job-based, simpler scope |

---

*Document Version: 1.1*
*Last Updated: January 2025*
*Maintained by: Cloud Infrastructure Team*
