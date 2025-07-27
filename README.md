# WiseCloud: Energy-Efficient Virtual Machine Scheduler Simulator

### Project Relevance: Energy Consumption in Virtualized Cloud Data Centers

This project directly addresses the critical challenge of energy consumption in modern cloud data centers through virtualization. Here's how WiseCloud contributes to this field:

#### Problem Statement
Modern cloud data centers face significant energy consumption challenges:
- Data centers consume approximately 1-2% of global electricity
- Virtualization, while improving resource utilization, can lead to inefficient energy usage
- Traditional VM scheduling often prioritizes performance over energy efficiency
- Underutilized servers continue to consume significant power
- Cooling systems account for up to 40% of total data center energy consumption

#### WiseCloud's Solution
Our simulator provides a comprehensive approach to energy-efficient VM scheduling:

1. **Energy-Aware Resource Allocation**
   The simulator implements multiple scheduling algorithms, each optimized for different aspects of energy efficiency:

   a) **Best-Fit Decreasing Algorithm**
      - Sorts VMs by CPU requirements in descending order
      - Places each VM in the host with least leftover CPU after placement
      - Optimizes for resource utilization and consolidation
      - Reduces the number of active hosts needed

   b) **Minimum Utilization Scheduler**
      - Assigns VMs to hosts with lowest current utilization
      - Balances load across available hosts
      - Prevents resource hotspots
      - Optimizes for even distribution of workload

   c) **Random Scheduler**
      - Provides baseline performance comparison
      - Useful for testing and benchmarking
      - Helps evaluate effectiveness of other algorithms
      - Simulates unpredictable workload patterns

   Each algorithm considers:
   - Both CPU and memory utilization in power consumption
   - Server consolidation opportunities
   - Load balancing requirements
   - Energy efficiency metrics

2. **Power Consumption Modeling**
   - Simulates real-world power consumption patterns
   - Accounts for different server states (idle, active, peak)
   - Models cooling system energy requirements
   - Calculates total data center power usage effectiveness (PUE)

3. **Virtualization Optimization**
   - Maximizes VM consolidation while maintaining performance
   - Implements intelligent VM migration to reduce energy waste
   - Balances load across servers to prevent hotspots
   - Optimizes resource utilization to minimize active servers

4. **Energy Efficiency Metrics**
   - Tracks power consumption per VM
   - Monitors server utilization efficiency
   - Calculates energy savings through consolidation
   - Provides carbon footprint estimation
   - Measures cooling system efficiency

#### Impact and Significance
WiseCloud's approach to energy-efficient VM scheduling can lead to:
- Up to 30% reduction in energy consumption through intelligent VM placement
- Improved resource utilization leading to fewer active servers
- Better cooling efficiency through optimized workload distribution
- Reduced operational costs and carbon footprint
- Sustainable cloud computing practices

This project serves as both a research tool and a practical solution for cloud data centers seeking to optimize their energy consumption while maintaining performance standards.

### Project Overview
WiseCloud is an advanced simulation platform designed to optimize virtual machine (VM) scheduling in cloud computing environments with a focus on energy efficiency. This project implements and simulates various scheduling algorithms to minimize energy consumption while maintaining performance in cloud data centers.

