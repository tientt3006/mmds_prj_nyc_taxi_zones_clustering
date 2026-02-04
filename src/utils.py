"""
Utility functions cho NYC Taxi Graph Mining Project
"""

import os
import time
from datetime import datetime
from functools import wraps


def timer(func):
    """Decorator để đo thời gian thực thi"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        print(f"\n{'='*60}")
        print(f"🚀 Bắt đầu: {func.__name__}")
        print(f"⏰ Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        duration = end_time - start_time
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        print(f"\n{'='*60}")
        print(f"✅ Hoàn thành: {func.__name__}")
        print(f"⏱️  Thời gian: {int(hours)}h {int(minutes)}m {seconds:.2f}s")
        print(f"{'='*60}\n")
        
        return result
    return wrapper


def ensure_dir(directory):
    """Tạo thư mục nếu chưa tồn tại"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"📁 Đã tạo thư mục: {directory}")


def print_section(title):
    """In header đẹp cho từng section"""
    print(f"\n{'#'*70}")
    print(f"# {title:^66} #")
    print(f"{'#'*70}\n")


def save_dataframe_as_csv(df, output_path, num_partitions=1):
    """
    Lưu Spark DataFrame thành CSV
    
    Args:
        df: Spark DataFrame
        output_path: Đường dẫn output
        num_partitions: Số partitions (1 = single file)
    """
    print(f"💾 Đang lưu kết quả vào: {output_path}")
    
    df.coalesce(num_partitions) \
        .write \
        .mode("overwrite") \
        .option("header", "true") \
        .csv(output_path)
    
    print(f"✅ Đã lưu thành công!")


def print_dataframe_stats(df, name="DataFrame"):
    """In thống kê cơ bản về DataFrame"""
    print(f"\n📊 Thống kê {name}:")
    print(f"   - Số dòng: {df.count():,}")
    print(f"   - Số cột: {len(df.columns)}")
    print(f"   - Columns: {', '.join(df.columns)}")
    

def format_large_number(num):
    """Format số lớn dễ đọc"""
    if num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num/1_000:.2f}K"
    else:
        return str(num)


def get_hdfs_file_list(spark, hdfs_path):
    """
    Lấy danh sách files trong HDFS directory
    
    Args:
        spark: SparkSession
        hdfs_path: HDFS path
        
    Returns:
        List of file paths
    """
    hadoop = spark._jvm.org.apache.hadoop
    fs = hadoop.fs.FileSystem.get(spark._jsc.hadoopConfiguration())
    path = hadoop.fs.Path(hdfs_path)
    
    if not fs.exists(path):
        print(f"⚠️  Path không tồn tại: {hdfs_path}")
        return []
    
    files = []
    file_iterator = fs.listStatus(path)
    
    for file_status in file_iterator:
        file_path = file_status.getPath().toString()
        if not file_path.endswith('/'):
            files.append(file_path)
    
    return files


def show_progress(current, total, prefix='Progress'):
    """
    Hiển thị thanh progress
    
    Args:
        current: Số hiện tại
        total: Tổng số
        prefix: Text prefix
    """
    percent = 100 * (current / float(total))
    filled = int(50 * current // total)
    bar = '█' * filled + '-' * (50 - filled)
    print(f'\r{prefix}: |{bar}| {percent:.1f}% ({current}/{total})', end='')
    if current == total:
        print()


def memory_usage_info():
    """In thông tin RAM usage (nếu có psutil)"""
    try:
        import psutil
        mem = psutil.virtual_memory()
        print(f"\n💾 Memory Usage:")
        print(f"   - Total: {mem.total / (1024**3):.2f} GB")
        print(f"   - Available: {mem.available / (1024**3):.2f} GB")
        print(f"   - Used: {mem.used / (1024**3):.2f} GB ({mem.percent}%)")
    except ImportError:
        print("⚠️  psutil không được cài đặt. Không thể xem memory info.")


class ProgressLogger:
    """Class để log progress cho các job dài"""
    
    def __init__(self, total_steps, job_name="Job"):
        self.total_steps = total_steps
        self.current_step = 0
        self.job_name = job_name
        self.start_time = time.time()
    
    def update(self, step_name):
        """Update progress"""
        self.current_step += 1
        elapsed = time.time() - self.start_time
        percent = 100 * self.current_step / self.total_steps
        
        print(f"\n[{self.job_name}] Step {self.current_step}/{self.total_steps} ({percent:.1f}%)")
        print(f"  ▶ {step_name}")
        print(f"  ⏱️  Elapsed: {elapsed:.1f}s")
        
        if self.current_step < self.total_steps:
            eta = (elapsed / self.current_step) * (self.total_steps - self.current_step)
            print(f"  ⏳ ETA: {eta:.1f}s")
    
    def finish(self):
        """Kết thúc progress"""
        total_time = time.time() - self.start_time
        print(f"\n✅ {self.job_name} hoàn thành trong {total_time:.1f}s")
