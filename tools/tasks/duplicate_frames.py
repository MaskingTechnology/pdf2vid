
from ..utils.filesystem import join_paths, copy_file, path_exists

def duplicate_frames(input_folder, output_folder, config):

    if not config or not config.strip():
        return

    duplications = _parse_duplications(config)

    source_offset = 0
    target_offset = 0

    for number, amount in duplications:

        gap_range = range(source_offset, number)

        for _ in gap_range:

            source_offset += 1
            target_offset += 1

            _copy_frame(input_folder, output_folder, str(source_offset).zfill(3), str(target_offset).zfill(3))

        for _ in range(0, amount):

            target_offset += 1

            _copy_frame(input_folder, output_folder, str(source_offset).zfill(3), str(target_offset).zfill(3))

def _parse_duplications(config):

    duplications = []

    for entry in config.split(","):

        settings = entry.split(":")

        if len(settings) != 2:
            raise RuntimeError(f"Invalid duplications entry {entry!r} — expected frame_number:amount")

        try:
            number = int(settings[0].strip())
            amount = int(settings[1].strip())
        except ValueError:
            raise RuntimeError(f"Invalid duplications entry {entry!r} — expected frame_number:amount")

        duplications.append((number, amount))

    return sorted(duplications, key = lambda item: item[0])

def _copy_frame(input_folder, output_folder, source_name, target_name):

    source_file_name = join_paths(input_folder, f"{source_name}.png")
    target_file_name = join_paths(output_folder, f"{target_name}.png")

    if not path_exists(source_file_name):
        raise RuntimeError(f"Frame {source_name} does not exist in {input_folder}!")

    copy_file(source_file_name, target_file_name)
