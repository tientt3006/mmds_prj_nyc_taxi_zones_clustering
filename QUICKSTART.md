# 🚀 QUICK START GUIDE - NYC Taxi Graph Mining

## TL;DR - Các bước chính

### 1️⃣ Setup Cluster (lần đầu tiên)

```bash
# Trên cả 2 máy Ubuntu VMs
sudo apt update && sudo apt upgrade -y
sudo apt install openjdk-11-jdk python3 python3-pip openssh-server -y

# Cài Hadoop (xem setup_guide.md cho chi tiết)
# Cài Spark
# Thiết lập SSH passwordless
```

### 2️⃣ Download Data

```bash
# Trên master node
mkdir ~/nyc_taxi_data
cd ~/nyc_taxi_data

# Download 24 tháng data (2019-2020)
for year in 2019 2020; do
    for month in {01..12}; do
        wget "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_${year}-${month}.parquet"
    done
done

# Upload lên HDFS
hdfs dfs -mkdir -p /user/taxi/raw_data
hdfs dfs -put *.parquet /user/taxi/raw_data/
```

### 3️⃣ Chạy Pipeline

```bash
cd ~/massive_data_mining

# **QUAN TRỌNG: Kiểm tra Python environment trước**
bash check_python_env.sh

# Cách 1: Chạy tất cả cùng lúc
bash run_all.sh

# Cách 2: Chạy từng bước với HDFS archive
cd src

# Bước 1: Build graph
spark-submit --master spark://master:7077 \
    --executor-memory 500m \
    --driver-memory 500m \
    --archives hdfs://master:9000/user/taxi/python_env/mmds-venv.tar.gz#mmds-venv \
    --conf spark.pyspark.python=./mmds-venv/bin/python3 \
    --conf spark.pyspark.driver.python=python3 \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    1_build_graph.py

# Bước 2: PageRank
spark-submit --master spark://master:7077 \
    --executor-memory 2g \
    --driver-memory 2g \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    2_pagerank.py

# Bước 3: Clustering
spark-submit --master spark://master:7077 \
    --executor-memory 2g \
    --driver-memory 2g \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    3_clustering.py

# Bước 4: Visualization
python3 4_visualization.py

# Bước 5: Benchmark
spark-submit --master spark://master:7077 \
    --executor-memory 2g \
    --driver-memory 2g \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    5_benchmark.py
```

### 4️⃣ Xem Kết Quả

```bash
# Download kết quả từ HDFS
hdfs dfs -get /user/taxi/results/ ~/results/

# Xem visualizations
cd ~/massive_data_mining/results/visualizations/
ls -lh

# Xem top zones
cat top50_zones_detailed.csv

# Xem summary
cat summary_statistics.csv
```

---

## 📊 Web UI để Monitor

Mở browser và truy cập:

- **HDFS NameNode:** http://master:9870
- **Spark Master:** http://master:8080
- **YARN ResourceManager:** http://master:8088
- **Spark Application UI:** http://master:4040 (khi job đang chạy)

---

## ⏱️ Thời gian ước tính

Với cluster 2 nodes (10GB RAM total):

| Bước | Thời gian | Ghi chú |
|------|-----------|---------|
| Download data | 2-4 giờ | Tùy tốc độ mạng |
| Upload to HDFS | 30-60 phút | ~30GB data |
| Build graph | 1-2 giờ | Scan toàn bộ data |
| PageRank | 30-60 phút | 20 iterations |
| Clustering | 20-40 phút | Label Propagation |
| Visualization | 5-10 phút | Chạy local |
| Benchmark | 30-60 phút | Multiple runs |

**Tổng cộng:** ~5-8 giờ (chạy tự động)

---

## 🔧 Troubleshooting Nhanh

### ❌ Out of Memory

```bash
# Giảm memory allocation
--executor-memory 1g --driver-memory 1g

# Hoặc tăng RAM cho VMs
# Shutdown VM → VMware Settings → Memory → Tăng lên 6GB
```

### ❌ HDFS Connection Refused

```bash
# Restart HDFS
stop-dfs.sh
start-dfs.sh

# Kiểm tra
jps  # Phải thấy NameNode, DataNode
```

### ❌ Spark Workers Not Connected

```bash
# Check /etc/hosts
cat /etc/hosts  # Phải có master và worker1

# Test SSH
ssh worker1  # Phải không cần password

# Restart Spark
stop-master.sh && stop-workers.sh
start-master.sh && start-workers.sh
```

### ❌ GraphFrames Not Found

```bash
# Đảm bảo dùng --packages
spark-submit --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 ...

# Hoặc download JAR thủ công
wget https://repos.spark-packages.org/graphframes/graphframes/0.8.3-spark3.5-s_2.12/graphframes-0.8.3-spark3.5-s_2.12.jar
sudo cp *.jar $SPARK_HOME/jars/
```

---

## 📋 Pre-flight Checklist

Trước khi chạy pipeline, đảm bảo:

- [ ] 2 VMs Ubuntu đã cài đặt và chạy
- [ ] Hadoop HDFS đã được cấu hình và khởi động
- [ ] Spark cluster đã được cấu hình và khởi động
- [ ] SSH passwordless giữa master-worker đã setup
- [ ] /etc/hosts đã có entries cho master và worker
- [ ] Java 11 đã được cài đặt
- [ ] Python 3 và pip đã được cài đặt
- [ ] Dữ liệu taxi đã được upload lên HDFS
- [ ] GraphFrames JAR đã được cài đặt

Kiểm tra nhanh:

```bash
# Check HDFS
hdfs dfs -ls /

# Check Spark
curl http://master:8080

# Check data
hdfs dfs -ls /user/taxi/raw_data/

# Check SSH
ssh worker1 "hostname"

# Check Java
java -version

# Check Python packages
pip3 list | grep pyspark
```

---

## 💡 Tips

### Để test nhanh trước khi chạy full data:

1. **Sửa trong `1_build_graph.py`:**
   ```python
   # Thêm .sample() để test với subset
   df = spark.read.parquet(HDFS_RAW_DATA).sample(0.01)  # 1% data
   ```

2. **Giảm số iterations trong PageRank:**
   ```python
   # Trong spark_config.py
   PAGERANK_ITERATIONS = 5  # Thay vì 20
   ```

### Để monitor resources:

```bash
# Trên master node
htop  # Xem CPU và RAM usage

# Xem Spark logs
tail -f $SPARK_HOME/logs/spark-*.out

# Xem HDFS disk usage
hdfs dfs -df -h
```

---

## 📞 Need Help?

1. **Xem logs chi tiết:**
   ```bash
   # Spark logs
   ls $SPARK_HOME/logs/
   
   # Hadoop logs
   ls $HADOOP_HOME/logs/
   ```

2. **Check cluster health:**
   ```bash
   # HDFS health
   hdfs dfsadmin -report
   
   # YARN health
   yarn node -list
   ```

3. **Xem setup_guide.md** để biết chi tiết cấu hình

4. **Xem README.md** để hiểu architecture và workflow

---

**Chúc may mắn với dự án! 🎉**
