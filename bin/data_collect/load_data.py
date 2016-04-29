import commands
import os
import sys


def get_folder_path():
    usage_message = "Usage: {} [folder_path]".format(sys.argv[0])

    if len(sys.argv) < 2:
        print usage_message
        exit(1)

    folder_path = sys.argv[1]
    folder_path = os.path.expanduser(folder_path)
    if not folder_path.endswith('/'):
        folder_path += '/'

    if not os.path.exists(folder_path):
        print usage_message
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


def get_csv_file_path():
    usage_message = "Usage: {} [csv_file_path]".format(sys.argv[0])

    if len(sys.argv) < 2:
        print usage_message
        exit(1)

    csv_file_path = sys.argv[1]
    csv_file_path = os.path.expanduser(csv_file_path)

    if not os.path.exists(csv_file_path):
        print usage_message
        print "CSV file not exists"
        exit(1)

    return csv_file_path

def get_lines_from_csv_file(csv_file_path):
    with open(csv_file_path, 'rb') as text:
        lines = [line.strip() for line in text]
    lines = [line.split(';') for line in lines]

    return lines
