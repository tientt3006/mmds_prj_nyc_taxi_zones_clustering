# ✅ CHECKLIST HOÀN THÀNH DỰ ÁN

## GIAI ĐOẠN 1: CHUẨN BỊ HẠ TẦNG

### Setup VMware VMs
- [ ] Tạo VM Ubuntu 1 (Master): 6GB RAM, 2-4 cores, 100GB disk
- [ ] Tạo VM Ubuntu 2 (Worker): 4GB RAM, 2 cores, 80GB disk
- [ ] Cấu hình network (NAT hoặc Bridged)
- [ ] Ghi lại IP addresses của cả 2 VMs
- [ ] Test ping giữa 2 VMs

### Cài đặt phần mềm cơ bản
- [ ] Update OS: `sudo apt update && sudo apt upgrade`
- [ ] Cài Java 11: `sudo apt install openjdk-11-jdk`
- [ ] Cài Python 3: `sudo apt install python3 python3-pip`
- [ ] Cài SSH: `sudo apt install openssh-server`
- [ ] Verify Java: `java -version`
- [ ] Verify Python: `python3 --version`

### Thiết lập /etc/hosts
- [ ] Trên Master: Thêm `192.168.x.x master` và `192.168.x.x worker1`
- [ ] Trên Worker: Thêm `192.168.x.x master` và `192.168.x.x worker1`
- [ ] Test: `ping master`, `ping worker1`

### Thiết lập SSH passwordless
- [ ] Trên Master: `ssh-keygen -t rsa`
- [ ] Copy key: `ssh-copy-id user@master` và `ssh-copy-id user@worker1`
- [ ] Test: `ssh worker1` (không cần password)
- [ ] Test: `ssh master` (không cần password)

---

## GIAI ĐOẠN 2: CÀI ĐẶT HADOOP

### Download và cài đặt
- [ ] Download Hadoop 3.3.6
- [ ] Extract vào /opt/hadoop
- [ ] Set HADOOP_HOME trong ~/.bashrc
- [ ] Set PATH để include Hadoop bins
- [ ] Source ~/.bashrc

### Cấu hình Hadoop
- [ ] Edit core-site.xml (fs.defaultFS)
- [ ] Edit hdfs-site.xml (replication, namenode, datanode)
- [ ] Edit yarn-site.xml (resourcemanager, nodemanager)
- [ ] Edit mapred-site.xml (framework.name)
- [ ] Edit workers file (list all nodes)
- [ ] Copy config sang worker node

### Khởi động HDFS
- [ ] Format namenode: `hdfs namenode -format`
- [ ] Start HDFS: `start-dfs.sh`
- [ ] Verify với jps (NameNode, DataNode)
- [ ] Test Web UI: http://master:9870
- [ ] Start YARN: `start-yarn.sh`
- [ ] Test YARN UI: http://master:8088

### Test HDFS
- [ ] Create test dir: `hdfs dfs -mkdir /test`
- [ ] Upload file: `hdfs dfs -put /etc/hosts /test/`
- [ ] List: `hdfs dfs -ls /test`
- [ ] Cat: `hdfs dfs -cat /test/hosts`
- [ ] Remove: `hdfs dfs -rm -r /test`

---

## GIAI ĐOẠN 3: CÀI ĐẶT SPARK

### Download và cài đặt
- [ ] Download Spark 3.5.0 (with Hadoop 3)
- [ ] Extract vào /opt/spark
- [ ] Set SPARK_HOME trong ~/.bashrc
- [ ] Set PATH để include Spark bins
- [ ] Source ~/.bashrc

### Cấu hình Spark
- [ ] Copy spark-env.sh.template → spark-env.sh
- [ ] Edit spark-env.sh (JAVA_HOME, HADOOP_CONF_DIR, master host)
- [ ] Copy workers.template → workers
- [ ] Edit workers (list all nodes)
- [ ] Copy config sang worker node

### Khởi động Spark
- [ ] Start Master: `start-master.sh`
- [ ] Start Workers: `start-workers.sh`
- [ ] Verify với jps (Master, Worker)
- [ ] Test Web UI: http://master:8080

### Test Spark
- [ ] Run example: `spark-submit --class org.apache.spark.examples.SparkPi ...`
- [ ] Test PySpark: `pyspark --master spark://master:7077`
- [ ] Create simple RDD, verify output

