"""
BƯỚC 4: VISUALIZATION VÀ PHÂN TÍCH KẾT QUẢ
Tạo các biểu đồ và visualizations cho kết quả

Note: Script này chạy local (không cần cluster) để tạo visualizations
"""

import sys
sys.path.append('../config')

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, desc
from spark_config import HDFS_RESULTS, LOCAL_VISUALIZATIONS_DIR
from utils import timer, print_section, ensure_dir


# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


@timer
def load_results(spark):
    """
    Load tất cả kết quả từ HDFS
    
    Args:
        spark: SparkSession
        
    Returns:
        tuple (pagerank_df, communities_df, community_sizes_df)
    """
    print_section("LOAD KẾT QUẢ")
    
    # PageRank
    print("📂 Load PageRank...")
    pr_df = spark.read.parquet(f"{HDFS_RESULTS}/pagerank_scores")
    
    # Communities
    print("📂 Load Communities...")
    comm_df = spark.read.parquet(f"{HDFS_RESULTS}/community_assignments")
    
    # Community sizes
    print("📂 Load Community Sizes...")
    sizes_df = spark.read.parquet(f"{HDFS_RESULTS}/community_sizes")
    
    print("✅ Đã load tất cả kết quả!")
    
    return pr_df, comm_df, sizes_df


@timer
def plot_pagerank_distribution(pagerank_df, output_dir):
    """
    Vẽ biểu đồ phân phối PageRank
    
    Args:
        pagerank_df: PageRank DataFrame
        output_dir: Output directory
    """
    print_section("VISUALIZE PAGERANK DISTRIBUTION")
    
    # Convert to Pandas
    print("📊 Chuyển sang Pandas...")
    pr_pd = pagerank_df.toPandas()
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Distribution histogram
    ax1 = axes[0, 0]
    pr_pd['pagerank'].hist(bins=50, ax=ax1, color='skyblue', edgecolor='black')
    ax1.set_xlabel('PageRank Score')
    ax1.set_ylabel('Frequency')
    ax1.set_title('PageRank Distribution (Histogram)')
    ax1.grid(True, alpha=0.3)
    
    # 2. Log scale histogram
    ax2 = axes[0, 1]
    pr_pd['pagerank'].hist(bins=50, ax=ax2, color='salmon', edgecolor='black')
    ax2.set_xlabel('PageRank Score')
    ax2.set_ylabel('Frequency (log scale)')
    ax2.set_title('PageRank Distribution (Log Scale)')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3)
    
    # 3. Top 30 zones bar chart
    ax3 = axes[1, 0]
    top30 = pr_pd.nlargest(30, 'pagerank')
    ax3.barh(range(len(top30)), top30['pagerank'].values, color='green', alpha=0.7)
    ax3.set_yticks(range(len(top30)))
    ax3.set_yticklabels(top30['zone_id'].astype(str), fontsize=8)
    ax3.set_xlabel('PageRank Score')
    ax3.set_title('Top 30 Zones by PageRank')
    ax3.invert_yaxis()
    ax3.grid(True, alpha=0.3, axis='x')
    
    # 4. Cumulative distribution
    ax4 = axes[1, 1]
    sorted_pr = np.sort(pr_pd['pagerank'].values)[::-1]
    cumsum = np.cumsum(sorted_pr)
    cumsum_pct = (cumsum / cumsum[-1]) * 100
    ax4.plot(range(len(cumsum_pct)), cumsum_pct, linewidth=2, color='purple')
    ax4.axhline(y=50, color='red', linestyle='--', label='50%')
    ax4.axhline(y=80, color='orange', linestyle='--', label='80%')
    ax4.set_xlabel('Number of Zones (sorted by PageRank)')
    ax4.set_ylabel('Cumulative PageRank (%)')
    ax4.set_title('Cumulative PageRank Distribution')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    output_path = f"{output_dir}/pagerank_distribution.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_path}")
    
    plt.close()


