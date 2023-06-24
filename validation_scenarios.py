validation_scenarios = [
    {'metric': 'CPUUtilization', 'metrics': [{'threshold': 70.0, 'datapoint': 3, 'period': 300}, {'threshold': 75.0, 'datapoint': 2, 'period': 300},{'threshold': 70.0, 'datapoint': 2, 'period': 300}]},
    {'metric': 'mem_used_percent', 'metrics': [{'threshold': 70.0, 'datapoint': 2, 'period': 300}]},
    {'metric': 'disk_used_percent', 'metrics': [{'threshold': 70.0, 'datapoint': 2, 'period': 300}, {'threshold': 75.0, 'datapoint': 3, 'period': 300}]}
]