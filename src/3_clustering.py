"""
BƯỚC 3: GRAPH CLUSTERING - PHÁT HIỆN COMMUNITIES
Sử dụng Label Propagation Algorithm để tìm clusters của taxi zones

Input: Graph từ bước 1
Output: Communities (clusters) của zones

Phát hiện các khu vực có giao thông nội bộ chặt chẽ
"""

import sys
sys.path.append('../config')

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, desc, avg
from graphframes import GraphFrame
from spark_config import (
    create_spark_session,
    HDFS_GRAPH_DATA,
    HDFS_RESULTS
)
from utils import timer, print_section, print_dataframe_stats


@timer
def load_graph_data(spark):
    """
    Load edge list và PageRank results
    
    Args:
        spark: SparkSession
        
    Returns:
        tuple (edges_df, pagerank_df)
    """
    print_section("LOAD GRAPH DATA")
    
    # Load edges
    edge_path = f"{HDFS_GRAPH_DATA}edge_list"
    print(f"📂 Load edges: {edge_path}")
    edges_df = spark.read.parquet(edge_path)
    print_dataframe_stats(edges_df, "Edges")
    
    # Load PageRank
    pr_path = f"{HDFS_RESULTS}/pagerank_scores"
    print(f"\n📂 Load PageRank: {pr_path}")
    pagerank_df = spark.read.parquet(pr_path)
    print_dataframe_stats(pagerank_df, "PageRank")
    
    return edges_df, pagerank_df


@timer
def create_graph_with_pagerank(edges_df, pagerank_df):
    """
    Tạo GraphFrame với thông tin PageRank
    
    Args:
        edges_df: Edge DataFrame
        pagerank_df: PageRank DataFrame
        
    Returns:
        GraphFrame
    """
    print_section("TẠO GRAPHFRAME VỚI PAGERANK")
    
    # Rename columns for GraphFrame
    vertices = pagerank_df.select(
        col("zone_id").alias("id"),
        col("pagerank")
    )
    
    gf_edges = edges_df.select(
        col("src"),
        col("dst"),
        col("trip_count").alias("weight")
    )
    
    graph = GraphFrame(vertices, gf_edges)
    
    print(f"✅ GraphFrame created:")
    print(f"   - Vertices: {vertices.count()}")
    print(f"   - Edges: {gf_edges.count()}")
    
    return graph


@timer
def run_label_propagation(graph, max_iter=10):
    """
    Chạy Label Propagation Algorithm
    
    Args:
        graph: GraphFrame
        max_iter: Số iteration tối đa
        
    Returns:
        DataFrame với label assignments
    """
    print_section(f"LABEL PROPAGATION ALGORITHM ({max_iter} iterations)")
    
    print("🚀 Chạy Label Propagation...")
    print("   Thuật toán này tự động phát hiện communities trong graph")
    print("   Các node trong cùng community có kết nối chặt chẽ với nhau")
    
    # Run Label Propagation
    result = graph.labelPropagation(maxIter=max_iter)
    
    communities = result.select(
        col("id").alias("zone_id"),
        col("label").alias("community_id"),
        col("pagerank")
    )
    
    print("\n✅ Label Propagation hoàn thành!")
    
    return communities


@timer
def analyze_communities(communities_df):
    """
    Phân tích các communities được phát hiện
    
    Args:
        communities_df: DataFrame với community assignments
    """
    print_section("PHÂN TÍCH COMMUNITIES")
    
    # Count communities
    num_communities = communities_df.select("community_id").distinct().count()
    print(f"🔍 Số communities phát hiện: {num_communities}")
    
    # Community size distribution
    print("\n📊 Phân bố kích thước communities:")
    
    community_sizes = communities_df.groupBy("community_id") \
        .agg(
            count("zone_id").alias("size"),
            avg("pagerank").alias("avg_pagerank")
        ) \
        .orderBy(desc("size"))
    
    community_sizes.describe("size").show()
    
    # Top communities
    print("\n🏆 TOP 20 COMMUNITIES LỚN NHẤT:")
    community_sizes.show(20, truncate=False)
    
    # Small communities
    small_communities = community_sizes.filter(col("size") <= 3)
    num_small = small_communities.count()
    print(f"\n🔍 Số communities nhỏ (≤3 zones): {num_small}")
    
    # Large communities (≥10 zones)
    large_communities = community_sizes.filter(col("size") >= 10)
    num_large = large_communities.count()
    print(f"🔍 Số communities lớn (≥10 zones): {num_large}")
    
    return community_sizes


