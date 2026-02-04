# Hướng dẫn cài đặt chi tiết - NYC Taxi Graph Mining

## PHẦN 1: CÀI ĐẶT HADOOP + SPARK CLUSTER

### 1.1. Chuẩn bị máy ảo Ubuntu

**Trên cả 2 máy Ubuntu (master và worker):**

```bash
# Update hệ thống
sudo apt update && sudo apt upgrade -y

# Cài đặt Java 11 (bắt buộc cho Hadoop/Spark)
sudo apt install openjdk-11-jdk -y

# Kiểm tra Java
java -version

# Cài đặt Python 3 và pip
sudo apt install python3 python3-pip -y
pip3 install pyspark numpy pandas matplotlib seaborn networkx

# Cài đặt SSH (để cluster nodes giao tiếp)
sudo apt install openssh-server -y
sudo systemctl enable ssh
sudo systemctl start ssh
```

### 1.2. Thiết lập SSH passwordless giữa các nodes

**Trên Master Node:**

```bash
# Tạo SSH key
ssh-keygen -t rsa -P "" -f ~/.ssh/id_rsa

# Copy public key sang chính nó
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys

# Copy sang Worker Node (thay <worker-ip> bằng IP thực tế)
ssh-copy-id user@<worker-ip>

# Test kết nối
ssh user@<worker-ip>
```

**Lưu ý IP addresses:**
- Master: 192.168.x.x (ví dụ: 192.168.56.101)
- Worker: 192.168.x.x (ví dụ: 192.168.56.102)

```bash
# Kiểm tra IP
ip addr show
```

### 1.3. Cài đặt Hadoop (Pseudo-Distributed hoặc Fully-Distributed)

**Tải Hadoop:**

```bash
cd ~
wget https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
tar -xzvf hadoop-3.3.6.tar.gz
sudo mv hadoop-3.3.6 /opt/hadoop
```

**Thiết lập biến môi trường (thêm vào ~/.bashrc):**

```bash
echo "export HADOOP_HOME=/opt/hadoop" >> ~/.bashrc
echo "export HADOOP_CONF_DIR=\$HADOOP_HOME/etc/hadoop" >> ~/.bashrc
echo "export PATH=\$PATH:\$HADOOP_HOME/bin:\$HADOOP_HOME/sbin" >> ~/.bashrc
echo "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64" >> ~/.bashrc
source ~/.bashrc
```

**Cấu hình Hadoop - file core-site.xml:**

```bash
nano $HADOOP_HOME/etc/hadoop/core-site.xml
```

Thêm nội dung:

```xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://master:9000</value>
    </property>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/home/user/hadoop_tmp</value>
    </property>
</configuration>
```

**Cấu hình HDFS - file hdfs-site.xml:**

```bash
nano $HADOOP_HOME/etc/hadoop/hdfs-site.xml
```

```xml
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>2</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>file:///home/user/hadoop_data/namenode</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>file:///home/user/hadoop_data/datanode</value>
    </property>
</configuration>
```

**Cấu hình YARN - file yarn-site.xml:**

```bash
nano $HADOOP_HOME/etc/hadoop/yarn-site.xml
```

```xml
<configuration>
    <property>
        <name>yarn.resourcemanager.hostname</name>
        <value>master</value>
    </property>
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>
    <property>
        <name>yarn.nodemanager.resource.memory-mb</name>
        <value>3072</value>
    </property>
    <property>
        <name>yarn.scheduler.maximum-allocation-mb</name>
        <value>3072</value>
    </property>
    <property>
        <name>yarn.nodemanager.resource.cpu-vcores</name>
        <value>2</value>
    </property>
</configuration>
```

**Cấu hình MapReduce - file mapred-site.xml:**

```bash
nano $HADOOP_HOME/etc/hadoop/mapred-site.xml
```

```xml
<configuration>
    <property>
        <name>mapreduce.framework.name</name>
        <value>yarn</value>
    </property>
    <property>
        <name>mapreduce.application.classpath</name>
        <value>$HADOOP_HOME/share/hadoop/mapreduce/*:$HADOOP_HOME/share/hadoop/mapreduce/lib/*</value>
    </property>
</configuration>
```

**Cấu hình workers:**

```bash
nano $HADOOP_HOME/etc/hadoop/workers
```

Nội dung:

```
master
worker1
```

**Thiết lập /etc/hosts (trên tất cả nodes):**

```bash
sudo nano /etc/hosts
```

Thêm:

```
192.168.56.101  master
192.168.56.102  worker1
```

**Tạo thư mục và format HDFS:**

```bash
mkdir -p ~/hadoop_tmp
mkdir -p ~/hadoop_data/namenode
mkdir -p ~/hadoop_data/datanode

# Format namenode (chỉ chạy lần đầu)
hdfs namenode -format
```

**Khởi động Hadoop:**

```bash
# Trên Master node
start-dfs.sh
start-yarn.sh

# Kiểm tra
jps  # Nên thấy: NameNode, DataNode, SecondaryNameNode, ResourceManager, NodeManager

# Xem Web UI
# HDFS: http://master:9870
# YARN: http://master:8088
```

### 1.4. Cài đặt Apache Spark

**Tải Spark:**

```bash
cd ~
wget https://archive.apache.org/dist/spark/spark-3.5.0/spark-3.5.0-bin-hadoop3.tgz
tar -xzvf spark-3.5.0-bin-hadoop3.tgz
sudo mv spark-3.5.0-bin-hadoop3 /opt/spark
```

**Thiết lập biến môi trường:**

