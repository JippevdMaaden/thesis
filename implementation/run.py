from base_implementation import MethodBase
from base_filesystem import merge_by_level

if __init__ == '__name__':
    path_to_dir = 'lasfiles/'

    file_list = merge_by_level(path_to_dir)
    file_dir = {x:x for x in file_list}

    # standard params from speck.ly example querry. Should be user input with click
    camera_parameters = (85000.00, 443750.00, 41.63)

    implementation = MethodBase(camera_parameters, file_dir)

    density_dict = implementation.determine_density()
    densjump_dict = implementation.determine_gradual_descent_formula(density_dict)

    # merge all files to out.las for base_method to work






    # clear lasfiles/
    os.system('rm -rf lasfiles')
    os.system('mkdir lasfiles')
