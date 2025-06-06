import time

class Host:
    def __init__(self, host_id, total_cpu, total_ram, base_power, max_power):
        self.host_id = host_id
        self.total_cpu = total_cpu
        self.total_ram = total_ram
        self.base_power = base_power      # idle power consumption (Watts)
        self.max_power = max_power        # max power consumption at full load
        self.vms = []                    # list of assigned VMs
        self.migration_history = []       # list of migrations performed

    def available_cpu(self):
        used_cpu = sum(vm.cpu for vm in self.vms)
        return self.total_cpu - used_cpu

    def available_ram(self):
        used_ram = sum(vm.ram for vm in self.vms)
        return self.total_ram - used_ram

    def utilization(self):
        used_cpu = sum(vm.cpu for vm in self.vms)
        return used_cpu / self.total_cpu if self.total_cpu else 0

    def migrate_vm(self, vm, target_host):
        """Migrate a VM from this host to the target host."""
        if vm in self.vms:
            self.vms.remove(vm)
            target_host.vms.append(vm)
            migration = {
                'vm_id': vm.vm_id,
                'source_host': self.host_id,
                'target_host': target_host.host_id,
                'timestamp': time.time()
            }
            self.migration_history.append(migration)
            target_host.migration_history.append(migration)
            return True
        return False


class VM:
    def __init__(self, vm_id, cpu, ram, duration=None):
        self.vm_id = vm_id
        self.cpu = cpu
        self.ram = ram
        self.duration = duration          # VM lifetime in seconds (None for infinite)
        self.start_time = time.time()     # When the VM was created
        self.migration_count = 0          # Number of times this VM has been migrated

    def is_expired(self):
        """Check if the VM has reached its duration."""
        if self.duration is None:
            return False
        return (time.time() - self.start_time) >= self.duration

    def remaining_time(self):
        """Get remaining time in seconds."""
        if self.duration is None:
            return float('inf')
        return max(0, self.duration - (time.time() - self.start_time)) 