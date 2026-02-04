# 📚 TÀI LIỆU TỔNG HỢP DỰ ÁN - NYC TAXI GRAPH MINING

## 📁 Cấu trúc thư mục hoàn chỉnh

```
massive_data_mining/
│
├── 📄 README.md                      ← Tổng quan dự án
├── 📄 QUICKSTART.md                  ← Hướng dẫn nhanh
├── 📄 setup_guide.md                 ← Hướng dẫn cài đặt chi tiết
├── 📄 PRESENTATION_GUIDE.md          ← Hướng dẫn báo cáo & bảo vệ
├── 📄 PROJECT_CHECKLIST.md           ← Checklist từng bước
├── 📄 intruction.md                  ← Đề bài gốc
├── 📄 requirements.txt               ← Python dependencies
├── 🔧 run_all.sh                     ← Script chạy toàn bộ pipeline
├── 🔧 check_setup.sh                 ← Script kiểm tra setup
│
├── 📂 config/
│   └── spark_config.py               ← Cấu hình Spark session
│
├── 📂 src/
│   ├── utils.py                      ← Utility functions
│   ├── 1_build_graph.py              ← Xây dựng đồ thị (MapReduce)
│   ├── 2_pagerank.py                 ← Tính PageRank
│   ├── 3_clustering.py               ← Graph clustering
│   ├── 4_visualization.py            ← Tạo visualizations
│   └── 5_benchmark.py                ← Benchmark & scalability
│
├── 📂 results/                        ← Kết quả (generated)
│   ├── visualizations/               ← Charts, graphs
│   │   ├── pagerank_distribution.png
│   │   ├── community_analysis.png
│   │   ├── summary_statistics.csv
│   │   └── top50_zones_detailed.csv
│   └── benchmarks/                   ← Benchmark results
│       └── benchmark_*.json
│
├── 📂 notebooks/                      ← Jupyter notebooks (optional)
│   ├── exploration.ipynb
│   └── analysis.ipynb
│
└── 📂 docs/                           ← Tài liệu báo cáo (tạo riêng)
    ├── report.pdf
    ├── slides.pptx
    └── screenshots/
```

---

## 🗺️ LỘ TRÌNH THỰC HIỆN (TIMELINE)

### Tuần 1-2: Setup cơ sở hạ tầng
- ✅ Cài đặt VMware VMs
- ✅ Cài đặt Hadoop cluster
- ✅ Cài đặt Spark cluster
- ✅ Test kết nối và services

### Tuần 3: Download và upload dữ liệu
- ✅ Download NYC Taxi data (24 tháng)
- ✅ Upload lên HDFS
- ✅ Verify data integrity

### Tuần 4-5: Development
- ✅ Viết code build graph
- ✅ Viết code PageRank
- ✅ Viết code clustering
- ✅ Test trên sample data

### Tuần 6-7: Chạy full pipeline
- ✅ Run build graph trên full data
- ✅ Run PageRank
- ✅ Run clustering
- ✅ Generate visualizations

### Tuần 8: Benchmark
- ✅ Chạy benchmark tests
- ✅ Thu thập metrics
- ✅ Phân tích scalability

### Tuần 9-10: Viết báo cáo
- ✅ Viết report (LaTeX/Word)
- ✅ Tạo slides presentation
- ✅ Chuẩn bị demo

### Tuần 11-12: Hoàn thiện và bảo vệ
- ✅ Review và polish
- ✅ Practice presentation
- ✅ Bảo vệ đồ án

---

## 🎯 CÁC FILE QUAN TRỌNG VÀ MỤC ĐÍCH

| File | Mục đích | Khi nào dùng |
|------|----------|--------------|
| **README.md** | Tổng quan project, architecture, usage | Đọc đầu tiên để hiểu project |
| **QUICKSTART.md** | Hướng dẫn nhanh, TL;DR | Cần setup và chạy nhanh |
| **setup_guide.md** | Hướng dẫn cài đặt chi tiết từng bước | Setup lần đầu, troubleshooting |
| **PRESENTATION_GUIDE.md** | Cấu trúc báo cáo, slides, Q&A | Viết báo cáo, chuẩn bị bảo vệ |
| **PROJECT_CHECKLIST.md** | Checklist từng bước thực hiện | Tracking progress, đảm bảo không miss bước |
| **run_all.sh** | Script tự động chạy pipeline | Chạy toàn bộ 5 bước cùng lúc |
| **check_setup.sh** | Kiểm tra hệ thống sẵn sàng | Trước khi chạy pipeline |

