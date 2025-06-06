import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from models import VM
import random

class WorkloadDataset:
    def __init__(self):
        # Default workload patterns based on real-world data
        self.workload_patterns = {
            'web_server': {
                'cpu_range': (1, 4),
                'ram_per_cpu': 2,
                'duration_range': (3600, 86400),  # 1 hour to 24 hours
                'utilization_pattern': 'high_peak'  # High CPU utilization with peaks
            },
            'database': {
                'cpu_range': (2, 8),
                'ram_per_cpu': 4,
                'duration_range': (86400, 604800),  # 1 day to 1 week
                'utilization_pattern': 'steady'  # Steady high utilization
            },
            'batch_job': {
                'cpu_range': (4, 16),
                'ram_per_cpu': 2,
                'duration_range': (1800, 7200),  # 30 minutes to 2 hours
                'utilization_pattern': 'burst'  # Burst of high utilization
            },
            'development': {
                'cpu_range': (1, 2),
                'ram_per_cpu': 2,
                'duration_range': (1800, 28800),  # 30 minutes to 8 hours
                'utilization_pattern': 'low'  # Low to medium utilization
            }
        }

    def load_google_trace(self, file_path: str) -> List[Dict]:
        """
        Load and process Google cluster trace data.
        Format: timestamp, job_id, task_id, machine_id, cpu, memory, etc.
        """
        try:
            df = pd.read_csv(file_path)
            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading Google trace: {e}")
            return []

    def generate_vms_from_pattern(self, pattern: str, count: int) -> List[VM]:
        """Generate VMs based on a specific workload pattern."""
        if pattern not in self.workload_patterns:
            raise ValueError(f"Unknown workload pattern: {pattern}")

        pattern_data = self.workload_patterns[pattern]
        vms = []

        for i in range(count):
            cpu = random.randint(*pattern_data['cpu_range'])
            ram = cpu * pattern_data['ram_per_cpu']
            duration = random.randint(*pattern_data['duration_range'])
            
            vm = VM(
                vm_id=f"{pattern}_{i+1}",
                cpu=cpu,
                ram=ram,
                duration=duration
            )
            vms.append(vm)

        return vms

    def generate_mixed_workload(self, counts: Dict[str, int]) -> List[VM]:
        """Generate a mix of VMs based on different workload patterns."""
        all_vms = []
        for pattern, count in counts.items():
            pattern_vms = self.generate_vms_from_pattern(pattern, count)
            all_vms.extend(pattern_vms)
        return all_vms

    def get_utilization_pattern(self, pattern: str, duration: int) -> List[float]:
        """Generate utilization pattern for a VM based on its type."""
        if pattern == 'high_peak':
            # Web server pattern: high utilization with peaks
            base = np.random.normal(0.7, 0.1, duration)
            peaks = np.random.normal(0.9, 0.05, duration)
            return np.maximum(base, peaks).tolist()
        
        elif pattern == 'steady':
            # Database pattern: steady high utilization
            return np.random.normal(0.8, 0.05, duration).tolist()
        
        elif pattern == 'burst':
            # Batch job pattern: burst of high utilization
            base = np.random.normal(0.3, 0.1, duration)
            bursts = np.random.normal(0.9, 0.05, duration)
            return np.maximum(base, bursts).tolist()
        
        else:  # 'low' pattern
            # Development pattern: low to medium utilization
            return np.random.normal(0.4, 0.1, duration).tolist()

    def get_workload_distribution(self) -> Dict[str, float]:
        """Get typical workload distribution based on real-world data."""
        return {
            'web_server': 0.4,    # 40% web servers
            'database': 0.2,      # 20% databases
            'batch_job': 0.3,     # 30% batch jobs
            'development': 0.1    # 10% development VMs
        } 