#!/bin/bash

# Script chạy test trên máy đơn và so sánh với cluster

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║     SINGLE MACHINE vs CLUSTER PERFORMANCE TEST                ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"

cd ~/massive_data_mining

# =====================================================================
# BƯỚC 1: Test trên máy đơn (Local Mode)
# =====================================================================
echo -e "\n📍 BƯỚC 1: Running Single Machine Test (Local Mode)"
echo "⚠️  WARNING: Có thể crash nếu data quá lớn!"

python3 src/test_single_machine.py \
    --data-path "hdfs://master:9000/user/taxi/raw_data/*.parquet" \
    --output-dir "results/single_machine" \
    --mode basic
# --mode stress: for tăng dần độ lớn data để test giới hạn máy đơn

if [ $? -ne 0 ]; then
    echo "❌ Single machine test FAILED (expected if data too large)"
fi

# =====================================================================
# BƯỚC 2: Test trên cluster (Distributed Mode)
# =====================================================================
echo -e "\n📍 BƯỚC 2: Running Cluster Test (Distributed Mode)"

# Chạy benchmark trên cluster (sử dụng script có sẵn)
bash run_benchmark.sh

# =====================================================================
# BƯỚC 3: So sánh kết quả
# =====================================================================
echo -e "\n📍 BƯỚC 3: Comparing Results"

python3 src/benchmark_comparison.py \
    --single "results/single_machine/single_machine_metrics.csv" \
    --cluster "results/benchmark/performance_metrics.csv" \
    --output "results/comparison_plots.png"

echo -e "\n╔════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ TEST COMPLETED                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"

echo -e "\n📂 Kết quả:"
echo "   - Single machine: results/single_machine/"
echo "   - Cluster:        results/benchmark/"
echo "   - Comparison:     results/comparison_plots.png"