import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from models import Host, VM
from scheduler import best_fit_decreasing, random_scheduler, minimum_utilization_scheduler
from energy_model import calculate_energy
from simulation import Simulation
from datasets import WorkloadDataset
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time

class EnergySchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WiseCloud - Energy-Efficient VM Scheduler Simulator")
        self.root.geometry("1200x800")  # Set initial window size
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("TNotebook", background="#f0f0f0")
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        
        # Initialize dataset handler
        self.dataset = WorkloadDataset()

        # Create main container
        main_container = ttk.Frame(root, padding="10")
        main_container.pack(fill='both', expand=True)

        # Create notebook for tabs with custom style
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Create tabs
        self.simulation_tab = ttk.Frame(self.notebook)
        self.host_tab = ttk.Frame(self.notebook)
        self.vm_tab = ttk.Frame(self.notebook)
        self.dataset_tab = ttk.Frame(self.notebook)
        self.monitoring_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.simulation_tab, text='Simulation')
        self.notebook.add(self.host_tab, text='Host Configuration')
        self.notebook.add(self.vm_tab, text='VM Configuration')
        self.notebook.add(self.dataset_tab, text='Dataset Configuration')
        self.notebook.add(self.monitoring_tab, text='Monitoring')

        # Setup each tab
        self._setup_simulation_tab()
        self._setup_host_tab()
        self._setup_vm_tab()
        self._setup_dataset_tab()
        self._setup_monitoring_tab()

        # Initialize simulation variables
        self.simulation = None
        self.simulation_thread = None
        self.is_simulation_running = False

    def _setup_simulation_tab(self):
        # Create two frames side by side
        left_frame = ttk.Frame(self.simulation_tab, padding="10")
        left_frame.pack(side='left', fill='both', expand=True)
        
        right_frame = ttk.Frame(self.simulation_tab, padding="10")
        right_frame.pack(side='right', fill='both', expand=True)

        # Input parameters frame
        input_frame = ttk.LabelFrame(left_frame, text="Simulation Parameters", padding="10")
        input_frame.pack(fill='x', padx=5, pady=5)

        # Create a grid of parameters
        params = [
            ("Number of Hosts:", "host_count_var", 3),
            ("Number of VMs:", "vm_count_var", 5),
            ("Simulation Duration (s):", "sim_duration_var", 3600),
            ("Migration Threshold:", "migration_threshold_var", 0.7)
        ]

        for i, (label, var_name, default) in enumerate(params):
            ttk.Label(input_frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            var = tk.IntVar(value=default) if isinstance(default, int) else tk.DoubleVar(value=default)
            setattr(self, var_name, var)
            ttk.Entry(input_frame, textvariable=var).grid(row=i, column=1, padx=5, pady=2)

        # Scheduling policy
        ttk.Label(input_frame, text="Scheduling Policy:").grid(row=len(params), column=0, sticky="w", pady=2)
        self.scheduler_var = tk.StringVar(value="Best-Fit Decreasing")
        scheduler_combo = ttk.Combobox(input_frame, textvariable=self.scheduler_var)
        scheduler_combo['values'] = ('Best-Fit Decreasing', 'Random', 'Minimum Utilization')
        scheduler_combo.grid(row=len(params), column=1, padx=5, pady=2)

        # Run button with custom style
        run_button = ttk.Button(input_frame, text="Run Simulation", command=self.run_simulation)
        run_button.grid(row=len(params)+1, column=0, columnspan=2, pady=10)

        # Status frame - Shows current simulation state
        status_frame = ttk.LabelFrame(left_frame, text="Current Simulation Status", padding="10")
        status_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.status_text = tk.Text(status_frame, width=40, height=15, wrap=tk.WORD)
        self.status_text.pack(fill='both', expand=True)
        self.status_text.insert(tk.END, "Simulation not started. Click 'Run Simulation' to begin.")

        # Results frame - Shows final results after simulation
        results_frame = ttk.LabelFrame(right_frame, text="Final Simulation Results", padding="10")
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.results_text = tk.Text(results_frame, width=40, height=15, wrap=tk.WORD)
        self.results_text.pack(fill='both', expand=True)
        self.results_text.insert(tk.END, "Results will appear here after simulation completes.")

    def _setup_host_tab(self):
        # Host configuration frame
        host_config_frame = ttk.LabelFrame(self.host_tab, text="Host Specifications", padding="10")
        host_config_frame.pack(fill='x', padx=5, pady=5)

        # Create a grid of host parameters
        host_params = [
            ("CPU Cores:", "host_cpu_var", 16),
            ("RAM (GB):", "host_ram_var", 32),
            ("Base Power (W):", "host_base_power_var", 100),
            ("Max Power (W):", "host_max_power_var", 200)
        ]

        for i, (label, var_name, default) in enumerate(host_params):
            ttk.Label(host_config_frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            var = tk.IntVar(value=default)
            setattr(self, var_name, var)
            ttk.Entry(host_config_frame, textvariable=var).grid(row=i, column=1, padx=5, pady=2)

        # Add host visualization
        viz_frame = ttk.LabelFrame(self.host_tab, text="Host Resource Visualization", padding="10")
        viz_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create matplotlib figure for host visualization
        self.host_fig = plt.Figure(figsize=(6, 4))
        self.host_canvas = FigureCanvasTkAgg(self.host_fig, master=viz_frame)
        self.host_canvas.get_tk_widget().pack(fill='both', expand=True)

    def _setup_vm_tab(self):
        # VM configuration frame
        vm_config_frame = ttk.LabelFrame(self.vm_tab, text="VM Generation Parameters", padding="10")
        vm_config_frame.pack(fill='x', padx=5, pady=5)

        # Create a grid of VM parameters
        vm_params = [
            ("Min CPU Cores:", "vm_min_cpu_var", 1),
            ("Max CPU Cores:", "vm_max_cpu_var", 16),
            ("RAM per CPU (GB):", "vm_ram_per_cpu_var", 4),
            ("Min Duration (s):", "vm_min_duration_var", 1800),
            ("Max Duration (s):", "vm_max_duration_var", 86400)
        ]

        for i, (label, var_name, default) in enumerate(vm_params):
            ttk.Label(vm_config_frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            var = tk.IntVar(value=default)
            setattr(self, var_name, var)
            ttk.Entry(vm_config_frame, textvariable=var).grid(row=i, column=1, padx=5, pady=2)

        # Add VM visualization
        viz_frame = ttk.LabelFrame(self.vm_tab, text="VM Resource Distribution", padding="10")
        viz_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create matplotlib figure for VM visualization
        self.vm_fig = plt.Figure(figsize=(6, 4))
        self.vm_canvas = FigureCanvasTkAgg(self.vm_fig, master=viz_frame)
        self.vm_canvas.get_tk_widget().pack(fill='both', expand=True)

    def _setup_dataset_tab(self):
        # Dataset configuration frame
        dataset_config_frame = ttk.LabelFrame(self.dataset_tab, text="Workload Configuration", padding="10")
        dataset_config_frame.pack(fill='x', padx=5, pady=5)

        # Workload type selection
        ttk.Label(dataset_config_frame, text="Workload Type:").grid(row=0, column=0, sticky="w", pady=2)
        self.workload_type_var = tk.StringVar(value="mixed")
        workload_combo = ttk.Combobox(dataset_config_frame, textvariable=self.workload_type_var)
        workload_combo['values'] = ('mixed', 'web_server', 'database', 'batch_job', 'development', 'custom')
        workload_combo.grid(row=0, column=1, padx=5, pady=2)

        # Custom dataset file selection
        ttk.Label(dataset_config_frame, text="Custom Dataset:").grid(row=1, column=0, sticky="w", pady=2)
        self.dataset_path_var = tk.StringVar()
        ttk.Entry(dataset_config_frame, textvariable=self.dataset_path_var, state='readonly').grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(dataset_config_frame, text="Browse", command=self.browse_dataset).grid(row=1, column=2, padx=5, pady=2)

        # Workload distribution
        distribution_frame = ttk.LabelFrame(self.dataset_tab, text="Workload Distribution", padding="10")
        distribution_frame.pack(fill='x', padx=5, pady=5)

        self.workload_vars = {}
        row = 0
        for workload_type, default_percent in self.dataset.get_workload_distribution().items():
            ttk.Label(distribution_frame, text=f"{workload_type.replace('_', ' ').title()}:").grid(row=row, column=0, sticky="w", pady=2)
            var = tk.DoubleVar(value=default_percent * 100)
            self.workload_vars[workload_type] = var
            ttk.Entry(distribution_frame, textvariable=var).grid(row=row, column=1, padx=5, pady=2)
            ttk.Label(distribution_frame, text="%").grid(row=row, column=2, pady=2)
            row += 1

        # Add workload visualization
        viz_frame = ttk.LabelFrame(self.dataset_tab, text="Workload Distribution Visualization", padding="10")
        viz_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create matplotlib figure for workload visualization
        self.workload_fig = plt.Figure(figsize=(6, 4))
        self.workload_canvas = FigureCanvasTkAgg(self.workload_fig, master=viz_frame)
        self.workload_canvas.get_tk_widget().pack(fill='both', expand=True)

    def _setup_monitoring_tab(self):
        # Create frames for different monitoring aspects
        metrics_frame = ttk.LabelFrame(self.monitoring_tab, text="Performance Metrics", padding="10")
        metrics_frame.pack(fill='x', padx=5, pady=5)

        # Add metric labels
        self.metric_vars = {}
        metrics = [
            ("Active VMs:", "active_vms"),
            ("Total Migrations:", "total_migrations"),
            ("Current Energy (W):", "current_energy"),
            ("Average Energy (W):", "average_energy")
        ]

        for i, (label, var_name) in enumerate(metrics):
            ttk.Label(metrics_frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            var = tk.StringVar(value="0")
            self.metric_vars[var_name] = var
            ttk.Label(metrics_frame, textvariable=var).grid(row=i, column=1, sticky="w", pady=2)

        # Add real-time charts
        charts_frame = ttk.LabelFrame(self.monitoring_tab, text="Real-time Monitoring", padding="10")
        charts_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create matplotlib figure for real-time monitoring
        self.monitoring_fig = plt.Figure(figsize=(8, 6))
        self.monitoring_canvas = FigureCanvasTkAgg(self.monitoring_fig, master=charts_frame)
        self.monitoring_canvas.get_tk_widget().pack(fill='both', expand=True)

    def _update_monitoring(self, stats):
        """Update monitoring tab with current statistics."""
        # Update metric labels
        self.metric_vars['active_vms'].set(str(stats['active_vms']))
        self.metric_vars['total_migrations'].set(str(stats['total_migrations']))
        self.metric_vars['current_energy'].set(f"{stats['total_energy']:.2f}")
        self.metric_vars['average_energy'].set(f"{stats['average_energy']:.2f}")

        # Update charts
        self.monitoring_fig.clear()
        
        # Host utilization chart
        ax1 = self.monitoring_fig.add_subplot(211)
        host_ids = list(stats['host_utilizations'].keys())
        utilizations = [u * 100 for u in stats['host_utilizations'].values()]
        ax1.bar(host_ids, utilizations, color='blue')
        ax1.set_title('Host Utilizations')
        ax1.set_ylabel('Utilization (%)')
        ax1.grid(True, axis='y', linestyle='--', alpha=0.7)

        # Energy consumption chart
        ax2 = self.monitoring_fig.add_subplot(212)
        ax2.bar(['Total', 'Average'], 
                [stats['total_energy'], stats['average_energy']], 
                color='green')
        ax2.set_title('Energy Consumption')
        ax2.set_ylabel('Energy (Watts)')
        ax2.grid(True, axis='y', linestyle='--', alpha=0.7)

        self.monitoring_fig.tight_layout()
        self.monitoring_canvas.draw()

    def _update_simulation_status(self):
        """Update the simulation status display."""
        if not self.is_simulation_running:
            # Simulation finished, show final statistics
            stats = self.simulation.get_statistics()
            self._display_statistics(stats)
            return

        # Update current status
        stats = self.simulation.get_statistics()
        
        # Update status text with current state
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert(tk.END, "=== Current Simulation State ===\n\n")
        self.status_text.insert(tk.END, f"Time Elapsed: {stats['simulation_time']:.1f}s\n")
        self.status_text.insert(tk.END, f"Active VMs: {stats['active_vms']}\n")
        self.status_text.insert(tk.END, f"Migrations So Far: {stats['total_migrations']}\n")
        self.status_text.insert(tk.END, f"Current Energy: {stats['total_energy']:.2f} W\n")
        self.status_text.insert(tk.END, f"Average Energy: {stats['average_energy']:.2f} W\n\n")

        self.status_text.insert(tk.END, "Current Host Utilizations:\n")
        for host_id, util in stats['host_utilizations'].items():
            self.status_text.insert(tk.END, f"{host_id}: {util*100:.1f}%\n")

        # Update monitoring tab
        self._update_monitoring(stats)

        # Schedule next update
        self.root.after(1000, self._update_simulation_status)

    def browse_dataset(self):
        """Open file dialog to select a custom dataset file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.dataset_path_var.set(file_path)

    def get_workload_distribution(self) -> dict:
        """Get the current workload distribution from the UI."""
        total = sum(var.get() for var in self.workload_vars.values())
        if total != 100:
            messagebox.showwarning(
                "Warning",
                f"Workload distribution must sum to 100%. Current sum: {total}%"
            )
            return None

        return {
            workload_type: var.get() / 100
            for workload_type, var in self.workload_vars.items()
        }

    def generate_vms(self, count: int) -> list:
        """Generate VMs based on the selected workload type."""
        workload_type = self.workload_type_var.get()

        if workload_type == 'custom':
            # Load from custom dataset
            if not self.dataset_path_var.get():
                messagebox.showerror("Error", "Please select a custom dataset file")
                return []
            data = self.dataset.load_google_trace(self.dataset_path_var.get())
            if not data:
                return []
            # Convert dataset to VMs
            vms = []
            for i, record in enumerate(data[:count]):
                vm = VM(
                    vm_id=f"custom_{i+1}",
                    cpu=record.get('cpu', 1),
                    ram=record.get('memory', 2),
                    duration=record.get('duration', 3600)
                )
                vms.append(vm)
            return vms

        elif workload_type == 'mixed':
            # Use distribution from UI
            distribution = self.get_workload_distribution()
            if not distribution:
                return []
            counts = {
                workload_type: int(percent * count)
                for workload_type, percent in distribution.items()
            }
            return self.dataset.generate_mixed_workload(counts)

        else:
            # Generate single workload type
            return self.dataset.generate_vms_from_pattern(workload_type, count)

    def run_simulation(self):
        if self.is_simulation_running:
            messagebox.showwarning("Warning", "Simulation is already running!")
            return

        # Clear output
        self.results_text.delete("1.0", tk.END)

        num_hosts = self.host_count_var.get()
        num_vms = self.vm_count_var.get()

        # Create Hosts with custom specs
        hosts = []
        for i in range(num_hosts):
            host = Host(
                host_id=f"H{i+1}",
                total_cpu=self.host_cpu_var.get(),
                total_ram=self.host_ram_var.get(),
                base_power=self.host_base_power_var.get(),
                max_power=self.host_max_power_var.get()
            )
            hosts.append(host)

        # Generate VMs based on workload type
        vms = self.generate_vms(num_vms)
        if not vms:
            return

        # Run selected scheduler
        scheduler_name = self.scheduler_var.get()
        if scheduler_name == "Best-Fit Decreasing":
            best_fit_decreasing(vms, hosts)
        elif scheduler_name == "Random":
            random_scheduler(vms, hosts)
        else:  # Minimum Utilization
            minimum_utilization_scheduler(vms, hosts)

        # Create and start simulation
        self.simulation = Simulation(
            hosts=hosts,
            vms=vms,
            migration_threshold=self.migration_threshold_var.get()
        )

        self.is_simulation_running = True
        self.simulation_thread = threading.Thread(
            target=self._run_simulation,
            args=(self.sim_duration_var.get(),)
        )
        self.simulation_thread.start()

        # Start update timer
        self.root.after(1000, self._update_simulation_status)

    def _run_simulation(self, duration):
        """Run the simulation in a separate thread."""
        self.simulation.run(duration)
        self.is_simulation_running = False

    def _display_statistics(self, stats):
        """Display final simulation statistics."""
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "=== Final Simulation Results ===\n\n")
        self.results_text.insert(tk.END, f"Total Duration: {stats['simulation_time']:.1f}s\n")
        self.results_text.insert(tk.END, f"Final Active VMs: {stats['active_vms']}\n")
        self.results_text.insert(tk.END, f"Total Migrations: {stats['total_migrations']}\n")
        self.results_text.insert(tk.END, f"Total Energy: {stats['total_energy']:.2f} W\n")
        self.results_text.insert(tk.END, f"Average Energy: {stats['average_energy']:.2f} W\n\n")

        self.results_text.insert(tk.END, "Final Host Utilizations:\n")
        for host_id, util in stats['host_utilizations'].items():
            self.results_text.insert(tk.END, f"{host_id}: {util*100:.1f}%\n")

        # Plot final energy consumption
        self._plot_final_statistics(stats)

    def _plot_final_statistics(self, stats):
        """Plot final simulation statistics."""
        plt.figure(figsize=(12, 6))
        
        # Plot host utilizations
        plt.subplot(1, 2, 1)
        host_ids = list(stats['host_utilizations'].keys())
        utilizations = [u * 100 for u in stats['host_utilizations'].values()]
        plt.bar(host_ids, utilizations, color='blue')
        plt.title('Final Host Utilizations')
        plt.ylabel('Utilization (%)')
        plt.xlabel('Host')
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)

        # Plot energy consumption
        plt.subplot(1, 2, 2)
        plt.bar(['Total', 'Average'], 
                [stats['total_energy'], stats['average_energy']], 
                color='green')
        plt.title('Energy Consumption')
        plt.ylabel('Energy (Watts)')
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    root = tk.Tk()
    app = EnergySchedulerApp(root)
    root.mainloop() 