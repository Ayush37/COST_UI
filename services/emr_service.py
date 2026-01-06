"""
EMR Service for cluster operations
Supports both Instance Groups and Instance Fleets configurations
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

    def list_recently_terminated_clusters(self, hours: int = 3) -> List[Dict]:
        """
        List EMR clusters that were terminated within the last N hours.
        These can still be analyzed using historical CloudWatch metrics.
        """
        from datetime import timedelta

        clusters = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        paginator = self.emr_client.get_paginator('list_clusters')

        for page in paginator.paginate(ClusterStates=['TERMINATED', 'TERMINATED_WITH_ERRORS']):
            for cluster in page['Clusters']:
                # Check if terminated within the time window
                end_time = cluster.get('Status', {}).get('Timeline', {}).get('EndDateTime')
                if end_time:
                    if end_time.tzinfo is None:
                        end_time = end_time.replace(tzinfo=timezone.utc)
                    if end_time >= cutoff_time:
                        cluster_info = self._get_cluster_details(cluster['Id'], include_terminated=True)
                        if cluster_info:
                            clusters.append(cluster_info)

        return clusters

    def _get_cluster_details(self, cluster_id: str, include_terminated: bool = False) -> Optional[Dict]:
        """Get detailed information about a cluster"""
        try:
            response = self.emr_client.describe_cluster(ClusterId=cluster_id)
            cluster = response['Cluster']

            # Get timeline info
            timeline = cluster['Status']['Timeline']
            created_time = timeline.get('CreationDateTime')
            end_time = timeline.get('EndDateTime')
            cluster_state = cluster['Status']['State']

            # Calculate runtime
            is_terminated = cluster_state in ['TERMINATED', 'TERMINATED_WITH_ERRORS']
            if is_terminated and end_time:
                runtime_hours = self._calculate_runtime_hours_for_terminated(created_time, end_time)
            else:
                runtime_hours = self._calculate_runtime_hours(created_time)

            # Classify cluster
            cluster_type = self._classify_cluster(cluster['Name'], runtime_hours)

            # Determine if cluster uses Instance Fleets or Instance Groups
            instance_collection_type = cluster.get('InstanceCollectionType', 'INSTANCE_GROUP')

            # Get instances based on collection type
            # For terminated clusters, we still get the configuration but won't have running EC2 instances
            if instance_collection_type == 'INSTANCE_FLEET':
                instance_groups = self._get_instance_fleets(cluster_id, include_terminated=is_terminated)
                uses_fleets = True
            else:
                instance_groups = self._get_instance_groups(cluster_id, include_terminated=is_terminated)
                uses_fleets = False

            result = {
                'id': cluster_id,
                'name': cluster['Name'],
                'state': cluster_state,
                'created_time': created_time.isoformat() if created_time else None,
                'end_time': end_time.isoformat() if end_time else None,
                'runtime_hours': runtime_hours,
                'cluster_type': cluster_type,
                'instance_collection_type': instance_collection_type,
                'uses_fleets': uses_fleets,
                'instance_groups': instance_groups,
                'normalized_instance_hours': cluster.get('NormalizedInstanceHours', 0),
                'release_label': cluster.get('ReleaseLabel', 'Unknown'),
                'applications': [app['Name'] for app in cluster.get('Applications', [])],
                'tags': {tag['Key']: tag['Value'] for tag in cluster.get('Tags', [])},
                'is_terminated': is_terminated
            }

            # Add termination reason for terminated clusters
            if is_terminated:
                state_change_reason = cluster['Status'].get('StateChangeReason', {})
                result['termination_reason'] = {
                    'code': state_change_reason.get('Code', 'UNKNOWN'),
                    'message': state_change_reason.get('Message', '')
                }

            return result
        except Exception as e:
            print(f"Error getting cluster details for {cluster_id}: {e}")
            return None

    def _calculate_runtime_hours_for_terminated(self, created_time: datetime, end_time: datetime) -> float:
        """Calculate runtime for a terminated cluster"""
        if not created_time or not end_time:
            return 0

        if created_time.tzinfo is None:
            created_time = created_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        delta = end_time - created_time
        return round(delta.total_seconds() / 3600, 2)

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

    def _get_instance_groups(self, cluster_id: str, include_terminated: bool = False) -> List[Dict]:
        """Get instance groups for a cluster (traditional configuration)"""
        instance_groups = []

        try:
            response = self.emr_client.list_instance_groups(ClusterId=cluster_id)

            for group in response['InstanceGroups']:
                # Get EC2 instance IDs for this group
                # For terminated clusters, get historical instances
                if include_terminated:
                    ec2_instances = self._get_historical_ec2_instances_for_group(cluster_id, group['Id'])
                else:
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
                    'ec2_instances': ec2_instances,
                    'is_fleet': False
                })
        except Exception as e:
            print(f"Error getting instance groups for {cluster_id}: {e}")

        return instance_groups

    def _get_instance_fleets(self, cluster_id: str, include_terminated: bool = False) -> List[Dict]:
        """Get instance fleets for a cluster (fleet configuration)"""
        instance_fleets = []

        try:
            response = self.emr_client.list_instance_fleets(ClusterId=cluster_id)

            for fleet in response['InstanceFleets']:
                # Get EC2 instance IDs for this fleet
                # For terminated clusters, get historical instances
                if include_terminated:
                    ec2_instances, instance_type_counts = self._get_historical_ec2_instances_for_fleet(
                        cluster_id, fleet['Id']
                    )
                else:
                    ec2_instances, instance_type_counts = self._get_ec2_instances_for_fleet(
                        cluster_id, fleet['Id']
                    )

                # Determine the primary instance type (most common in the fleet)
                primary_instance_type = self._get_primary_instance_type(
                    fleet, instance_type_counts
                )

                # Get all instance types configured in the fleet
                instance_type_specs = []
                for spec in fleet.get('InstanceTypeSpecifications', []):
                    instance_type_specs.append({
                        'instance_type': spec['InstanceType'],
                        'weighted_capacity': spec.get('WeightedCapacity', 1),
                        'bid_price': spec.get('BidPrice'),
                        'bid_price_as_percentage': spec.get('BidPriceAsPercentageOfOnDemandPrice')
                    })

                instance_fleets.append({
                    'id': fleet['Id'],
                    'name': fleet.get('Name', fleet['InstanceFleetType']),
                    'type': fleet['InstanceFleetType'],  # MASTER, CORE, TASK
                    'instance_type': primary_instance_type,  # Primary/most common type
                    'instance_type_specs': instance_type_specs,  # All configured types
                    'requested_count': fleet.get('TargetOnDemandCapacity', 0) + fleet.get('TargetSpotCapacity', 0),
                    'running_count': fleet.get('ProvisionedOnDemandCapacity', 0) + fleet.get('ProvisionedSpotCapacity', 0),
                    'target_on_demand': fleet.get('TargetOnDemandCapacity', 0),
                    'target_spot': fleet.get('TargetSpotCapacity', 0),
                    'provisioned_on_demand': fleet.get('ProvisionedOnDemandCapacity', 0),
                    'provisioned_spot': fleet.get('ProvisionedSpotCapacity', 0),
                    'market': 'MIXED' if fleet.get('TargetSpotCapacity', 0) > 0 else 'ON_DEMAND',
                    'state': fleet['Status']['State'],
                    'ec2_instances': ec2_instances,
                    'instance_type_counts': instance_type_counts,  # Count per instance type
                    'is_fleet': True
                })
        except Exception as e:
            print(f"Error getting instance fleets for {cluster_id}: {e}")

        return instance_fleets

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

    def _get_historical_ec2_instances_for_group(self, cluster_id: str, instance_group_id: str) -> List[str]:
        """
        Get EC2 instance IDs for a terminated cluster's instance group.
        Includes terminated instances for historical analysis.
        """
        ec2_instances = []

        try:
            paginator = self.emr_client.get_paginator('list_instances')
            # Include TERMINATED state to get historical instances
            for page in paginator.paginate(
                ClusterId=cluster_id,
                InstanceGroupId=instance_group_id,
                InstanceStates=['RUNNING', 'TERMINATED']
            ):
                for instance in page['Instances']:
                    if 'Ec2InstanceId' in instance:
                        ec2_instances.append(instance['Ec2InstanceId'])
        except Exception as e:
            print(f"Error getting historical EC2 instances for group {instance_group_id}: {e}")

        return ec2_instances

    def _get_ec2_instances_for_fleet(self, cluster_id: str, fleet_id: str) -> tuple:
        """
        Get EC2 instance IDs for an instance fleet.
        Returns tuple of (list of instance IDs, dict of instance type counts)
        """
        ec2_instances = []
        instance_type_counts = {}

        try:
            paginator = self.emr_client.get_paginator('list_instances')
            for page in paginator.paginate(
                ClusterId=cluster_id,
                InstanceFleetId=fleet_id,
                InstanceStates=['RUNNING']
            ):
                for instance in page['Instances']:
                    if 'Ec2InstanceId' in instance:
                        ec2_instances.append(instance['Ec2InstanceId'])

                        # Track instance type counts
                        inst_type = instance.get('InstanceType', 'unknown')
                        instance_type_counts[inst_type] = instance_type_counts.get(inst_type, 0) + 1
        except Exception as e:
            print(f"Error getting EC2 instances for fleet {fleet_id}: {e}")

        return ec2_instances, instance_type_counts

    def _get_historical_ec2_instances_for_fleet(self, cluster_id: str, fleet_id: str) -> tuple:
        """
        Get EC2 instance IDs for a terminated cluster's instance fleet.
        Includes terminated instances for historical analysis.
        Returns tuple of (list of instance IDs, dict of instance type counts)
        """
        ec2_instances = []
        instance_type_counts = {}

        try:
            paginator = self.emr_client.get_paginator('list_instances')
            # Include TERMINATED state to get historical instances
            for page in paginator.paginate(
                ClusterId=cluster_id,
                InstanceFleetId=fleet_id,
                InstanceStates=['RUNNING', 'TERMINATED']
            ):
                for instance in page['Instances']:
                    if 'Ec2InstanceId' in instance:
                        ec2_instances.append(instance['Ec2InstanceId'])

                        # Track instance type counts
                        inst_type = instance.get('InstanceType', 'unknown')
                        instance_type_counts[inst_type] = instance_type_counts.get(inst_type, 0) + 1
        except Exception as e:
            print(f"Error getting historical EC2 instances for fleet {fleet_id}: {e}")

        return ec2_instances, instance_type_counts

    def _get_primary_instance_type(self, fleet: Dict, instance_type_counts: Dict) -> str:
        """
        Determine the primary instance type for a fleet.
        Uses the most common running instance type, or first configured type.
        """
        # If we have running instances, use the most common type
        if instance_type_counts:
            return max(instance_type_counts, key=instance_type_counts.get)

        # Otherwise, use the first instance type from specifications
        specs = fleet.get('InstanceTypeSpecifications', [])
        if specs:
            return specs[0]['InstanceType']

        # Fallback to launch specifications
        launch_specs = fleet.get('LaunchSpecifications', {})
        on_demand_spec = launch_specs.get('OnDemandSpecification', {})
        if on_demand_spec:
            return 'on-demand-fleet'

        return 'unknown'

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
