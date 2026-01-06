"""
Static pricing data for EC2 instances in us-east-1 (On-Demand)
Prices are in USD per hour
"""

# Instance specifications and pricing for us-east-1
# Format: instance_type: {vcpus, memory_gb, price_per_hour, family, generation}
INSTANCE_DATA = {
    # General Purpose - M5 Family
    'm5.large': {'vcpus': 2, 'memory_gb': 8, 'price': 0.096, 'family': 'm5', 'generation': 5, 'category': 'general'},
    'm5.xlarge': {'vcpus': 4, 'memory_gb': 16, 'price': 0.192, 'family': 'm5', 'generation': 5, 'category': 'general'},
    'm5.2xlarge': {'vcpus': 8, 'memory_gb': 32, 'price': 0.384, 'family': 'm5', 'generation': 5, 'category': 'general'},
    'm5.4xlarge': {'vcpus': 16, 'memory_gb': 64, 'price': 0.768, 'family': 'm5', 'generation': 5, 'category': 'general'},
    'm5.8xlarge': {'vcpus': 32, 'memory_gb': 128, 'price': 1.536, 'family': 'm5', 'generation': 5, 'category': 'general'},
    'm5.12xlarge': {'vcpus': 48, 'memory_gb': 192, 'price': 2.304, 'family': 'm5', 'generation': 5, 'category': 'general'},
    'm5.16xlarge': {'vcpus': 64, 'memory_gb': 256, 'price': 3.072, 'family': 'm5', 'generation': 5, 'category': 'general'},
    'm5.24xlarge': {'vcpus': 96, 'memory_gb': 384, 'price': 4.608, 'family': 'm5', 'generation': 5, 'category': 'general'},

    # General Purpose - M5a Family (AMD)
    'm5a.large': {'vcpus': 2, 'memory_gb': 8, 'price': 0.086, 'family': 'm5a', 'generation': 5, 'category': 'general'},
    'm5a.xlarge': {'vcpus': 4, 'memory_gb': 16, 'price': 0.172, 'family': 'm5a', 'generation': 5, 'category': 'general'},
    'm5a.2xlarge': {'vcpus': 8, 'memory_gb': 32, 'price': 0.344, 'family': 'm5a', 'generation': 5, 'category': 'general'},
    'm5a.4xlarge': {'vcpus': 16, 'memory_gb': 64, 'price': 0.688, 'family': 'm5a', 'generation': 5, 'category': 'general'},
    'm5a.8xlarge': {'vcpus': 32, 'memory_gb': 128, 'price': 1.376, 'family': 'm5a', 'generation': 5, 'category': 'general'},
    'm5a.12xlarge': {'vcpus': 48, 'memory_gb': 192, 'price': 2.064, 'family': 'm5a', 'generation': 5, 'category': 'general'},
    'm5a.16xlarge': {'vcpus': 64, 'memory_gb': 256, 'price': 2.752, 'family': 'm5a', 'generation': 5, 'category': 'general'},
    'm5a.24xlarge': {'vcpus': 96, 'memory_gb': 384, 'price': 4.128, 'family': 'm5a', 'generation': 5, 'category': 'general'},

    # General Purpose - M6i Family
    'm6i.large': {'vcpus': 2, 'memory_gb': 8, 'price': 0.096, 'family': 'm6i', 'generation': 6, 'category': 'general'},
    'm6i.xlarge': {'vcpus': 4, 'memory_gb': 16, 'price': 0.192, 'family': 'm6i', 'generation': 6, 'category': 'general'},
    'm6i.2xlarge': {'vcpus': 8, 'memory_gb': 32, 'price': 0.384, 'family': 'm6i', 'generation': 6, 'category': 'general'},
    'm6i.4xlarge': {'vcpus': 16, 'memory_gb': 64, 'price': 0.768, 'family': 'm6i', 'generation': 6, 'category': 'general'},
    'm6i.8xlarge': {'vcpus': 32, 'memory_gb': 128, 'price': 1.536, 'family': 'm6i', 'generation': 6, 'category': 'general'},
    'm6i.12xlarge': {'vcpus': 48, 'memory_gb': 192, 'price': 2.304, 'family': 'm6i', 'generation': 6, 'category': 'general'},
    'm6i.16xlarge': {'vcpus': 64, 'memory_gb': 256, 'price': 3.072, 'family': 'm6i', 'generation': 6, 'category': 'general'},
    'm6i.24xlarge': {'vcpus': 96, 'memory_gb': 384, 'price': 4.608, 'family': 'm6i', 'generation': 6, 'category': 'general'},

    # General Purpose - M7i Family
    'm7i.large': {'vcpus': 2, 'memory_gb': 8, 'price': 0.1008, 'family': 'm7i', 'generation': 7, 'category': 'general'},
    'm7i.xlarge': {'vcpus': 4, 'memory_gb': 16, 'price': 0.2016, 'family': 'm7i', 'generation': 7, 'category': 'general'},
    'm7i.2xlarge': {'vcpus': 8, 'memory_gb': 32, 'price': 0.4032, 'family': 'm7i', 'generation': 7, 'category': 'general'},
    'm7i.4xlarge': {'vcpus': 16, 'memory_gb': 64, 'price': 0.8064, 'family': 'm7i', 'generation': 7, 'category': 'general'},
    'm7i.8xlarge': {'vcpus': 32, 'memory_gb': 128, 'price': 1.6128, 'family': 'm7i', 'generation': 7, 'category': 'general'},
    'm7i.12xlarge': {'vcpus': 48, 'memory_gb': 192, 'price': 2.4192, 'family': 'm7i', 'generation': 7, 'category': 'general'},
    'm7i.16xlarge': {'vcpus': 64, 'memory_gb': 256, 'price': 3.2256, 'family': 'm7i', 'generation': 7, 'category': 'general'},
    'm7i.24xlarge': {'vcpus': 96, 'memory_gb': 384, 'price': 4.8384, 'family': 'm7i', 'generation': 7, 'category': 'general'},

    # Compute Optimized - C5 Family
    'c5.large': {'vcpus': 2, 'memory_gb': 4, 'price': 0.085, 'family': 'c5', 'generation': 5, 'category': 'compute'},
    'c5.xlarge': {'vcpus': 4, 'memory_gb': 8, 'price': 0.17, 'family': 'c5', 'generation': 5, 'category': 'compute'},
    'c5.2xlarge': {'vcpus': 8, 'memory_gb': 16, 'price': 0.34, 'family': 'c5', 'generation': 5, 'category': 'compute'},
    'c5.4xlarge': {'vcpus': 16, 'memory_gb': 32, 'price': 0.68, 'family': 'c5', 'generation': 5, 'category': 'compute'},
    'c5.9xlarge': {'vcpus': 36, 'memory_gb': 72, 'price': 1.53, 'family': 'c5', 'generation': 5, 'category': 'compute'},
    'c5.12xlarge': {'vcpus': 48, 'memory_gb': 96, 'price': 2.04, 'family': 'c5', 'generation': 5, 'category': 'compute'},
    'c5.18xlarge': {'vcpus': 72, 'memory_gb': 144, 'price': 3.06, 'family': 'c5', 'generation': 5, 'category': 'compute'},
    'c5.24xlarge': {'vcpus': 96, 'memory_gb': 192, 'price': 4.08, 'family': 'c5', 'generation': 5, 'category': 'compute'},

    # Compute Optimized - C5a Family (AMD)
    'c5a.large': {'vcpus': 2, 'memory_gb': 4, 'price': 0.077, 'family': 'c5a', 'generation': 5, 'category': 'compute'},
    'c5a.xlarge': {'vcpus': 4, 'memory_gb': 8, 'price': 0.154, 'family': 'c5a', 'generation': 5, 'category': 'compute'},
    'c5a.2xlarge': {'vcpus': 8, 'memory_gb': 16, 'price': 0.308, 'family': 'c5a', 'generation': 5, 'category': 'compute'},
    'c5a.4xlarge': {'vcpus': 16, 'memory_gb': 32, 'price': 0.616, 'family': 'c5a', 'generation': 5, 'category': 'compute'},
    'c5a.8xlarge': {'vcpus': 32, 'memory_gb': 64, 'price': 1.232, 'family': 'c5a', 'generation': 5, 'category': 'compute'},
    'c5a.12xlarge': {'vcpus': 48, 'memory_gb': 96, 'price': 1.848, 'family': 'c5a', 'generation': 5, 'category': 'compute'},
    'c5a.16xlarge': {'vcpus': 64, 'memory_gb': 128, 'price': 2.464, 'family': 'c5a', 'generation': 5, 'category': 'compute'},
    'c5a.24xlarge': {'vcpus': 96, 'memory_gb': 192, 'price': 3.696, 'family': 'c5a', 'generation': 5, 'category': 'compute'},

    # Compute Optimized - C6i Family
    'c6i.large': {'vcpus': 2, 'memory_gb': 4, 'price': 0.085, 'family': 'c6i', 'generation': 6, 'category': 'compute'},
    'c6i.xlarge': {'vcpus': 4, 'memory_gb': 8, 'price': 0.17, 'family': 'c6i', 'generation': 6, 'category': 'compute'},
    'c6i.2xlarge': {'vcpus': 8, 'memory_gb': 16, 'price': 0.34, 'family': 'c6i', 'generation': 6, 'category': 'compute'},
    'c6i.4xlarge': {'vcpus': 16, 'memory_gb': 32, 'price': 0.68, 'family': 'c6i', 'generation': 6, 'category': 'compute'},
    'c6i.8xlarge': {'vcpus': 32, 'memory_gb': 64, 'price': 1.36, 'family': 'c6i', 'generation': 6, 'category': 'compute'},
    'c6i.12xlarge': {'vcpus': 48, 'memory_gb': 96, 'price': 2.04, 'family': 'c6i', 'generation': 6, 'category': 'compute'},
    'c6i.16xlarge': {'vcpus': 64, 'memory_gb': 128, 'price': 2.72, 'family': 'c6i', 'generation': 6, 'category': 'compute'},
    'c6i.24xlarge': {'vcpus': 96, 'memory_gb': 192, 'price': 4.08, 'family': 'c6i', 'generation': 6, 'category': 'compute'},

    # Compute Optimized - C7i Family
    'c7i.large': {'vcpus': 2, 'memory_gb': 4, 'price': 0.0893, 'family': 'c7i', 'generation': 7, 'category': 'compute'},
    'c7i.xlarge': {'vcpus': 4, 'memory_gb': 8, 'price': 0.1785, 'family': 'c7i', 'generation': 7, 'category': 'compute'},
    'c7i.2xlarge': {'vcpus': 8, 'memory_gb': 16, 'price': 0.357, 'family': 'c7i', 'generation': 7, 'category': 'compute'},
    'c7i.4xlarge': {'vcpus': 16, 'memory_gb': 32, 'price': 0.714, 'family': 'c7i', 'generation': 7, 'category': 'compute'},
    'c7i.8xlarge': {'vcpus': 32, 'memory_gb': 64, 'price': 1.428, 'family': 'c7i', 'generation': 7, 'category': 'compute'},
    'c7i.12xlarge': {'vcpus': 48, 'memory_gb': 96, 'price': 2.142, 'family': 'c7i', 'generation': 7, 'category': 'compute'},
    'c7i.16xlarge': {'vcpus': 64, 'memory_gb': 128, 'price': 2.856, 'family': 'c7i', 'generation': 7, 'category': 'compute'},
    'c7i.24xlarge': {'vcpus': 96, 'memory_gb': 192, 'price': 4.284, 'family': 'c7i', 'generation': 7, 'category': 'compute'},

    # Memory Optimized - R5 Family
    'r5.large': {'vcpus': 2, 'memory_gb': 16, 'price': 0.126, 'family': 'r5', 'generation': 5, 'category': 'memory'},
    'r5.xlarge': {'vcpus': 4, 'memory_gb': 32, 'price': 0.252, 'family': 'r5', 'generation': 5, 'category': 'memory'},
    'r5.2xlarge': {'vcpus': 8, 'memory_gb': 64, 'price': 0.504, 'family': 'r5', 'generation': 5, 'category': 'memory'},
    'r5.4xlarge': {'vcpus': 16, 'memory_gb': 128, 'price': 1.008, 'family': 'r5', 'generation': 5, 'category': 'memory'},
    'r5.8xlarge': {'vcpus': 32, 'memory_gb': 256, 'price': 2.016, 'family': 'r5', 'generation': 5, 'category': 'memory'},
    'r5.12xlarge': {'vcpus': 48, 'memory_gb': 384, 'price': 3.024, 'family': 'r5', 'generation': 5, 'category': 'memory'},
    'r5.16xlarge': {'vcpus': 64, 'memory_gb': 512, 'price': 4.032, 'family': 'r5', 'generation': 5, 'category': 'memory'},
    'r5.24xlarge': {'vcpus': 96, 'memory_gb': 768, 'price': 6.048, 'family': 'r5', 'generation': 5, 'category': 'memory'},

    # Memory Optimized - R5a Family (AMD)
    'r5a.large': {'vcpus': 2, 'memory_gb': 16, 'price': 0.113, 'family': 'r5a', 'generation': 5, 'category': 'memory'},
    'r5a.xlarge': {'vcpus': 4, 'memory_gb': 32, 'price': 0.226, 'family': 'r5a', 'generation': 5, 'category': 'memory'},
    'r5a.2xlarge': {'vcpus': 8, 'memory_gb': 64, 'price': 0.452, 'family': 'r5a', 'generation': 5, 'category': 'memory'},
    'r5a.4xlarge': {'vcpus': 16, 'memory_gb': 128, 'price': 0.904, 'family': 'r5a', 'generation': 5, 'category': 'memory'},
    'r5a.8xlarge': {'vcpus': 32, 'memory_gb': 256, 'price': 1.808, 'family': 'r5a', 'generation': 5, 'category': 'memory'},
    'r5a.12xlarge': {'vcpus': 48, 'memory_gb': 384, 'price': 2.712, 'family': 'r5a', 'generation': 5, 'category': 'memory'},
    'r5a.16xlarge': {'vcpus': 64, 'memory_gb': 512, 'price': 3.616, 'family': 'r5a', 'generation': 5, 'category': 'memory'},
    'r5a.24xlarge': {'vcpus': 96, 'memory_gb': 768, 'price': 5.424, 'family': 'r5a', 'generation': 5, 'category': 'memory'},

    # Memory Optimized - R6i Family
    'r6i.large': {'vcpus': 2, 'memory_gb': 16, 'price': 0.126, 'family': 'r6i', 'generation': 6, 'category': 'memory'},
    'r6i.xlarge': {'vcpus': 4, 'memory_gb': 32, 'price': 0.252, 'family': 'r6i', 'generation': 6, 'category': 'memory'},
    'r6i.2xlarge': {'vcpus': 8, 'memory_gb': 64, 'price': 0.504, 'family': 'r6i', 'generation': 6, 'category': 'memory'},
    'r6i.4xlarge': {'vcpus': 16, 'memory_gb': 128, 'price': 1.008, 'family': 'r6i', 'generation': 6, 'category': 'memory'},
    'r6i.8xlarge': {'vcpus': 32, 'memory_gb': 256, 'price': 2.016, 'family': 'r6i', 'generation': 6, 'category': 'memory'},
    'r6i.12xlarge': {'vcpus': 48, 'memory_gb': 384, 'price': 3.024, 'family': 'r6i', 'generation': 6, 'category': 'memory'},
    'r6i.16xlarge': {'vcpus': 64, 'memory_gb': 512, 'price': 4.032, 'family': 'r6i', 'generation': 6, 'category': 'memory'},
    'r6i.24xlarge': {'vcpus': 96, 'memory_gb': 768, 'price': 6.048, 'family': 'r6i', 'generation': 6, 'category': 'memory'},

    # Memory Optimized - R7i Family
    'r7i.large': {'vcpus': 2, 'memory_gb': 16, 'price': 0.1323, 'family': 'r7i', 'generation': 7, 'category': 'memory'},
    'r7i.xlarge': {'vcpus': 4, 'memory_gb': 32, 'price': 0.2646, 'family': 'r7i', 'generation': 7, 'category': 'memory'},
    'r7i.2xlarge': {'vcpus': 8, 'memory_gb': 64, 'price': 0.5292, 'family': 'r7i', 'generation': 7, 'category': 'memory'},
    'r7i.4xlarge': {'vcpus': 16, 'memory_gb': 128, 'price': 1.0584, 'family': 'r7i', 'generation': 7, 'category': 'memory'},
    'r7i.8xlarge': {'vcpus': 32, 'memory_gb': 256, 'price': 2.1168, 'family': 'r7i', 'generation': 7, 'category': 'memory'},
    'r7i.12xlarge': {'vcpus': 48, 'memory_gb': 384, 'price': 3.1752, 'family': 'r7i', 'generation': 7, 'category': 'memory'},
    'r7i.16xlarge': {'vcpus': 64, 'memory_gb': 512, 'price': 4.2336, 'family': 'r7i', 'generation': 7, 'category': 'memory'},
    'r7i.24xlarge': {'vcpus': 96, 'memory_gb': 768, 'price': 6.3504, 'family': 'r7i', 'generation': 7, 'category': 'memory'},

    # Storage Optimized - I3 Family
    'i3.large': {'vcpus': 2, 'memory_gb': 15.25, 'price': 0.156, 'family': 'i3', 'generation': 3, 'category': 'storage'},
    'i3.xlarge': {'vcpus': 4, 'memory_gb': 30.5, 'price': 0.312, 'family': 'i3', 'generation': 3, 'category': 'storage'},
    'i3.2xlarge': {'vcpus': 8, 'memory_gb': 61, 'price': 0.624, 'family': 'i3', 'generation': 3, 'category': 'storage'},
    'i3.4xlarge': {'vcpus': 16, 'memory_gb': 122, 'price': 1.248, 'family': 'i3', 'generation': 3, 'category': 'storage'},
    'i3.8xlarge': {'vcpus': 32, 'memory_gb': 244, 'price': 2.496, 'family': 'i3', 'generation': 3, 'category': 'storage'},
    'i3.16xlarge': {'vcpus': 64, 'memory_gb': 488, 'price': 4.992, 'family': 'i3', 'generation': 3, 'category': 'storage'},

    # Storage Optimized - D2 Family
    'd2.xlarge': {'vcpus': 4, 'memory_gb': 30.5, 'price': 0.69, 'family': 'd2', 'generation': 2, 'category': 'storage'},
    'd2.2xlarge': {'vcpus': 8, 'memory_gb': 61, 'price': 1.38, 'family': 'd2', 'generation': 2, 'category': 'storage'},
    'd2.4xlarge': {'vcpus': 16, 'memory_gb': 122, 'price': 2.76, 'family': 'd2', 'generation': 2, 'category': 'storage'},
    'd2.8xlarge': {'vcpus': 36, 'memory_gb': 244, 'price': 5.52, 'family': 'd2', 'generation': 2, 'category': 'storage'},
}


