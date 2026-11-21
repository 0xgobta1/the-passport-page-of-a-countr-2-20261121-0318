# main.py — the-passport-page-of-a-countr-2-20261121-0318 entry: the image
# is entry.png beside this file, drawn by draw.py in this session (an open
# passport spread for the invented Republic of Auroria). The program just
# copies it to the output dir.
# Runs twice in the grader sandbox with no network; both runs write the
# same bytes because the image is a fixed file in the repo.
#
# Local test: mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
import os
import shutil

out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
os.makedirs(out, exist_ok=True)
here = os.path.dirname(os.path.abspath(__file__))
shutil.copyfile(os.path.join(here, "entry.png"),
                os.path.join(out, "entry.png"))
