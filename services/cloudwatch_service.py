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
        """Process CloudWatch datapoints and calculate statistics"""
        if not datapoints:
            return self._empty_metrics()

        # Extract values
        averages = [dp[avg_stat] for dp in datapoints if avg_stat in dp]
        maximums = [dp['Maximum'] for dp in datapoints if 'Maximum' in dp]
        minimums = [dp['Minimum'] for dp in datapoints if 'Minimum' in dp]

        if not averages:
            return self._empty_metrics()

        # Calculate statistics
        avg_value = np.mean(averages)
        p95_value = np.percentile(averages, 95)  # 95th percentile as peak
        max_value = max(maximums) if maximums else max(averages)
        min_value = min(minimums) if minimums else min(averages)

        return {
            'average': round(avg_value, 2),
            'p95': round(p95_value, 2),
            'max': round(max_value, 2),
            'min': round(min_value, 2),
            'datapoints': len(averages),
            'available': True
        }

    def _empty_metrics(self) -> Dict:
        """Return empty metrics structure"""
        return {
            'average': None,
            'p95': None,
            'max': None,
            'min': None,
            'datapoints': 0,
            'available': False
        }

    def get_aggregated_metrics_for_instances(
        self,
        instance_ids: List[str],
        start_time: datetime,
        end_time: datetime = None
    ) -> Dict:
        """
        Get aggregated metrics across multiple instances (for instance groups).
        Calculates weighted average across all instances.
        """
        if not instance_ids:
            return {
                'instance_count': 0,
                'instances_with_metrics': 0,
                'cpu': self._empty_metrics(),
                'memory': self._empty_metrics(),
                'per_instance': []
            }

        all_cpu_averages = []
        all_cpu_p95 = []
        all_memory_averages = []
        all_memory_p95 = []
        per_instance_metrics = []
        instances_with_metrics = 0

        for instance_id in instance_ids:
            metrics = self.get_instance_metrics(instance_id, start_time, end_time)
            per_instance_metrics.append(metrics)

            if metrics['metrics_available']:
                instances_with_metrics += 1

                if metrics['cpu']['available']:
                    all_cpu_averages.append(metrics['cpu']['average'])
                    all_cpu_p95.append(metrics['cpu']['p95'])

                if metrics['memory']['available']:
                    all_memory_averages.append(metrics['memory']['average'])
                    all_memory_p95.append(metrics['memory']['p95'])

        # Calculate aggregated metrics
        aggregated_cpu = self._aggregate_values(all_cpu_averages, all_cpu_p95)
        aggregated_memory = self._aggregate_values(all_memory_averages, all_memory_p95)

        return {
            'instance_count': len(instance_ids),
            'instances_with_metrics': instances_with_metrics,
            'cpu': aggregated_cpu,
            'memory': aggregated_memory,
            'per_instance': per_instance_metrics
        }

    def _aggregate_values(
        self,
        averages: List[float],
        p95_values: List[float]
    ) -> Dict:
        """Aggregate values across multiple instances"""
        if not averages:
            return self._empty_metrics()

        return {
            'average': round(np.mean(averages), 2),
            'p95': round(np.mean(p95_values), 2) if p95_values else round(np.percentile(averages, 95), 2),
            'max': round(max(averages), 2),
            'min': round(min(averages), 2),
            'datapoints': len(averages),
            'available': True
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
