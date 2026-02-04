# NYC Taxi Graph Mining - Massive Data Mining Project

## 📌 Tổng quan

Dự án phân tích đồ thị giao thông taxi NYC quy mô lớn (~30GB dữ liệu) sử dụng các thuật toán Graph Mining phân tán.

**Mục tiêu:**
- Xây dựng đồ thị giao thông từ 200-300 triệu chuyến taxi
- Tính PageRank để xác định taxi zones quan trọng nhất
- Phát hiện communities (clusters) của các zones
- Chứng minh scalability trên cluster phân tán

**Dataset:** NYC TLC Yellow Taxi Trip Records (2019-2020)

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────┐
│                    HDFS Layer                        │
│  - Raw Data (~30GB Parquet files)                   │
│  - Processed Edge List                               │
│  - Results (PageRank, Communities)                   │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│              Spark Processing Layer                  │
│  - MapReduce: Build Graph                           │
│  - GraphX: PageRank Algorithm                       │
│  - GraphFrames: Community Detection                 │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│                Visualization Layer                   │
│  - Matplotlib/Seaborn Charts                        │
│  - Summary Statistics                                │
│  - Reports                                           │
└─────────────────────────────────────────────────────┘
```

**Cluster Setup:**
- Master Node (Ubuntu VM): 6GB RAM, 2-4 CPU cores
- Worker Node (Ubuntu VM): 4GB RAM, 2 CPU cores
- HDFS replication: 2
- Spark Standalone Mode

---

## 📂 Cấu trúc project

```
massive_data_mining/
├── config/
│   └── spark_config.py          # Cấu hình Spark session
├── src/
│   ├── utils.py                 # Utility functions
│   ├── 1_build_graph.py         # Bước 1: Xây dựng edge list
│   ├── 2_pagerank.py            # Bước 2: Tính PageRank
│   ├── 3_clustering.py          # Bước 3: Graph clustering
│   ├── 4_visualization.py       # Bước 4: Visualizations
│   └── 5_benchmark.py           # Bước 5: Benchmark
├── results/                      # Kết quả output
│   ├── visualizations/          # Charts và graphs
│   └── benchmarks/              # Benchmark results
├── notebooks/                    # Jupyter notebooks (optional)
├── setup_guide.md               # Hướng dẫn cài đặt chi tiết
├── intruction.md                # Đề bài gốc
└── README.md                    # File này
```

---

## 🚀 Hướng dẫn sử dụng

### Bước 1: Cài đặt môi trường

**Chi tiết xem file: `setup_guide.md`**

Tóm tắt:
1. Cài đặt 2 máy ảo Ubuntu trên VMware
2. Cài đặt Hadoop cluster (HDFS + YARN)
3. Cài đặt Spark cluster
4. Cài đặt GraphFrames
5. Thiết lập SSH passwordless giữa các nodes

### Bước 2: Download và upload dữ liệu

```bash
# Trên master node
cd ~
mkdir nyc_taxi_data

# Download dữ liệu (2019-2020)
for year in 2019 2020; do
    for month in {01..12}; do
        wget "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_${year}-${month}.parquet"
    done
done

# Upload lên HDFS
hdfs dfs -mkdir -p /user/taxi/raw_data
hdfs dfs -put *.parquet /user/taxi/raw_data/

# Kiểm tra
hdfs dfs -ls /user/taxi/raw_data/
```

### Bước 3: Chạy các bước processing

**Trên master node:**

```bash
cd massive_data_mining/src

# Bước 1: Build graph (edge list)
spark-submit --master spark://master:7077 \
    --executor-memory 2g \
    --driver-memory 2g \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    1_build_graph.py

# Bước 2: Tính PageRank
spark-submit --master spark://master:7077 \
    --executor-memory 2g \
    --driver-memory 2g \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    2_pagerank.py

# Bước 3: Graph clustering
spark-submit --master spark://master:7077 \
    --executor-memory 2g \
    --driver-memory 2g \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    3_clustering.py

# Bước 4: Visualization (chạy local)
python3 4_visualization.py

# Bước 5: Benchmark
spark-submit --master spark://master:7077 \
    --executor-memory 2g \
    --driver-memory 2g \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    5_benchmark.py
```

### Bước 4: Xem kết quả

```bash
# Download kết quả từ HDFS về local
hdfs dfs -get /user/taxi/results/ ../results/hdfs_results/

# Xem visualizations
cd ../results/visualizations/
ls -lh

