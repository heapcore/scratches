import os
import subprocess
from pathlib import Path


def main(work_dir=None, files_list=None):
    if work_dir:
        os.chdir(work_dir)

    if not files_list:
        os.chdir(work_dir)
        files_list = []

        for path, subdirs, files in os.walk(work_dir):
            for name in files:
                if not name.endswith(".mkv"):
                    files_list.append((os.path.join(path, name), None, None))

    is_sample = False
    for filename_full, size, crf in files_list:
        filename, ext = filename_full.rsplit(".", 1)

        my_file = Path(f"{filename}.mkv")
        if my_file.exists():
            continue

        cmd = ["ffmpeg", "-i", filename_full]
        if size == "1/2":
            cmd.extend(["-vf", "scale=trunc(iw/4)*2:trunc(ih/4)*2"])
        if size == "1/4":
            cmd.extend(["-vf", "scale=trunc(iw/8)*2:trunc(ih/8)*2"])
        elif size == "2/3":
            cmd.extend(["-vf", "scale=trunc(iw/3)*2:trunc(ih/3)*2"])

        if is_sample:
            cmd.extend(["-ss", "00:03:00", "-to", "00:04:00"])

        if not crf:
            crf = "28"

        cmd.extend(["-c:v", "libx265", "-crf", crf, f"{filename}.mkv"])
        subprocess.call(cmd)


if __name__ == "__main__":
    main(
        work_dir=r"D:\Videos",
        files_list=[
            ("D:\Videos\Test.mp4", "1/2", "20"),
        ],
    )
