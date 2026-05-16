import os
from pathlib import Path

# File paths
ROOT_PATH = str(Path(__file__).resolve().parent.parent)
SRC_PATH = str(Path(__file__).resolve().parent)
CSV = ROOT_PATH + r'/data/raw/US_Accidents_March23.csv'
SAMPLE_CSV = ROOT_PATH + r'/data/processed/first_1000_rows.csv'
# CSV = r"D:\dataset\US_Accidents_March23.csv"
# CSV_TEST = r'data/processed/first_1000_rows.csv'
# CSV = CSV_TEST


PARENT_PATH = str(Path(ROOT_PATH).parent)

EXTERNAL_RAW_DIR       = os.path.join(PARENT_PATH, "dataset")
EXTERNAL_RAW_CSV       = os.path.join(EXTERNAL_RAW_DIR, "US_Accidents_March23.csv")

EXTERNAL_PROCESSED_DIR = os.path.join(PARENT_PATH, "accidents_clean")
EXTERNAL_CLEAN_CSV     = os.path.join(EXTERNAL_PROCESSED_DIR, "US_Accidents_March23_clean.csv")
# Other consts
NUM_ROWS = 5    # default number of rows shown in menu reports
EXIT_COMMANDS = (
    "break",
    "bye",
    "close",
    "close app",
    "end",
    "end program",
    "exit",
    "exit program",
    "goodbye",
    "halt",
    "i want to quit",
    "i'm done",
    "kill",
    "kill program",
    "let me out",
    "quit",
    "quit program",
    "see you",
    "shut down",
    "stop",
    "stop program",
    "terminate",
    "terminate program",
    "that's it"
)

USER_INPUT_FORM = "\n>> "