# Xem summary
cat summary_statistics.csv
cat top50_zones_detailed.csv
```

---

## 📊 Kết quả mong đợi

### 1. Edge List
- ~50-100 triệu edges (cặp zones có trip)
- Trọng số = số chuyến taxi giữa 2 zones
- Format: `(src_zone, dst_zone, trip_count, total_fare, avg_distance)`

### 2. PageRank Results
- Xếp hạng 260 taxi zones theo importance
- Top zones: Manhattan CBD, airports (JFK, LaGuardia)
- Phân phối power-law (vài zones rất cao, nhiều zones thấp)

### 3. Communities
- 20-50 communities được phát hiện
- Mỗi community = nhóm zones có giao thông nội bộ chặt chẽ
- Có thể map với các khu vực địa lý thực tế

### 4. Visualizations
- Histogram phân phối PageRank
- Bar chart top zones
- Community size distribution
- Scatter plots

### 5. Benchmark
- So sánh runtime 1M vs 10M rows
- Đo speedup khi dùng cluster vs single node
- Chứng minh scalability

---

## 🔧 Troubleshooting

### Lỗi thường gặp

**1. Out of Memory**
```bash
# Giảm executor memory trong spark-submit
--executor-memory 1g
--driver-memory 1g

# Tăng số partitions
spark.sql.shuffle.partitions 400
```

**2. HDFS connection refused**
```bash
# Kiểm tra HDFS đang chạy
jps  # Phải thấy NameNode, DataNode

# Restart nếu cần
stop-dfs.sh
start-dfs.sh

# Kiểm tra Web UI
http://master:9870
```

**3. Spark worker không connect**
```bash
# Kiểm tra SSH passwordless
ssh worker1

# Kiểm tra /etc/hosts
cat /etc/hosts  # Phải có entry cho master và worker

# Restart Spark
stop-master.sh
stop-workers.sh
start-master.sh
start-workers.sh
```

**4. GraphFrames not found**
```bash
# Đảm bảo dùng --packages trong spark-submit
--packages graphframes:graphframes:0.8.3-spark3.5-s_2.12

# Hoặc copy JAR vào $SPARK_HOME/jars/
```

---

## 📈 Performance Tips

### Tối ưu cho RAM hạn chế

1. **Tăng số partitions:**
   ```python
   df.repartition(200)
   ```

2. **Unpersist không cần thiết:**
   ```python
   df.unpersist()
   ```

3. **Sử dụng broadcast cho small tables:**
   ```python
   from pyspark.sql.functions import broadcast
   large_df.join(broadcast(small_df), ...)
   ```

4. **Checkpoint cho iterative algorithms:**
   ```python
   sc.setCheckpointDir("/tmp/checkpoints")
   rdd.checkpoint()
   ```

---

## 📚 Tài liệu tham khảo

### Học thuật
- **Mining of Massive Datasets** - Leskovec, Rajaraman, Ullman (CS246 textbook)
- **PageRank Algorithm** - Page & Brin, 1998
- **Label Propagation** - Raghavan et al., 2007

### Kỹ thuật
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [GraphFrames User Guide](https://graphframes.github.io/graphframes/docs/_site/user-guide.html)
- [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

### Hadoop/HDFS
- [Hadoop Documentation](https://hadoop.apache.org/docs/stable/)
- [HDFS Architecture](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html)

---

## ✅ Checklist cho báo cáo

- [ ] Mô tả bài toán và dataset
- [ ] Giải thích vì sao "massive" (không chạy được trên PC)
- [ ] Mô hình hóa thành đồ thị (nodes, edges, weights)
- [ ] Giải thích thuật toán PageRank
- [ ] Công thức toán học (LaTeX)
- [ ] Pseudocode MapReduce
- [ ] Kết quả PageRank (top zones, phân phối)
- [ ] Kết quả Community Detection
- [ ] Visualization (charts, graphs)
- [ ] Benchmark và scalability analysis
- [ ] So sánh 1 node vs 2 nodes (runtime, memory)
- [ ] Kết luận và insight

---

## 👥 Thông tin nhóm

**Tên đề tài:** Graph-based Clustering các Taxi Zone từ NYC TLC Yellow Taxi Data

**Môn học:** Mining of Massive Data (MMDS)

**Công nghệ:**
- Apache Hadoop 3.3.6
- Apache Spark 3.5.0
- GraphFrames 0.8.3
- Python 3, PySpark

**Cluster:**
- 2 nodes Ubuntu VMs (VMware)
- Total RAM: 10GB
- HDFS replication: 2

---

## 📝 License

Educational project for Mining of Massive Data course.

---

## 🙏 Acknowledgments

- NYC Taxi & Limousine Commission for open data
- CS246 course materials (Stanford)
- Apache Spark and GraphFrames communities

---

**Last updated:** 2026-02-04
