# Energy-Efficient VM Scheduler Simulator

This project simulates an energy-efficient virtual machine scheduler that uses the Best-Fit Decreasing algorithm to allocate VMs to physical hosts while minimizing energy consumption.

## Features

- GUI-based simulation interface
- Best-Fit Decreasing scheduling algorithm
- Energy consumption calculation and visualization
- Random VM generation with varying CPU and RAM requirements
- Real-time energy consumption monitoring

## Requirements

- Python 3.8 or higher
- Tkinter (usually comes with Python)
- Matplotlib

## Installation

1. Clone this repository or download the source code
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the main application:
   ```
   python main.py
   ```
2. Enter the number of hosts and VMs in the GUI
3. Click "Run Simulation" to start the simulation
4. View the results in the text window and the energy consumption chart

## Project Structure

- `main.py`: Main application with GUI
- `models.py`: Host and VM class definitions
- `scheduler.py`: Scheduling algorithms
- `energy_model.py`: Energy consumption calculations

## Future Improvements

- Add more scheduling policies
- Allow customization of host and VM specifications
- Implement VM migration simulation
- Add support for real-world datasets
- Export reports and graphs 