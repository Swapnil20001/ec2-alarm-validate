import boto3
import json
import pandas as pd
from validation_scenarios import validation_scenarios  # to get input as file


# Initialize Boto3 clients
region_name = "ap-south-1"
ec2_client = boto3.client('ec2', region_name=region_name)
paginator = ec2_client.get_paginator('describe_instances')

cloudwatch_client = boto3.client('cloudwatch', region_name=region_name)

# Function to retrieve alarms for a given instance ID, metric name, and namespace
def get_instance_alarms(instance_id, metric_name, namespace, validation_scenarios):
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
            'alarmconfig': False,
            'Validation': 'fail',
            'Reason': 'alarm not configured'
        })
    else:
        for alarm in response['MetricAlarms']:
            alarmname = alarm['AlarmName']
            alarmconfig = True
            validation = 'fail'
            reason = ''

            # Check if alarm matches any of the validation scenarios
            for scenario in validation_scenarios:
                if scenario['metric'] == metric_name:
                    for metric_scenario in scenario['metrics']:
                        threshold = metric_scenario['threshold']
                        datapoint = metric_scenario['datapoint']
                        period = metric_scenario['period']

                        # Check if alarm threshold, datapoint, and period match the scenario
                        if alarm['Threshold'] == threshold and alarm['EvaluationPeriods'] == datapoint and alarm['Period'] == period:
                            validation = 'pass'
                            reason = 'Success'
                            break
                        elif alarm['Threshold'] != threshold and alarm['EvaluationPeriods'] != datapoint:
                            reason = 'Threshold and Datapoint not matched'
                        elif alarm['Threshold'] != threshold:
                            reason = 'Threshold not matched'
                        elif alarm['EvaluationPeriods'] != datapoint:
                            reason = 'Datapoint not matched'

                        if validation == 'pass':
                            break

            alarms.append({
                'alarmname': alarmname,
                'alarmconfig': alarmconfig,
                'Validation': validation,
                'Reason': reason,
                'Threshold': threshold,
                'Datapoint': datapoint,
                'Period': period,
                'Alarm_Threshold': alarm['Threshold'],
                'Alarm_Datapoint': alarm['EvaluationPeriods'],
                'Alarm_Period': alarm['Period']
            })
    return alarms

# Get list of instances
response = paginator.paginate().build_full_result()
instances = response['Reservations']

# Generate JSON document
result = {}
for reservation in instances:
    for instance in reservation['Instances']:
        instance_id = instance['InstanceId']
        alarms_cpu = get_instance_alarms(instance_id, 'CPUUtilization', 'AWS/EC2', validation_scenarios)
        alarms_memory = get_instance_alarms(instance_id, 'mem_used_percent', 'CWAgent', validation_scenarios)
        alarms_disk = get_instance_alarms(instance_id, 'disk_used_percent', 'CWAgent', validation_scenarios)

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


# Convert JSON to DataFrame
json_data = json.loads(json_data_str)
data = []
for instance_id, metrics in json_data.items():
    for metric, alarms in metrics.items():
        for alarm in alarms:
            data.append({
                "Instance ID": instance_id,
                "Metric": metric,
                "Alarm Name": alarm["alarmname"],
                "Alarm_Configured": alarm["alarmconfig"],
                "Validation": alarm["Validation"],
                "Reason": alarm["Reason"]
            })
df = pd.DataFrame(data)
df['Alarm_Configured'] = df['Alarm_Configured'].map({False: 'No', True: 'Yes'})
df.to_excel("alarm_for_instance.xlsx", index=False)
print("Excel for alarm validation created successfully")
