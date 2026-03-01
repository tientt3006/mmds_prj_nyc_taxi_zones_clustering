# Hướng dẫn cài đặt NYC Taxi Graph Mining với Docker

## MỤC LỤC
1. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
3. [Build và khởi động cluster](#build-và-khởi-động-cluster)
4. [Kiểm tra hệ thống](#kiểm-tra-hệ-thống)
5. [Upload dữ liệu](#upload-dữ-liệu)
6. [Chạy code phân tích](#chạy-code-phân-tích)
7. [Troubleshooting](#troubleshooting)

---

## BUILD VÀ KHỞI ĐỘNG CLUSTER

### 1. Clone project

```bash
cd <your prj folder>
```

### 2. Build Docker images

```bash
cd docker

# Build images
docker-compose build

# Xem images đã build
docker images | grep taxi-mining
```

### 3. Khởi động cluster

```bash
# Khởi động tất cả services (detached mode)
docker-compose up -d

# Xem logs
docker-compose logs -f

# Xem logs của từng service
docker-compose logs -f master
docker-compose logs -f worker1
```

### 4. Kiểm tra containers đang chạy

```bash
# List containers
docker-compose ps

# Kết quả mong đợi:
# NAME                  STATUS         PORTS
# taxi-mining-master    Up 2 minutes   0.0.0.0:8088->8088/tcp, ...
# taxi-mining-worker1   Up 2 minutes   
# taxi-mining-worker2   Up 2 minutes   

# nếu cần rebuilt
docker-compose down -v
# Xóa images cũ
docker rmi docker-master docker-worker1 taxi-mining-master taxi-mining-worker 2>nul

```

---

## KIỂM TRA HỆ THỐNG

### 1. Kiểm tra Web UIs

Mở trình duyệt và truy cập:

| Service | URL | Mô tả |
|---------|-----|-------|
| **HDFS NameNode** | http://localhost:9870 | Quản lý HDFS |
| **YARN ResourceManager** | http://localhost:8088 | Quản lý jobs |
| **Spark Master** | http://localhost:8080 | Spark cluster UI |
| **Spark History Server** | http://localhost:18080 | Lịch sử Spark jobs |

### 2. Kiểm tra HDFS

```bash
# Vào container master
docker exec -it taxi-mining-master bash

# Test HDFS
hdfs dfs -mkdir /test
echo "Hello HDFS" > /tmp/test.txt
hdfs dfs -put /tmp/test.txt /test/
hdfs dfs -cat /test/test.txt
hdfs dfs -rm -r /test

# Thoát container
exit
```

### 3. Kiểm tra Spark

```bash
# Vào container master
docker exec -it taxi-mining-master bash

# Test Spark job (tính Pi)
spark-submit \
    --class org.apache.spark.examples.SparkPi \
    --master spark://master:7077 \
    $SPARK_HOME/examples/jars/spark-examples_*.jar 100

# PySpark shell
pyspark --master spark://master:7077

# Trong PySpark shell:
>>> rdd = sc.parallelize(range(100))
>>> print(rdd.sum())
>>> exit()

# Thoát container
exit
```

---

## UPLOAD DỮ LIỆU

### 1. Download dữ liệu NYC Taxi

```bash
# Trên máy host (Windows/Mac/Linux)
cd <your prj folder>

# Tạo thư mục data
mkdir -p data/raw

# Download sample data (tháng 1/2019)
# Windows (PowerShell)
Invoke-WebRequest -Uri "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2019-01.parquet" -OutFile "data/raw/yellow_tripdata_2019-01.parquet"

# Linux/Mac
cd data/raw
wget "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2019-01.parquet"

# Download zone lookup
wget "https://d37ci6vzurychx.cloudfront.net/misc/taxi+_zone_lookup.csv"
```

### 2. Copy dữ liệu vào container

```bash
# Copy từ host vào container master
docker cp data/raw/yellow_tripdata_2019-01.parquet taxi-mining-master:/tmp/
docker cp data/raw/taxi+_zone_lookup.csv taxi-mining-master:/tmp/
```

### 3. Upload lên HDFS

```bash
# Vào container master
docker exec -it taxi-mining-master bash

# Tạo thư mục HDFS
hdfs dfs -mkdir -p /user/taxi/raw_data
hdfs dfs -mkdir -p /user/taxi/zone_lookup

# Upload dữ liệu
hdfs dfs -put /tmp/yellow_tripdata_2019-01.parquet /user/taxi/raw_data/
hdfs dfs -put /tmp/taxi+_zone_lookup.csv /user/taxi/zone_lookup/

# Kiểm tra
hdfs dfs -ls /user/taxi/raw_data/
hdfs dfs -ls /user/taxi/zone_lookup/

# Xem thông tin chi tiết
hdfs fsck /user/taxi/raw_data/ -files -blocks -locations

# Thoát container
exit
```

---

## CHẠY CODE PHÂN TÍCH

### 1. Copy code vào container

```bash
# Từ thư mục project root
docker cp src/ taxi-mining-master:/workspace/
docker cp notebooks/ taxi-mining-master:/workspace/
docker cp config/ taxi-mining-master:/workspace/
```

### 2. Chạy script Python

```bash
# Vào container master
docker exec -it taxi-mining-master bash

# Navigate to workspace
cd /workspace

# Chạy script build graph
spark-submit \
    --master spark://master:7077 \
    --deploy-mode client \
    --driver-memory 2g \
    --executor-memory 2g \
    --executor-cores 2 \
    --num-executors 2 \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    src/1_build_graph.py

# Chạy PageRank
spark-submit \
    --master spark://master:7077 \
    --deploy-mode client \
    --driver-memory 2g \
    --executor-memory 2g \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    src/2_pagerank.py

# Thoát container
exit
```

### 3. Sử dụng Jupyter Notebook

```bash
# Khởi động Jupyter trong container
docker exec -it taxi-mining-master bash

# Start Jupyter
jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root

# Copy token từ output, ví dụ:
# http://127.0.0.1:8888/?token=abc123...

# Mở trình duyệt trên máy host:
# http://localhost:8888/?token=abc123...
```

### 4. Lấy kết quả về máy host

```bash
# Copy results từ container ra host
docker cp taxi-mining-master:/workspace/results/ ./results/

# Hoặc từ HDFS
docker exec taxi-mining-master hdfs dfs -get /user/taxi/results/ /tmp/results
docker cp taxi-mining-master:/tmp/results ./results/
```

---

## QUẢN LÝ CLUSTER

### Dừng cluster

```bash
# Dừng tất cả containers (giữ lại dữ liệu)
docker-compose stop

# Dừng và xóa containers (giữ volumes)
docker-compose down

# Dừng và xóa containers + volumes (MẤT DỮ LIỆU)
docker-compose down -v
```

### Khởi động lại cluster

```bash
# Khởi động lại từ trạng thái stopped
docker-compose start

# Hoặc khởi động mới hoàn toàn
docker-compose up -d
```

### Xem logs

```bash
# Logs tất cả services
docker-compose logs -f

# Logs service cụ thể
docker-compose logs -f master
docker-compose logs -f worker1

# Logs 100 dòng cuối
docker-compose logs --tail=100 master
```

### Scale workers

```bash
# Cluster hiện có 2 workers (worker1, worker2)
# Để thêm worker động dùng scale (nếu dùng service tên 'worker'):
docker-compose up -d --scale worker=3

# Để restart worker cụ thể
docker-compose restart worker1
docker-compose restart worker2
```

### Vào container để debug

```bash
# Vào master
docker exec -it taxi-mining-master bash

# Vào worker1
docker exec -it taxi-mining-worker1 bash

# Vào worker2
docker exec -it taxi-mining-worker2 bash

# Chạy lệnh trực tiếp không vào shell
docker exec taxi-mining-master hdfs dfs -ls /
```

---

## TROUBLESHOOTING

### 1. Container không khởi động

```bash
# Xem logs chi tiết
docker-compose logs master

# Kiểm tra tài nguyên
docker stats

# Restart container
docker-compose restart master
```

### 2. HDFS không hoạt động

```bash
# Vào container master
docker exec -it taxi-mining-master bash

# Kiểm tra HDFS processes
jps
# Nên thấy: NameNode, DataNode, SecondaryNameNode
# Trên mỗi worker: DataNode

# Format lại NameNode (CHỈ khi cần thiết - MẤT DỮ LIỆU)
hdfs namenode -format -force

# Restart HDFS
stop-dfs.sh
start-dfs.sh
```

### 3. Spark job bị fail

```bash
# Xem logs Spark
docker exec taxi-mining-master tail -f $SPARK_HOME/logs/*

# Xem Spark UI
# http://localhost:8080

# Kiểm tra workers
docker exec taxi-mining-master cat $SPARK_HOME/conf/workers
```

### 4. Out of Memory

```bash
# Tăng memory cho container trong docker-compose.yml
# Sửa phần:
    deploy:
      resources:
        limits:
          memory: 4G  # Tăng từ 3G lên 4G

# Hoặc giảm executor memory trong spark-submit
spark-submit \
    --driver-memory 1g \
    --executor-memory 1g \
    ...
```

### 5. Port đã được sử dụng

```bash
# Windows: Tìm process sử dụng port
netstat -ano | findstr :9870
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :9870
kill -9 <PID>

# Hoặc đổi port trong docker-compose.yml
```

### 6. Clean up toàn bộ

```bash
# Dừng và xóa containers
docker-compose down -v

# Xóa images
docker rmi $(docker images -q 'taxi-mining*')

# Xóa volumes
docker volume prune -f

# Xóa tất cả
docker system prune -a --volumes -f
```

---

## MONITORING VÀ PERFORMANCE

### 1. Theo dõi tài nguyên

```bash
# Real-time stats
docker stats

# Top processes trong container
docker exec taxi-mining-master top
```

### 2. Kiểm tra HDFS health

```bash
docker exec taxi-mining-master hdfs dfsadmin -report
docker exec taxi-mining-master hdfs fsck / -files -blocks -locations
```

### 3. Kiểm tra Spark cluster

```bash
# Spark Master UI: http://localhost:8080
# YARN UI: http://localhost:8088
# Application UI: http://localhost:4040 (khi job chạy)
```

---

## BEST PRACTICES

### 1. Backup dữ liệu

```bash
# Backup HDFS
docker exec taxi-mining-master hdfs dfs -get /user/taxi /tmp/backup
docker cp taxi-mining-master:/tmp/backup ./backup/

# Restore
docker cp ./backup/ taxi-mining-master:/tmp/
docker exec taxi-mining-master hdfs dfs -put /tmp/backup/* /user/taxi/
```

### 2. Lưu kết quả

```bash
# Luôn copy results ra host
docker cp taxi-mining-master:/workspace/results ./results/

# Hoặc mount volume (thêm vào docker-compose.yml)
volumes:
  - ./results:/workspace/results
```

### 3. Development workflow

```bash
# 1. Viết code trên host (VSCode, PyCharm, etc.)
# 2. Copy vào container
docker cp src/new_script.py taxi-mining-master:/workspace/src/

# 3. Test
docker exec taxi-mining-master spark-submit /workspace/src/new_script.py

# 4. Lấy kết quả
docker cp taxi-mining-master:/workspace/results ./results/
```

---

## TÀI LIỆU THAM KHẢO

- [Docker Documentation](https://docs.docker.com/)
- [Hadoop Documentation](https://hadoop.apache.org/docs/stable/)
- [Spark Documentation](https://spark.apache.org/docs/latest/)
- [GraphFrames Guide](https://graphframes.github.io/graphframes/docs/_site/user-guide.html)

---

**🎉 HOÀN THÀNH! Cluster đã sẵn sàng để phân tích dữ liệu NYC Taxi.**