@timer
def analyze_community_details(communities_df, edges_df, top_n=5):
    """
    Phân tích chi tiết các communities lớn nhất
    
    Args:
        communities_df: Community assignments
        edges_df: Edge list
        top_n: Số communities lớn nhất để phân tích
    """
    print_section(f"PHÂN TÍCH CHI TIẾT TOP {top_n} COMMUNITIES")
    
    # Get top communities
    top_communities = communities_df.groupBy("community_id") \
        .agg(count("zone_id").alias("size")) \
        .orderBy(desc("size")) \
        .limit(top_n) \
        .select("community_id") \
        .rdd.flatMap(lambda x: x).collect()
    
    for i, comm_id in enumerate(top_communities, 1):
        print(f"\n{'='*60}")
        print(f"📍 COMMUNITY #{i} (ID: {comm_id})")
        print(f"{'='*60}")
        
        # Get zones in this community
        comm_zones = communities_df.filter(col("community_id") == comm_id)
        
        print(f"\n🏙️  Zones trong community:")
        comm_zones.orderBy(desc("pagerank")).show(20, truncate=False)
        
        # Internal edges (edges within community)
        zone_list = comm_zones.select("zone_id").rdd.flatMap(lambda x: x).collect()
        
        internal_edges = edges_df.filter(
            (col("src").isin(zone_list)) & 
            (col("dst").isin(zone_list))
        )
        
        # External edges
        external_edges_out = edges_df.filter(
            (col("src").isin(zone_list)) & 
            (~col("dst").isin(zone_list))
        )
        
        external_edges_in = edges_df.filter(
            (~col("src").isin(zone_list)) & 
            (col("dst").isin(zone_list))
        )
        
        from pyspark.sql.functions import sum as _sum
        
        internal_trips = internal_edges.agg(_sum("trip_count")).collect()[0][0] or 0
        external_trips_out = external_edges_out.agg(_sum("trip_count")).collect()[0][0] or 0
        external_trips_in = external_edges_in.agg(_sum("trip_count")).collect()[0][0] or 0
        
        total_trips = internal_trips + external_trips_out + external_trips_in
        internal_ratio = (internal_trips / total_trips * 100) if total_trips > 0 else 0
        
        print(f"\n📊 Traffic Statistics:")
        print(f"   - Internal trips: {internal_trips:,} ({internal_ratio:.2f}%)")
        print(f"   - External trips (out): {external_trips_out:,}")
        print(f"   - External trips (in): {external_trips_in:,}")
        
        # Modularity-like metric
        if internal_ratio > 50:
            print(f"   ✅ Đây là community chặt chẽ (>50% internal traffic)")
        else:
            print(f"   ⚠️  Community lỏng lẻo (<50% internal traffic)")


@timer
def save_clustering_results(communities_df, community_sizes, output_path):
    """
    Lưu kết quả clustering
    
    Args:
        communities_df: Community assignments
        community_sizes: Community size statistics
        output_path: Output path
    """
    print_section("LƯU KẾT QUẢ CLUSTERING")
    
    # Save community assignments
    assignments_path = f"{output_path}/community_assignments"
    print(f"💾 Lưu community assignments: {assignments_path}")
    
    communities_df.write \
        .mode("overwrite") \
        .parquet(assignments_path)
    
    print("✅ Đã lưu assignments!")
    
    # Save community sizes
    sizes_path = f"{output_path}/community_sizes"
    print(f"\n💾 Lưu community sizes: {sizes_path}")
    
    community_sizes.write \
        .mode("overwrite") \
        .parquet(sizes_path)
    
    print("✅ Đã lưu sizes!")
    
    # Save as CSV for easy viewing
    csv_path = f"{output_path}/communities_csv"
    print(f"\n💾 Lưu CSV: {csv_path}")
    
    communities_df.join(community_sizes, on="community_id") \
        .orderBy("community_id", desc("pagerank")) \
        .coalesce(1) \
        .write \
        .mode("overwrite") \
        .option("header", "true") \
        .csv(csv_path)
    
    print("✅ Đã lưu CSV!")


def main():
    """Main execution"""
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║      NYC TAXI GRAPH MINING - BƯỚC 3: GRAPH CLUSTERING         ║
    ║                                                                ║
    ║  Mục tiêu: Phát hiện communities (clusters) của taxi zones   ║
    ║  Phương pháp: Label Propagation Algorithm                     ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Create Spark session
    spark = create_spark_session("NYC_Taxi_Clustering")
    
    try:
        # Step 1: Load data
        edges_df, pagerank_df = load_graph_data(spark)
        
        # Step 2: Create graph
        graph = create_graph_with_pagerank(edges_df, pagerank_df)
        
        # Step 3: Run Label Propagation
        communities_df = run_label_propagation(graph)
        
        # Step 4: Analyze communities
        community_sizes = analyze_communities(communities_df)
        
        # Step 5: Detailed analysis
        analyze_community_details(communities_df, edges_df)
        
        # Step 6: Save results
        save_clustering_results(communities_df, community_sizes, HDFS_RESULTS)
        
        print("\n" + "="*70)
        print("🎉 HOÀN THÀNH BƯỚC 3: GRAPH CLUSTERING")
        print("="*70)
        print(f"\n📂 Kết quả đã được lưu tại: {HDFS_RESULTS}")
        print("\n📌 Next steps:")
        print("   1. Chạy 4_visualization.py để visualize kết quả")
        print("   2. Phân tích ý nghĩa của các communities")
        
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