```bash
echo "export SPARK_HOME=/opt/spark" >> ~/.bashrc
echo "export PATH=\$PATH:\$SPARK_HOME/bin:\$SPARK_HOME/sbin" >> ~/.bashrc
echo "export PYSPARK_PYTHON=python3" >> ~/.bashrc
source ~/.bashrc
```

**Cấu hình Spark:**

```bash
cd $SPARK_HOME/conf
cp spark-env.sh.template spark-env.sh
nano spark-env.sh
```

Thêm:

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
export SPARK_MASTER_HOST=master
export SPARK_WORKER_CORES=2
export SPARK_WORKER_MEMORY=3g
export SPARK_DRIVER_MEMORY=2g
```

**Cấu hình workers:**

```bash
cp workers.template workers
nano workers
```

Nội dung:

```
master
worker1
```

**Khởi động Spark Standalone Cluster:**

```bash
# Trên Master
start-master.sh
start-workers.sh

# Kiểm tra
jps  # Nên thấy: Master, Worker

# Web UI: http://master:8080
```

### 1.5. Cài đặt GraphFrames

```bash
# Tải GraphFrames
cd ~
wget https://repos.spark-packages.org/graphframes/graphframes/0.8.3-spark3.5-s_2.12/graphframes-0.8.3-spark3.5-s_2.12.jar
sudo cp graphframes-0.8.3-spark3.5-s_2.12.jar $SPARK_HOME/jars/

# Hoặc cài qua pip
pip3 install graphframes
```

---

## PHẦN 2: DOWNLOAD VÀ CHUẨN BỊ DỮ LIỆU

### 2.1. Download NYC TLC Yellow Taxi Data

**Script download dữ liệu (1-2 năm để đủ massive):**

```bash
mkdir -p ~/nyc_taxi_data
cd ~/nyc_taxi_data

# Download từ tháng 1/2019 đến 12/2020 (24 tháng ~ 30GB)
for year in 2019 2020; do
    for month in {01..12}; do
        wget "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_${year}-${month}.parquet"
    done
done
```

**Nếu link không hoạt động, dùng alternative:**

```bash
# Tải từ NYC TLC website
# https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
```

### 2.2. Upload dữ liệu lên HDFS

```bash
# Tạo thư mục trên HDFS
hdfs dfs -mkdir -p /user/taxi/raw_data

# Upload dữ liệu
hdfs dfs -put ~/nyc_taxi_data/*.parquet /user/taxi/raw_data/

# Kiểm tra
hdfs dfs -ls /user/taxi/raw_data/
hdfs dfs -df -h  # Xem dung lượng
```

### 2.3. Download Taxi Zone Lookup

```bash
cd ~/nyc_taxi_data
wget "https://d37ci6vzurychx.cloudfront.net/misc/taxi+_zone_lookup.csv"
hdfs dfs -put taxi+_zone_lookup.csv /user/taxi/
```

---

## PHẦN 3: IMPLEMENTATION CODE

### 3.1. Cấu trúc project

```
massive_data_mining/
├── data/                          # Dữ liệu local (sample)
├── notebooks/                     # Jupyter notebooks
├── src/
│   ├── 1_build_graph.py          # MapReduce build edge list
│   ├── 2_pagerank.py             # PageRank implementation
│   ├── 3_clustering.py           # Graph clustering
│   ├── 4_visualization.py        # Vẽ đồ thị và charts
│   └── utils.py                  # Helper functions
├── config/
│   └── spark_config.py           # Spark configuration
├── results/                       # Kết quả output
├── docs/                         # Báo cáo
└── README.md
```

Các file code chi tiết sẽ được tạo ở phần sau.

---

## PHẦN 4: KIỂM TRA HỆ THỐNG

### 4.1. Test Hadoop

```bash
# Test HDFS
hdfs dfs -mkdir /test
hdfs dfs -put /etc/hosts /test/
hdfs dfs -cat /test/hosts
hdfs dfs -rm -r /test

# Test MapReduce
hadoop jar $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-*.jar pi 2 100
```

### 4.2. Test Spark

```bash
# Test Spark standalone
spark-submit --class org.apache.spark.examples.SparkPi \
    --master spark://master:7077 \
    $SPARK_HOME/examples/jars/spark-examples_*.jar 100

# Test PySpark
pyspark --master spark://master:7077
```

Trong PySpark shell:

```python
# Test RDD
rdd = sc.parallelize(range(1000))
print(rdd.sum())

# Test DataFrame
df = spark.createDataFrame([(1, "a"), (2, "b")], ["id", "value"])
df.show()
```

### 4.3. Test đọc Parquet từ HDFS

```python
# pyspark --master spark://master:7077

df = spark.read.parquet("hdfs://master:9000/user/taxi/raw_data/yellow_tripdata_2019-01.parquet")
print(f"Số dòng: {df.count()}")
df.printSchema()
df.show(5)
```

---

## LƯU Ý QUAN TRỌNG

### Memory Management

Với RAM hạn chế, cần tune cẩn thận:

```bash
# spark-defaults.conf
spark.driver.memory              2g
spark.executor.memory            2g
spark.executor.cores             2
spark.default.parallelism        8
spark.sql.shuffle.partitions     200
spark.memory.fraction            0.8
spark.memory.storageFraction     0.3
```

### Monitoring

- HDFS UI: http://master:9870
- YARN UI: http://master:8088  
- Spark UI: http://master:8080
- Spark Application UI: http://master:4040 (khi job chạy)

### Troubleshooting

```bash
# Xem logs
tail -f $HADOOP_HOME/logs/*
tail -f $SPARK_HOME/logs/*

# Restart services nếu có lỗi
stop-all.sh
start-dfs.sh
start-yarn.sh
start-master.sh
start-workers.sh
```

---

**Tiếp theo: Tạo các file code implementation**
