import os

def merge_by_level(path_to_directory):
    dir_list = os.listdir(path_to_directory)
    file_dir = {}
    depthlist = []
    for file in dir_list:
        split_file = file.split(' ')
        file_dir['depthBegin'] = split_file[0]
        file_dir['depthEnd'] = split_file[1]
        file_dir['filename'] = file
        if dir_list['depthBegin'] not in depthlist:
            depthlist.append(dir_list['depthBegin']
    file_name_list = []
    for begindepth in depthlist:
        merge_string = 'lasmerge -i '
        file_name = path_to_directory + begindepth + '.las'
        for file in file_dir:
            if file['depthBegin'] == begindepth:
                merge_string += path_to_directory
                merge_string += file['filename']
                merge_string += ' '
        file_name_list.append(file_name)
        merge_string += '-o '
        merge_string += path_to_directory
        merge_string += file_name
        os.system(merge_string)

    return file_name_list

def merge_all(path_to_directory):
    dir_list = os.listdir(path_to_directory)
    merge_string = 'lasmerge -i '
    file_name = path_to_diirectory + 'all.las'

    for file in dir_list:
	merge_string += path_to_directory
	merge_string += file
	merge_string += ' '

    merge_string += '-o '
    merge_string += path_to_directory
    merge_string += file_name
    os.system(merge_string)

    return file_name
