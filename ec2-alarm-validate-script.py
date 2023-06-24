import boto3
import json
import pandas as pd


# Initialize Boto3 clients
region_name = "ap-south-1"
ec2_client = boto3.client('ec2', region_name=region_name)
paginator = ec2_client.get_paginator('describe_instances')

cloudwatch_client = boto3.client('cloudwatch', region_name=region_name)

# Function to retrieve alarms for a given instance ID, metric name, and namespace
def get_instance_alarms(instance_id, metric_name, namespace, threshold1, threshold2):
    alarms = []
    response = cloudwatch_client.describe_alarms_for_metric(
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        MetricName=metric_name,
        Namespace=namespace
    )

    if not response['MetricAlarms']:
        # Alarm not configured for the metric
        alarms.append({
            'alarmname': None,
            # 'alarmconfig': False, # it will give blank space in alarm section.
            'alarmconfig': 'No',
            'Validation': 'fail',
            'Reason': 'alarm not configured'
        })
    else:
        for alarm in response['MetricAlarms']:
            alarmname = alarm['AlarmName']
            alarmconfig = True
            validation = 'fail'
            reason = 'notconfigured'

            # Check if alarm threshold matches the specified thresholds
            if alarm['Threshold'] == threshold1 or alarm['Threshold'] == threshold2:
                # Check if alarm has 2 datapoints and period is 300 seconds (5 minutes)
                if alarm['EvaluationPeriods'] == 2 and alarm['Period'] == 300:
                    validation = 'pass'
                    reason = 'Success'
                else:
                    reason = 'Datapoint not matched'
            else:
                reason = 'Threshold not matched'

            alarms.append({
                'alarmname': alarmname,
                'alarmconfig': alarmconfig,
                'Validation': validation,
                'Reason': reason
            })
    return alarms

# Get list of instances
response = paginator.paginate().build_full_result()
instances = response['Reservations']

# print(response)

# Specify thresholds for CPU, disk, and memory
cpu_threshold1 = 75
cpu_threshold2 = 70
memory_threshold1 = 70
memory_threshold2 = 80
disk_threshold1 = 60
disk_threshold2 = 75

# Namespaces to check for alarms
namespaces_cpu = ['AWS/EC2']
namespaces_memory = ['CWAgent']
namespaces_disk = ['CWAgent']

# Generate JSON document
result = {}
for reservation in instances:
    for instance in reservation['Instances']:
        instance_id = instance['InstanceId']
        alarms_cpu = []
        for namespace in namespaces_cpu:
            alarms_cpu += get_instance_alarms(instance_id, 'CPUUtilization', namespace, cpu_threshold1, cpu_threshold2)
        alarms_memory = []
        for namespace in namespaces_memory:
            alarms_memory += get_instance_alarms(instance_id, 'mem_used_percent', namespace, memory_threshold1, memory_threshold2)
        alarms_disk = []
        for namespace in namespaces_disk:
            alarms_disk += get_instance_alarms(instance_id, 'disk_used_percent', namespace, disk_threshold1, disk_threshold2)

        result[instance_id] = {
            'CPU': alarms_cpu or [{
                'alarmname': None,
                'alarmconfig': False,
                'Validation': 'fail',
                'Reason': 'alarm not configured'
            }],
            'Memory': alarms_memory or [{
                'alarmname': None,
                'alarmconfig': False,
                'Validation': 'fail',
                'Reason': 'alarm not configured'
            }],
            'Disk': alarms_disk or [{
                'alarmname': None,
                'alarmconfig': False,
                'Validation': 'fail',
                'Reason': 'alarm not configured'
            }]
        }

# Print the JSON document
json_data_str = json.dumps(result, indent=4)
print(json_data_str)
json_data = json.loads(json_data_str)
# print(json_data)
# print(type(json_data))
data = []
for instance_id, metrics in json_data.items():
    for metric, alarms in metrics.items():
        for alarm in alarms:
            # alarm_configured = "Yes" if alarm["alarmconfig"] else "No"
            data.append({
                "Instance ID": instance_id,
                "Metric": metric,
                "Alarm Name": alarm["alarmname"] or 'No',
                "Alarm_Configured": alarm["alarmconfig"],
                # "Alarm_Configured": alarm_configured,
                "Validation": alarm["Validation"],
                "Reason": alarm["Reason"]
            })
df = pd.DataFrame(data)
df['Alarm_Configured'] = df['Alarm_Configured'].map({ 'No': 'No', 1: 'Yes'}) # Map 1 to "Yes"
df.to_excel("alarm_for_instance.xlsx", index=False)
print("excel for alarm validation created successfully")
