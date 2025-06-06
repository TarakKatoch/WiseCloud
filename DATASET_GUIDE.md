# Dataset Guide for Energy-Efficient VM Scheduler

This guide explains how to prepare and use custom datasets with the VM Scheduler application.

## Dataset Format

The application accepts CSV files with the following columns:

1. `timestamp`: Unix timestamp when the VM was created
2. `job_id`: Unique identifier for the job
3. `task_id`: Unique identifier for the task
4. `machine_id`: Identifier for the physical machine
5. `cpu`: Number of CPU cores required
6. `memory`: Amount of RAM required in GB
7. `duration`: VM lifetime in seconds

## Example Dataset

```csv
timestamp,job_id,task_id,machine_id,cpu,memory,duration
1625097600,job1,task1,machine1,2,4,3600
1625097600,job1,task2,machine2,4,8,7200
```

## How to Use Custom Datasets

1. Prepare your dataset:
   - Create a CSV file with the required columns
   - Ensure all values are numeric (except for IDs)
   - Save the file with a `.csv` extension

2. Load the dataset in the application:
   - Go to the "Dataset Configuration" tab
   - Select "custom" from the Workload Type dropdown
   - Click "Browse" and select your CSV file
   - The application will automatically load and process the dataset

3. Run the simulation:
   - The application will create VMs based on your dataset
   - Each row in the dataset becomes a VM with the specified resources
   - The simulation will run using your real workload data

## Dataset Requirements

- File format: CSV (Comma-Separated Values)
- Required columns: timestamp, job_id, task_id, machine_id, cpu, memory, duration
- CPU values: Positive integers
- Memory values: Positive numbers (in GB)
- Duration values: Positive integers (in seconds)

## Tips for Creating Datasets

1. Use realistic values:
   - CPU: 1-16 cores
   - Memory: 2-32 GB
   - Duration: 1800-86400 seconds (30 minutes to 24 hours)

2. Consider workload patterns:
   - Web servers: 1-4 CPU cores, 2-8 GB RAM
   - Databases: 2-8 CPU cores, 8-32 GB RAM
   - Batch jobs: 4-16 CPU cores, 8-32 GB RAM
   - Development: 1-2 CPU cores, 2-4 GB RAM

3. Balance your dataset:
   - Include a mix of different VM sizes
   - Vary the durations
   - Consider peak and off-peak times

## Example Use Cases

1. Web Application Workload:
   - Many small VMs (1-2 CPU cores)
   - Short to medium durations
   - Higher memory requirements

2. Database Workload:
   - Fewer, larger VMs (4-8 CPU cores)
   - Longer durations
   - High memory requirements

3. Batch Processing:
   - Large VMs (8-16 CPU cores)
   - Short durations
   - High CPU utilization

## Troubleshooting

If you encounter issues with your dataset:

1. Check the file format:
   - Ensure it's a valid CSV file
   - Verify all required columns are present
   - Check for missing or invalid values

2. Verify the data:
   - All numeric values should be positive
   - Durations should be reasonable
   - Resource requirements should match your hosts' capabilities

3. Common errors:
   - "Invalid file format": Check if the file is a valid CSV
   - "Missing required columns": Verify all required columns are present
   - "Invalid values": Check for negative or non-numeric values 