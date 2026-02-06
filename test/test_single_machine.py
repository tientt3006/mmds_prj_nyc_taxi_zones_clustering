"""
Test NYC Taxi Graph Mining trên MÁY ĐƠN (Local Mode)
Mục đích: Chứng minh bottleneck khi xử lý massive data trên 1 máy
"""

import time
import psutil
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, desc
import matplotlib.pyplot as plt
import pandas as pd

class SingleMachineTest:
    def __init__(self, data_path, output_dir="results/single_machine"):
        """
        Args:
            data_path: Path to parquet files (local hoặc HDFS)
            output_dir: Thư mục lưu kết quả
        """
        self.data_path = data_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Tạo Spark session với LOCAL MODE (1 máy duy nhất)
        # ⚠️ CHÚ Ý: Không dùng --master spark://master:7077
        self.spark = SparkSession.builder \
            .appName("NYC_Taxi_SingleMachine_Test") \
            .master("local[*]") \
            .config("spark.driver.memory", "2g") \
            .config("spark.executor.memory", "2g") \
            .config("spark.sql.shuffle.partitions", "200") \
            .config("spark.default.parallelism", "8") \
            .getOrCreate()
        
        self.metrics = []
    
    def monitor_resources(self):
        """Theo dõi CPU, RAM, Disk"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_used_gb': memory.used / (1024**3),
            'memory_percent': memory.percent,
            'disk_used_gb': disk.used / (1024**3),
            'disk_percent': disk.percent
        }
    
    def test_data_loading(self, num_months=1):
        """Test 1: Load dữ liệu"""
        print(f"\n{'='*60}")
        print(f"TEST 1: Loading {num_months} tháng dữ liệu")
        print(f"{'='*60}")
        
        start_time = time.time()
        start_resources = self.monitor_resources()
        
        try:
            # Đọc dữ liệu (điều chỉnh path theo số tháng)
            df = self.spark.read.parquet(self.data_path)
            
            # Force action để thực sự load data
            total_rows = df.count()
            
            end_time = time.time()
            end_resources = self.monitor_resources()
            
            elapsed_time = end_time - start_time
            
            result = {
                'test': 'data_loading',
                'num_months': num_months,
                'total_rows': total_rows,
                'time_seconds': elapsed_time,
                'cpu_start': start_resources['cpu_percent'],
                'cpu_end': end_resources['cpu_percent'],
                'memory_start_gb': start_resources['memory_used_gb'],
                'memory_end_gb': end_resources['memory_used_gb'],
                'memory_delta_gb': end_resources['memory_used_gb'] - start_resources['memory_used_gb'],
                'status': 'SUCCESS'
            }
            
            print(f"✅ Thành công!")
            print(f"   - Số dòng: {total_rows:,}")
            print(f"   - Thời gian: {elapsed_time:.2f}s")
            print(f"   - RAM sử dụng: {result['memory_delta_gb']:.2f} GB")
            
        except Exception as e:
            result = {
                'test': 'data_loading',
                'num_months': num_months,
                'status': 'FAILED',
                'error': str(e),
                'time_seconds': time.time() - start_time
            }
            print(f"❌ FAILED: {e}")
        
        self.metrics.append(result)
        return result
    
    def test_graph_construction(self, sample_fraction=0.1):
        """Test 2: Xây dựng graph (edge list)"""
        print(f"\n{'='*60}")
        print(f"TEST 2: Graph Construction (sample {sample_fraction*100}%)")
        print(f"{'='*60}")
        
        start_time = time.time()
        start_resources = self.monitor_resources()
        
        try:
            df = self.spark.read.parquet(self.data_path)
            
            # Sample để giảm tải (vẫn có thể crash nếu data quá lớn)
            df_sampled = df.sample(fraction=sample_fraction, seed=42)
            
            # Tạo edge list: (PULocationID -> DOLocationID)
            edges = df_sampled.groupBy("PULocationID", "DOLocationID") \
                .agg(count("*").alias("trip_count")) \
                .filter(col("PULocationID").isNotNull() & col("DOLocationID").isNotNull()) \
                .orderBy(desc("trip_count"))
            
            # Force computation
            num_edges = edges.count()
            
            end_time = time.time()
            end_resources = self.monitor_resources()
            elapsed_time = end_time - start_time
            
            result = {
                'test': 'graph_construction',
                'sample_fraction': sample_fraction,
                'num_edges': num_edges,
                'time_seconds': elapsed_time,
                'memory_delta_gb': end_resources['memory_used_gb'] - start_resources['memory_used_gb'],
                'status': 'SUCCESS'
            }
            
            print(f"✅ Thành công!")
            print(f"   - Số edges: {num_edges:,}")
            print(f"   - Thời gian: {elapsed_time:.2f}s")
            
        except Exception as e:
            result = {
                'test': 'graph_construction',
                'sample_fraction': sample_fraction,
                'status': 'FAILED',
                'error': str(e),
                'time_seconds': time.time() - start_time
            }
            print(f"❌ FAILED: {e}")
        
        self.metrics.append(result)
        return result
    
    def test_pagerank_simulation(self, sample_fraction=0.01):
        """Test 3: Giả lập PageRank (tính toán nặng)"""
        print(f"\n{'='*60}")
        print(f"TEST 3: PageRank Simulation (sample {sample_fraction*100}%)")
        print(f"{'='*60}")
        
        start_time = time.time()
        start_resources = self.monitor_resources()
        
        try:
            df = self.spark.read.parquet(self.data_path)
            df_sampled = df.sample(fraction=sample_fraction, seed=42)
            
            # Tính degree centrality (đơn giản hơn PageRank nhưng vẫn nặng)
            out_degree = df_sampled.groupBy("PULocationID") \
                .agg(count("*").alias("out_degree")) \
                .orderBy(desc("out_degree"))
            
            in_degree = df_sampled.groupBy("DOLocationID") \
                .agg(count("*").alias("in_degree")) \
                .orderBy(desc("in_degree"))
            
            # Join 2 bảng (heavy operation)
            degree_centrality = out_degree.join(
                in_degree,
                out_degree.PULocationID == in_degree.DOLocationID,
                "outer"
            )
            
            result_count = degree_centrality.count()
            
            end_time = time.time()
            end_resources = self.monitor_resources()
            elapsed_time = end_time - start_time
            
            result = {
                'test': 'pagerank_simulation',
                'sample_fraction': sample_fraction,
                'result_count': result_count,
                'time_seconds': elapsed_time,
                'memory_delta_gb': end_resources['memory_used_gb'] - start_resources['memory_used_gb'],
                'status': 'SUCCESS'
            }
            
            print(f"✅ Thành công!")
            print(f"   - Thời gian: {elapsed_time:.2f}s")
            
        except Exception as e:
            result = {
                'test': 'pagerank_simulation',
                'sample_fraction': sample_fraction,
                'status': 'FAILED',
                'error': str(e),
                'time_seconds': time.time() - start_time
            }
            print(f"❌ FAILED: {e}")
        
        self.metrics.append(result)
        return result
    
    def run_stress_test(self):
        """Chạy stress test với data tăng dần cho đến khi crash"""
        print(f"\n{'='*60}")
        print(f"STRESS TEST: Tăng dần data size cho đến khi crash")
        print(f"{'='*60}")
        
        sample_fractions = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0]
        
        for frac in sample_fractions:
            print(f"\n🔄 Testing với sample fraction: {frac*100}%")
            
            result = self.test_graph_construction(sample_fraction=frac)
            
            if result['status'] == 'FAILED':
                print(f"\n💥 CRASH tại sample fraction: {frac*100}%")
                print(f"   Lý do: {result.get('error', 'Unknown')}")
                break
            
            # Delay để monitor có thể reset
            time.sleep(2)
    
    def generate_report(self):
        """Tạo báo cáo chi tiết"""
        print(f"\n{'='*60}")
        print(f"PERFORMANCE REPORT - SINGLE MACHINE")
        print(f"{'='*60}")
        
        df_metrics = pd.DataFrame(self.metrics)
        
        # Lưu CSV
        csv_path = f"{self.output_dir}/single_machine_metrics.csv"
        df_metrics.to_csv(csv_path, index=False)
        print(f"\n📄 Metrics saved to: {csv_path}")
        
        # Vẽ biểu đồ
        self._plot_performance(df_metrics)
        
        return df_metrics
    
    def _plot_performance(self, df_metrics):
        """Vẽ biểu đồ performance"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Single Machine Performance Analysis', fontsize=16)
        
        # Plot 1: Time vs Test
        ax1 = axes[0, 0]
        success_metrics = df_metrics[df_metrics['status'] == 'SUCCESS']
        if not success_metrics.empty:
            ax1.bar(success_metrics['test'], success_metrics['time_seconds'])
            ax1.set_xlabel('Test Type')
            ax1.set_ylabel('Time (seconds)')
            ax1.set_title('Execution Time by Test')
            ax1.tick_params(axis='x', rotation=45)
        
        # Plot 2: Memory Usage
        ax2 = axes[0, 1]
        if 'memory_delta_gb' in success_metrics.columns:
            ax2.bar(success_metrics['test'], success_metrics['memory_delta_gb'])
            ax2.set_xlabel('Test Type')
            ax2.set_ylabel('Memory Delta (GB)')
            ax2.set_title('Memory Usage by Test')
            ax2.tick_params(axis='x', rotation=45)
        
        # Plot 3: Success/Failure Rate
        ax3 = axes[1, 0]
        status_counts = df_metrics['status'].value_counts()
        ax3.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%')
        ax3.set_title('Success vs Failure Rate')
        
        # Plot 4: Sample Fraction vs Time (nếu có stress test)
        ax4 = axes[1, 1]
        stress_data = df_metrics[df_metrics['test'] == 'graph_construction']
        if not stress_data.empty and 'sample_fraction' in stress_data.columns:
            ax4.plot(stress_data['sample_fraction'] * 100, 
                    stress_data['time_seconds'], 
                    marker='o')
            ax4.set_xlabel('Sample Fraction (%)')
            ax4.set_ylabel('Time (seconds)')
            ax4.set_title('Stress Test: Time vs Data Size')
            ax4.grid(True)
        
        plt.tight_layout()
        plot_path = f"{self.output_dir}/performance_plots.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"📊 Plots saved to: {plot_path}")
        plt.close()
    
    def cleanup(self):
        """Dọn dẹp resources"""
        self.spark.stop()