### Table of Contents
1. [Project Architecture](#project-architecture)
2. [Technical Stack](#technical-stack)
3. [Core Components](#core-components)
4. [Features and Capabilities](#features-and-capabilities)
5. [Implementation Details](#implementation-details)
6. [Usage Guide](#usage-guide)
7. [Performance Metrics](#performance-metrics)
8. [Future Enhancements](#future-enhancements)

### Project Architecture
The project follows a modular architecture with clear separation of concerns:
- **GUI Layer**: User interface for simulation control and visualization
- **Business Logic Layer**: Core scheduling algorithms and simulation logic
- **Data Layer**: Dataset management and model definitions
- **Utility Layer**: Energy calculations and helper functions

### Technical Stack
- **Programming Language**: Python 3.8+
- **GUI Framework**: Tkinter
- **Data Visualization**: Matplotlib
- **Cloud Integration**: AWS Boto3
- **Version Control**: Git
- **Dependencies**: See requirements.txt for complete list

### Core Components

#### 1. Main Application (`main.py`)
The central component that orchestrates the entire simulation:
- Implements the graphical user interface
- Manages user interactions
- Coordinates between different modules
- Handles real-time visualization
- Processes simulation results

Key Features:
- Interactive control panel
- Real-time energy consumption graphs
- Dynamic VM allocation visualization
- Configuration management
- Results export functionality

#### 2. Models (`models.py`)
Defines the core data structures and classes:
- `Host` class: Represents physical servers
  - CPU and RAM capacity management
  - Power consumption tracking
  - Resource utilization monitoring
- `VM` class: Represents virtual machines
  - Resource requirements specification
  - Migration status tracking
  - Performance metrics

#### 3. Scheduler (`scheduler.py`)
Implements the scheduling algorithms:
- Best-Fit Decreasing algorithm
- Resource allocation optimization
- Load balancing mechanisms
- Migration policies
- Energy-aware placement strategies

#### 4. Energy Model (`energy_model.py`)
Handles energy consumption calculations:
- Power consumption modeling
- Energy efficiency metrics
- Resource utilization impact analysis
- Cooling cost considerations
- Carbon footprint estimation

#### 5. Simulation Engine (`simulation.py`)
Manages the simulation environment:
- Scenario generation
- Time-based simulation
- Event handling
- Performance monitoring
- Results collection

#### 6. Dataset Management (`datasets.py`)
Handles data operations:
- Dataset loading and parsing
- Data validation
- Sample data generation
- Historical data analysis
- Performance benchmarking

#### 7. AWS Integration (`aws_data_fetcher.py`)
Provides cloud integration capabilities:
- Real-time EC2 metrics fetching
- AWS CloudWatch integration
- Instance discovery and monitoring
- Credential management
- Cloud-based VM data generation

### Features and Capabilities

#### 1. VM Scheduling
- Dynamic VM allocation
- Resource-aware placement
- Load balancing
- Migration support
- Failure handling

#### 2. Energy Optimization
- Power consumption monitoring
- Energy-efficient resource allocation
- Cooling optimization
- Green computing metrics
- Cost analysis

#### 3. Visualization
- Real-time energy consumption graphs
- Resource utilization charts
- VM distribution maps
- Performance metrics dashboard
- Historical data analysis

#### 4. Simulation Controls
- Customizable scenarios
- Parameter adjustment
- Real-time monitoring
- Pause/Resume functionality
- Results export

#### 5. AWS Cloud Integration
- Real-time EC2 instance monitoring
- CloudWatch metrics integration
- Automatic VM data generation from AWS
- Credential validation and management
- Multi-region support

### Implementation Details

#### Installation
1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd WiseCloud
   ```
2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

#### Configuration
- Host specifications in `models.py`
- VM templates in `datasets.py`
- Energy parameters in `energy_model.py`
- Simulation parameters in `main.py`

#### AWS Setup Requirements
To use AWS integration features:
1. AWS Account with EC2 and CloudWatch access
2. IAM user with appropriate permissions:
   - `ec2:DescribeInstances`
   - `cloudwatch:GetMetricStatistics`
   - `cloudwatch:ListMetrics`
3. Access Key ID and Secret Access Key
4. EC2 instances running in your selected region

#### AWS Integration: Local Usage & Real-Time Cloud Data

WiseCloud now supports **real-time integration with AWS EC2 and CloudWatch**. You can fetch live metrics from your own AWS account and use them to drive VM simulation scenarios—**all from your local machine**.

---

##### How AWS Integration Works
- **No deployment to AWS is required.**  
  You run the app locally on your computer.
- The app connects to AWS using your credentials and fetches metrics for the EC2 instances you specify.
- All AWS API calls are made securely over the internet using the `boto3` library.

---

##### Requirements for AWS Integration
1. **AWS Account**  
   You must have an AWS account.
2. **IAM User & Permissions**  
   Create an IAM user with these permissions:
   - `ec2:DescribeInstances`
   - `cloudwatch:GetMetricStatistics`
   - `cloudwatch:ListMetrics`
3. **Access Keys**  
   Obtain your **Access Key ID** and **Secret Access Key** for the IAM user.
4. **Running EC2 Instances**  
   You must have EC2 instances running in your AWS account and know their **Instance IDs**.
5. **Internet Connection**  
   Your computer must be online to connect to AWS.

---

##### How to Use AWS Integration (Step-by-Step)
1. **Run the Application Locally**
   ```bash
   python main.py
   ```
2. **Configure AWS Credentials**
   - Go to the **"AWS Integration"** tab.
   - Enter your **Access Key ID** and **Secret Access Key**.
   - Select the correct **AWS region** (e.g., `us-east-1`).
   - (Optional) Test your credentials using the "Test AWS Credentials" button.
3. **Enable Live AWS Data in Dataset Tab**
   - Go to the **"Dataset Configuration"** tab.
   - Check the **"Use Live AWS Data"** checkbox.
   - Enter your EC2 **Instance IDs** (comma-separated, e.g., `i-1234567890abcdef0,i-0987654321fedcba0`).
4. **Run the Simulation**
   - Click **Run Simulation**.
   - The app will fetch real-time metrics from AWS for the specified instances, create VMs, and start the simulation.

---

##### Threading and UI Responsiveness
- **All AWS data fetching is performed in background threads.**
- The UI remains responsive and shows a "Loading..." status while waiting for AWS.
- Once data is fetched, the simulation starts automatically.
- All error messages (e.g., invalid credentials, no data) are shown in the UI.

---

##### Security Note
- **Never share your AWS credentials.**
- Use an IAM user with only the permissions required for this app.
- Credentials are only used locally and are not stored or transmitted anywhere except to AWS.

---

##### Troubleshooting
- If you see errors like `InvalidClientTokenId`, check your credentials.
- If you see "No valid VMs could be created from AWS data," check your instance IDs and that your instances are running.
- The app must be able to reach AWS over the internet.

---

##### Summary Table: Local AWS Integration

| Feature                | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| Deployment             | **Not required** (run locally)                                              |
| AWS Credentials        | Required (Access Key ID & Secret Access Key)                                |
| EC2 Instance IDs       | Required (comma-separated, e.g., `i-xxxxxx,i-yyyyyy`)                       |
| Internet Connection    | Required                                                                    |
| Permissions Needed     | `ec2:DescribeInstances`, `cloudwatch:GetMetricStatistics`, `cloudwatch:ListMetrics` |
| UI Responsiveness      | Maintained via threading                                                    |
| Error Handling         | All errors shown in the GUI                                                 |

---

### Usage Guide

> **Note:** You do NOT need to deploy this app to AWS. It works locally on your computer. All AWS integration is handled securely via your credentials and internet connection.

1. Launch the application:
   ```bash
   python main.py
   ```
2. Configure simulation parameters:
   - Number of hosts
   - VM specifications
   - Scheduling policy
   - Energy model parameters
3. Start the simulation
4. Monitor results in real-time
5. Export data for analysis

#### Key Parameters
- Host CPU: 2-32 cores
- Host RAM: 8-256 GB
- VM CPU: 1-16 cores
- VM RAM: 1-64 GB
- Simulation duration: 1-24 hours
- Scheduling interval: 1-60 minutes

### Performance Metrics

#### 1. Energy Efficiency
- Power Usage Effectiveness (PUE)
- Energy consumption per VM
- Resource utilization efficiency
- Cooling efficiency
- Carbon footprint

#### 2. Resource Utilization
- CPU utilization
- Memory utilization
- Storage efficiency
- Network bandwidth usage
- Migration overhead

#### 3. Cost Analysis
- Energy costs
- Hardware utilization
- Operational expenses
- Maintenance costs
- ROI calculations

### Future Enhancements

#### Planned Features
1. Advanced Scheduling Algorithms
   - Machine learning-based scheduling
   - Predictive resource allocation
   - Multi-objective optimization
   - Dynamic workload adaptation

2. Enhanced Visualization
   - 3D data center visualization
   - Interactive dashboards
   - Custom report generation
   - Real-time analytics

3. Integration Capabilities
   - Cloud provider APIs
   - Monitoring tools
   - Management systems
   - Reporting platforms

4. Performance Optimizations
   - Parallel processing
   - Distributed simulation
   - GPU acceleration
   - Memory optimization
