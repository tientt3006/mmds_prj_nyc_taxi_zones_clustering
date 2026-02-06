import pandas as pd
import glob
import time
import sys
import gc
import os

folder_path = "../yellow_tripdata"
# (lấy 1, 3, 5 file hoặc None để lấy tất cả)
limit_files = 2
seconds_to_sleep = 5

all_files = glob.glob(os.path.join(folder_path, "*.parquet"))

files_to_load = all_files[:limit_files] if limit_files else all_files

dfs = []

try:
    if not files_to_load:
        print(f"Không tìm thấy file nào trong thư mục: {folder_path}")
    else:
        print(f"Tiến hành nạp {len(files_to_load)} file.")

        for i, f in enumerate(files_to_load):
            df_temp = pd.read_parquet(f)
            dfs.append(df_temp)
            
            mem_usage = sys.getsizeof(df_temp) / (1024**2)
            print(f"[{i+1}/{len(files_to_load)}] Nạp file: {os.path.basename(f)}")
            print(f"   -> RAM chiếm dụng: {mem_usage:.2f} MB")
            
            # Tạm dừng để quan sát
            time.sleep(seconds_to_sleep)

        print("\n--- Đang thực hiện gộp dữ liệu (pd.concat) ---")
        df_final = pd.concat(dfs, ignore_index=True)
        df_final.to_parquet("all.parquet")
        
        print("Hoàn tất! Cấu trúc dữ liệu sau khi nạp:")
        print(df_final.info())
        print("\n5 dòng dữ liệu đầu tiên:")
        print(df_final.head())

except MemoryError:
    print("\nLỖI: Tràn bộ nhớ RAM. Hãy giảm 'limit_files' xuống.")
    del dfs
    gc.collect()
except Exception as e:
    print(f"\nĐã xảy ra lỗi: {e}")