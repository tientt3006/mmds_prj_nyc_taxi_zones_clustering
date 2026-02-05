#!/bin/bash

# Script tự động chạy toàn bộ pipeline NYC Taxi Graph Mining

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║     NYC TAXI GRAPH MINING - AUTOMATED PIPELINE                ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"

cd ~/massive_data_mining

export PYTHONPATH="${PWD}:${PYTHONPATH}"

# Check prerequisites
echo -e "\n📋 Kiểm tra prerequisites..."
bash check_python_env.sh

echo -e "\n❓ Bạn có muốn tiếp tục? (y/n)"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Hủy bỏ pipeline"
    exit 0
fi

# Bước 1: Build Graph
echo -e "\n╔════════════════════════════════════════════════════════════════╗"
echo "║                    BƯỚC 1: BUILD GRAPH                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"

spark-submit \
    --master spark://master:7077 \
    --deploy-mode client \
    --driver-memory 500m \
    --executor-memory 500m \
    --executor-cores 1 \
    --num-executors 2 \
    --archives hdfs://master:9000/user/taxi/python_env/mmds-venv.tar.gz#mmds-venv \
    --conf spark.pyspark.python=./mmds-venv/bin/python3 \
    --conf spark.pyspark.driver.python=python3 \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    src/1_build_graph.py

if [ $? -ne 0 ]; then
    echo "❌ Lỗi ở bước 1: Build Graph"
    exit 1
fi

# Bước 2: PageRank
echo -e "\n╔════════════════════════════════════════════════════════════════╗"
echo "║                    BƯỚC 2: PAGERANK                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"

spark-submit \
    --master spark://master:7077 \
    --deploy-mode client \
    --driver-memory 1g \
    --executor-memory 2g \
    --executor-cores 2 \
    --num-executors 2 \
    --archives hdfs://master:9000/user/taxi/python_env/mmds-venv.tar.gz#mmds-venv \
    --conf spark.pyspark.python=./mmds-venv/bin/python3 \
    --conf spark.pyspark.driver.python=python3 \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    src/2_pagerank.py

if [ $? -ne 0 ]; then
    echo "❌ Lỗi ở bước 2: PageRank"
    exit 1
fi

# Bước 3: Clustering
echo -e "\n╔════════════════════════════════════════════════════════════════╗"
echo "║                    BƯỚC 3: CLUSTERING                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"

bash run_clustering.sh

if [ $? -ne 0 ]; then
    echo "❌ Lỗi ở bước 3: Clustering"
    exit 1
fi

# Bước 4: Visualization
echo -e "\n╔════════════════════════════════════════════════════════════════╗"
echo "║                   BƯỚC 4: VISUALIZATION                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"

bash run_visualization.sh

if [ $? -ne 0 ]; then
    echo "❌ Lỗi ở bước 4: Visualization"
    exit 1
fi

# Bước 5: Benchmark
echo -e "\n╔════════════════════════════════════════════════════════════════╗"
echo "║                    BƯỚC 5: BENCHMARK                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"

bash run_benchmark.sh

if [ $? -ne 0 ]; then
    echo "❌ Lỗi ở bước 5: Benchmark"
    exit 1
fi

echo -e "\n╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║           🎉 HOÀN THÀNH TOÀN BỘ PIPELINE! 🎉                  ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"

echo -e "\n📂 Kết quả đã được lưu tại:"
echo "   - HDFS: /user/taxi/results/"
echo "   - Local: ~/massive_data_mining/results/"
