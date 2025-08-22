import os, sys
import pandas as pd
from src.interface import user_interface as ui
from src.constants import CSV
from src.preprocessing import base_preprocess_datetime
import src.preprocessing as prepro
from src.data_loader import load_external_clean_or_build
import src.stats as stats

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
if os.name == 'nt':
    os.system('chcp 65001 > nul')


df_original = pd.read_csv('data/processed/first_1000_rows.csv')
# df_processed = prepro.object_columns_to_category(df_original, columns=['City'])
df_processed = prepro.parse_dates(df_original)


def load_full() -> pd.DataFrame:
    df = pd.read_csv(CSV, nrows= 1000000)
    df = base_preprocess_datetime(df)
    return df


def main(df: pd.DataFrame):
    # print(df_processed.info())
    # print(df_processed['City'].head())
    # ui.press_to_continue()
    ui.enable_utf8()
    ui.clear()
    ui.print_logo_centered(ui.PROGRAM_LOGO)
    ui.main_menu(df)

if __name__ == "__main__":
    try:
        try:
            # df = df_original
            df = load_external_clean_or_build()
        except FileNotFoundError as e:
            print(str(e))
            sys.exit(1)
        main(df)
    except (KeyboardInterrupt, EOFError):
        print('\nBye!')
        sys.exit(0)
