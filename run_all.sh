#!/bin/bash

###############################################################################
# RUN_ALL.SH - Chạy toàn bộ pipeline NYC Taxi Graph Mining
# 
# Sử dụng: bash run_all.sh
#
# Lưu ý: 
# - Chạy script này trên Master node
# - Đảm bảo HDFS và Spark đã được khởi động
# - Đảm bảo dữ liệu đã được upload lên HDFS
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SPARK_MASTER="spark://master:7077"
EXECUTOR_MEMORY="2g"
DRIVER_MEMORY="2g"
GRAPHFRAMES_PACKAGE="graphframes:graphframes:0.8.3-spark3.5-s_2.12"

# Functions
print_header() {
    echo ""
    echo "================================================================="
    echo -e "${BLUE}$1${NC}"
    echo "================================================================="
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_services() {
    print_header "KIỂM TRA CÁC SERVICES"
    
    # Check HDFS
    echo "Checking HDFS..."
    if hdfs dfs -ls / > /dev/null 2>&1; then
        print_success "HDFS is running"
    else
        print_error "HDFS is not running. Please start HDFS first."
        exit 1
    fi
    
    # Check Spark
    echo "Checking Spark..."
    if curl -s http://master:8080 > /dev/null 2>&1; then
        print_success "Spark Master is running"
    else
        print_warning "Cannot connect to Spark Web UI. Check if Spark is running."
    fi
    
    # Check data
    echo "Checking data..."
    if hdfs dfs -ls /user/taxi/raw_data/ > /dev/null 2>&1; then
        file_count=$(hdfs dfs -ls /user/taxi/raw_data/ | grep -c "\.parquet")
        print_success "Found $file_count Parquet files in HDFS"
    else
        print_error "No data found in HDFS. Please upload data first."
        exit 1
    fi
}

run_step() {
    local step_num=$1
    local step_name=$2
    local script_name=$3
    local run_mode=$4  # "spark" or "local"
    
    print_header "BƯỚC $step_num: $step_name"
    
    echo "Script: $script_name"
    echo "Start time: $(date)"
    echo ""
    
    start_time=$(date +%s)
    
    if [ "$run_mode" == "spark" ]; then
        # Run with spark-submit
        spark-submit \
            --master $SPARK_MASTER \
            --executor-memory $EXECUTOR_MEMORY \
            --driver-memory $DRIVER_MEMORY \
            --packages $GRAPHFRAMES_PACKAGE \
            --conf spark.sql.adaptive.enabled=true \
            --conf spark.serializer=org.apache.spark.serializer.KryoSerializer \
            $script_name
    else
        # Run local Python
        python3 $script_name
    fi
    
    exit_code=$?
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    
    echo ""
    echo "End time: $(date)"
    echo "Duration: $duration seconds"
    
    if [ $exit_code -eq 0 ]; then
        print_success "Bước $step_num hoàn thành!"
    else
        print_error "Bước $step_num thất bại với exit code $exit_code"
        exit $exit_code
    fi
    
    echo ""
    sleep 2
}

cleanup_previous_results() {
    print_header "DỌN DẸP KẾT QUẢ CŨ"
    
    echo "Xóa kết quả cũ trên HDFS..."
    hdfs dfs -rm -r -f /user/taxi/graph/ || true
    hdfs dfs -rm -r -f /user/taxi/results/ || true
    
    echo "Tạo thư mục mới..."
    hdfs dfs -mkdir -p /user/taxi/graph/
    hdfs dfs -mkdir -p /user/taxi/results/
    
    print_success "Đã dọn dẹp xong"
}

main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║     NYC TAXI GRAPH MINING - FULL PIPELINE EXECUTION           ║"
    echo "║                                                                ║"
    echo "║  Sẽ chạy toàn bộ 5 bước:                                      ║"
    echo "║    1. Build Graph (Edge List)                                 ║"
    echo "║    2. PageRank Calculation                                    ║"
    echo "║    3. Community Detection                                     ║"
    echo "║    4. Visualization                                           ║"
    echo "║    5. Benchmark                                               ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Check if user wants to continue
    read -p "Tiếp tục? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Đã hủy."
        exit 0
    fi
    
    # Record start time
    pipeline_start=$(date +%s)
    
    # Pre-flight checks
    check_services
    
    # Optional: cleanup
    read -p "Xóa kết quả cũ? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup_previous_results
    fi
    
    # Navigate to src directory
    cd "$(dirname "$0")/src"
    
    # Run all steps
    run_step 1 "BUILD GRAPH" "1_build_graph.py" "spark"
    run_step 2 "PAGERANK" "2_pagerank.py" "spark"
    run_step 3 "CLUSTERING" "3_clustering.py" "spark"
    run_step 4 "VISUALIZATION" "4_visualization.py" "local"
    run_step 5 "BENCHMARK" "5_benchmark.py" "spark"
    
    # Calculate total time
    pipeline_end=$(date +%s)
    total_duration=$((pipeline_end - pipeline_start))
    hours=$((total_duration / 3600))
    minutes=$(((total_duration % 3600) / 60))
    seconds=$((total_duration % 60))
    
    # Final summary
    print_header "🎉 HOÀN THÀNH TẤT CẢ CÁC BƯỚC!"
    
    echo "Tổng thời gian: ${hours}h ${minutes}m ${seconds}s"
    echo ""
    echo "📂 Kết quả được lưu tại:"
    echo "   - HDFS: /user/taxi/graph/ và /user/taxi/results/"
    echo "   - Local: ../results/"
    echo ""
    echo "📊 Các file output:"
    echo "   - Edge list: /user/taxi/graph/edge_list/"
    echo "   - PageRank scores: /user/taxi/results/pagerank_scores/"
    echo "   - Communities: /user/taxi/results/community_assignments/"
    echo "   - Visualizations: ../results/visualizations/"
    echo "   - Benchmarks: ../results/benchmarks/"
    echo ""
    echo "🔗 Web UIs để theo dõi:"
    echo "   - HDFS: http://master:9870"
    echo "   - Spark: http://master:8080"
    echo "   - YARN: http://master:8088"
    echo ""
    
    print_success "Pipeline execution completed successfully!"
}

# Run main function
main
