import time
import random
from typing import List, Tuple
from models import Host, VM

class Simulation:
    def __init__(self, hosts: List[Host], vms: List[VM], migration_threshold: float = 0.8):
        self.hosts = hosts
        self.vms = vms
        self.migration_threshold = migration_threshold  # Host utilization threshold for migration
        self.simulation_time = 0
        self.total_migrations = 0
        self.total_energy = 0

    def run(self, duration: int, interval: int = 1):
        """
        Run the simulation for the specified duration.
        Args:
            duration: Total simulation time in seconds
            interval: Check interval in seconds
        """
        start_time = time.time()
        self.simulation_time = 0

        while self.simulation_time < duration:
            # Update simulation time
            self.simulation_time = time.time() - start_time

            # Check for expired VMs
            self._remove_expired_vms()

            # Check for migration opportunities
            self._check_migrations()

            # Calculate and accumulate energy
            current_energy = sum(host.base_power + (host.max_power - host.base_power) * host.utilization() 
                               for host in self.hosts)
            self.total_energy += current_energy * interval

            # Sleep until next interval
            time.sleep(interval)

    def _remove_expired_vms(self):
        """Remove VMs that have reached their duration."""
        for host in self.hosts:
            expired_vms = [vm for vm in host.vms if vm.is_expired()]
            for vm in expired_vms:
                host.vms.remove(vm)

    def _check_migrations(self):
        """Check for and perform migrations based on host utilization."""
        # Find overloaded hosts
        overloaded_hosts = [host for host in self.hosts 
                          if host.utilization() > self.migration_threshold]
        
        # Find underloaded hosts
        underloaded_hosts = [host for host in self.hosts 
                           if host.utilization() < self.migration_threshold * 0.5]

        for source_host in overloaded_hosts:
            if not underloaded_hosts:
                break

            # Try to migrate VMs to underloaded hosts
            for vm in source_host.vms[:]:  # Copy list to avoid modification during iteration
                if vm.migration_count >= 3:  # Limit migrations per VM
                    continue

                for target_host in underloaded_hosts:
                    if (target_host.available_cpu() >= vm.cpu and 
                        target_host.available_ram() >= vm.ram):
                        if source_host.migrate_vm(vm, target_host):
                            vm.migration_count += 1
                            self.total_migrations += 1
                            break

    def get_statistics(self) -> dict:
        """Get simulation statistics."""
        return {
            'simulation_time': self.simulation_time,
            'total_migrations': self.total_migrations,
            'total_energy': self.total_energy,
            'average_energy': self.total_energy / self.simulation_time if self.simulation_time > 0 else 0,
            'host_utilizations': {host.host_id: host.utilization() for host in self.hosts},
            'active_vms': sum(len(host.vms) for host in self.hosts)
        } 