---

## 🔑 LỆNH QUAN TRỌNG CẦN NHỚ

### Quản lý Hadoop/Spark

```bash
# Start services
start-dfs.sh              # Start HDFS
start-yarn.sh             # Start YARN
start-master.sh           # Start Spark Master
start-workers.sh          # Start Spark Workers

# Stop services
stop-dfs.sh
stop-yarn.sh
stop-master.sh
stop-workers.sh

# Stop all
stop-all.sh

# Check running processes
jps                       # Java processes (NameNode, DataNode, Master, Worker...)
```

### HDFS Commands

```bash
# Basic operations
hdfs dfs -ls /                          # List root
hdfs dfs -ls /user/taxi/raw_data/      # List data
hdfs dfs -mkdir -p /path/to/dir        # Create directory
hdfs dfs -put localfile /hdfs/path     # Upload file
hdfs dfs -get /hdfs/path localpath     # Download file
hdfs dfs -rm -r /hdfs/path             # Delete

# Check health
hdfs dfsadmin -report                  # Cluster report
hdfs dfs -du -h /user/taxi/            # Disk usage
```

### Spark Submit

```bash
# Standard command
spark-submit \
  --master spark://master:7077 \
  --executor-memory 2g \
  --driver-memory 2g \
  --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
  path/to/script.py

# With more configs
spark-submit \
  --master spark://master:7077 \
  --executor-memory 2g \
  --driver-memory 2g \
  --executor-cores 2 \
  --num-executors 2 \
  --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
  --conf spark.sql.shuffle.partitions=200 \
  path/to/script.py
```

### Monitor & Debug

```bash
# View logs
tail -f $SPARK_HOME/logs/spark-*.out
tail -f $HADOOP_HOME/logs/hadoop-*-namenode-*.log

# Web UIs
http://master:9870    # HDFS NameNode
http://master:8080    # Spark Master
http://master:8088    # YARN ResourceManager
http://master:4040    # Spark Application (when running)

# System resources
htop                  # CPU & RAM
df -h                 # Disk space
```

---

## 🐛 TROUBLESHOOTING QUICK REFERENCE

### Lỗi: Out of Memory

**Triệu chứng:**
```
java.lang.OutOfMemoryError: Java heap space
```

**Giải pháp:**
1. Giảm executor memory: `--executor-memory 1g`
2. Tăng partitions trong code: `df.repartition(400)`
3. Tăng RAM cho VMs (shutdown → settings → memory)

---

### Lỗi: Connection Refused (HDFS)

**Triệu chứng:**
```
Call From master/192.168.x.x to master:9000 failed on connection exception
```

**Giải pháp:**
```bash
# Kiểm tra HDFS running
jps | grep NameNode

# Nếu không thấy, restart
stop-dfs.sh
start-dfs.sh

# Check Web UI
curl http://master:9870
```

---

### Lỗi: Spark Workers not connecting

**Triệu chứng:**
- Spark Web UI chỉ thấy Master, không thấy Workers

**Giải pháp:**
```bash
# 1. Check /etc/hosts
cat /etc/hosts   # Phải có entry cho master, worker1

# 2. Check SSH passwordless
ssh worker1      # Không cần password

# 3. Restart Spark
stop-workers.sh
stop-master.sh
start-master.sh
start-workers.sh
```

---

### Lỗi: GraphFrames not found

**Triệu chứng:**
```
Py4JJavaError: ... graphframes not found
```

**Giải pháp:**
```bash
# Option 1: Use --packages
spark-submit --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 ...

# Option 2: Download JAR manually
wget https://repos.spark-packages.org/.../graphframes-0.8.3-spark3.5-s_2.12.jar
sudo cp *.jar $SPARK_HOME/jars/
```

---

### Lỗi: Data not found in HDFS

**Triệu chứng:**
```
Path does not exist: /user/taxi/raw_data
```

**Giải pháp:**
```bash
# Check path exists
hdfs dfs -ls /user/taxi/

# Create if not exists
hdfs dfs -mkdir -p /user/taxi/raw_data

# Upload data
hdfs dfs -put ~/nyc_taxi_data/*.parquet /user/taxi/raw_data/

# Verify
hdfs dfs -ls /user/taxi/raw_data/ | wc -l
```

---