@timer
def plot_community_analysis(community_sizes_df, output_dir):
    """
    Vẽ biểu đồ phân tích communities
    
    Args:
        community_sizes_df: Community sizes DataFrame
        output_dir: Output directory
    """
    print_section("VISUALIZE COMMUNITY ANALYSIS")
    
    # Convert to Pandas
    print("📊 Chuyển sang Pandas...")
    sizes_pd = community_sizes_df.toPandas()
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Community size distribution
    ax1 = axes[0, 0]
    sizes_pd['size'].hist(bins=30, ax=ax1, color='teal', edgecolor='black')
    ax1.set_xlabel('Community Size (number of zones)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Community Size Distribution')
    ax1.grid(True, alpha=0.3)
    
    # Add statistics
    mean_size = sizes_pd['size'].mean()
    median_size = sizes_pd['size'].median()
    ax1.axvline(mean_size, color='red', linestyle='--', label=f'Mean: {mean_size:.1f}')
    ax1.axvline(median_size, color='orange', linestyle='--', label=f'Median: {median_size:.1f}')
    ax1.legend()
    
    # 2. Top 20 communities
    ax2 = axes[0, 1]
    top20 = sizes_pd.nlargest(20, 'size')
    bars = ax2.bar(range(len(top20)), top20['size'].values, color='coral', alpha=0.7)
    ax2.set_xlabel('Community Rank')
    ax2.set_ylabel('Size (number of zones)')
    ax2.set_title('Top 20 Communities by Size')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Avg PageRank vs Community Size
    ax3 = axes[1, 0]
    ax3.scatter(sizes_pd['size'], sizes_pd['avg_pagerank'], 
                alpha=0.6, s=50, color='navy')
    ax3.set_xlabel('Community Size')
    ax3.set_ylabel('Average PageRank')
    ax3.set_title('Community Size vs Average PageRank')
    ax3.grid(True, alpha=0.3)
    
    # Add trend line
    z = np.polyfit(sizes_pd['size'], sizes_pd['avg_pagerank'], 1)
    p = np.poly1d(z)
    ax3.plot(sizes_pd['size'], p(sizes_pd['size']), 
             "r--", alpha=0.8, linewidth=2, label='Trend')
    ax3.legend()
    
    # 4. Community size categories
    ax4 = axes[1, 1]
    
    # Categorize communities
    categories = pd.cut(sizes_pd['size'], 
                       bins=[0, 3, 10, 20, 50, float('inf')],
                       labels=['Tiny (1-3)', 'Small (4-10)', 
                              'Medium (11-20)', 'Large (21-50)', 
                              'Very Large (>50)'])
    
    category_counts = categories.value_counts().sort_index()
    
    colors_cat = ['lightcoral', 'gold', 'lightgreen', 'skyblue', 'mediumpurple']
    ax4.pie(category_counts.values, labels=category_counts.index, 
            autopct='%1.1f%%', colors=colors_cat, startangle=90)
    ax4.set_title('Community Size Categories')
    
    plt.tight_layout()
    
    output_path = f"{output_dir}/community_analysis.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_path}")
    
    plt.close()


@timer
def create_summary_statistics(pagerank_df, communities_df, community_sizes_df, output_dir):
    """
    Tạo bảng thống kê tổng hợp
    
    Args:
        pagerank_df: PageRank DataFrame
        communities_df: Communities DataFrame
        community_sizes_df: Community sizes DataFrame
        output_dir: Output directory
    """
    print_section("TẠO SUMMARY STATISTICS")
    
    # Convert to Pandas
    pr_pd = pagerank_df.toPandas()
    comm_pd = communities_df.toPandas()
    sizes_pd = community_sizes_df.toPandas()
    
    # Create summary
    summary = {
        'Metric': [],
        'Value': []
    }
    
    # PageRank stats
    summary['Metric'].append('Total Zones')
    summary['Value'].append(f"{len(pr_pd):,}")
    
    summary['Metric'].append('Mean PageRank')
    summary['Value'].append(f"{pr_pd['pagerank'].mean():.6f}")
    
    summary['Metric'].append('Median PageRank')
    summary['Value'].append(f"{pr_pd['pagerank'].median():.6f}")
    
    summary['Metric'].append('Max PageRank')
    summary['Value'].append(f"{pr_pd['pagerank'].max():.6f}")
    
    summary['Metric'].append('Min PageRank')
    summary['Value'].append(f"{pr_pd['pagerank'].min():.6f}")
    
    # Top zone concentration
    top10_sum = pr_pd.nlargest(10, 'pagerank')['pagerank'].sum()
    total_sum = pr_pd['pagerank'].sum()
    summary['Metric'].append('Top 10 Zones Concentration')
    summary['Value'].append(f"{(top10_sum/total_sum)*100:.2f}%")
    
    # Community stats
    summary['Metric'].append('Number of Communities')
    summary['Value'].append(f"{len(sizes_pd):,}")
    
    summary['Metric'].append('Mean Community Size')
    summary['Value'].append(f"{sizes_pd['size'].mean():.2f}")
    
    summary['Metric'].append('Median Community Size')
    summary['Value'].append(f"{sizes_pd['size'].median():.1f}")
    
    summary['Metric'].append('Largest Community Size')
    summary['Value'].append(f"{sizes_pd['size'].max():,} zones")
    
    summary['Metric'].append('Smallest Community Size')
    summary['Value'].append(f"{sizes_pd['size'].min():,} zones")
    
    # Create DataFrame
    summary_df = pd.DataFrame(summary)
    
    # Save as CSV
    csv_path = f"{output_dir}/summary_statistics.csv"
    summary_df.to_csv(csv_path, index=False)
    print(f"✅ Saved: {csv_path}")
    
    # Print summary
    print("\n📊 SUMMARY STATISTICS:")
    print(summary_df.to_string(index=False))
    
    return summary_df


