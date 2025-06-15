from models import Host

def calculate_energy(host: Host) -> float:
    """
    Linear energy model:
    energy = base_power + (max_power - base_power) * utilization
    """
    utilization = host.utilization()
    energy = host.base_power + (host.max_power - host.base_power) * utilization
    return energy 