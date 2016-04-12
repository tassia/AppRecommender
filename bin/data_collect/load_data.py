import commands
import os
import sys


def get_folder_path():
    if len(sys.argv) < 2:
        print "Usage: load_user_data.py [folder_path]"
        exit(1)

    folder_path = sys.argv[1]
    folder_path = os.path.expanduser(folder_path)
    if not folder_path.endswith('/'):
        folder_path += '/'

    if not os.path.exists(folder_path):
        print "Usage: load_user_data.py [folder_path]"
        print "Folder not exists"
        exit(1)

    return folder_path


def get_all_folders_path(folder_path):
    folders_path = commands.getoutput("ls {}".format(folder_path)).splitlines()
    folders_path = [folder for folder in folders_path
                    if folder.startswith('app_recommender_log')]
    folders_path = ["{}{}/".format(folder_path, folder)
                    for folder in folders_path]

    return folders_path
