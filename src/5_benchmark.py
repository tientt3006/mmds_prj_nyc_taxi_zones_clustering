"""
BƯỚC 5: BENCHMARK VÀ SCALABILITY TESTING
Đo performance của pipeline và chứng minh tính massive

Input: Sample data với kích thước khác nhau
Output: Benchmark metrics (runtime, memory, etc.)
"""

import sys
import os
import json
import time
from datetime import datetime

# Thêm parent directory vào Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum as _sum

# Import từ config
from config.spark_config import (
    create_spark_session,
    HDFS_RAW_DATA,
    HDFS_RESULTS
)

# Import utils
try:
    from utils import timer, print_section
except ImportError:
    from src.utils import timer, print_section


def benchmark_build_graph(spark, sample_fraction, run_name):
    """
    Benchmark build graph step
    
    Args:
        spark: SparkSession
        sample_fraction: Fraction of data to sample (0.01 = 1%)
        run_name: Name of this benchmark run
        
    Returns:
        dict with metrics
    """
    print_section(f"BENCHMARK: BUILD GRAPH - {run_name}")
    
    start_time = time.time()
    
    # Load data
    print(f"📂 Loading {sample_fraction*100}% of data...")
    df = spark.read.parquet(HDFS_RAW_DATA).sample(sample_fraction)
    
    # Count raw data
    raw_count = df.count()
    print(f"   Raw data: {raw_count:,} rows")
    
    # Clean data
    print("🧹 Cleaning data...")
    from config.spark_config import PICKUP_LOCATION, DROPOFF_LOCATION, FARE_AMOUNT
    
    cleaned_df = df.filter(
        (col(PICKUP_LOCATION).isNotNull()) &
        (col(DROPOFF_LOCATION).isNotNull()) &
        (col(PICKUP_LOCATION) >= 1) &
        (col(PICKUP_LOCATION) <= 263) &
        (col(DROPOFF_LOCATION) >= 1) &
        (col(DROPOFF_LOCATION) <= 263) &
        (col(PICKUP_LOCATION) != col(DROPOFF_LOCATION)) &
        (col(FARE_AMOUNT) >= 0)
    )
    
    cleaned_count = cleaned_df.count()
    print(f"   Cleaned data: {cleaned_count:,} rows")
    
    # Build edge list
    print("🔨 Building edge list...")
    edge_list = cleaned_df.groupBy(
        col(PICKUP_LOCATION).alias("src"),
        col(DROPOFF_LOCATION).alias("dst")
    ).agg(
        count("*").alias("trip_count")
    )
    
    edge_count = edge_list.count()
    print(f"   Edges: {edge_count:,}")
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    metrics = {
        "run_name": run_name,
        "step": "build_graph",
        "sample_fraction": sample_fraction,
        "raw_rows": raw_count,
        "cleaned_rows": cleaned_count,
        "edges": edge_count,
        "runtime_seconds": elapsed,
        "runtime_minutes": elapsed / 60,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"\n⏱️  Runtime: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
    
    return metrics


def benchmark_pagerank(spark, sample_fraction, run_name, iterations=5):
    """
    Benchmark PageRank step
    
    Args:
        spark: SparkSession
        sample_fraction: Fraction of data
        run_name: Name of run
        iterations: Number of PageRank iterations
        
    Returns:
        dict with metrics
    """
    print_section(f"BENCHMARK: PAGERANK - {run_name}")
    
    try:
        from graphframes import GraphFrame
    except ImportError:
        print("⚠️  GraphFrames not available, skipping PageRank benchmark")
        return None
    
    start_time = time.time()
    
    # Load and build graph (reuse logic)
    print(f"📂 Preparing graph with {sample_fraction*100}% data...")
    from config.spark_config import PICKUP_LOCATION, DROPOFF_LOCATION, FARE_AMOUNT
    
    df = spark.read.parquet(HDFS_RAW_DATA).sample(sample_fraction)
    
    cleaned_df = df.filter(
        (col(PICKUP_LOCATION).isNotNull()) &
        (col(DROPOFF_LOCATION).isNotNull()) &
        (col(PICKUP_LOCATION) >= 1) &
        (col(PICKUP_LOCATION) <= 263) &
        (col(DROPOFF_LOCATION) >= 1) &
        (col(DROPOFF_LOCATION) <= 263) &
        (col(PICKUP_LOCATION) != col(DROPOFF_LOCATION)) &
        (col(FARE_AMOUNT) >= 0)
    )
    
    edges = cleaned_df.groupBy(
        col(PICKUP_LOCATION).alias("src"),
        col(DROPOFF_LOCATION).alias("dst")
    ).agg(count("*").alias("weight"))
    
    # Create vertices
    src_v = edges.select(col("src").alias("id")).distinct()
    dst_v = edges.select(col("dst").alias("id")).distinct()
    vertices = src_v.union(dst_v).distinct()
    
    num_vertices = vertices.count()
    num_edges = edges.count()
    
    print(f"   Vertices: {num_vertices:,}, Edges: {num_edges:,}")
    
    # Create GraphFrame
    graph = GraphFrame(vertices, edges)
    
    # Run PageRank
    print(f"🚀 Running PageRank ({iterations} iterations)...")
    pr_start = time.time()
    
    results = graph.pageRank(resetProbability=0.15, maxIter=iterations)
    pagerank_df = results.vertices
    
    # Force computation
    pr_count = pagerank_df.count()
    
    pr_end = time.time()
    pr_elapsed = pr_end - pr_start
    
    end_time = time.time()
    total_elapsed = end_time - start_time
    
    metrics = {
        "run_name": run_name,
        "step": "pagerank",
        "sample_fraction": sample_fraction,
        "vertices": num_vertices,
        "edges": num_edges,
        "iterations": iterations,
        "pagerank_runtime_seconds": pr_elapsed,
        "total_runtime_seconds": total_elapsed,
        "total_runtime_minutes": total_elapsed / 60,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"\n⏱️  PageRank time: {pr_elapsed:.2f}s")
    print(f"⏱️  Total time: {total_elapsed:.2f}s ({total_elapsed/60:.2f} min)")
    
    return metrics


def save_benchmark_results(results, output_dir="../results/benchmarks"):
    """
    Save benchmark results to JSON
    
    Args:
        results: List of metric dicts
        output_dir: Output directory
    """
    print_section("SAVE BENCHMARK RESULTS")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"benchmark_{timestamp}.json")
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Saved results to: {output_file}")
    
    # Print summary
    print("\n📊 BENCHMARK SUMMARY:")
    print("-" * 70)
    for result in results:
        if result:
            print(f"\n{result['run_name']} - {result['step']}")
            if 'runtime_minutes' in result:
                print(f"  Runtime: {result['runtime_minutes']:.2f} minutes")
            elif 'total_runtime_minutes' in result:
                print(f"  Runtime: {result['total_runtime_minutes']:.2f} minutes")


