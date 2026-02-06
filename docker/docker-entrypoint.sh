#!/bin/bash

echo "========================================="
echo "Starting NYC Taxi Mining Container"
echo "Role: ${HADOOP_ROLE:-unknown} / ${SPARK_ROLE:-unknown}"
echo "========================================="

# Khởi động SSH service
service ssh start

# Kiểm tra role và thực hiện khởi động tương ứng
if [ "$HADOOP_ROLE" = "master" ]; then
    echo "Initializing HDFS NameNode..."
    
    # Format NameNode nếu chưa được format
    if [ ! -d "/hadoop_data/namenode/current" ]; then
        hdfs namenode -format -force -nonInteractive
    fi
    
    echo "Starting HDFS services..."
    start-dfs.sh
    
    echo "Starting YARN services..."
    start-yarn.sh
fi

if [ "$SPARK_ROLE" = "master" ]; then
    echo "Starting Spark Master..."
    start-master.sh
    
    echo "Starting Spark History Server..."
    start-history-server.sh
fi

if [ "$SPARK_ROLE" = "worker" ]; then
    echo "Waiting for Spark Master to be ready..."
    sleep 30
    
    echo "Starting Spark Worker..."
    start-worker.sh ${SPARK_MASTER_URL:-spark://master:7077}
fi

echo "========================================="
echo "Container started successfully!"
echo "========================================="

# Giữ container chạy
exec "$@"