# =====================================================================
# MAIN EXECUTION
# =====================================================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test NYC Taxi Graph Mining trên máy đơn')
    parser.add_argument('--data-path', type=str, 
                       default="hdfs://master:9000/user/taxi/raw_data/*.parquet",
                       help='Path to parquet files')
    parser.add_argument('--output-dir', type=str,
                       default="results/single_machine",
                       help='Output directory')
    parser.add_argument('--mode', type=str, 
                       choices=['basic', 'stress'],
                       default='basic',
                       help='Test mode: basic (3 tests cơ bản) hoặc stress (tăng dần đến crash)')
    
    args = parser.parse_args()
    
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║     NYC TAXI GRAPH MINING - SINGLE MACHINE TEST                ║
║                                                                ║
║  Mục đích: Chứng minh bottleneck khi xử lý massive data       ║
║            trên 1 máy duy nhất (Local Mode)                   ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

Configuration:
  - Data Path: {args.data_path}
  - Output Dir: {args.output_dir}
  - Test Mode: {args.mode}
  - Spark Master: local[*] (ALL CPU cores trên 1 máy)
""")
    
    # Khởi tạo test
    tester = SingleMachineTest(
        data_path=args.data_path,
        output_dir=args.output_dir
    )
    
    try:
        if args.mode == 'basic':
            # Test cơ bản
            tester.test_data_loading(num_months=1)
            tester.test_graph_construction(sample_fraction=0.1)
            tester.test_pagerank_simulation(sample_fraction=0.01)
        
        elif args.mode == 'stress':
            # Stress test
            tester.run_stress_test()
        
        # Tạo báo cáo
        tester.generate_report()
        
    except KeyboardInterrupt:
        print("\n⚠️ Test bị interrupt bởi user")
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        tester.cleanup()
        print("\n✅ Test completed. Check results in:", args.output_dir)