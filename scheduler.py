import random

def best_fit_decreasing(vms, hosts):
    """
    Assign VMs to hosts using Best-Fit Decreasing on CPU.
    Sort VMs by CPU descending.
    Place each VM into the host with least leftover CPU after placement.
    """
    # Sort VMs descending by CPU
    vms = sorted(vms, key=lambda vm: vm.cpu, reverse=True)
    
    for vm in vms:
        best_host = None
        min_leftover = None
        
        for host in hosts:
            if host.available_cpu() >= vm.cpu and host.available_ram() >= vm.ram:
                leftover = host.available_cpu() - vm.cpu
                if (min_leftover is None) or (leftover < min_leftover):
                    min_leftover = leftover
                    best_host = host
        
        if best_host:
            best_host.vms.append(vm)
        else:
            print(f"VM {vm.vm_id} could not be allocated.")

def random_scheduler(vms, hosts):
    """
    Randomly assign VMs to hosts that have sufficient resources.
    """
    # Shuffle VMs to randomize the order
    random.shuffle(vms)
    
    for vm in vms:
        # Get all hosts that can accommodate the VM
        available_hosts = [host for host in hosts 
                         if host.available_cpu() >= vm.cpu 
                         and host.available_ram() >= vm.ram]
        
        if available_hosts:
            # Randomly select one of the available hosts
            selected_host = random.choice(available_hosts)
            selected_host.vms.append(vm)
        else:
            print(f"VM {vm.vm_id} could not be allocated.")

def minimum_utilization_scheduler(vms, hosts):
    """
    Assign VMs to hosts with the lowest current utilization.
    This helps balance the load across hosts.
    """
    for vm in vms:
        # Find all hosts that can accommodate the VM
        available_hosts = [host for host in hosts 
                         if host.available_cpu() >= vm.cpu 
                         and host.available_ram() >= vm.ram]
        
        if available_hosts:
            # Select the host with minimum utilization
            selected_host = min(available_hosts, key=lambda h: h.utilization())
            selected_host.vms.append(vm)
        else:
            print(f"VM {vm.vm_id} could not be allocated.") 