## 📊 EXPECTED RESULTS - KẾT QUẢ CHUẨN

### Edge List
```
Total edges: 50-100 million
Example top edges:
  Zone 237 → 236: 8,500,000 trips
  Zone 236 → 237: 8,200,000 trips
  Zone 161 → 237: 5,100,000 trips
```

### PageRank
```
Top 10 zones (expected PageRank ~ 0.04 - 0.10):
  1. Zone 237 (Manhattan Upper East)
  2. Zone 236 (Manhattan Upper West)
  3. Zone 161 (Manhattan Midtown)
  4. Zone 230 (Times Square area)
  5. Zone 132 (JFK Airport)
  ...
  
Distribution: Power-law
  - Top 10: ~45% total PageRank
  - Top 20: ~65% total PageRank
```

### Communities
```
Number of communities: 25-35
Top 5 largest:
  1. Community 1: 40-50 zones (Manhattan CBD)
  2. Community 2: 30-40 zones (Brooklyn)
  3. Community 3: 25-35 zones (Queens + airports)
  4. Community 4: 20-25 zones (Bronx)
  5. Community 5: 15-20 zones (Staten Island)
```

### Benchmark
```
Build Graph:
  1M rows:   25-45 seconds (2 nodes)
  10M rows:  400-700 seconds (2 nodes)
  Full data: 1-2 hours (2 nodes)
  
PageRank (20 iterations):
  25-60 minutes (2 nodes)
  
Speedup (2 nodes vs 1 node):
  ~1.5-2.0x
```

---

## 📝 TEMPLATES & EXAMPLES

### LaTeX công thức PageRank

```latex
\begin{equation}
PR(i) = \frac{1-d}{|V|} + d \sum_{j \in In(i)} \frac{PR(j)}{outdeg(j)}
\end{equation}

where:
\begin{itemize}
  \item $d = 0.85$ (damping factor)
  \item $In(i)$ = set of nodes with edge to $i$
  \item $outdeg(j)$ = out-degree of node $j$
  \item $|V|$ = total number of nodes
\end{itemize}
```

### Table cho báo cáo

```markdown
| Metric | Value |
|--------|-------|
| Dataset Size | ~30 GB |
| Number of Trips | 200-300 million |
| Number of Zones | 260 |
| Number of Edges | 50-100 million |
| PageRank Iterations | 20 |
| Clustering Algorithm | Label Propagation |
| Cluster Size | 2 nodes (10GB RAM) |
```

---

## 🎓 HỌC TỪ DỰ ÁN NÀY

### Kỹ năng học được:

✅ **Distributed Systems:**
- Setup Hadoop/Spark cluster
- HDFS operations
- Distributed computing concepts

✅ **Big Data Processing:**
- MapReduce paradigm
- PySpark DataFrame operations
- Memory management với large datasets

✅ **Graph Mining:**
- PageRank algorithm
- Community detection
- Graph analysis techniques

✅ **System Administration:**
- Linux VM management
- Network configuration
- Service monitoring

✅ **Software Engineering:**
- Project structure
- Code organization
- Documentation

---

## 🔗 RESOURCES HỮU ÍCH

### Documentation
- [Spark Documentation](https://spark.apache.org/docs/latest/)
- [GraphFrames Guide](https://graphframes.github.io/graphframes/docs/_site/index.html)
- [Hadoop HDFS Guide](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsUserGuide.html)

### Learning Resources
- [Mining of Massive Datasets Book](http://www.mmds.org/)
- [CS246 Course (Stanford)](http://web.stanford.edu/class/cs246/)
- [PySpark Tutorial](https://spark.apache.org/docs/latest/api/python/)

### NYC Taxi Data
- [TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
- [Taxi Zone Maps](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

---

## ✉️ CONTACT & SUPPORT

**Nếu gặp vấn đề:**

1. Xem `setup_guide.md` cho troubleshooting
2. Check logs: `$SPARK_HOME/logs/` và `$HADOOP_HOME/logs/`
3. Google error message + "spark" hoặc "hadoop"
4. Stack Overflow: [apache-spark] tag

---

## 📜 LICENSE & CREDITS

**Project Type:** Educational (MMDS Course Project)

**Credits:**
- NYC TLC for open data
- Apache Spark & Hadoop communities
- CS246 course materials
- GraphFrames library developers

---

**Good luck với dự án! 🎉🚀**

---

*Last updated: 2026-02-04*