---

## GIAI ĐOẠN 4: CÀI ĐẶT GRAPHFRAMES

- [ ] Download GraphFrames JAR
- [ ] Copy JAR vào $SPARK_HOME/jars/
- [ ] Hoặc install via pip: `pip3 install graphframes`
- [ ] Test import trong PySpark

---

## GIAI ĐOẠN 5: DOWNLOAD VÀ UPLOAD DỮ LIỆU

### Download NYC Taxi Data
- [ ] Tạo thư mục: `mkdir ~/nyc_taxi_data`
- [ ] Download 2019 data (12 files): `wget ...`
- [ ] Download 2020 data (12 files): `wget ...`
- [ ] Verify 24 parquet files tổng ~30GB
- [ ] Download taxi zone lookup CSV

### Upload lên HDFS
- [ ] Create HDFS dir: `hdfs dfs -mkdir -p /user/taxi/raw_data`
- [ ] Upload data: `hdfs dfs -put *.parquet /user/taxi/raw_data/`
- [ ] Upload lookup: `hdfs dfs -put taxi_zone_lookup.csv /user/taxi/`
- [ ] Verify: `hdfs dfs -ls /user/taxi/raw_data/`
- [ ] Check size: `hdfs dfs -du -h /user/taxi/raw_data/`

---

## GIAI ĐOẠN 6: SETUP PROJECT

### Clone/Download project code
- [ ] Tạo thư mục project: `~/massive_data_mining`
- [ ] Copy tất cả code files vào
- [ ] Cấu trúc đúng: src/, config/, results/, ...
- [ ] Verify all Python files exist

### Cài đặt Python dependencies
- [ ] Install requirements: `pip3 install -r requirements.txt`
- [ ] Verify imports: Test import pyspark, pandas, matplotlib

### Cấu hình paths
- [ ] Check spark_config.py: Verify HDFS paths
- [ ] Adjust nếu cần (HDFS namenode address)

---

## GIAI ĐOẠN 7: CHẠY PIPELINE

### Pre-flight check
- [ ] Run: `bash check_setup.sh`
- [ ] Fix any errors reported
- [ ] Ensure all services running

### Chạy từng bước
- [ ] Bước 1 - Build Graph: 
  ```bash
  spark-submit --master spark://master:7077 \
    --executor-memory 2g --driver-memory 2g \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    src/1_build_graph.py
  ```
  - [ ] Verify output in HDFS: /user/taxi/graph/edge_list
  
- [ ] Bước 2 - PageRank:
  ```bash
  spark-submit --master spark://master:7077 \
    --executor-memory 2g --driver-memory 2g \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    src/2_pagerank.py
  ```
  - [ ] Verify output: /user/taxi/results/pagerank_scores
  
- [ ] Bước 3 - Clustering:
  ```bash
  spark-submit --master spark://master:7077 \
    --executor-memory 2g --driver-memory 2g \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    src/3_clustering.py
  ```
  - [ ] Verify output: /user/taxi/results/community_assignments
  
- [ ] Bước 4 - Visualization:
  ```bash
  python3 src/4_visualization.py
  ```
  - [ ] Verify PNG files in results/visualizations/
  
- [ ] Bước 5 - Benchmark:
  ```bash
  spark-submit --master spark://master:7077 \
    --executor-memory 2g --driver-memory 2g \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    src/5_benchmark.py
  ```
  - [ ] Verify JSON in results/benchmarks/

### Hoặc chạy tất cả
- [ ] Run: `bash run_all.sh`
- [ ] Monitor progress
- [ ] Check logs nếu có lỗi

---

## GIAI ĐOẠN 8: THU THẬP KẾT QUẢ

### Download từ HDFS
- [ ] Download edge list: `hdfs dfs -get /user/taxi/graph/edge_list ./`
- [ ] Download PageRank: `hdfs dfs -get /user/taxi/results/pagerank_scores ./`
- [ ] Download communities: `hdfs dfs -get /user/taxi/results/community_assignments ./`
- [ ] Download CSV files từ HDFS

