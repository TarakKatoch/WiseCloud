import boto3
from datetime import datetime, timedelta
import logging

def fetch_ec2_metrics(instance_ids, region='us-east-1', access_key_id=None, secret_access_key=None):
    """
    Fetch EC2 metrics from AWS CloudWatch for the specified instance IDs.
    
    Args:
        instance_ids (list): List of EC2 instance IDs to fetch metrics for
        region (str): AWS region (default: us-east-1)
        access_key_id (str): AWS access key ID (optional, uses default credentials if None)
        secret_access_key (str): AWS secret access key (optional, uses default credentials if None)
    
    Returns:
        list: List of dictionaries with 'cpu', 'ram', and 'duration' keys for each instance
    """
    try:
        # Configure AWS credentials if provided
        if access_key_id and secret_access_key:
            cloudwatch = boto3.client(
                'cloudwatch',
                region_name=region,
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key
            )
        else:
            # Use default credentials
            cloudwatch = boto3.client('cloudwatch', region_name=region)
        
        # Calculate time range (last 15 minutes)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=15)
        
        vm_data = []
        
        for instance_id in instance_ids:
            try:
                # Get CPU utilization metric
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    Dimensions=[
                        {
                            'Name': 'InstanceId',
                            'Value': instance_id
                        }
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,  # 5-minute intervals
                    Statistics=['Average']
                )
                
                # Calculate average CPU utilization
                if response['Datapoints']:
                    cpu_values = [point['Average'] for point in response['Datapoints']]
                    avg_cpu = sum(cpu_values) / len(cpu_values)
                else:
                    avg_cpu = 0.0
                
                # Create VM data dictionary
                # For VM scheduling, we need CPU cores, not utilization percentage
                # AWS instances typically have 1-32 cores, so we'll estimate based on instance type
                # For now, we'll use a reasonable default and store utilization separately
                estimated_cpu_cores = max(1, round(avg_cpu / 10))  # Rough estimate: 10% utilization = 1 core
                
                vm_info = {
                    'cpu': estimated_cpu_cores,  # CPU cores (not percentage)
                    'cpu_utilization': avg_cpu,  # Store actual utilization percentage
                    'ram': 8.0,  # Default RAM in GB
                    'duration': 15.0,  # Default duration in minutes
                    'instance_id': instance_id
                }
                
                vm_data.append(vm_info)
                logging.info(f"Successfully fetched metrics for instance {instance_id}: CPU={avg_cpu:.2f}%")
                
            except Exception as e:
                logging.error(f"Error fetching metrics for instance {instance_id}: {str(e)}")
                # Add default data for failed instances
                vm_data.append({
                    'cpu': 1,  # Default to 1 CPU core
                    'cpu_utilization': 0.0,  # Default utilization
                    'ram': 8.0,
                    'duration': 15.0,
                    'instance_id': instance_id,
                    'error': str(e)
                })
        
        return vm_data
        
    except Exception as e:
        logging.error(f"Error connecting to AWS CloudWatch: {str(e)}")
        return []

def validate_aws_credentials(access_key_id, secret_access_key, region='us-east-1'):
    """
    Validate AWS credentials by attempting to list EC2 instances.
    
    Args:
        access_key_id (str): AWS access key ID
        secret_access_key (str): AWS secret access key
        region (str): AWS region
    
    Returns:
        tuple: (bool, str) - (is_valid, error_message)
    """
    try:
        ec2 = boto3.client(
            'ec2',
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key
        )
        
        # Try to describe instances (this will fail if credentials are invalid)
        ec2.describe_instances(MaxResults=5)
        return True, "Credentials are valid"
        
    except Exception as e:
        return False, f"Invalid credentials: {str(e)}"

def get_available_instances(access_key_id, secret_access_key, region='us-east-1'):
    """
    Get list of available EC2 instances in the specified region.
    
    Args:
        access_key_id (str): AWS access key ID
        secret_access_key (str): AWS secret access key
        region (str): AWS region
    
    Returns:
        list: List of instance IDs
    """
    try:
        ec2 = boto3.client(
            'ec2',
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key
        )
        
        response = ec2.describe_instances(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': ['running', 'stopped']
                }
            ]
        )
        
        instance_ids = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_ids.append(instance['InstanceId'])
        
        return instance_ids
        
    except Exception as e:
        logging.error(f"Error getting available instances: {str(e)}")
        return [] 