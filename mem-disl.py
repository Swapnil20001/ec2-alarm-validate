import boto3
import json

# Initialize Boto3 clients
region_name = "ap-south-1"
ec2_client = boto3.client('ec2', region_name=region_name)
cloudwatch_client = boto3.client('cloudwatch', region_name=region_name)

# Function to retrieve alarms for a given instance ID, metric name, and namespace
def get_instance_alarms(instance_id, metric_name, namespace):
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
            alarms_cpu += get_instance_alarms(instance_id, 'CPUUtilization', namespace)
        alarms_memory = []
        for namespace in namespaces_memory:
            alarms_memory += get_instance_alarms(instance_id, 'mem_used_percent', namespace)
        alarms_disk = []
        for namespace in namespaces_disk:
            alarms_disk += get_instance_alarms(instance_id, 'disk_used_percent', namespace)

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
print(json.dumps(result, indent=4))
