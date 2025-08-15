import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from models import Host, VM
from scheduler import best_fit_decreasing, random_scheduler, minimum_utilization_scheduler
from energy_model import calculate_energy
from simulation import Simulation
from datasets import WorkloadDataset
from aws_data_fetcher import fetch_ec2_metrics, validate_aws_credentials, get_available_instances
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import copy  # Add this import for deep copying objects

class EnergySchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Energy-Efficient VM Scheduler Simulator")
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
        self.aws_tab = ttk.Frame(self.notebook)
        self.monitoring_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.simulation_tab, text='Simulation')
        self.notebook.add(self.host_tab, text='Host Configuration')
        self.notebook.add(self.vm_tab, text='VM Configuration')
        self.notebook.add(self.dataset_tab, text='Dataset Configuration')
        self.notebook.add(self.aws_tab, text='AWS Integration')
        self.notebook.add(self.monitoring_tab, text='Monitoring')

        # Setup each tab
        self._setup_simulation_tab()
        self._setup_host_tab()
        self._setup_vm_tab()
        self._setup_dataset_tab()
        self._setup_aws_tab()
        self._setup_monitoring_tab()

        # Initialize simulation variables
        self.simulation = None
        self.simulation_thread = None
        self.is_simulation_running = False

    def _setup_simulation_tab(self):
        # Clear and rebuild the simulation tab for a more spacious, organized layout
        for widget in self.simulation_tab.winfo_children():
            widget.destroy()

        # Main container with padding
        main_frame = ttk.Frame(self.simulation_tab, padding="20 20 20 20")
        main_frame.pack(fill='both', expand=True)

        # Use grid for better alignment
        main_frame.columnconfigure(0, weight=1, minsize=350)
        main_frame.columnconfigure(1, weight=2, minsize=500)

        # --- Left: Input and Progress ---
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 30), pady=0)
        left_frame.columnconfigure(0, weight=1)

        # Section: Simulation Parameters
        input_frame = ttk.LabelFrame(left_frame, text="Simulation Parameters", padding="15 10 15 10")
        input_frame.pack(fill='x', pady=(0, 20))

        params = [
            ("Number of Hosts:", "host_count_var", 3),
            ("Number of VMs:", "vm_count_var", 5),
            ("Simulation Duration (s):", "sim_duration_var", 3600),
            ("Migration Threshold:", "migration_threshold_var", 0.7)
        ]
        for i, (label, var_name, default) in enumerate(params):
            ttk.Label(input_frame, text=label, font=("Segoe UI", 11)).grid(row=i, column=0, sticky="w", pady=6, padx=(0,10))
            var = tk.IntVar(value=default) if isinstance(default, int) else tk.DoubleVar(value=default)
            setattr(self, var_name, var)
            ttk.Entry(input_frame, textvariable=var, font=("Segoe UI", 11), width=12).grid(row=i, column=1, padx=5, pady=6, sticky="ew")
        input_frame.columnconfigure(1, weight=1)

        # Scheduling policy
        ttk.Label(input_frame, text="Scheduling Policy:", font=("Segoe UI", 11, "bold")).grid(row=len(params), column=0, sticky="w", pady=6)
        self.scheduler_var = tk.StringVar(value="Best-Fit Decreasing")
        scheduler_combo = ttk.Combobox(input_frame, textvariable=self.scheduler_var, font=("Segoe UI", 11), state="readonly")
        scheduler_combo['values'] = ('Best-Fit Decreasing', 'Random', 'Minimum Utilization')
        scheduler_combo.grid(row=len(params), column=1, padx=5, pady=6, sticky="ew")
        
        # Bind the scheduler change to update the indicator
        scheduler_combo.bind('<<ComboboxSelected>>', self._on_scheduler_change)

        # Buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=len(params)+1, column=0, columnspan=2, pady=(16, 0))
        run_button = ttk.Button(button_frame, text="Run Simulation", command=self.run_simulation, width=18)
        run_button.pack(side='left', padx=(0, 10))
        run_all_button = ttk.Button(button_frame, text="Compare All Algorithms", command=self.run_all_schedulers, width=22)
        run_all_button.pack(side='left', padx=(0, 10))
        reset_button = ttk.Button(button_frame, text="Reset to Generated VMs", command=self.reset_to_generated_vms, width=20)
        reset_button.pack(side='left', padx=(0, 10))
        # Place Stop button on a new row for visibility, but keep its appearance the same as others
        stop_button_frame = ttk.Frame(input_frame)
        stop_button_frame.grid(row=len(params)+2, column=0, columnspan=2, pady=(12, 0))
        self.stop_button = ttk.Button(
            stop_button_frame,
            text="Stop Simulation",
            command=self.stop_simulation,
            width=22,
            state='disabled'
        )
        self.stop_button.pack()

        # Progress bar and status label
        progress_frame = ttk.Frame(left_frame)
        progress_frame.pack(fill='x', pady=(10, 0))
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=3, length=220)
        self.progress_bar.pack(fill='x', pady=(0, 4))
        self.status_var = tk.StringVar(value="Idle")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var, font=("Segoe UI", 10, "italic"), foreground="#0078D7")
        self.status_label.pack(anchor='w')
        
        # VM Source Indicator
        self.vm_source_var = tk.StringVar(value="VM Source: Generated VMs")
        self.vm_source_label = ttk.Label(progress_frame, textvariable=self.vm_source_var, font=("Segoe UI", 9), foreground="#666666")
        self.vm_source_label.pack(anchor='w')
        
        # Scheduling Policy Indicator
        self.scheduling_policy_var = tk.StringVar(value="Scheduling Policy: Best-Fit Decreasing")
        self.scheduling_policy_label = ttk.Label(progress_frame, textvariable=self.scheduling_policy_var, font=("Segoe UI", 9), foreground="#666666")
        self.scheduling_policy_label.pack(anchor='w')

        # Section: Simulation Status
        status_frame = ttk.LabelFrame(left_frame, text="Simulation Status", padding="12 8 12 8")
        status_frame.pack(fill='both', expand=True, pady=(30, 0))
        self.status_text = tk.Text(status_frame, width=38, height=14, wrap=tk.WORD, font=("Consolas", 10), bg="#f8f8fa")
        self.status_text.pack(fill='both', expand=True, padx=2, pady=2)

        # --- Right: Results ---
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.columnconfigure(0, weight=1)

        # Section: Real-time Results
        results_frame = ttk.LabelFrame(right_frame, text="Real-time Results", padding="12 8 12 8")
        results_frame.pack(fill='both', expand=True, pady=(0, 20))
        results_scrollbar = ttk.Scrollbar(results_frame, orient="vertical")
        results_hscrollbar = ttk.Scrollbar(results_frame, orient="horizontal")
        self.results_text = tk.Text(
            results_frame,
            width=80,
            height=18,
            wrap="none",
            font=("Consolas", 11),
            bg="#f8f8fa",
            yscrollcommand=results_scrollbar.set,
            xscrollcommand=results_hscrollbar.set
        )
        self.results_text.pack(fill='both', expand=True, padx=2, pady=2, side='left')
        results_scrollbar.config(command=self.results_text.yview)
        results_scrollbar.pack(fill='y', side='right')
        results_hscrollbar.config(command=self.results_text.xview)
        results_hscrollbar.pack(fill='x', side='bottom')

        # Section: Visualization (optional, can be expanded)
        # You can add matplotlib or other visualizations here in a similar frame

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

        # AWS Data Configuration
        ttk.Label(dataset_config_frame, text="AWS Configuration:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, columnspan=3, sticky="w", pady=(10, 5))
        
        # Use Live AWS Data checkbox
        self.use_aws_data_var = tk.BooleanVar()
        ttk.Checkbutton(dataset_config_frame, text="Use Live AWS Data", variable=self.use_aws_data_var).grid(row=3, column=0, columnspan=3, sticky="w", pady=2)
        
        # EC2 Instance IDs entry
        ttk.Label(dataset_config_frame, text="EC2 Instance IDs:").grid(row=4, column=0, sticky="w", pady=2)
        self.aws_instance_ids_var = tk.StringVar()
        ttk.Entry(dataset_config_frame, textvariable=self.aws_instance_ids_var, width=50).grid(row=4, column=1, columnspan=2, padx=5, pady=2, sticky="ew")
        ttk.Label(dataset_config_frame, text="(comma-separated, e.g., i-1234567890abcdef0,i-0987654321fedcba0)").grid(row=5, column=1, columnspan=2, sticky="w", pady=(0, 5))

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

    def _setup_aws_tab(self):
        """Setup AWS integration tab with configuration options."""
        # AWS Configuration Frame
        aws_config_frame = ttk.LabelFrame(self.aws_tab, text="AWS Configuration", padding="15")
        aws_config_frame.pack(fill='x', padx=10, pady=10)

        # AWS Credentials
        credentials_frame = ttk.Frame(aws_config_frame)
        credentials_frame.pack(fill='x', pady=(0, 15))

        ttk.Label(credentials_frame, text="AWS Access Key ID:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.aws_access_key_var = tk.StringVar()
        ttk.Entry(credentials_frame, textvariable=self.aws_access_key_var, width=40, show="*").grid(row=0, column=1, padx=(10, 5), pady=5, sticky="ew")

        ttk.Label(credentials_frame, text="AWS Secret Access Key:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.aws_secret_key_var = tk.StringVar()
        ttk.Entry(credentials_frame, textvariable=self.aws_secret_key_var, width=40, show="*").grid(row=1, column=1, padx=(10, 5), pady=5, sticky="ew")

        ttk.Label(credentials_frame, text="AWS Region:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        self.aws_region_var = tk.StringVar(value="us-east-1")
        region_combo = ttk.Combobox(credentials_frame, textvariable=self.aws_region_var, width=37)
        region_combo['values'] = ('us-east-1', 'us-west-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 'ap-southeast-1', 'ap-northeast-1')
        region_combo.grid(row=2, column=1, padx=(10, 5), pady=5, sticky="ew")

        credentials_frame.columnconfigure(1, weight=1)

        # Test credentials button
        test_frame = ttk.Frame(aws_config_frame)
        test_frame.pack(fill='x', pady=(0, 15))
        ttk.Button(test_frame, text="Test AWS Credentials", command=self._test_aws_credentials, 
                  style="Accent.TButton").pack(side='left', padx=(0, 10))
        self.aws_status_label = ttk.Label(test_frame, text="", font=("Segoe UI", 9))
        self.aws_status_label.pack(side='left')

        # Instance Selection Frame
        instance_frame = ttk.LabelFrame(self.aws_tab, text="EC2 Instance Selection", padding="15")
        instance_frame.pack(fill='x', padx=10, pady=(0, 10))

        # Refresh instances button
        refresh_frame = ttk.Frame(instance_frame)
        refresh_frame.pack(fill='x', pady=(0, 10))
        ttk.Button(refresh_frame, text="Refresh Available Instances", command=self._refresh_aws_instances,
                  style="Accent.TButton").pack(side='left')

        # Instance list
        list_frame = ttk.Frame(instance_frame)
        list_frame.pack(fill='both', expand=True)
        
        ttk.Label(list_frame, text="Available EC2 Instances:", font=("Segoe UI", 10, "bold")).pack(anchor='w', pady=(0, 5))
        
        # Create a frame for the listbox and scrollbar
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill='both', expand=True)
        
        self.aws_instances_listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE, height=8)
        self.aws_instances_listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient='vertical', command=self.aws_instances_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.aws_instances_listbox.configure(yscrollcommand=scrollbar.set)

        # Fetch metrics frame
        fetch_frame = ttk.LabelFrame(self.aws_tab, text="Fetch AWS Metrics", padding="15")
        fetch_frame.pack(fill='x', padx=10, pady=(0, 10))

        ttk.Label(fetch_frame, text="Selected instances will be used to create VMs with real AWS metrics.", 
                 font=("Segoe UI", 9)).pack(anchor='w', pady=(0, 10))

        button_frame = ttk.Frame(fetch_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(button_frame, text="Fetch Selected Instance Metrics", command=self._fetch_aws_metrics,
                  style="Accent.TButton").pack(side='left', padx=(0, 10))
        ttk.Button(button_frame, text="Use AWS Data for Simulation", command=self._use_aws_data_for_simulation).pack(side='left')

        # Results frame
        results_frame = ttk.LabelFrame(self.aws_tab, text="AWS Metrics Results", padding="15")
        results_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        self.aws_results_text = tk.Text(results_frame, height=10, wrap=tk.WORD)
        self.aws_results_text.pack(fill='both', expand=True)
        
        # Add scrollbar to results text
        results_scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.aws_results_text.yview)
        results_scrollbar.pack(side='right', fill='y')
        self.aws_results_text.configure(yscrollcommand=results_scrollbar.set)

        # Initialize AWS data storage
        self.aws_vm_data = []
        self.aws_generated_vms = None
        self.aws_fetching_vms = False
        self.aws_fetch_thread = None
        self._aws_vm_results = None
        self._aws_credentials_results = None
        self._aws_instances_results = None
        self._aws_metrics_results = None

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
        
        # Update status text
        self.status_text.delete("1.0", tk.END)
        self.status_text.insert(tk.END, f"Simulation Time: {stats['simulation_time']:.1f}s\n")
        self.status_text.insert(tk.END, f"Active VMs: {stats['active_vms']}\n")
        self.status_text.insert(tk.END, f"Total Migrations: {stats['total_migrations']}\n")
        self.status_text.insert(tk.END, f"Current Energy: {stats['total_energy']:.2f} W\n")
        self.status_text.insert(tk.END, f"Average Energy: {stats['average_energy']:.2f} W\n\n")

        self.status_text.insert(tk.END, "Host Utilizations:\n")
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
        # Check if AWS data is available and should be used
        if hasattr(self, 'aws_generated_vms') and self.aws_generated_vms:
            # Use AWS-generated VMs
            aws_vms = self.aws_generated_vms[:count]  # Limit to requested count
            # Clear the AWS VMs after use to allow normal generation next time
            self.aws_generated_vms = None
            return aws_vms
        
        # Check if AWS data should be used from dataset tab configuration
        if hasattr(self, 'use_aws_data_var') and self.use_aws_data_var.get():
            # Start AWS data fetching in a separate thread
            self._start_aws_vm_generation(count)
            return []  # Return empty list for now, VMs will be generated asynchronously
        
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
        self._stop_requested = False
        self.stop_button.config(state='normal')
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

        # Check if AWS data is being fetched asynchronously
        if hasattr(self, 'aws_fetching_vms') and self.aws_fetching_vms:
            # AWS data is being fetched, don't start simulation yet
            return
        
        # Check if we have AWS-generated VMs to use
        if hasattr(self, 'aws_generated_vms') and self.aws_generated_vms:
            # Use AWS-generated VMs
            vms = self.aws_generated_vms
            self.vm_source_var.set(f"VM Source: AWS Data ({len(vms)} VMs)")
            self.results_text.insert(tk.END, f"Using {len(vms)} VMs generated from AWS data:\n")
            for vm in vms:
                # Check if this is an AWS VM with utilization data
                if hasattr(vm, 'aws_utilization'):
                    self.results_text.insert(tk.END, f"  {vm.vm_id}: CPU={vm.cpu} cores ({vm.aws_utilization:.2f}% util), RAM={vm.ram:.1f}GB\n")
                else:
                    self.results_text.insert(tk.END, f"  {vm.vm_id}: CPU={vm.cpu} cores, RAM={vm.ram:.1f}GB\n")
            self.results_text.insert(tk.END, "\n")
        else:
            # Generate VMs based on workload type
            vms = self.generate_vms(num_vms)
            self.vm_source_var.set(f"VM Source: Generated VMs ({len(vms)} VMs)")
            self.results_text.insert(tk.END, f"Generated {len(vms)} VMs using workload patterns:\n")
            for vm in vms:
                self.results_text.insert(tk.END, f"  {vm.vm_id}: CPU={vm.cpu} cores, RAM={vm.ram:.1f}GB\n")
            self.results_text.insert(tk.END, "\n")
        
        if not vms:
            return

        # Get scheduler name for configuration summary
        scheduler_name = self.scheduler_var.get()

        # Add simulation configuration summary
        self.results_text.insert(tk.END, "=== SIMULATION CONFIGURATION ===\n")
        self.results_text.insert(tk.END, f"Scheduling Policy: {scheduler_name}\n")
        if hasattr(self, 'aws_generated_vms') and self.aws_generated_vms:
            self.results_text.insert(tk.END, f"VM Source: AWS Data ({len(self.aws_generated_vms)} VMs)\n")
        else:
            self.results_text.insert(tk.END, f"VM Source: Generated VMs ({len(vms)} VMs)\n")
        self.results_text.insert(tk.END, f"Hosts: {len(hosts)} (CPU: {hosts[0].total_cpu}, RAM: {hosts[0].total_ram}GB)\n")
        self.results_text.insert(tk.END, f"Migration Threshold: {self.migration_threshold_var.get()}\n")
        self.results_text.insert(tk.END, f"Duration: {self.sim_duration_var.get()} seconds\n")
        self.results_text.insert(tk.END, "=" * 40 + "\n\n")
        self.results_text.insert(tk.END, "Starting simulation...\n\n")

        # Run selected scheduler
        if scheduler_name == "Best-Fit Decreasing":
            best_fit_decreasing(vms, hosts)
        elif scheduler_name == "Random":
            random_scheduler(vms, hosts)
        else:  # Minimum Utilization
            minimum_utilization_scheduler(vms, hosts)
        
        # Update scheduling policy indicator to show which policy is being used
        self.scheduling_policy_var.set(f"Scheduling Policy: {scheduler_name} (Active)")

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
        elapsed = 0
        interval = 1
        while elapsed < duration and not getattr(self, '_stop_requested', False):
            self.simulation.run(interval)
            elapsed += interval
        self.is_simulation_running = False
        self.root.after(0, lambda: self.stop_button.config(state='disabled'))
        
        # Reset scheduling policy indicator when simulation completes
        self.root.after(0, self._reset_scheduling_policy_indicator)

    def _display_statistics(self, stats):
        """Display final simulation statistics."""
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "Simulation Complete!\n\n")
        
        # Show which scheduling policy was used
        scheduler_name = self.scheduler_var.get()
        self.results_text.insert(tk.END, f"Scheduling Policy Used: {scheduler_name}\n")
        
        # Show VM source if AWS data was used
        if hasattr(self, 'aws_generated_vms') and self.aws_generated_vms:
            self.results_text.insert(tk.END, f"VM Source: AWS Data ({len(self.aws_generated_vms)} VMs)\n")
        else:
            self.results_text.insert(tk.END, "VM Source: Generated VMs\n")
        
        self.results_text.insert(tk.END, f"Total Simulation Time: {stats['simulation_time']:.1f}s\n")
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

    def run_all_schedulers(self):
        if self.is_simulation_running:
            messagebox.showwarning("Warning", "Simulation is already running!")
            return
        self.is_simulation_running = True
        self.results_text.delete("1.0", tk.END)
        self.progress_var.set(0)
        self.status_var.set("Starting comparison...")
        self._stop_requested = False
        self.stop_button.config(state='normal')
        threading.Thread(target=self._run_all_schedulers_worker, daemon=True).start()

    def _run_all_schedulers_worker(self):
        try:
            sched_names = ["Best-Fit Decreasing", "Minimum Utilization", "Random"]
            print("[DEBUG] Started _run_all_schedulers_worker")
            num_hosts = self.host_count_var.get()
            num_vms = self.vm_count_var.get()
            migration_threshold = self.migration_threshold_var.get()
            sim_duration = self.sim_duration_var.get()

            # Prepare base hosts and VMs
            base_hosts = [Host(
                host_id=f"H{i+1}",
                total_cpu=self.host_cpu_var.get(),
                total_ram=self.host_ram_var.get(),
                base_power=self.host_base_power_var.get(),
                max_power=self.host_max_power_var.get()
            ) for i in range(num_hosts)]
            base_vms = self.generate_vms(num_vms)
            print(f"[DEBUG] Generated {len(base_vms)} VMs")
            if not base_vms:
                print("[DEBUG] No VMs generated, aborting.")
                self.is_simulation_running = False
                self.root.after(0, lambda: self.status_var.set("No VMs generated."))
                return

            # Prepare results dict
            results = {}
            schedulers = [
                ("Best-Fit Decreasing", best_fit_decreasing),
                ("Minimum Utilization", minimum_utilization_scheduler),
                ("Random", random_scheduler)
            ]

            for idx, (name, scheduler) in enumerate(schedulers):
                print(f"[DEBUG] Running scheduler: {name}")
                self.root.after(0, lambda n=name: self.status_var.set(f"Running: {n}"))
                hosts = copy.deepcopy(base_hosts)
                vms = copy.deepcopy(base_vms)
                scheduler(vms, hosts)
                sim = Simulation(hosts=hosts, vms=vms, migration_threshold=migration_threshold)
                elapsed = 0
                interval = 1
                while elapsed < sim_duration and not getattr(self, '_stop_requested', False):
                    sim.run(interval)
                    elapsed += interval
                stats = sim.get_statistics()
                results[name] = stats
                print(f"[DEBUG] Finished scheduler: {name}")
                self.root.after(0, lambda v=idx+1: self.progress_var.set(v))
                if getattr(self, '_stop_requested', False):
                    break
            best_algo = min(results, key=lambda k: results[k]['total_energy']) if results else None
            def update_results():
                self.results_text.delete("1.0", tk.END)
                if results:
                    self.results_text.insert(tk.END, "Algorithm Comparison Results:\n\n")
                    header = f"{'Algorithm':<25}{'Total Energy (W)':<20}{'Avg Energy (W)':<20}{'Migrations':<15}{'Active VMs':<12}\n"
                    self.results_text.insert(tk.END, header)
                    self.results_text.insert(tk.END, "-" * 80 + "\n")
                    for name, stats in results.items():
                        line = f"{name:<25}{stats['total_energy']:<20.2f}{stats['average_energy']:<20.2f}{stats['total_migrations']:<15}{stats['active_vms']:<12}\n"
                        if name == best_algo:
                            line = "* " + line
                        else:
                            line = "  " + line
                        self.results_text.insert(tk.END, line)
                    self.results_text.insert(tk.END, f"\n* Best algorithm: {best_algo}\n")
                else:
                    self.results_text.insert(tk.END, "Simulation stopped. No results to display.\n")
                self._trim_results_text(max_lines=100)
                self.status_var.set("Comparison complete." if results else "Simulation stopped.")
                self.progress_var.set(3)
                self.is_simulation_running = False
                self.stop_button.config(state='disabled')
            self.root.after(0, update_results)
        except Exception as e:
            import traceback
            print("[ERROR] Exception in _run_all_schedulers_worker:", e)
            traceback.print_exc()
            self.is_simulation_running = False
            self.root.after(0, lambda: self.status_var.set("Error during comparison."))
            self.root.after(0, lambda: self.stop_button.config(state='disabled'))

    def stop_simulation(self):
        self._stop_requested = True
        self.status_var.set("Stopping simulation...")
        self.stop_button.config(state='disabled')
        
        # Reset scheduling policy indicator to show current selection (not active)
        scheduler_name = self.scheduler_var.get()
        self.scheduling_policy_var.set(f"Scheduling Policy: {scheduler_name}")

    def _test_aws_credentials(self):
        """Test AWS credentials by attempting to connect."""
        access_key = self.aws_access_key_var.get().strip()
        secret_key = self.aws_secret_key_var.get().strip()
        region = self.aws_region_var.get().strip()
        
        if not access_key or not secret_key:
            self.aws_status_label.config(text="Please enter both Access Key and Secret Key", foreground="red")
            return
        
        # Run credential validation in a separate thread
        def validate_credentials():
            try:
                is_valid, message = validate_aws_credentials(access_key, secret_key, region)
                self._aws_credentials_results = (is_valid, message, None)
            except Exception as e:
                self._aws_credentials_results = (False, f"Error: {str(e)}", None)
        
        threading.Thread(target=validate_credentials, daemon=True).start()
        
        # Start checking for results
        self._check_aws_credentials_results_timer()
        
        self.aws_status_label.config(text="Testing credentials...", foreground="blue")
        threading.Thread(target=validate_credentials, daemon=True).start()

    def _refresh_aws_instances(self):
        """Refresh the list of available EC2 instances."""
        access_key = self.aws_access_key_var.get().strip()
        secret_key = self.aws_secret_key_var.get().strip()
        region = self.aws_region_var.get().strip()
        
        if not access_key or not secret_key:
            messagebox.showerror("Error", "Please enter AWS credentials first")
            return
        
        def fetch_instances():
            try:
                instances = get_available_instances(access_key, secret_key, region)
                self._aws_instances_results = (instances, None)
            except Exception as e:
                self._aws_instances_results = (None, f"Failed to fetch instances: {str(e)}")
        
        threading.Thread(target=fetch_instances, daemon=True).start()
        
        # Start checking for results
        self._check_aws_instances_results_timer()

    def _update_instances_list(self, instances):
        """Update the instances listbox with fetched instances."""
        self.aws_instances_listbox.delete(0, tk.END)
        if instances:
            for instance_id in instances:
                self.aws_instances_listbox.insert(tk.END, instance_id)
            messagebox.showinfo("Success", f"Found {len(instances)} EC2 instances")
        else:
            messagebox.showinfo("Info", "No EC2 instances found in the specified region")

    def _fetch_aws_metrics(self):
        """Fetch metrics for selected EC2 instances."""
        selected_indices = self.aws_instances_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one EC2 instance")
            return
        
        selected_instances = [self.aws_instances_listbox.get(i) for i in selected_indices]
        access_key = self.aws_access_key_var.get().strip()
        secret_key = self.aws_secret_key_var.get().strip()
        region = self.aws_region_var.get().strip()
        
        if not access_key or not secret_key:
            messagebox.showerror("Error", "Please enter AWS credentials first")
            return
        
        def fetch_metrics():
            try:
                vm_data = fetch_ec2_metrics(selected_instances, region, access_key, secret_key)
                self._aws_metrics_results = (vm_data, None)
            except Exception as e:
                self._aws_metrics_results = (None, f"Failed to fetch metrics: {str(e)}")
        
        threading.Thread(target=fetch_metrics, daemon=True).start()
        
        # Start checking for results
        self._check_aws_metrics_results_timer()

    def _display_aws_metrics(self, vm_data):
        """Display fetched AWS metrics in the results text area."""
        self.aws_vm_data = vm_data  # Store for later use
        self.aws_results_text.delete("1.0", tk.END)
        
        if not vm_data:
            self.aws_results_text.insert(tk.END, "No metrics data retrieved.\n")
            return
        
        self.aws_results_text.insert(tk.END, "AWS EC2 Metrics Results:\n")
        self.aws_results_text.insert(tk.END, "=" * 50 + "\n\n")
        
        for i, vm_info in enumerate(vm_data, 1):
            self.aws_results_text.insert(tk.END, f"Instance {i}:\n")
            self.aws_results_text.insert(tk.END, f"  Instance ID: {vm_info.get('instance_id', 'N/A')}\n")
            self.aws_results_text.insert(tk.END, f"  CPU Utilization: {vm_info.get('cpu_utilization', 0):.2f}%\n")
            self.aws_results_text.insert(tk.END, f"  Estimated CPU Cores: {vm_info.get('cpu', 1)}\n")
            self.aws_results_text.insert(tk.END, f"  RAM: {vm_info.get('ram', 8):.1f} GB\n")
            self.aws_results_text.insert(tk.END, f"  Duration: {vm_info.get('duration', 15):.1f} minutes\n")
            
            if 'error' in vm_info:
                self.aws_results_text.insert(tk.END, f"  Error: {vm_info['error']}\n")
            
            self.aws_results_text.insert(tk.END, "\n")
        
        self.aws_results_text.insert(tk.END, f"Total instances processed: {len(vm_data)}\n")
        messagebox.showinfo("Success", f"Successfully fetched metrics for {len(vm_data)} instances")

    def _use_aws_data_for_simulation(self):
        """Use AWS data to create VMs for simulation."""
        if not self.aws_vm_data:
            messagebox.showwarning("Warning", "No AWS data available. Please fetch metrics first.")
            return
        
        # Create VMs from AWS data
        vms = []
        for vm_info in self.aws_vm_data:
            if 'error' not in vm_info:  # Skip instances with errors
                vm = VM(
                    vm_id=f"AWS-{vm_info['instance_id']}",
                    cpu=vm_info['cpu'],  # Now using CPU cores directly
                    ram=vm_info['ram'],
                    duration=vm_info['duration'] * 60  # Convert minutes to seconds
                )
                # Store AWS utilization data for display purposes
                vm.aws_utilization = vm_info.get('cpu_utilization', 0.0)
                vms.append(vm)
        
        if not vms:
            messagebox.showwarning("Warning", "No valid VM data available from AWS metrics.")
            return
        
        # Update VM count in simulation tab
        self.vm_count_var.set(len(vms))
        
        # Store the AWS-generated VMs for use in simulation
        self.aws_generated_vms = vms
        
        # Update VM source indicator
        self.vm_source_var.set(f"VM Source: AWS Data ({len(vms)} VMs)")
        
        messagebox.showinfo("Success", f"Created {len(vms)} VMs from AWS data. Ready for simulation!")

    def _start_aws_vm_generation(self, count: int):
        """Start AWS VM generation in a separate thread."""
        if self.aws_fetching_vms:
            messagebox.showwarning("Warning", "AWS data fetching is already in progress.")
            return
        
        # Validate inputs
        instance_ids_str = self.aws_instance_ids_var.get().strip()
        if not instance_ids_str:
            messagebox.showerror("Error", "Please enter EC2 instance IDs.")
            return
        
        access_key = self.aws_access_key_var.get().strip()
        secret_key = self.aws_secret_key_var.get().strip()
        if not access_key or not secret_key:
            messagebox.showerror("Error", "Please enter AWS credentials in the AWS Integration tab.")
            return
        
        # Parse instance IDs
        instance_ids = [id.strip() for id in instance_ids_str.split(',') if id.strip()]
        if not instance_ids:
            messagebox.showerror("Error", "No valid instance IDs found.")
            return
        
        # Set fetching state
        self.aws_fetching_vms = True
        
        # Update UI to show loading state
        self._update_aws_loading_state(True)
        
        # Get region before starting thread
        region = self.aws_region_var.get().strip()
        
        # Start fetching in a separate thread
        self.aws_fetch_thread = threading.Thread(
            target=self._fetch_aws_vms_worker,
            args=(instance_ids, count, access_key, secret_key, region),
            daemon=True
        )
        self.aws_fetch_thread.start()
        
        # Start checking for results periodically
        self._check_aws_results_timer()

    def _fetch_aws_vms_worker(self, instance_ids: list, count: int, access_key: str, secret_key: str, region: str):
        """Worker thread for fetching AWS VMs."""
        try:
            # Fetch AWS metrics
            vm_data = fetch_ec2_metrics(instance_ids, region, access_key, secret_key)
            
            if vm_data:
                                # Create VMs from AWS data
                vms = []
                for vm_info in vm_data[:count]:  # Limit to requested count
                    if 'error' not in vm_info:
                        vm = VM(
                            vm_id=f"AWS-{vm_info['instance_id']}",
                            cpu=vm_info['cpu'],  # Now using CPU cores directly
                            ram=vm_info['ram'],
                            duration=vm_info['duration'] * 60  # Convert minutes to seconds
                        )
                        # Store AWS utilization data for display purposes
                        vm.aws_utilization = vm_info.get('cpu_utilization', 0.0)
                        vms.append(vm)
                
                # Store results for main thread to process
                self._aws_vm_results = (vms, None)
            else:
                self._aws_vm_results = ([], "No AWS data retrieved")
                
        except Exception as e:
            error_msg = f"Failed to fetch AWS metrics: {str(e)}"
            self._aws_vm_results = (error_msg, None)

    def _aws_vm_generation_complete(self, vms: list, error: str = None):
        """Handle completion of AWS VM generation."""
        # Reset fetching state
        self.aws_fetching_vms = False
        self.aws_fetch_thread = None
        
        # Update UI to hide loading state
        self._update_aws_loading_state(False)
        
        if error:
            messagebox.showerror("AWS Error", error)
            return
        
        if not vms:
            messagebox.showwarning("Warning", "No valid VMs could be created from AWS data.")
            return
        
        # Store the generated VMs
        self.aws_generated_vms = vms
        
        # Update VM count
        self.vm_count_var.set(len(vms))
        
        # Update VM source indicator
        self.vm_source_var.set(f"VM Source: AWS Data ({len(vms)} VMs)")
        
        # Show success message
        messagebox.showinfo("Success", f"Successfully created {len(vms)} VMs from AWS data!")
        
        # Re-enable run button if it was disabled
        if hasattr(self, 'run_button'):
            self.run_button.config(state='normal')
        
        # Automatically start simulation with the generated VMs
        self._start_simulation_with_vms(vms)

    def _update_aws_loading_state(self, loading: bool):
        """Update UI to show/hide AWS loading state."""
        if loading:
            # Show loading message
            if hasattr(self, 'status_var'):
                self.status_var.set("Fetching AWS data...")
            if hasattr(self, 'results_text'):
                self.results_text.delete("1.0", tk.END)
                self.results_text.insert(tk.END, "Fetching AWS EC2 metrics...\nPlease wait...")
            
            # Disable run button if it exists
            if hasattr(self, 'run_button'):
                self.run_button.config(state='disabled')
        else:
            # Clear loading message
            if hasattr(self, 'status_var'):
                self.status_var.set("Ready")
            if hasattr(self, 'results_text'):
                self.results_text.delete("1.0", tk.END)
            
                    # Re-enable run button if it exists
        if hasattr(self, 'run_button'):
            self.run_button.config(state='normal')
        
        # Check for AWS results and process them
        self._check_aws_results()

    def _check_aws_results(self):
        """Check for AWS results and process them in the main thread."""
        if hasattr(self, '_aws_vm_results') and self._aws_vm_results:
            vms, error = self._aws_vm_results
            self._aws_vm_results = None  # Clear the results
            self._aws_vm_generation_complete(vms, error)

    def _check_aws_results_timer(self):
        """Timer to check for AWS results periodically."""
        if self.aws_fetching_vms:
            self._check_aws_results()
            # Schedule next check in 100ms
            self.root.after(100, self._check_aws_results_timer)

    def _check_aws_credentials_results_timer(self):
        """Timer to check for AWS credentials validation results."""
        if hasattr(self, '_aws_credentials_results') and self._aws_credentials_results:
            is_valid, message, _ = self._aws_credentials_results
            self._aws_credentials_results = None  # Clear results
            self.aws_status_label.config(
                text=message, 
                foreground="green" if is_valid else "red"
            )
        else:
            # Continue checking
            self.root.after(100, self._check_aws_credentials_results_timer)

    def _check_aws_instances_results_timer(self):
        """Timer to check for AWS instances results."""
        if hasattr(self, '_aws_instances_results') and self._aws_instances_results:
            instances, error = self._aws_instances_results
            self._aws_instances_results = None  # Clear results
            if error:
                messagebox.showerror("Error", error)
            else:
                self._update_instances_list(instances)
        else:
            # Continue checking
            self.root.after(100, self._check_aws_instances_results_timer)

    def _check_aws_metrics_results_timer(self):
        """Timer to check for AWS metrics results."""
        if hasattr(self, '_aws_metrics_results') and self._aws_metrics_results:
            vm_data, error = self._aws_metrics_results
            self._aws_metrics_results = None  # Clear results
            if error:
                messagebox.showerror("Error", error)
            else:
                self._display_aws_metrics(vm_data)
        else:
            # Continue checking
            self.root.after(100, self._check_aws_metrics_results_timer)

    def _start_simulation_with_vms(self, vms: list):
        """Start simulation with the provided VMs."""
        if self.is_simulation_running:
            messagebox.showwarning("Warning", "Simulation is already running!")
            return
        
        num_hosts = self.host_count_var.get()
        
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

        # Run selected scheduler
        scheduler_name = self.scheduler_var.get()
        if scheduler_name == "Best-Fit Decreasing":
            best_fit_decreasing(vms, hosts)
        elif scheduler_name == "Random":
            random_scheduler(vms, hosts)
        else:  # Minimum Utilization
            minimum_utilization_scheduler(vms, hosts)
        
        # Update scheduling policy indicator to show which policy is being used
        self.scheduling_policy_var.set(f"Scheduling Policy: {scheduler_name} (Active)")

        # Add simulation configuration summary to results
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "=== SIMULATION CONFIGURATION ===\n")
        self.results_text.insert(tk.END, f"Scheduling Policy: {scheduler_name}\n")
        self.results_text.insert(tk.END, f"VM Source: AWS Data ({len(vms)} VMs)\n")
        self.results_text.insert(tk.END, f"Hosts: {len(hosts)} (CPU: {hosts[0].total_cpu}, RAM: {hosts[0].total_ram}GB)\n")
        self.results_text.insert(tk.END, f"Migration Threshold: {self.migration_threshold_var.get()}\n")
        self.results_text.insert(tk.END, f"Duration: {self.sim_duration_var.get()} seconds\n")
        self.results_text.insert(tk.END, "=" * 40 + "\n\n")
        self.results_text.insert(tk.END, "Starting simulation...\n\n")

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

    def reset_to_generated_vms(self):
        """Reset to use generated VMs instead of AWS-generated VMs."""
        if hasattr(self, 'aws_generated_vms'):
            delattr(self, 'aws_generated_vms')
        
        # Clear results and show reset message
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "Reset to generated VMs mode.\n")
        self.results_text.insert(tk.END, "AWS-generated VMs have been cleared.\n")
        self.results_text.insert(tk.END, "Next simulation will use generated VMs based on workload patterns.\n\n")
        
        # Update status and VM source indicator
        self.status_var.set("Reset to generated VMs")
        self.vm_source_var.set("VM Source: Generated VMs")
        
        messagebox.showinfo("Reset Complete", "Successfully reset to generated VMs mode. AWS-generated VMs have been cleared.")

    def _on_scheduler_change(self, event=None):
        """Update the scheduling policy indicator when scheduler changes."""
        scheduler_name = self.scheduler_var.get()
        self.scheduling_policy_var.set(f"Scheduling Policy: {scheduler_name}")

    def _reset_scheduling_policy_indicator(self):
        """Reset the scheduling policy indicator to show current selection (not active)."""
        scheduler_name = self.scheduler_var.get()
        self.scheduling_policy_var.set(f"Scheduling Policy: {scheduler_name}")

    def _trim_results_text(self, max_lines=100):
        """Trim the results_text widget to keep at most max_lines."""
        lines = self.results_text.get("1.0", tk.END).splitlines()
        if len(lines) > max_lines:
            trimmed = "\n".join(lines[-max_lines:])
            self.results_text.delete("1.0", tk.END)
            self.results_text.insert(tk.END, trimmed)


if __name__ == "__main__":
    root = tk.Tk()
    app = EnergySchedulerApp(root)
    root.mainloop() 