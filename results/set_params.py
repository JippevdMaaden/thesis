"""
Contains the parameters for the method, should be converted to click if there is time.
"""


def get_global_param_dict():
    global_param_dict = {
        'camera_url': 'http://speck.ly/?s=ec2-18-185-97-202.eu-central-1.compute.amazonaws.com%3A8080%2F&r=municipality-delft&ca=15.959&ce=34.245&ct=85000%2C443750%2C41.635&cd=1348.159&cmd=20001.589&ps=2&pa=0.1&ze=1&c0s=local%3A%2F%2Framp%3Ffield%3DZ%26start%3D%23FFFFFF%26end%3D%230000FF',
        'potree_file': 'POTREE_reads.txt',
        'var_linear': 0.0025,
        'var_exponential': 0.525,
        'var_logarithmic': 1.015,
    }
    return global_param_dict