class PricingService:
    """Service for EC2 instance pricing and specifications"""

    def __init__(self):
        self.instance_data = INSTANCE_DATA

    def get_instance_specs(self, instance_type: str) -> dict:
        """Get specifications for an instance type"""
        return self.instance_data.get(instance_type, None)

    def get_instance_price(self, instance_type: str) -> float:
        """Get hourly price for an instance type"""
        specs = self.get_instance_specs(instance_type)
        return specs['price'] if specs else None

    def get_instances_by_family(self, family: str) -> list:
        """Get all instances in a family, sorted by price"""
        instances = [
            {'type': k, **v}
            for k, v in self.instance_data.items()
            if v['family'] == family
        ]
        return sorted(instances, key=lambda x: x['price'])

    def get_instances_by_category(self, category: str) -> list:
        """Get all instances in a category (general, compute, memory, storage)"""
        instances = [
            {'type': k, **v}
            for k, v in self.instance_data.items()
            if v['category'] == category
        ]
        return sorted(instances, key=lambda x: x['price'])

    def find_suitable_instances(
        self,
        required_vcpus: float,
        required_memory_gb: float,
        current_instance_type: str = None,
        category_preference: str = None
    ) -> dict:
        """
        Find suitable instances that meet the requirements.
        Returns both same-family and cross-family recommendations.
        """
        current_specs = self.get_instance_specs(current_instance_type) if current_instance_type else None
        current_family = current_specs['family'] if current_specs else None

        suitable = []
        for instance_type, specs in self.instance_data.items():
            if specs['vcpus'] >= required_vcpus and specs['memory_gb'] >= required_memory_gb:
                suitable.append({'type': instance_type, **specs})

        # Sort by price
        suitable = sorted(suitable, key=lambda x: x['price'])

        result = {
            'same_family': None,
            'cross_family': None,
            'category_optimized': None
        }

        # Find best in same family
        if current_family:
            same_family = [i for i in suitable if i['family'] == current_family]
            if same_family:
                result['same_family'] = same_family[0]

        # Find best cross-family (cheapest overall)
        if suitable:
            result['cross_family'] = suitable[0]

        # Find best in preferred category
        if category_preference:
            category_instances = [i for i in suitable if i['category'] == category_preference]
            if category_instances:
                result['category_optimized'] = category_instances[0]

        return result

    def calculate_savings(
        self,
        current_instance_type: str,
        recommended_instance_type: str,
        instance_count: int = 1,
        hours_per_month: float = 730  # Average hours in a month
    ) -> dict:
        """Calculate potential savings between current and recommended instance"""
        current_price = self.get_instance_price(current_instance_type)
        recommended_price = self.get_instance_price(recommended_instance_type)

        if not current_price or not recommended_price:
            return None

        hourly_savings = (current_price - recommended_price) * instance_count
        monthly_savings = hourly_savings * hours_per_month
        yearly_savings = monthly_savings * 12
        savings_percent = ((current_price - recommended_price) / current_price) * 100

        return {
            'hourly_savings': round(hourly_savings, 4),
            'monthly_savings': round(monthly_savings, 2),
            'yearly_savings': round(yearly_savings, 2),
            'savings_percent': round(savings_percent, 1),
            'current_hourly_cost': round(current_price * instance_count, 4),
            'recommended_hourly_cost': round(recommended_price * instance_count, 4)
        }

    def get_all_families(self) -> list:
        """Get list of all instance families"""
        return list(set(v['family'] for v in self.instance_data.values()))

    def get_all_categories(self) -> list:
        """Get list of all instance categories"""
        return list(set(v['category'] for v in self.instance_data.values()))
