
import argparse
import glob
import shutil

def duplicate_frames(input_folder, output_folder, config):

    duplications = config.split(",")

    source_offset = 0
    target_offset = 0

    for duplication in duplications:

        settings = duplication.split(":")
        number = int(settings[0])
        amount = int(settings[1])

        gap_range = range(source_offset, number)

        for i in gap_range:
            source_offset += 1
            target_offset += 1

            source_name = str(source_offset).zfill(3)
            target_name = str(target_offset).zfill(3)

            source_file_name = f"{input_folder}/{source_name}.png"
            target_file_name = f"{output_folder}/{target_name}.png"

            shutil.copy2(source_file_name, target_file_name)

            print(f" ► Copied {source_file_name} -> {target_file_name}")

        for i in range(0, amount):
            target_offset += 1

            source_name = str(source_offset).zfill(3)
            target_name = str(target_offset).zfill(3)

            source_file_name = f"{input_folder}/{source_name}.png"
            target_file_name = f"{output_folder}/{target_name}.png"

            shutil.copy2(source_file_name, target_file_name)

            print(f" ► Duplicated {source_file_name} -> {target_file_name}")
