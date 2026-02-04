"""
BƯỚC 5: BENCHMARK - ĐO SCALABILITY
So sánh performance khi chạy trên 1 node vs 2 nodes

Đây là phần quan trọng để chứng minh bài toán "MASSIVE"
"""

import sys
sys.path.append('../config')

import time
import json
from datetime import datetime
from pyspark.sql import SparkSession
from spark_config import HDFS_RAW_DATA, HDFS_GRAPH_DATA
from utils import timer, print_section, ensure_dir


def benchmark_build_graph(spark, sample_size=None):
    """
    Benchmark quá trình build graph
    
    Args:
        spark: SparkSession
        sample_size: Số dòng để sample (None = all data)
        
    Returns:
        dict với timing results
    """
    print_section(f"BENCHMARK: BUILD GRAPH")
    
    if sample_size:
        print(f"⚠️  Running on SAMPLE: {sample_size:,} rows")
    else:
        print(f"🔥 Running on FULL DATA")
    
    results = {}
    
    # Load data
    start_time = time.time()
    df = spark.read.parquet(HDFS_RAW_DATA)
    
    if sample_size:
        df = df.limit(sample_size)
    
    load_time = time.time() - start_time
    results['load_time'] = load_time
    results['row_count'] = df.count()
    
    print(f"✅ Load time: {load_time:.2f}s")
    print(f"   Rows: {results['row_count']:,}")
    
    # Clean data
    start_time = time.time()
    from pyspark.sql.functions import col
    
    cleaned = df.filter(
        (col("PULocationID").isNotNull()) &
        (col("DOLocationID").isNotNull()) &
        (col("PULocationID") != col("DOLocationID"))
    ).cache()
    
    clean_count = cleaned.count()
    clean_time = time.time() - start_time
    
    results['clean_time'] = clean_time
    results['clean_row_count'] = clean_count
    
    print(f"✅ Clean time: {clean_time:.2f}s")
    print(f"   Rows after cleaning: {clean_count:,}")
    
    # Build edge list
    start_time = time.time()
    from pyspark.sql.functions import count as _count
    
    edge_list = cleaned.groupBy("PULocationID", "DOLocationID") \
        .agg(_count("*").alias("trip_count")) \
        .cache()
    
    edge_count = edge_list.count()
    build_time = time.time() - start_time
    
    results['build_time'] = build_time
    results['edge_count'] = edge_count
    
    print(f"✅ Build time: {build_time:.2f}s")
    print(f"   Edges: {edge_count:,}")
    
    # Total time
    results['total_time'] = load_time + clean_time + build_time
    
    return results


def benchmark_pagerank(spark, iterations=5):
    """
    Benchmark PageRank
    
    Args:
        spark: SparkSession
        iterations: Số iteration
        
    Returns:
        dict với timing results
    """
    print_section(f"BENCHMARK: PAGERANK ({iterations} iterations)")
    
    results = {'iterations': iterations}
    
    # Load edge list
    start_time = time.time()
    edges = spark.read.parquet(f"{HDFS_GRAPH_DATA}edge_list")
    
    from pyspark.sql.functions import col
    
    # Create vertices
    src_v = edges.select(col("src").alias("id")).distinct()
    dst_v = edges.select(col("dst").alias("id")).distinct()
    vertices = src_v.union(dst_v).distinct()
    
    gf_edges = edges.select("src", "dst", col("trip_count").alias("weight"))
    
    from graphframes import GraphFrame
    graph = GraphFrame(vertices, gf_edges)
    
    setup_time = time.time() - start_time
    results['setup_time'] = setup_time
    
    print(f"✅ Setup time: {setup_time:.2f}s")
    
    # Run PageRank
    start_time = time.time()
    pr_result = graph.pageRank(resetProbability=0.15, maxIter=iterations)
    pr_count = pr_result.vertices.count()
    
    pagerank_time = time.time() - start_time
    results['pagerank_time'] = pagerank_time
    results['num_vertices'] = pr_count
    
    print(f"✅ PageRank time: {pagerank_time:.2f}s")
    print(f"   Vertices: {pr_count}")
    
    results['total_time'] = setup_time + pagerank_time
    
    return results


