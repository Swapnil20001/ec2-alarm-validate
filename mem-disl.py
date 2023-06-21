import boto3
import json
import pandas

# Initialize Boto3 clients
region_name = "ap-south-1"
ec2_client = boto3.client('ec2', region_name=region_name)
cloudwatch_client = boto3.client('cloudwatch', region_name=region_name)

def get_instance_alarms(instance_id, metric_name, namespaces):
    alarms = []
    for namespace in namespaces:
        response = cloudwatch_client.describe_alarms_for_metric(
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            MetricName=metric_name,
            Namespace=namespace
        )
        for alarm in response['MetricAlarms']:
            alarmname = alarm['AlarmName']
            alarmconfig = True
            validation = 'fail'
            if alarm['Threshold'] == 70 or alarm['Threshold'] == 75:
                reason = "Threshold not matched"
            elif alarm['EvaluationPeriods'] == 2:
                reason = 'Datapoint not matched'
            elif alarm['Period'] == 300:
                reason = 'period not matched'
            else:
                reason = 'notconfigured'
            
            # Check if alarm threshold is 70 or above
            if alarm['Threshold'] == 70 or alarm['Threshold'] == 75:
                # Check if alarm has 2 datapoints and period is 300 seconds (5 minutes)
                if alarm['EvaluationPeriods'] == 2 and alarm['Period'] == 300:
                    validation = 'pass'
                    reason = 'Success'
            
            alarms.append({
                'alarmname': alarmname,
                'alarmconfig': alarmconfig,
                'Validation': validation,
                'Reason': reason
            })
    return alarms

# Get list of instances
response = ec2_client.describe_instances()
instances = response['Reservations']

# Namespaces to check for Memory and Disk utilization alarms
namespaces_memory = ['CWAgent']
namespaces_disk = ['CWAgent']

# Generate JSON document
result = {}
for reservation in instances:
    for instance in reservation['Instances']:
        instance_id = instance['InstanceId']
        alarms_cpu = get_instance_alarms(instance_id, 'CPUUtilization', ['AWS/EC2'])
        alarms_memory = get_instance_alarms(instance_id, 'mem_used_percent', namespaces_memory)
        alarms_disk = get_instance_alarms(instance_id, 'disk_used_percent', namespaces_disk) 
        
        result[instance_id] = {
            'CPU': alarms_cpu,
            'Memory': alarms_memory,
            'Disk': alarms_disk
        }

# Print the JSON document
print(json.dumps(result, indent=4))