### Kiểm tra outputs
- [ ] Xem visualizations: `ls results/visualizations/`
- [ ] Xem summary: `cat results/visualizations/summary_statistics.csv`
- [ ] Xem top zones: `cat results/visualizations/top50_zones_detailed.csv`
- [ ] Xem benchmark: `cat results/benchmarks/benchmark_*.json`

### Screenshots
- [ ] Screenshot HDFS Web UI (http://master:9870)
- [ ] Screenshot Spark Web UI (http://master:8080)
- [ ] Screenshot running job (http://master:4040)
- [ ] Screenshot visualizations (charts)
- [ ] Screenshot terminal output

---

## GIAI ĐOẠN 9: VIẾT BÁO CÁO

### Nội dung báo cáo
- [ ] Trang bìa
- [ ] Abstract
- [ ] Introduction (đặt vấn đề, mục tiêu)
- [ ] Dataset và mô hình hóa đồ thị
- [ ] Thuật toán (PageRank, Label Propagation)
  - [ ] Công thức toán (LaTeX)
  - [ ] Pseudocode
- [ ] Implementation (architecture, tech stack)
- [ ] Results
  - [ ] Tables: Top zones, communities
  - [ ] Charts: Visualizations
- [ ] Benchmark và scalability analysis
  - [ ] Runtime comparison table
  - [ ] Speedup chart
- [ ] Discussion (insights, applications)
- [ ] Conclusion
- [ ] References

### Slides thuyết trình
- [ ] Slide 1: Title
- [ ] Slide 2-3: Introduction
- [ ] Slide 4: Dataset
- [ ] Slide 5-6: Algorithms
- [ ] Slide 7: Architecture
- [ ] Slide 8-10: Results (với visualizations)
- [ ] Slide 11: Benchmark
- [ ] Slide 12: Demo (optional)
- [ ] Slide 13: Conclusion

---

## GIAI ĐOẠN 10: CHUẨN BỊ BẢO VỆ

### Technical prep
- [ ] Ensure cluster still running và accessible
- [ ] Test demo commands trước
- [ ] Backup kết quả (in case cluster crashes)
- [ ] Prepare video recording (if needed)

### Practice
- [ ] Rehearse presentation (15-20 phút)
- [ ] Prepare answers cho Q&A thường gặp
- [ ] Review key metrics (có thể bị hỏi numbers)

### Checklist demo
- [ ] Laptop kết nối được VMs
- [ ] Web browsers với tabs sẵn (HDFS, Spark UIs)
- [ ] Terminal sẵn SSH vào master
- [ ] Command history prepared
- [ ] Backup screenshots nếu demo fail

---

## 📊 KẾT QUẢ MONG ĐỢI

### Metrics cần nhớ
- Dataset size: ~30GB, 200-300M trips
- Số zones: 260
- Số edges: 50-100M unique pairs
- PageRank iterations: 20
- Top zone PageRank: ~0.08-0.10
- Số communities: 25-35
- Runtime build graph: ~1-2 giờ
- Runtime PageRank: ~30-60 phút
- Speedup 2 nodes vs 1 node: ~1.5-2x

### Key insights
- Manhattan zones có PageRank cao nhất
- Airports (JFK, LaGuardia) cũng rất quan trọng
- Communities map với NYC boroughs
- Phân phối power-law rõ ràng

---

## 🎯 TIÊU CHÍ ĐÁNH GIÁ (DỰ KIẾN)

- [ ] **Tính massive (30%):** Chứng minh không chạy được trên PC, cần cluster
- [ ] **Thuật toán (25%):** Hiểu và implement đúng PageRank, clustering
- [ ] **Implementation (20%):** Code chạy được, có kết quả
- [ ] **Benchmark (15%):** Đo được scalability, có comparison
- [ ] **Presentation (10%):** Trình bày rõ ràng, trả lời tốt Q&A

---

## ⚠️ RỦI RO VÀ MITIGATION

| Rủi ro | Mitigation |
|--------|------------|
| VM crash trong demo | Backup screenshots, video recording |
| HDFS/Spark không start | Practice restart commands, có script |
| OOM khi chạy | Đã tune memory config, test trước |
| Download data quá lâu | Bắt đầu sớm, có thể dùng subset |
| Cluster quá chậm | Optimize config, reduce iterations |

---

**Status:** ☐ Not Started | ◐ In Progress | ✅ Completed

**Last updated:** _________

**Notes:**
_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________
