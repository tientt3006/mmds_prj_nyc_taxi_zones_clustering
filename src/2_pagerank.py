"""
BƯỚC 2: TÍNH PAGERANK CHO TAXI ZONES
Sử dụng GraphX/GraphFrames với thuật toán iterative PageRank

Input: Edge list từ bước 1
Output: PageRank scores cho mỗi zone

Đây là thuật toán ITERATIVE - shuffle dữ liệu lớn qua nhiều vòng lặp
"""

import sys
sys.path.append('../config')

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, desc, broadcast
from graphframes import GraphFrame
from spark_config import (
    create_spark_session,
    HDFS_GRAPH_DATA,
    HDFS_RESULTS,
    DAMPING_FACTOR,
    PAGERANK_ITERATIONS,
    PAGERANK_TOLERANCE
)
from utils import timer, print_section, print_dataframe_stats


@timer
def load_edge_list(spark, edge_path):
    """
    Load edge list từ HDFS
    
    Args:
        spark: SparkSession
        edge_path: Path to edge list parquet
        
    Returns:
        Edge DataFrame
    """
    print_section("LOAD EDGE LIST")
    
    print(f"📂 Đọc edge list từ: {edge_path}")
    edges_df = spark.read.parquet(edge_path)
    
    print_dataframe_stats(edges_df, "Edge List")
    edges_df.show(5)
    
    return edges_df


@timer
def create_graph(spark, edges_df):
    """
    Tạo GraphFrame từ edge list
    
    Args:
        spark: SparkSession
        edges_df: Edge DataFrame
        
    Returns:
        GraphFrame object
    """
    print_section("TẠO GRAPHFRAME")
    
    # Create vertices DataFrame
    print("🔨 Tạo vertices từ edges...")
    
    # Combine all unique zone IDs
    src_vertices = edges_df.select(col("src").alias("id")).distinct()
    dst_vertices = edges_df.select(col("dst").alias("id")).distinct()
    vertices = src_vertices.union(dst_vertices).distinct()
    
    num_vertices = vertices.count()
    print(f"✅ Số vertices: {num_vertices}")
    
    # Prepare edges for GraphFrame (rename columns)
    print("\n🔨 Chuẩn bị edges cho GraphFrame...")
    gf_edges = edges_df.select(
        col("src"),
        col("dst"),
        col("trip_count").alias("weight")
    )
    
    num_edges = gf_edges.count()
    print(f"✅ Số edges: {num_edges}")
    
    # Create GraphFrame
    print("\n🔨 Tạo GraphFrame object...")
    graph = GraphFrame(vertices, gf_edges)
    
    print(f"✅ GraphFrame đã được tạo!")
    print(f"   - Vertices: {num_vertices}")
    print(f"   - Edges: {num_edges}")
    print(f"   - Avg degree: {2 * num_edges / num_vertices:.2f}")
    
    return graph


@timer
def run_pagerank(graph, iterations=PAGERANK_ITERATIONS, reset_prob=1-DAMPING_FACTOR):
    """
    Chạy PageRank algorithm
    
    Args:
        graph: GraphFrame
        iterations: Số vòng lặp
        reset_prob: Xác suất reset (1 - damping factor)
        
    Returns:
        DataFrame với PageRank scores
    """
    print_section(f"CHẠY PAGERANK ({iterations} ITERATIONS)")
    
    print(f"⚙️  Tham số:")
    print(f"   - Max iterations: {iterations}")
    print(f"   - Reset probability: {reset_prob:.3f}")
    print(f"   - Damping factor: {1-reset_prob:.3f}")
    
    print(f"\n🚀 Bắt đầu PageRank...")
    print(f"   (Đây là thuật toán iterative, sẽ mất vài phút)")
    
    # Run PageRank
    results = graph.pageRank(
        resetProbability=reset_prob,
        maxIter=iterations
    )
    
    # Extract vertices with PageRank scores
    pagerank_df = results.vertices.select(
        col("id").alias("zone_id"),
        col("pagerank")
    ).orderBy(desc("pagerank"))
    
    print(f"\n✅ PageRank hoàn thành!")
    
    # Show statistics
    print("\n📊 PageRank Statistics:")
    pagerank_df.describe("pagerank").show()
    
    # Show top zones
    print("\n🏆 TOP 20 ZONES QUAN TRỌNG NHẤT (PageRank):")
    pagerank_df.show(20, truncate=False)
    
    return pagerank_df


@timer
def analyze_pagerank_distribution(pagerank_df):
    """
    Phân tích phân phối PageRank
    
    Args:
        pagerank_df: DataFrame với PageRank scores
    """
    print_section("PHÂN TÍCH PAGERANK DISTRIBUTION")
    
    from pyspark.sql.functions import sum as _sum, count, min as _min, max as _max
    
    # Basic stats
    stats = pagerank_df.agg(
        _sum("pagerank").alias("total_pr"),
        count("zone_id").alias("num_zones"),
        _min("pagerank").alias("min_pr"),
        _max("pagerank").alias("max_pr")
    ).collect()[0]
    
    print(f"📊 Statistics:")
    print(f"   - Total PageRank sum: {stats['total_pr']:.4f}")
    print(f"   - Number of zones: {stats['num_zones']}")
    print(f"   - Min PageRank: {stats['min_pr']:.6f}")
    print(f"   - Max PageRank: {stats['max_pr']:.6f}")
    print(f"   - Ratio (max/min): {stats['max_pr']/stats['min_pr']:.2f}x")
    
    # Top zones concentration
    print("\n🎯 Concentration Analysis:")
    
    total_pr = stats['total_pr']
    
    # Top 10
    top10_pr = pagerank_df.limit(10).agg(_sum("pagerank")).collect()[0][0]
    top10_pct = (top10_pr / total_pr) * 100
    print(f"   - Top 10 zones: {top10_pct:.2f}% of total PageRank")
    
    # Top 20
    top20_pr = pagerank_df.limit(20).agg(_sum("pagerank")).collect()[0][0]
    top20_pct = (top20_pr / total_pr) * 100
    print(f"   - Top 20 zones: {top20_pct:.2f}% of total PageRank")
    
    # Top 50
    top50_pr = pagerank_df.limit(50).agg(_sum("pagerank")).collect()[0][0]
    top50_pct = (top50_pr / total_pr) * 100
    print(f"   - Top 50 zones: {top50_pct:.2f}% of total PageRank")


