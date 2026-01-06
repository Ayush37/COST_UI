"""
Analyzer Service for utilization analysis and recommendations
"""
import json
import os
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser
from typing import Dict, List, Optional
import config
from services.emr_service import EMRService
from services.cloudwatch_service import CloudWatchService
from services.pricing_service import PricingService


class AnalyzerService:
    """Service for analyzing cluster utilization and generating recommendations"""

    def __init__(self):
        self.emr_service = EMRService()
        self.cloudwatch_service = CloudWatchService()
        self.pricing_service = PricingService()
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs(config.DATA_DIR, exist_ok=True)

    def analyze_cluster(self, cluster_id: str, lookback_hours: int = None) -> Dict:
        """
        Perform full analysis on a cluster.
        Returns detailed metrics, sizing status, and recommendations.

        Args:
            cluster_id: EMR cluster ID
            lookback_hours: Number of hours to look back for metrics.
                           If None, uses default from config.
        """
        # Get cluster details
        cluster = self.emr_service.get_cluster_by_id(cluster_id)
        if not cluster:
            return {'error': f'Cluster {cluster_id} not found'}

        # Parse cluster creation time
        created_time = date_parser.parse(cluster['created_time'])

        # Calculate lookback time based on provided hours or default
        if lookback_hours:
            now = datetime.now(timezone.utc)
            max_lookback = now - timedelta(hours=lookback_hours)
            # Don't look back further than cluster creation
            if created_time.tzinfo is None:
                created_time = created_time.replace(tzinfo=timezone.utc)
            start_time = max(created_time, max_lookback)
        else:
            # Use the automatic calculation based on cluster type
            start_time = self.cloudwatch_service.calculate_lookback_time(
                cluster['cluster_type'],
                created_time
            )

        # Calculate actual lookback hours for display
        now = datetime.now(timezone.utc)
        actual_lookback_hours = round((now - start_time).total_seconds() / 3600, 1)

        # Analyze each instance group (CORE and TASK only, skip MASTER)
        node_analyses = {}
        total_potential_savings = 0

        for group in cluster['instance_groups']:
            if group['type'] in ['CORE', 'TASK']:
                analysis = self._analyze_instance_group(
                    group,
                    start_time,
                    cluster['cluster_type']
                )
                node_analyses[group['type']] = analysis

                if analysis.get('recommendations') and analysis['recommendations'].get('best_recommendation'):
                    savings = analysis['recommendations']['best_recommendation'].get('savings', {})
                    total_potential_savings += savings.get('hourly_savings', 0)

        # Build analysis result
        result = {
            'cluster_id': cluster_id,
            'cluster_name': cluster['name'],
            'cluster_type': cluster['cluster_type'],
            'runtime_hours': cluster['runtime_hours'],
            'analyzed_at': datetime.now(timezone.utc).isoformat(),
            'lookback_hours': actual_lookback_hours,
            'requested_lookback_hours': lookback_hours or config.DEFAULT_LOOKBACK_HOURS,
            'analysis_period': {
                'start': start_time.isoformat(),
                'end': datetime.now(timezone.utc).isoformat()
            },
            'node_analyses': node_analyses,
            'total_potential_hourly_savings': round(total_potential_savings, 4),
            'total_potential_monthly_savings': round(total_potential_savings * 730, 2)
        }

        # Persist analysis
        self._save_analysis(result)

        return result

    def _analyze_instance_group(
        self,
        group: Dict,
        start_time: datetime,
        cluster_type: str
    ) -> Dict:
        """Analyze a single instance group"""
        instance_type = group['instance_type']
        instance_count = group['running_count']
        ec2_instances = group.get('ec2_instances', [])

        # Get instance specifications
        instance_specs = self.pricing_service.get_instance_specs(instance_type)

        # Get metrics
        metrics = self.cloudwatch_service.get_aggregated_metrics_for_instances(
            ec2_instances,
            start_time
        )

        # Determine if metrics are available
        metrics_available = metrics['instances_with_metrics'] > 0
        partial_metrics = (
            metrics['instances_with_metrics'] > 0 and
            metrics['instances_with_metrics'] < metrics['instance_count']
        )

        # Build metrics warning for task nodes in long-running clusters
        metrics_warning = None
        if cluster_type == 'LONG_RUNNING' and group['type'] == 'TASK':
            if not metrics_available:
                metrics_warning = (
                    "Task node metrics unavailable - nodes scale frequently "
                    "and EC2 only retains 3 hours of metrics data."
                )
            elif partial_metrics:
                metrics_warning = (
                    f"Partial metrics available ({metrics['instances_with_metrics']}/{metrics['instance_count']} instances). "
                    "Some task nodes may have scaled recently."
                )

        # Determine sizing status and generate recommendations
        sizing_status = None
        workload_profile = None
        recommendations = None
        confidence = None

        if metrics_available:
            # Determine workload profile (CPU-heavy, Memory-heavy, or Balanced)
            workload_profile = self._determine_workload_profile(metrics)

            # Determine sizing status
            sizing_status = self._determine_sizing_status(metrics)

            # Calculate confidence
            confidence = self._calculate_confidence(metrics, cluster_type)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                instance_type,
                instance_specs,
                instance_count,
                metrics,
                workload_profile,
                sizing_status
            )

        return {
            'group_id': group['id'],
            'group_name': group['name'],
            'group_type': group['type'],
            'instance_type': instance_type,
            'instance_count': instance_count,
            'instance_specs': instance_specs,
            'current_hourly_cost': round(
                (instance_specs['price'] if instance_specs else 0) * instance_count, 4
            ),
            'metrics': {
                'cpu': metrics['cpu'],
                'memory': metrics['memory'],
                'instances_analyzed': metrics['instances_with_metrics'],
                'total_instances': metrics['instance_count']
            },
            'metrics_available': metrics_available,
            'partial_metrics': partial_metrics,
            'metrics_warning': metrics_warning,
            'workload_profile': workload_profile,
            'sizing_status': sizing_status,
            'confidence': confidence,
            'recommendations': recommendations
        }

    def _determine_workload_profile(self, metrics: Dict) -> str:
        """
        Determine workload profile based on CPU vs Memory utilization.
        Uses the higher of avg and p95 for comparison.
        """
        cpu_util = max(
            metrics['cpu'].get('average', 0) or 0,
            metrics['cpu'].get('p95', 0) or 0
        )
        mem_util = max(
            metrics['memory'].get('average', 0) or 0,
            metrics['memory'].get('p95', 0) or 0
        )

        if cpu_util == 0 and mem_util == 0:
            return 'unknown'

        ratio = cpu_util / mem_util if mem_util > 0 else float('inf')

        if ratio > 1.5:
            return 'cpu_heavy'
        elif ratio < 0.67:
            return 'memory_heavy'
        else:
            return 'balanced'

    def _determine_sizing_status(self, metrics: Dict) -> Dict:
        """
        Determine if the instance group is oversized, right-sized, or undersized.
        Uses the HIGHER of CPU and Memory utilization.
        Now uses effective_peak (sustained) instead of raw P95 for more accurate sizing.
        """
        # Get the higher utilization metric
        cpu_avg = metrics['cpu'].get('average', 0) or 0
        mem_avg = metrics['memory'].get('average', 0) or 0

        # Use effective_peak (which accounts for sustained vs momentary peaks)
        cpu_effective_peak = metrics['cpu'].get('effective_peak', 0) or metrics['cpu'].get('p95', 0) or 0
        mem_effective_peak = metrics['memory'].get('effective_peak', 0) or metrics['memory'].get('p95', 0) or 0

        # Use higher of CPU/Memory for both avg and effective peak
        effective_avg = max(cpu_avg, mem_avg)
        effective_peak = max(cpu_effective_peak, mem_effective_peak)

        thresholds = config.THRESHOLDS

        if (effective_avg < thresholds['heavily_oversized']['avg_max'] and
                effective_peak < thresholds['heavily_oversized']['peak_max']):
            return {
                'status': 'heavily_oversized',
                'label': 'Heavily Oversized',
                'description': 'Instance is significantly larger than needed',
                'color': 'danger',
                'downsizing_levels': 2
            }
        elif (effective_avg < thresholds['moderately_oversized']['avg_max'] and
              effective_peak < thresholds['moderately_oversized']['peak_max']):
            return {
                'status': 'moderately_oversized',
                'label': 'Moderately Oversized',
                'description': 'Instance is larger than needed',
                'color': 'warning',
                'downsizing_levels': 1
            }
        elif (effective_avg < thresholds['right_sized']['avg_max'] and
              effective_peak < thresholds['right_sized']['peak_max']):
            return {
                'status': 'right_sized',
                'label': 'Right-Sized',
                'description': 'Instance size matches workload requirements',
                'color': 'success',
                'downsizing_levels': 0
            }
        else:
            return {
                'status': 'undersized',
                'label': 'Potentially Undersized',
                'description': 'Instance may need more resources',
                'color': 'info',
                'downsizing_levels': -1
            }

    def _calculate_confidence(self, metrics: Dict, cluster_type: str) -> Dict:
        """Calculate confidence score for the recommendation"""
        # Factors:
        # 1. Data availability (number of datapoints)
        # 2. Metrics consistency (variance)
        # 3. Instance coverage

        cpu_datapoints = metrics['cpu'].get('datapoints', 0)
        mem_datapoints = metrics['memory'].get('datapoints', 0)
        instance_coverage = (
            metrics['instances_with_metrics'] / metrics['instance_count']
            if metrics['instance_count'] > 0 else 0
        )

        # Calculate data score (based on datapoints)
        total_datapoints = cpu_datapoints + mem_datapoints
        if cluster_type == 'TRANSIENT':
            expected_datapoints = 48 * 2  # ~4 hours of 5-min intervals, CPU + MEM
        else:
            expected_datapoints = 864 * 2  # ~3 days of 5-min intervals, CPU + MEM

        data_score = min(total_datapoints / expected_datapoints, 1.0) if expected_datapoints > 0 else 0

        # Calculate coverage score
        coverage_score = instance_coverage

        # Calculate overall confidence
        confidence_score = (data_score * 0.6 + coverage_score * 0.4)

        if confidence_score >= 0.8:
            level = 'high'
        elif confidence_score >= 0.5:
            level = 'medium'
        else:
            level = 'low'

        reasons = []
        if data_score < 0.5:
            reasons.append('Limited metric data available')
        if coverage_score < 1.0:
            reasons.append(f'Metrics from {metrics["instances_with_metrics"]}/{metrics["instance_count"]} instances')

        return {
            'level': level,
            'score': round(confidence_score, 2),
            'data_score': round(data_score, 2),
            'coverage_score': round(coverage_score, 2),
            'reasons': reasons if reasons else ['Sufficient data for analysis']
        }

    def _generate_recommendations(
        self,
        current_instance_type: str,
        current_specs: Dict,
        instance_count: int,
        metrics: Dict,
        workload_profile: str,
        sizing_status: Dict
    ) -> Optional[Dict]:
        """Generate instance recommendations based on analysis"""
        if not current_specs:
            return None

        # If right-sized or undersized, no downsizing recommendations
        if sizing_status['status'] in ['right_sized', 'undersized']:
            return {
                'action': 'none' if sizing_status['status'] == 'right_sized' else 'consider_upsizing',
                'reason': sizing_status['description'],
                'same_family': None,
                'cross_family': None,
                'best_recommendation': None
            }

        # Calculate required resources with headroom
        # Use effective_peak (which accounts for sustained vs momentary peaks)
        cpu_effective_peak = metrics['cpu'].get('effective_peak', 0) or metrics['cpu'].get('p95', 0) or 0
        mem_effective_peak = metrics['memory'].get('effective_peak', 0) or metrics['memory'].get('p95', 0) or 0

        # Get peak analysis info for context
        cpu_peak_type = metrics['cpu'].get('peak_type', 'sustained')
        mem_peak_type = metrics['memory'].get('peak_type', 'sustained')
        cpu_peak_percentile = metrics['cpu'].get('effective_peak_percentile', 'P95')
        mem_peak_percentile = metrics['memory'].get('effective_peak_percentile', 'P95')

        # Calculate required resources based on effective peak usage + headroom
        headroom_multiplier = 1 + (config.HEADROOM_PERCENT / 100)

        required_vcpus = (current_specs['vcpus'] * cpu_effective_peak / 100) * headroom_multiplier
        required_memory = (current_specs['memory_gb'] * mem_effective_peak / 100) * headroom_multiplier

        # Ensure minimum resources
        required_vcpus = max(required_vcpus, 1)
        required_memory = max(required_memory, 2)

        # Determine preferred category based on workload profile
        category_preference = {
            'cpu_heavy': 'compute',
            'memory_heavy': 'memory',
            'balanced': 'general',
            'unknown': 'general'
        }.get(workload_profile, 'general')

        # Find suitable instances
        suitable = self.pricing_service.find_suitable_instances(
            required_vcpus,
            required_memory,
            current_instance_type,
            category_preference
        )

        recommendations = {
            'action': 'downsize',
            'reason': f'{sizing_status["label"]} - can reduce instance size',
            'required_vcpus': round(required_vcpus, 1),
            'required_memory_gb': round(required_memory, 1),
            'same_family': None,
            'same_family_note': None,
            'cross_family': None,
            'category_optimized': None,
            'cheaper_alternative': None,
            'best_recommendation': None,
            # Peak analysis info
            'peak_analysis': {
                'cpu': {
                    'p95': metrics['cpu'].get('p95'),
                    'effective_peak': cpu_effective_peak,
                    'peak_type': cpu_peak_type,
                    'percentile_used': cpu_peak_percentile,
                    'is_spike': metrics['cpu'].get('is_spike', False),
                    'duration_at_p95_minutes': metrics['cpu'].get('duration_at_p95_minutes', 0)
                },
                'memory': {
                    'p95': metrics['memory'].get('p95'),
                    'effective_peak': mem_effective_peak,
                    'peak_type': mem_peak_type,
                    'percentile_used': mem_peak_percentile,
                    'is_spike': metrics['memory'].get('is_spike', False),
                    'duration_at_p95_minutes': metrics['memory'].get('duration_at_p95_minutes', 0)
                }
            }
        }

        current_family = current_specs.get('family')
        current_price = current_specs.get('price', 0)

        # Process same-family recommendation
        if suitable['same_family']:
            rec = suitable['same_family']
            if rec['type'] != current_instance_type:
                # Found a smaller instance in the same family
                savings = self.pricing_service.calculate_savings(
                    current_instance_type,
                    rec['type'],
                    instance_count
                )
                recommendations['same_family'] = {
                    'instance_type': rec['type'],
                    'vcpus': rec['vcpus'],
                    'memory_gb': rec['memory_gb'],
                    'price_per_hour': rec['price'],
                    'savings': savings
                }
            else:
                # The smallest suitable instance IS the current instance
                # No smaller option available in the same family
                recommendations['same_family_note'] = (
                    f"No smaller {current_family} instance can meet the "
                    f"required {round(required_memory, 1)} GB memory with {config.HEADROOM_PERCENT}% headroom. "
                    f"Current size is optimal for this family."
                )

        # Process cross-family recommendation - look for CHEAPER alternatives
        # This could be same size but cheaper family, or smaller in different family
        if suitable['cross_family']:
            rec = suitable['cross_family']
            if rec['type'] != current_instance_type:
                savings = self.pricing_service.calculate_savings(
                    current_instance_type,
                    rec['type'],
                    instance_count
                )
                # Only recommend if there are actual savings
                if savings and savings['hourly_savings'] > 0:
                    recommendations['cross_family'] = {
                        'instance_type': rec['type'],
                        'vcpus': rec['vcpus'],
                        'memory_gb': rec['memory_gb'],
                        'price_per_hour': rec['price'],
                        'family': rec['family'],
                        'category': rec['category'],
                        'savings': savings
                    }

        # Look for cheaper alternatives at SAME OR SIMILAR specs
        # This handles cases like r7g.4xlarge -> r6g.4xlarge (same size, older gen, cheaper)
        cheaper_same_size = self.pricing_service.find_cheaper_alternative(
            current_instance_type,
            current_specs['vcpus'],
            current_specs['memory_gb']
        )
        if cheaper_same_size and cheaper_same_size['type'] != current_instance_type:
            savings = self.pricing_service.calculate_savings(
                current_instance_type,
                cheaper_same_size['type'],
                instance_count
            )
            if savings and savings['hourly_savings'] > 0:
                recommendations['cheaper_alternative'] = {
                    'instance_type': cheaper_same_size['type'],
                    'vcpus': cheaper_same_size['vcpus'],
                    'memory_gb': cheaper_same_size['memory_gb'],
                    'price_per_hour': cheaper_same_size['price'],
                    'family': cheaper_same_size['family'],
                    'category': cheaper_same_size['category'],
                    'savings': savings,
                    'note': 'Same specs, different family - potential cost savings'
                }

        # Process category-optimized recommendation
        if (suitable['category_optimized'] and
                suitable['category_optimized']['type'] != current_instance_type and
                suitable['category_optimized'] != suitable['cross_family']):
            rec = suitable['category_optimized']
            savings = self.pricing_service.calculate_savings(
                current_instance_type,
                rec['type'],
                instance_count
            )
            if savings and savings['hourly_savings'] > 0:
                recommendations['category_optimized'] = {
                    'instance_type': rec['type'],
                    'vcpus': rec['vcpus'],
                    'memory_gb': rec['memory_gb'],
                    'price_per_hour': rec['price'],
                    'family': rec['family'],
                    'category': rec['category'],
                    'workload_profile': workload_profile,
                    'savings': savings
                }

        # Determine best recommendation (highest savings)
        best = None
        best_savings = 0
        for key in ['same_family', 'cross_family', 'category_optimized', 'cheaper_alternative']:
            rec = recommendations.get(key)
            if rec and rec.get('savings'):
                if rec['savings']['hourly_savings'] > best_savings:
                    best = rec
                    best_savings = rec['savings']['hourly_savings']

        recommendations['best_recommendation'] = best

        # Update action and reason based on what we found
        if not best and recommendations.get('same_family_note'):
            # No cost savings possible, but we have an explanation
            recommendations['action'] = 'optimal_for_workload'
            recommendations['reason'] = (
                f"{sizing_status['label']} by utilization, but current instance is the "
                f"smallest in the {current_family} family that meets memory requirements. "
                f"Consider if peak usage patterns justify current sizing."
            )
        elif not best:
            # No recommendations found at all
            recommendations['action'] = 'none'
            recommendations['reason'] = 'No cost-saving alternatives found that meet workload requirements.'

        return recommendations

    def _save_analysis(self, analysis: Dict):
        """Save analysis to JSON file"""
        try:
            # Load existing data
            history = self._load_analysis_history()

            # Add new analysis (keyed by cluster_id)
            cluster_id = analysis['cluster_id']
            if cluster_id not in history:
                history[cluster_id] = []

            # Keep last 10 analyses per cluster
            history[cluster_id].append(analysis)
            history[cluster_id] = history[cluster_id][-10:]

            # Save
            with open(config.ANALYSIS_HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving analysis: {e}")

    def _load_analysis_history(self) -> Dict:
        """Load analysis history from JSON file"""
        try:
            if os.path.exists(config.ANALYSIS_HISTORY_FILE):
                with open(config.ANALYSIS_HISTORY_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading analysis history: {e}")
        return {}

    def get_analysis_history(self, cluster_id: str = None) -> Dict:
        """Get analysis history, optionally filtered by cluster_id"""
        history = self._load_analysis_history()
        if cluster_id:
            return {cluster_id: history.get(cluster_id, [])}
        return history

    def get_latest_analysis(self, cluster_id: str) -> Optional[Dict]:
        """Get the most recent analysis for a cluster"""
        history = self._load_analysis_history()
        cluster_history = history.get(cluster_id, [])
        return cluster_history[-1] if cluster_history else None
