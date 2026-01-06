"""
EMR Service for cluster operations
"""
import re
import boto3
from datetime import datetime, timezone
from typing import List, Dict, Optional
import config


class EMRService:
    """Service for EMR cluster operations"""

    def __init__(self):
        session_kwargs = {'region_name': config.AWS_REGION}
        if config.AWS_PROFILE:
            session_kwargs['profile_name'] = config.AWS_PROFILE

        self.session = boto3.Session(**session_kwargs)
        self.emr_client = self.session.client('emr')
        self.ec2_client = self.session.client('ec2')

        # Compile transient cluster pattern
        self.transient_pattern = re.compile(config.TRANSIENT_CLUSTER_PATTERN)

    def list_running_clusters(self) -> List[Dict]:
        """List all running EMR clusters with classification"""
        clusters = []
        paginator = self.emr_client.get_paginator('list_clusters')

        for page in paginator.paginate(ClusterStates=['RUNNING', 'WAITING']):
            for cluster in page['Clusters']:
                cluster_info = self._get_cluster_details(cluster['Id'])
                if cluster_info:
                    clusters.append(cluster_info)

        return clusters

    def _get_cluster_details(self, cluster_id: str) -> Optional[Dict]:
        """Get detailed information about a cluster"""
        try:
            response = self.emr_client.describe_cluster(ClusterId=cluster_id)
            cluster = response['Cluster']

            # Calculate runtime
            created_time = cluster['Status']['Timeline'].get('CreationDateTime')
            runtime_hours = self._calculate_runtime_hours(created_time)

            # Classify cluster
            cluster_type = self._classify_cluster(cluster['Name'], runtime_hours)

            # Get instance groups
            instance_groups = self._get_instance_groups(cluster_id)

            return {
                'id': cluster_id,
                'name': cluster['Name'],
                'state': cluster['Status']['State'],
                'created_time': created_time.isoformat() if created_time else None,
                'runtime_hours': runtime_hours,
                'cluster_type': cluster_type,
                'instance_groups': instance_groups,
                'normalized_instance_hours': cluster.get('NormalizedInstanceHours', 0),
                'release_label': cluster.get('ReleaseLabel', 'Unknown'),
                'applications': [app['Name'] for app in cluster.get('Applications', [])],
                'tags': {tag['Key']: tag['Value'] for tag in cluster.get('Tags', [])}
            }
        except Exception as e:
            print(f"Error getting cluster details for {cluster_id}: {e}")
            return None

    def _calculate_runtime_hours(self, created_time: datetime) -> float:
        """Calculate how long the cluster has been running"""
        if not created_time:
            return 0

        now = datetime.now(timezone.utc)
        if created_time.tzinfo is None:
            created_time = created_time.replace(tzinfo=timezone.utc)

        delta = now - created_time
        return round(delta.total_seconds() / 3600, 2)

    def _classify_cluster(self, cluster_name: str, runtime_hours: float) -> str:
        """
        Classify cluster as TRANSIENT or LONG_RUNNING

        Rules:
        1. If name matches pattern STRESS-XXXXXX-{S,L,XL} -> TRANSIENT
        2. If runtime > LONG_RUNNING_THRESHOLD_HOURS -> LONG_RUNNING
        3. Default to TRANSIENT for shorter-running clusters
        """
        # Check name pattern first
        if self.transient_pattern.match(cluster_name):
            return 'TRANSIENT'

        # Check runtime
        if runtime_hours > config.LONG_RUNNING_THRESHOLD_HOURS:
            return 'LONG_RUNNING'

        # Default to transient for shorter-running clusters
        return 'TRANSIENT'

    def _get_instance_groups(self, cluster_id: str) -> List[Dict]:
        """Get instance groups for a cluster"""
        instance_groups = []

        try:
            response = self.emr_client.list_instance_groups(ClusterId=cluster_id)

            for group in response['InstanceGroups']:
                # Get EC2 instance IDs for this group
                ec2_instances = self._get_ec2_instances_for_group(cluster_id, group['Id'])

                instance_groups.append({
                    'id': group['Id'],
                    'name': group.get('Name', group['InstanceGroupType']),
                    'type': group['InstanceGroupType'],  # MASTER, CORE, TASK
                    'instance_type': group['InstanceType'],
                    'requested_count': group.get('RequestedInstanceCount', 0),
                    'running_count': group.get('RunningInstanceCount', 0),
                    'market': group.get('Market', 'ON_DEMAND'),
                    'state': group['Status']['State'],
                    'ec2_instances': ec2_instances
                })
        except Exception as e:
            print(f"Error getting instance groups for {cluster_id}: {e}")

        return instance_groups

    def _get_ec2_instances_for_group(self, cluster_id: str, instance_group_id: str) -> List[str]:
        """Get EC2 instance IDs for an instance group"""
        ec2_instances = []

        try:
            paginator = self.emr_client.get_paginator('list_instances')
            for page in paginator.paginate(
                ClusterId=cluster_id,
                InstanceGroupId=instance_group_id,
                InstanceStates=['RUNNING']
            ):
                for instance in page['Instances']:
                    if 'Ec2InstanceId' in instance:
                        ec2_instances.append(instance['Ec2InstanceId'])
        except Exception as e:
            print(f"Error getting EC2 instances for group {instance_group_id}: {e}")

        return ec2_instances

    def get_cluster_by_id(self, cluster_id: str) -> Optional[Dict]:
        """Get a specific cluster by ID"""
        return self._get_cluster_details(cluster_id)

    def get_instance_group_ec2_details(self, ec2_instance_ids: List[str]) -> List[Dict]:
        """Get EC2 instance details for monitoring"""
        if not ec2_instance_ids:
            return []

        ec2_details = []
        try:
            response = self.ec2_client.describe_instances(InstanceIds=ec2_instance_ids)
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    ec2_details.append({
                        'instance_id': instance['InstanceId'],
                        'instance_type': instance['InstanceType'],
                        'launch_time': instance['LaunchTime'].isoformat(),
                        'private_ip': instance.get('PrivateIpAddress'),
                        'state': instance['State']['Name']
                    })
        except Exception as e:
            print(f"Error getting EC2 details: {e}")

        return ec2_details