@timer
def save_pagerank_results(pagerank_df, output_path):
    """
    Lưu kết quả PageRank
    
    Args:
        pagerank_df: DataFrame với PageRank scores
        output_path: Output path
    """
    print_section("LƯU KẾT QUẢ PAGERANK")
    
    # Save as Parquet
    parquet_path = f"{output_path}/pagerank_scores"
    print(f"💾 Lưu Parquet: {parquet_path}")
    
    pagerank_df.write \
        .mode("overwrite") \
        .parquet(parquet_path)
    
    print(f"✅ Đã lưu Parquet!")
    
    # Save top 100 as CSV
    csv_path = f"{output_path}/pagerank_top100"
    print(f"\n💾 Lưu top 100 zones (CSV): {csv_path}")
    
    pagerank_df.limit(100).coalesce(1).write \
        .mode("overwrite") \
        .option("header", "true") \
        .csv(csv_path)
    
    print(f"✅ Đã lưu CSV!")


@timer
def compare_with_simple_metrics(spark, edge_list_path, pagerank_df):
    """
    So sánh PageRank với các metrics đơn giản
    
    Args:
        spark: SparkSession
        edge_list_path: Path to edge list
        pagerank_df: PageRank results
    """
    print_section("SO SÁNH PAGERANK VS SIMPLE METRICS")
    
    # Load edge list
    edges = spark.read.parquet(edge_list_path)
    
    # Calculate total trips per zone (as destination)
    print("🔍 Tính tổng trips đến mỗi zone...")
    total_trips_in = edges.groupBy("dst") \
        .agg({"trip_count": "sum"}) \
        .select(
            col("dst").alias("zone_id"),
            col("sum(trip_count)").alias("total_trips_in")
        )
    
    # Join with PageRank
    comparison = pagerank_df.join(
        total_trips_in,
        on="zone_id",
        how="left"
    ).fillna(0)
    
    # Add rank columns
    from pyspark.sql.window import Window
    from pyspark.sql.functions import row_number
    
    window_pr = Window.orderBy(desc("pagerank"))
    window_trips = Window.orderBy(desc("total_trips_in"))
    
    comparison = comparison.withColumn("pr_rank", row_number().over(window_pr)) \
                           .withColumn("trips_rank", row_number().over(window_trips))
    
    # Show comparison
    print("\n📊 Top 20 zones - PageRank vs Total Trips:")
    comparison.select(
        "zone_id",
        "pr_rank",
        "pagerank",
        "trips_rank",
        "total_trips_in"
    ).orderBy("pr_rank").show(20, truncate=False)
    
    # Calculate correlation
    print("\n🔗 Correlation analysis:")
    from pyspark.sql.functions import corr
    
    correlation = comparison.agg(
        corr("pagerank", "total_trips_in").alias("correlation")
    ).collect()[0]["correlation"]
    
    print(f"   - Pearson correlation (PageRank vs Total Trips): {correlation:.4f}")
    
    if correlation > 0.8:
        print("   ✅ Correlation cao - PageRank tương đồng với traffic volume")
    elif correlation > 0.5:
        print("   ⚠️  Correlation trung bình - PageRank có khác biệt với traffic volume")
    else:
        print("   ⚠️  Correlation thấp - PageRank khác biệt đáng kể với traffic volume")


def main():
    """Main execution"""
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║         NYC TAXI GRAPH MINING - BƯỚC 2: PAGERANK              ║
    ║                                                                ║
    ║  Mục tiêu: Tính importance của mỗi zone bằng PageRank        ║
    ║  Phương pháp: Iterative GraphX algorithm                      ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Create Spark session
    spark = create_spark_session("NYC_Taxi_PageRank")
    
    try:
        # Step 1: Load edge list
        edge_path = f"{HDFS_GRAPH_DATA}edge_list"
        edges_df = load_edge_list(spark, edge_path)
        
        # Step 2: Create graph
        graph = create_graph(spark, edges_df)
        
        # Step 3: Run PageRank
        pagerank_df = run_pagerank(graph)
        
        # Step 4: Analyze results
        analyze_pagerank_distribution(pagerank_df)
        
        # Step 5: Compare with simple metrics
        compare_with_simple_metrics(spark, edge_path, pagerank_df)
        
        # Step 6: Save results
        save_pagerank_results(pagerank_df, HDFS_RESULTS)
        
        print("\n" + "="*70)
        print("🎉 HOÀN THÀNH BƯỚC 2: PAGERANK")
        print("="*70)
        print(f"\n📂 Kết quả đã được lưu tại: {HDFS_RESULTS}")
        print("\n📌 Next steps:")
        print("   1. Chạy 3_clustering.py để phát hiện communities")
        print("   2. Chạy 4_visualization.py để visualize kết quả")
        
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
