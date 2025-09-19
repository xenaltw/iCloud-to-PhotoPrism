#!/usr/bin/python3

import os
import shutil
import heapq
import subprocess
from pathlib import Path
import datetime


def get_files(source_dir):
    for dirpath, dirnames, filenames in os.walk(source_dir):
        for name in filenames:
            yield os.path.join(dirpath, name)


def move_files(source_dir, dest_dir):
    # create destination directory if it does not exist
    Path(dest_dir).mkdir(parents=True, exist_ok=True)

    # get all files
    files = list(get_files(source_dir))

    # get the creation time of all files and select the 5 with the most recent creation time
    recent_files = heapq.nlargest(5, files, key=lambda f: os.path.getmtime(f))

    # move all directories and files
    for dirpath, dirnames, filenames in os.walk(source_dir):
       dest_path = os.path.join(dest_dir, os.path.relpath(dirpath, source_dir))
       os.makedirs(dest_path, exist_ok=True)

       for filename in filenames:

           file_path = os.path.join(dirpath, filename)
           destination_file_path = os.path.join(dest_path, filename)

           # skip files that should not be moved
           if filename == '.mounted':  
               continue
           if file_path in recent_files:
               continue
           if os.path.exists(destination_file_path):
               continue

           shutil.move(file_path, dest_path)
           print(f'moved {file_path}')

    # copy most recent files preserving directory structure
    for file in recent_files:
        dest_path = os.path.join(dest_dir, os.path.relpath(os.path.dirname(file), source_dir))
        shutil.copy2(file, dest_path)  # copy2 preserves metadata
        print(f'copied {file}')

    # remove empty directories
    for dirpath, dirnames, filenames in os.walk(source_dir, topdown=False):
        if dirpath == source_dir:
            continue
        if os.listdir(dirpath):
            continue
        os.rmdir(dirpath)


def import_to_photoprism(container):
    print('starting photoprism import')
    cmd = ['docker', 'exec', container, 'photoprism', 'import']
    subprocess.run(cmd, check=True)


def main():
    # Edit the username
    user = "user"
	# Edit these paths
    storage_directory = f"/mnt/data/{user}/Pictures"
    source_directory = f"/mnt/data/{user}/.icloud"
    dest_directory = f"/mnt/.ix-apps/app_mounts/photoprism-{user}/import"

    move_files(source_directory, dest_directory)
    

    photoprism_container = f"ix-photoprism-{user}-photoprism-1"
    import_to_photoprism(photoprism_container)
    print('finished importing files to Photoprism')
    files = os.popen(f"find {storage_directory} ! -user \"{user}\" -printf \"%p\n\"").read().splitlines()
    print('finished moving all files')
    for file in files:
        os.system(f"chown {user}:{user} {file}")
    print(f"change the owner of files to {user}")
 

if __name__ == '__main__':
    main()

