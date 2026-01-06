"""
CloudWatch Service for metrics collection
"""
import boto3
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import config


class CloudWatchService:
    """Service for CloudWatch metrics collection"""

    def __init__(self):
        session_kwargs = {'region_name': config.AWS_REGION}
        if config.AWS_PROFILE:
            session_kwargs['profile_name'] = config.AWS_PROFILE

        self.session = boto3.Session(**session_kwargs)
        self.cloudwatch_client = self.session.client('cloudwatch')

    def get_instance_metrics(
        self,
        instance_id: str,
        start_time: datetime,
        end_time: datetime = None
    ) -> Dict:
        """
        Get CPU and Memory metrics for an EC2 instance.
        Returns average, p95 (peak), min, max, and datapoint count.
        """
        if end_time is None:
            end_time = datetime.now(timezone.utc)

        # Ensure timezone awareness
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        cpu_metrics = self._get_cpu_metrics(instance_id, start_time, end_time)
        memory_metrics = self._get_memory_metrics(instance_id, start_time, end_time)

        return {
            'instance_id': instance_id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'cpu': cpu_metrics,
            'memory': memory_metrics,
            'metrics_available': cpu_metrics['datapoints'] > 0 or memory_metrics['datapoints'] > 0
        }

    def _get_cpu_metrics(
        self,
        instance_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """Get CPU utilization metrics from AWS/EC2 namespace"""
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace=config.EC2_NAMESPACE,
                MetricName=config.CPU_METRIC_NAME,
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': instance_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=config.CLOUDWATCH_PERIOD_SECONDS,
                Statistics=['Average', 'Maximum', 'Minimum']
            )

            return self._process_metric_datapoints(response['Datapoints'], 'Average')
        except Exception as e:
            print(f"Error getting CPU metrics for {instance_id}: {e}")
            return self._empty_metrics()

    def _get_memory_metrics(
        self,
        instance_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """Get Memory utilization metrics from CWAgent namespace"""
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace=config.CWAGENT_NAMESPACE,
                MetricName=config.MEMORY_METRIC_NAME,
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': instance_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=config.CLOUDWATCH_PERIOD_SECONDS,
                Statistics=['Average', 'Maximum', 'Minimum']
            )

            return self._process_metric_datapoints(response['Datapoints'], 'Average')
        except Exception as e:
            print(f"Error getting Memory metrics for {instance_id}: {e}")
            return self._empty_metrics()

    def _process_metric_datapoints(self, datapoints: List[Dict], avg_stat: str) -> Dict:
        """Process CloudWatch datapoints and calculate statistics with sustained peak analysis"""
        if not datapoints:
            return self._empty_metrics()

        # Extract values
        averages = [dp[avg_stat] for dp in datapoints if avg_stat in dp]
        maximums = [dp['Maximum'] for dp in datapoints if 'Maximum' in dp]
        minimums = [dp['Minimum'] for dp in datapoints if 'Minimum' in dp]

        if not averages:
            return self._empty_metrics()

        # Calculate basic statistics
        avg_value = np.mean(averages)
        max_value = max(maximums) if maximums else max(averages)
        min_value = min(minimums) if minimums else min(averages)

        # Calculate multiple percentiles for sustained peak analysis
        p75_value = np.percentile(averages, 75)
        p90_value = np.percentile(averages, 90)
        p95_value = np.percentile(averages, 95)
        p99_value = np.percentile(averages, 99)

        # Calculate duration above thresholds (in minutes)
        # Each datapoint represents CLOUDWATCH_PERIOD_SECONDS
        period_minutes = config.CLOUDWATCH_PERIOD_SECONDS / 60
        duration_above = {}
        for threshold in config.UTILIZATION_THRESHOLDS:
            count_above = sum(1 for v in averages if v >= threshold)
            duration_above[threshold] = round(count_above * period_minutes, 1)

        # Detect if P95 is a spike (large gap between P90 and P95)
        spike_gap = p95_value - p90_value
        is_spike = bool(spike_gap > config.SPIKE_DETECTION_GAP_PERCENT)

        # Determine sustained peak and which percentile to use for sizing
        # Check if P95 was sustained for at least the threshold duration
        sustained_threshold = config.SUSTAINED_PEAK_THRESHOLD_MINUTES
        p95_threshold = p95_value * 0.95  # Consider values within 5% of P95 as "at P95 level"
        count_at_p95_level = sum(1 for v in averages if v >= p95_threshold)
        duration_at_p95_level = count_at_p95_level * period_minutes

        # Select effective peak for sizing
        if duration_at_p95_level >= sustained_threshold and not is_spike:
            effective_peak = p95_value
            peak_type = 'sustained'
            effective_peak_percentile = 'P95'
        elif duration_above.get(80, 0) >= sustained_threshold:
            # P95 wasn't sustained, check if P90 level was
            effective_peak = p90_value
            peak_type = 'moderate'
            effective_peak_percentile = 'P90'
        else:
            # Neither was sustained, use P75 for more conservative sizing
            effective_peak = p75_value
            peak_type = 'momentary'
            effective_peak_percentile = 'P75'

        return {
            'average': round(avg_value, 2),
            'p75': round(p75_value, 2),
            'p90': round(p90_value, 2),
            'p95': round(p95_value, 2),
            'p99': round(p99_value, 2),
            'max': round(max_value, 2),
            'min': round(min_value, 2),
            'datapoints': len(averages),
            'available': True,
            # Sustained peak analysis
            'effective_peak': round(effective_peak, 2),
            'effective_peak_percentile': effective_peak_percentile,
            'peak_type': peak_type,
            'is_spike': is_spike,
            'spike_gap': round(spike_gap, 2),
            'duration_above': duration_above,
            'duration_at_p95_minutes': round(duration_at_p95_level, 1)
        }

    def _empty_metrics(self) -> Dict:
        """Return empty metrics structure"""
        return {
            'average': None,
            'p75': None,
            'p90': None,
            'p95': None,
            'p99': None,
            'max': None,
            'min': None,
            'datapoints': 0,
            'available': False,
            # Sustained peak analysis
            'effective_peak': None,
            'effective_peak_percentile': None,
            'peak_type': None,
            'is_spike': False,
            'spike_gap': None,
            'duration_above': {},
            'duration_at_p95_minutes': 0
        }

    def get_aggregated_metrics_for_instances(
        self,
        instance_ids: List[str],
        start_time: datetime,
        end_time: datetime = None
    ) -> Dict:
        """
        Get aggregated metrics across multiple instances (for instance groups).
        Calculates weighted average across all instances with sustained peak analysis.
        """
        if not instance_ids:
            return {
                'instance_count': 0,
                'instances_with_metrics': 0,
                'cpu': self._empty_metrics(),
                'memory': self._empty_metrics(),
                'per_instance': []
            }

        all_cpu_metrics = []
        all_memory_metrics = []
        per_instance_metrics = []
        instances_with_metrics = 0

        for instance_id in instance_ids:
            metrics = self.get_instance_metrics(instance_id, start_time, end_time)
            per_instance_metrics.append(metrics)

            if metrics['metrics_available']:
                instances_with_metrics += 1

                if metrics['cpu']['available']:
                    all_cpu_metrics.append(metrics['cpu'])

                if metrics['memory']['available']:
                    all_memory_metrics.append(metrics['memory'])

        # Calculate aggregated metrics with sustained peak analysis
        aggregated_cpu = self._aggregate_values(all_cpu_metrics)
        aggregated_memory = self._aggregate_values(all_memory_metrics)

        return {
            'instance_count': len(instance_ids),
            'instances_with_metrics': instances_with_metrics,
            'cpu': aggregated_cpu,
            'memory': aggregated_memory,
            'per_instance': per_instance_metrics
        }

    def _aggregate_values(
        self,
        instance_metrics: List[Dict]
    ) -> Dict:
        """Aggregate values across multiple instances with sustained peak analysis"""
        if not instance_metrics:
            return self._empty_metrics()

        # Extract values from instance metrics
        averages = [m['average'] for m in instance_metrics if m.get('average') is not None]
        p75_values = [m['p75'] for m in instance_metrics if m.get('p75') is not None]
        p90_values = [m['p90'] for m in instance_metrics if m.get('p90') is not None]
        p95_values = [m['p95'] for m in instance_metrics if m.get('p95') is not None]
        p99_values = [m['p99'] for m in instance_metrics if m.get('p99') is not None]
        effective_peaks = [m['effective_peak'] for m in instance_metrics if m.get('effective_peak') is not None]

        if not averages:
            return self._empty_metrics()

        # Calculate aggregated basic stats (convert to native Python floats for JSON serialization)
        avg_value = float(np.mean(averages))
        p75_value = float(np.mean(p75_values) if p75_values else np.percentile(averages, 75))
        p90_value = float(np.mean(p90_values) if p90_values else np.percentile(averages, 90))
        p95_value = float(np.mean(p95_values) if p95_values else np.percentile(averages, 95))
        p99_value = float(np.mean(p99_values) if p99_values else np.percentile(averages, 99))
        effective_peak = float(np.mean(effective_peaks) if effective_peaks else p95_value)

        # Aggregate duration above thresholds
        duration_above = {}
        for threshold in config.UTILIZATION_THRESHOLDS:
            durations = [m.get('duration_above', {}).get(threshold, 0) for m in instance_metrics]
            if durations:
                duration_above[threshold] = round(float(np.mean(durations)), 1)

        # Aggregate duration at P95
        duration_at_p95_list = [m.get('duration_at_p95_minutes', 0) for m in instance_metrics]
        duration_at_p95_avg = float(np.mean(duration_at_p95_list)) if duration_at_p95_list else 0

        # Determine aggregate spike detection
        spike_gaps = [m.get('spike_gap', 0) for m in instance_metrics if m.get('spike_gap') is not None]
        avg_spike_gap = float(np.mean(spike_gaps)) if spike_gaps else 0
        is_spike = bool(avg_spike_gap > config.SPIKE_DETECTION_GAP_PERCENT)

        # Determine aggregate peak type based on most common type
        peak_types = [m.get('peak_type') for m in instance_metrics if m.get('peak_type')]
        if peak_types:
            # Use the most conservative (worst case) peak type
            if 'momentary' in peak_types:
                peak_type = 'momentary'
                effective_peak_percentile = 'P75'
            elif 'moderate' in peak_types:
                peak_type = 'moderate'
                effective_peak_percentile = 'P90'
            else:
                peak_type = 'sustained'
                effective_peak_percentile = 'P95'
        else:
            peak_type = 'sustained'
            effective_peak_percentile = 'P95'

        return {
            'average': round(avg_value, 2),
            'p75': round(p75_value, 2),
            'p90': round(p90_value, 2),
            'p95': round(p95_value, 2),
            'p99': round(p99_value, 2),
            'max': round(max(averages), 2),
            'min': round(min(averages), 2),
            'datapoints': len(averages),
            'available': True,
            # Sustained peak analysis
            'effective_peak': round(effective_peak, 2),
            'effective_peak_percentile': effective_peak_percentile,
            'peak_type': peak_type,
            'is_spike': is_spike,
            'spike_gap': round(avg_spike_gap, 2),
            'duration_above': duration_above,
            'duration_at_p95_minutes': round(duration_at_p95_avg, 1)
        }

    def calculate_lookback_time(
        self,
        cluster_type: str,
        cluster_created_time: datetime
    ) -> datetime:
        """
        Calculate the appropriate lookback time based on cluster type.

        For TRANSIENT: Look back to cluster creation or TRANSIENT_LOOKBACK_HOURS
        For LONG_RUNNING: Look back to cluster creation or MAX_LOOKBACK_DAYS
        """
        now = datetime.now(timezone.utc)

        if cluster_created_time.tzinfo is None:
            cluster_created_time = cluster_created_time.replace(tzinfo=timezone.utc)

        if cluster_type == 'TRANSIENT':
            max_lookback = now - timedelta(hours=config.TRANSIENT_LOOKBACK_HOURS)
        else:  # LONG_RUNNING
            max_lookback = now - timedelta(days=config.MAX_LOOKBACK_DAYS)

        # Use the more recent of cluster creation time or max lookback
        return max(cluster_created_time, max_lookback)