@timer
def create_top_zones_report(pagerank_df, communities_df, output_dir):
    """
    Tạo báo cáo top zones với thông tin chi tiết
    
    Args:
        pagerank_df: PageRank DataFrame
        communities_df: Communities DataFrame
        output_dir: Output directory
    """
    print_section("TẠO TOP ZONES REPORT")
    
    # Join PageRank với Communities
    joined = pagerank_df.join(communities_df, on="zone_id", how="inner") \
        .select("zone_id", "pagerank", "community_id") \
        .orderBy(desc("pagerank"))
    
    # Convert to Pandas top 50
    top50 = joined.limit(50).toPandas()
    
    # Add rank
    top50['rank'] = range(1, len(top50) + 1)
    
    # Reorder columns
    top50 = top50[['rank', 'zone_id', 'pagerank', 'community_id']]
    
    # Save as CSV
    csv_path = f"{output_dir}/top50_zones_detailed.csv"
    top50.to_csv(csv_path, index=False)
    print(f"✅ Saved: {csv_path}")
    
    # Print top 20
    print("\n🏆 TOP 20 MOST IMPORTANT ZONES:")
    print(top50.head(20).to_string(index=False))


def main():
    """Main execution"""
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║     NYC TAXI GRAPH MINING - BƯỚC 4: VISUALIZATION             ║
    ║                                                                ║
    ║  Mục tiêu: Tạo visualizations và reports cho kết quả         ║
    ║  Output: Charts, graphs, and summary statistics              ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Create output directory
    ensure_dir(LOCAL_VISUALIZATIONS_DIR)
    
    # Create Spark session (local mode for visualization)
    from spark_config import create_local_spark_session
    spark = create_local_spark_session("NYC_Taxi_Visualization")
    
    try:
        # Step 1: Load results
        pagerank_df, communities_df, community_sizes_df = load_results(spark)
        
        # Step 2: PageRank visualizations
        plot_pagerank_distribution(pagerank_df, LOCAL_VISUALIZATIONS_DIR)
        
        # Step 3: Community visualizations
        plot_community_analysis(community_sizes_df, LOCAL_VISUALIZATIONS_DIR)
        
        # Step 4: Summary statistics
        create_summary_statistics(
            pagerank_df, 
            communities_df, 
            community_sizes_df,
            LOCAL_VISUALIZATIONS_DIR
        )
        
        # Step 5: Top zones report
        create_top_zones_report(
            pagerank_df,
            communities_df,
            LOCAL_VISUALIZATIONS_DIR
        )
        
        print("\n" + "="*70)
        print("🎉 HOÀN THÀNH TẤT CẢ VISUALIZATIONS!")
        print("="*70)
        print(f"\n📂 Tất cả visualizations đã được lưu tại:")
        print(f"   {LOCAL_VISUALIZATIONS_DIR}")
        print("\n📊 Files tạo ra:")
        print("   - pagerank_distribution.png")
        print("   - community_analysis.png")
        print("   - summary_statistics.csv")
        print("   - top50_zones_detailed.csv")
        
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