def main():
    """Main execution"""
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║        NYC TAXI GRAPH MINING - BƯỚC 5: BENCHMARK              ║
    ║                                                                ║
    ║  Mục tiêu: Đo performance và chứng minh scalability          ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Create Spark session
    spark = create_spark_session("NYC_Taxi_Benchmark")
    
    results = []
    
    try:
        # Test 1: Small sample (1%)
        print("\n" + "="*70)
        print("TEST 1: 1% DATA SAMPLE")
        print("="*70)
        metrics_1 = benchmark_build_graph(spark, 0.01, "1% Sample")
        results.append(metrics_1)
        
        # Test 2: Medium sample (5%)
        print("\n" + "="*70)
        print("TEST 2: 5% DATA SAMPLE")
        print("="*70)
        metrics_2 = benchmark_build_graph(spark, 0.05, "5% Sample")
        results.append(metrics_2)
        
        # Test 3: PageRank on 1% data
        print("\n" + "="*70)
        print("TEST 3: PAGERANK ON 1% DATA")
        print("="*70)
        metrics_3 = benchmark_pagerank(spark, 0.01, "PageRank 1%", iterations=5)
        results.append(metrics_3)
        
        # Save results
        save_benchmark_results(results)
        
        print("\n" + "="*70)
        print("🎉 HOÀN THÀNH BƯỚC 5: BENCHMARK")
        print("="*70)
        print("\n📌 Kết quả benchmark đã được lưu!")
        print("📊 Sử dụng kết quả này để:")
        print("   - Chứng minh tính massive của bài toán")
        print("   - So sánh performance giữa các cấu hình")
        print("   - Phân tích scalability")
        
    except Exception as e:
        print(f"\n❌ LỖI: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Stop Spark
        spark.stop()
        print("\n🛑 Đã dừng Spark session")


if __name__ == "__main__":
    main()