def run_full_benchmark():
    """
    Chạy full benchmark suite
    """
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║           NYC TAXI GRAPH MINING - BENCHMARK SUITE             ║
    ║                                                                ║
    ║  Mục đích: Đo performance và chứng minh scalability          ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Get cluster info
    from spark_config import create_spark_session
    spark = create_spark_session("NYC_Taxi_Benchmark")
    
    # Collect cluster info
    cluster_info = {
        'timestamp': datetime.now().isoformat(),
        'num_executors': spark.sparkContext.getConf().get('spark.executor.instances', 'N/A'),
        'executor_memory': spark.sparkContext.getConf().get('spark.executor.memory', 'N/A'),
        'executor_cores': spark.sparkContext.getConf().get('spark.executor.cores', 'N/A'),
        'driver_memory': spark.sparkContext.getConf().get('spark.driver.memory', 'N/A'),
    }
    
    print(f"\n📊 CLUSTER CONFIGURATION:")
    for key, value in cluster_info.items():
        print(f"   {key}: {value}")
    
    all_results = {
        'cluster_info': cluster_info,
        'benchmarks': {}
    }
    
    try:
        # Benchmark 1: Build graph on sample
        print("\n" + "="*70)
        print("BENCHMARK 1: Build Graph (Sample - 1M rows)")
        print("="*70)
        
        sample_results = benchmark_build_graph(spark, sample_size=1_000_000)
        all_results['benchmarks']['build_graph_sample_1M'] = sample_results
        
        # Benchmark 2: Build graph on larger sample
        print("\n" + "="*70)
        print("BENCHMARK 2: Build Graph (Sample - 10M rows)")
        print("="*70)
        
        large_sample_results = benchmark_build_graph(spark, sample_size=10_000_000)
        all_results['benchmarks']['build_graph_sample_10M'] = large_sample_results
        
        # Benchmark 3: PageRank
        print("\n" + "="*70)
        print("BENCHMARK 3: PageRank (5 iterations)")
        print("="*70)
        
        pr_results = benchmark_pagerank(spark, iterations=5)
        all_results['benchmarks']['pagerank_5iter'] = pr_results
        
        # Calculate speedup metrics
        print("\n" + "="*70)
        print("📈 SCALABILITY ANALYSIS")
        print("="*70)
        
        sample_1m_time = sample_results['total_time']
        sample_10m_time = large_sample_results['total_time']
        
        # Linear vs actual
        expected_10m = sample_1m_time * 10
        speedup = expected_10m / sample_10m_time
        
        print(f"\n🔍 Build Graph Scaling:")
        print(f"   1M rows:  {sample_1m_time:.2f}s")
        print(f"   10M rows: {sample_10m_time:.2f}s")
        print(f"   Expected (linear): {expected_10m:.2f}s")
        print(f"   Speedup: {speedup:.2f}x")
        
        if speedup > 1.5:
            print(f"   ✅ Good parallelization! ({speedup:.2f}x faster than linear)")
        elif speedup > 1.0:
            print(f"   ⚠️  Some parallelization benefit ({speedup:.2f}x)")
        else:
            print(f"   ❌ No parallelization benefit ({speedup:.2f}x)")
        
        all_results['scalability'] = {
            'scaling_factor': 10,
            'expected_time': expected_10m,
            'actual_time': sample_10m_time,
            'speedup': speedup
        }
        
        # Save results
        ensure_dir("../results/benchmarks/")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"../results/benchmarks/benchmark_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n💾 Benchmark results saved to: {filename}")
        
    except Exception as e:
        print(f"\n❌ BENCHMARK ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        spark.stop()
        print("\n🛑 Benchmark complete")


if __name__ == "__main__":
    run_full_benchmark()
