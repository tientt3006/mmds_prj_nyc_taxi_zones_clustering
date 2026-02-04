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
sudo apt install python3 python3-pip python3-venv -y

# Tạo virtual environment (trên cả 2 nodes)
python3 -m venv ~/mmds-venv
source ~/mmds-venv/bin/activate

# Cài đặt dependencies
pip install --upgrade pip
pip install pyspark numpy pandas matplotlib seaborn networkx

# Deactivate venv
deactivate

# Cài đặt SSH (để cluster nodes giao tiếp)
sudo apt install openssh-server -y
sudo systemctl enable ssh
sudo systemctl start ssh
```

---

### 1.1.1. **KHUYẾN NGHỊ: Đóng gói và phân phối venv qua HDFS**

Để đảm bảo môi trường Python đồng nhất trên cả 2 nodes:

**Trên Master Node:**

```bash
# Activate venv
source ~/mmds-venv/bin/activate

# Cài đặt tất cả dependencies
pip install pyspark==3.5.0 numpy pandas matplotlib seaborn networkx

# Đóng gói venv (bỏ cache để giảm size)
cd ~
tar -czf mmds-venv.tar.gz \
    --exclude='mmds-venv/__pycache__' \
    --exclude='mmds-venv/**/__pycache__' \
    --exclude='mmds-venv/lib/python3.*/site-packages/*.dist-info' \
    mmds-venv/

# Kiểm tra kích thước (nên < 500MB)
ls -lh mmds-venv.tar.gz

# Upload lên HDFS
hdfs dfs -mkdir -p /user/taxi/python_env/
hdfs dfs -put mmds-venv.tar.gz /user/taxi/python_env/

# Kiểm tra
hdfs dfs -ls /user/taxi/python_env/
```

**Lợi ích:**
- ✅ Môi trường Python đồng nhất trên tất cả executors
- ✅ Không cần cài đặt thủ công trên Worker
- ✅ Spark tự động giải nén trên mỗi executor

---

### 1.1.2. **ALTERNATIVE: Cài thủ công trên Worker (nếu không dùng HDFS archive)**

**Trên Worker Node:**

```bash
# SSH vào worker
ssh worker1

# Tạo venv giống Master
python3 -m venv ~/mmds-venv
source ~/mmds-venv/bin/activate

# Cài dependencies (phải GIỐNG Master)
pip install --upgrade pip
pip install pyspark==3.5.0 numpy pandas matplotlib seaborn networkx

# Verify
python3 -c "import pyspark, numpy, pandas; print('OK')"

deactivate
```

---

### 1.1.3. Lệnh spark-submit đúng chuẩn

**Option 1: Sử dụng HDFS archive (KHUYẾN NGHỊ)**

```bash
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
```

**Giải thích:**
- `--archives`: Spark download từ HDFS và giải nén trên mỗi executor
- `#mmds-venv`: Tên thư mục sau khi giải nén
- `./mmds-venv/bin/python3`: Executor dùng Python từ thư mục này

**Option 2: Sử dụng venv đã cài sẵn trên Worker**

```bash
spark-submit \
    --master spark://master:7077 \
    --deploy-mode client \
    --driver-memory 500m \
    --executor-memory 500m \
    --executor-cores 1 \
    --num-executors 2 \
    --conf spark.pyspark.python=/home/tiennd/mmds-venv/bin/python3 \
    --conf spark.pyspark.driver.python=python3 \
    --packages graphframes:graphframes:0.8.3-spark3.5-s_2.12 \
    src/1_build_graph.py
```

**Chú ý:** Đường dẫn `/home/tiennd/mmds-venv/bin/python3` phải tồn tại trên **TẤT CẢ** nodes.

---

### 1.1.4. Kiểm tra môi trường Python trên Worker

**Test trên Worker:**

```bash
# SSH vào worker
ssh worker1

# Activate venv
source ~/mmds-venv/bin/activate

# Test imports
python3 << EOF
import pyspark
import numpy
import pandas
print("PySpark version:", pyspark.__version__)
print("NumPy version:", numpy.__version__)
print("Pandas version:", pandas.__version__)
print("✅ All imports OK!")
EOF

deactivate
```

**Kết quả mong đợi:**
```
PySpark version: 3.5.0
NumPy version: 1.26.x
Pandas version: 2.x.x
✅ All imports OK!
```

---

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

---
window
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0


### 1.3. Cài đặt Hadoop (Pseudo-Distributed hoặc Fully-Distributed)

> **⚠️ QUAN TRỌNG: Các bước sau chạy trên CÁ 2 NODES (Master và Worker)**
> 
> Tuy nhiên, một số bước chỉ chạy trên Master. Sẽ được chú thích rõ ràng.

---

**Tải Hadoop (trên CẢ 2 NODES - Master và Worker):**

```bash
cd ~
wget https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
tar -xzvf hadoop-3.3.6.tar.gz
sudo mv hadoop-3.3.6 /opt/hadoop
```

---

**Thiết lập biến môi trường (trên CẢ 2 NODES):**

Thêm vào `~/.bashrc` trên cả Master và Worker:

```bash
echo "export HADOOP_HOME=/opt/hadoop" >> ~/.bashrc
echo "export HADOOP_CONF_DIR=\$HADOOP_HOME/etc/hadoop" >> ~/.bashrc
echo "export PATH=\$PATH:\$HADOOP_HOME/bin:\$HADOOP_HOME/sbin" >> ~/.bashrc
echo "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64" >> ~/.bashrc
    or echo "export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64" >> ~/.bashrc
source ~/.bashrc
```

---

**Cấu hình Hadoop (trên CẢ 2 NODES):**

> **Lưu ý:** Cấu hình phải GIỐNG NHAU trên cả Master và Worker để cluster hoạt động đồng bộ.

**File core-site.xml (trên CẢ 2 NODES):**

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
        <value>/home/tiennd/hadoop_tmp</value>
    </property>
</configuration>
```

---

**File hdfs-site.xml (trên CẢ 2 NODES):**

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
        <value>file:///home/tiennd/hadoop_data/namenode</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>file:///home/tiennd/hadoop_data/datanode</value>
    </property>
</configuration>
```

---

**File yarn-site.xml (trên CẢ 2 NODES):**

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
        <value>2048</value>
    </property>
    <property>
        <name>yarn.scheduler.maximum-allocation-mb</name>
        <value>2048</value>
    </property>
    <property>
        <name>yarn.nodemanager.resource.cpu-vcores</name>
        <value>2</value>
    </property>
</configuration>
```

---

**File mapred-site.xml (trên CẢ 2 NODES):**

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

---

**Cấu hình workers (trên CẢ 2 NODES):**

```bash
nano $HADOOP_HOME/etc/hadoop/workers
```

Nội dung (giống nhau trên cả 2 nodes, xóa mục localhost nếu có):

```
master
worker1
```

---

**Thiết lập /etc/hosts (trên CẢ 2 NODES):**

```bash
sudo nano /etc/hosts
```

Thêm (thay IP thực tế của bạn):

```
192.168.56.101  master
192.168.56.102  worker1
```

---

**Tạo thư mục và format HDFS:**

> **⚠️ CHÚ Ý: Phần này CHỈ QUAN TRỌNG cho phân biệt Master vs Worker**

**Trên CẢ 2 NODES:** Tạo thư mục

```bash
mkdir -p ~/hadoop_tmp
mkdir -p ~/hadoop_data/namenode
mkdir -p ~/hadoop_data/datanode
```

**CHỈ TRÊN MASTER NODE:** Format NameNode

```bash
# ⚠️ CHỈ CHẠY LỆNH NÀY TRÊN MASTER
# KHÔNG chạy trên Worker
hdfs namenode -format
```

> **Giải thích:**
> - **Master:** Chạy NameNode (quản lý metadata) → cần format
> - **Worker:** Chỉ chạy DataNode (lưu dữ liệu) → KHÔNG cần format

---

**Khởi động Hadoop:**

> **⚠️ TẤT CẢ LỆNH KHỞI ĐỘNG ĐỀU CHẠY TRÊN MASTER NODE**
> 
> SSH passwordless sẽ tự động kích hoạt services trên Worker

**CHỈ TRÊN MASTER NODE:**

```bash
# Mở file cấu hình
nano $HADOOP_HOME/etc/hadoop/hadoop-env.sh
# Tìm dòng:
# export JAVA_HOME=
# Bỏ comment và sửa thành:
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
# Copy từ Master sang Worker
scp $HADOOP_HOME/etc/hadoop/hadoop-env.sh tiennd@worker1:$HADOOP_HOME/etc/hadoop/

# Khởi động HDFS (NameNode trên master, DataNode trên cả 2 nodes)
start-dfs.sh

# Khởi động YARN (ResourceManager trên master, NodeManager trên cả 2 nodes)
start-yarn.sh


# Mở file
nano ~/.bashrc

# Thêm (chọn 1 trong 2 dòng phù hợp):
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
# hoặc
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64

# Thêm bin vào PATH
export PATH=$JAVA_HOME/bin:$PATH

# Lưu và áp dụng
source ~/.bashrc

sudo apt install openjdk-21-jdk openjdk-21-jdk-headless -y

# Làm cả 2 node master và worker1
# Mở file cấu hình môi trường của Hadoop: 
nano $HADOOP_HOME/etc/hadoop/hadoop-env.sh

# Tìm đến phần cấu hình HADOOP_OPTS hoặc thêm vào cuối file dòng sau:
export HADOOP_OPTS="$HADOOP_OPTS --add-opens java.base/java.lang=ALL-UNNAMED --add-opens java.base/java.util=ALL-UNNAMED --add-opens java.base/java.lang.reflect=ALL-UNNAMED --add-opens java.base/java.text=ALL-UNNAMED --add-opens java.desktop/java.awt.font=ALL-UNNAMED"

# Kiểm tra trên MASTER
jps  
# Nên thấy: NameNode, DataNode, SecondaryNameNode, ResourceManager, NodeManager

# Kiểm tra trên WORKER (SSH vào Worker để check)
ssh worker1 "jps"
# Nên thấy: DataNode, NodeManager
```

**Xem Web UI:**

```bash
# HDFS NameNode: http://master:9870
# YARN ResourceManager: http://master:8088
```

---

**📝 TÓM TẮT - AI LÀM GÌ:**

| Bước | Master Node | Worker Node |
|------|-------------|-------------|
| Download Hadoop | ✅ Có | ✅ Có |
| Thiết lập biến môi trường | ✅ Có | ✅ Có |
| Cấu hình XML files | ✅ Có (giống nhau) | ✅ Có (giống nhau) |
| Edit /etc/hosts | ✅ Có | ✅ Có |
| Tạo thư mục | ✅ Có | ✅ Có |
| **Format NameNode** | ✅ **CHỈ Master** | ❌ **KHÔNG** |
| **Khởi động services** | ✅ **CHỈ Master** (SSH tự động start Worker) | ❌ Tự động bởi Master |
| Kiểm tra `jps` | ✅ NameNode + DataNode + RM + NM | ✅ DataNode + NodeManager |

---

**💡 MẸO COPY CẤU HÌNH:**

Nếu không muốn config thủ công trên Worker, có thể copy từ Master:

```bash
# Trên Master, sau khi cấu hình xong
scp -r /opt/hadoop/etc/hadoop/* user@worker1:/opt/hadoop/etc/hadoop/

# Copy .bashrc
scp ~/.bashrc user@worker1:~/
ssh worker1 "source ~/.bashrc"
```

Nhưng **vẫn phải** tạo thư mục và edit /etc/hosts trên Worker.

### 1.4. Cài đặt Apache Spark

> **⚠️ QUAN TRỌNG: Các bước sau chạy trên CẢ 2 NODES (Master và Worker)**
> 
> Tương tự Hadoop, Spark cần được cài đặt trên cả Master và Worker để cluster hoạt động.

---

**Tải Spark (trên CẢ 2 NODES - Master và Worker):**

```bash
cd ~
wget https://archive.apache.org/dist/spark/spark-3.5.0/spark-3.5.0-bin-hadoop3.tgz
tar -xzvf spark-3.5.0-bin-hadoop3.tgz
sudo mv spark-3.5.0-bin-hadoop3 /opt/spark
```

---

**Thiết lập biến môi trường (trên CẢ 2 NODES):**

```bash
echo "export SPARK_HOME=/opt/spark" >> ~/.bashrc
echo "export PATH=\$PATH:\$SPARK_HOME/bin:\$SPARK_HOME/sbin" >> ~/.bashrc
echo "export PYSPARK_PYTHON=python3" >> ~/.bashrc
source ~/.bashrc
```

---

**Cấu hình Spark (trên CẢ 2 NODES):**

> **Lưu ý:** Cấu hình phải GIỐNG NHAU trên cả Master và Worker.

```bash
cd $SPARK_HOME/conf
cp spark-env.sh.template spark-env.sh
nano spark-env.sh
```

Thêm (trên cả 2 nodes):

```bash
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
export SPARK_MASTER_HOST=master
export SPARK_WORKER_CORES=2
export SPARK_WORKER_MEMORY=2g
export SPARK_DRIVER_MEMORY=1g
```

---

**Cấu hình workers (trên CẢ 2 NODES):**

```bash
cp workers.template workers
nano workers
```

Nội dung (giống nhau trên cả 2 nodes):

```
master
worker1
```

---

**Khởi động Spark Standalone Cluster:**
> **⚠️ TẤT CẢ LỆNH KHỞI ĐỘNG ĐỀU CHẠY TRÊN MASTER NODE**
> 
> SSH passwordless sẽ tự động kích hoạt Worker nodes

**CHỈ TRÊN MASTER NODE:**

```bash
# Khởi động Spark Master
start-master.sh

# Khởi động Spark Workers (tự động trên cả Master và Worker)
start-workers.sh

# Kiểm tra trên MASTER
jps  
# Nên thấy: Master, Worker (nếu Master cũng là Worker)

# Kiểm tra trên WORKER
ssh worker1 "jps"
# Nên thấy: Worker

# Web UI: http://master:8080
```

---

**💡 MẸO COPY CẤU HÌNH:**

Nếu đã cấu hình xong trên Master, có thể copy sang Worker:

```bash
# Trên Master
scp -r /opt/spark/conf/* user@worker1:/opt/spark/conf/

# Copy .bashrc (phần Spark)
scp ~/.bashrc user@worker1:~/
ssh worker1 "source ~/.bashrc"
```

---

**📝 TÓM TẮT - AI LÀM GÌ:**

| Bước | Master Node | Worker Node |
|------|-------------|-------------|
| Download Spark | ✅ Có | ✅ Có |
| Thiết lập biến môi trường | ✅ Có | ✅ Có |
| Cấu hình spark-env.sh | ✅ Có (giống nhau) | ✅ Có (giống nhau) |
| Cấu hình workers file | ✅ Có (giống nhau) | ✅ Có (giống nhau) |
| **Khởi động services** | ✅ **CHỈ Master** (SSH tự động start Worker) | ❌ Tự động bởi Master |
| Kiểm tra `jps` | ✅ Master + Worker | ✅ Worker |

### 1.5. Cài đặt GraphFrames

> **⚠️ CÀI ĐẶT TRÊN CẢ 2 NODES (Master và Worker)**

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

> **⚠️ CHỈ CHẠY TRÊN MASTER NODE**
> 
> Chỉ cần download dữ liệu trên Master, sau đó upload lên HDFS. HDFS sẽ tự động phân tán dữ liệu sang các Worker nodes.

**Script download dữ liệu (1-2 năm để đủ massive):**

**CHỈ TRÊN MASTER NODE:**
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
```bash
mkdir -p ~/nyc_taxi_data
cd ~/nyc_taxi_data

for year in 2025; do
    for month in {01..12}; do
        wget "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_${year}-${month}.parquet"
    done
done
```

> **💡 Giải thích:**
> - **Tại sao chỉ trên Master?** HDFS sẽ tự động replicate dữ liệu sang Worker khi upload
> - **Tiết kiệm băng thông:** Không cần download trùng lặp trên nhiều máy
> - **Quản lý tập trung:** Dễ kiểm soát version và tính toàn vẹn dữ liệu

**Nếu link không hoạt động, dùng alternative:**

```bash
# Tải từ NYC TLC website
# https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
```

### 2.2. Upload dữ liệu lên HDFS

> **⚠️ CHỈ CHẠY TRÊN MASTER NODE**

**CHỈ TRÊN MASTER NODE:**
```bash
# Tạo thư mục trên HDFS
# ⚠️ LƯU Ý: /user/ là thư mục convention của HDFS, KHÔNG phải user OS của bạn
# Bạn có thể đặt tên bất kỳ, ví dụ:
hdfs dfs -mkdir -p /user/taxi/raw_data
# hoặc
hdfs dfs -mkdir -p /user/tiennd/taxi/raw_data
# hoặc
hdfs dfs -mkdir -p /data/taxi/raw_data

# Upload dữ liệu (điều chỉnh path tương ứng)
hdfs dfs -put ~/nyc_taxi_data/*.parquet /user/taxi/raw_data/

# Kiểm tra
hdfs dfs -ls /user/taxi/raw_data/
hdfs dfs -df -h  # Xem dung lượng

# Kiểm tra replication (dữ liệu đã được sao sang Worker chưa)
hdfs fsck /user/taxi/raw_data/ -files -blocks -locations
```

> **💡 Giải thích về đường dẫn HDFS:**
> - `/user/` là **CONVENTION** của HDFS (giống `/home/` trong Linux), KHÔNG liên quan đến user OS
> - Bạn hoàn toàn tự do đặt: `/data/`, `/project/`, `/taxi_mining/`, etc.
> - Nếu muốn theo username: `/user/tiennd/taxi/` (nhưng không bắt buộc)
> - **Quan trọng:** Nhất quán đường dẫn trong toàn bộ project

> **💡 Sau khi upload:**
> - HDFS tự động replicate dữ liệu sang Worker theo cấu hình `dfs.replication=2`
> - Có thể xem phân bố block trên Web UI: http://master:9870

### 2.3. Download Taxi Zone Lookup

> **⚠️ CHỈ CHẠY TRÊN MASTER NODE**

**CHỈ TRÊN MASTER NODE:**
```bash
cd ~/nyc_taxi_data
wget "https://d37ci6vzurychx.cloudfront.net/misc/taxi+_zone_lookup.csv"

# Upload vào cùng namespace với dữ liệu chính
hdfs dfs -put taxi+_zone_lookup.csv /user/taxi/
# hoặc nếu dùng path khác:
# hdfs dfs -put taxi+_zone_lookup.csv /user/tiennd/taxi/
```

---

**📝 MẸO QUẢN LÝ HDFS PATH:**

```bash
# Option 1: Theo convention /user/<username>/ (giống Linux)
hdfs dfs -mkdir -p /user/tiennd/taxi/{raw_data,processed,results}
hdfs dfs -put *.parquet /user/tiennd/taxi/raw_data/

# Option 2: Theo tên project
hdfs dfs -mkdir -p /taxi_mining/{raw,processed,graphs,results}
hdfs dfs -put *.parquet /taxi_mining/raw/

# Option 3: Đơn giản nhất
hdfs dfs -mkdir -p /taxi/raw_data
hdfs dfs -put *.parquet /taxi/raw_data/

# Xem toàn bộ HDFS
hdfs dfs -ls /
hdfs dfs -ls -R /user/
```

**📌 KHUYẾN NGHỊ:**
- Chọn 1 cấu trúc và giữ nhất quán
- Đề xuất: `/user/tiennd/taxi/` (dễ phân quyền và quản lý sau này)

---

**📝 TÓM TẮT - PHẦN 2:**

| Bước | Master Node | Worker Node |
|------|-------------|-------------|
| Download dữ liệu thô | ✅ **CHỈ Master** | ❌ Không cần |
| Upload lên HDFS | ✅ **CHỈ Master** | ❌ Tự động nhận từ HDFS |
| Lưu trữ HDFS blocks | ✅ Có (NameNode + DataNode) | ✅ Có (DataNode - tự động replicate) |
| Đọc dữ liệu từ HDFS | ✅ Có | ✅ Có |

---

## PHẦN 3: IMPLEMENTATION CODE

> **⚠️ QUAN TRỌNG: CODE CHẠY Ở ĐÂU?**
> 
> - **Development & Submit Jobs:** Chạy trên **MASTER NODE** (hoặc máy client bất kỳ có kết nối cluster)
> - **Execution:** Spark tự động phân tán tasks sang **CẢ 2 NODES** (Master + Worker)
> - **Notebooks:** Chạy trên **MASTER NODE** (hoặc laptop của bạn nếu có kết nối)

### 3.1. Cấu trúc project

> **📌 Khuyến nghị:** Tạo project trên **MASTER NODE** tại `~/massive_data_mining/`

```bash
# Trên MASTER NODE
cd ~
mkdir -p massive_data_mining/{data,notebooks,src,config,results,docs}
cd massive_data_mining
```
cd ~
mkdir -p massive_data_mining
cd massive_data_mining

**Cấu trúc thư mục:**
```
~/massive_data_mining/              # ⚠️ Tạo trên MASTER NODE
├── data/                           # Dữ liệu local (sample nhỏ để test)
├── notebooks/                      # Jupyter notebooks (chạy trên Master)
│   ├── 1_explore_data.ipynb
│   ├── 2_build_graph.ipynb
│   ├── 3_pagerank_analysis.ipynb
│   └── 4_clustering.ipynb
├── src/                            # Python scripts
│   ├── 1_build_graph.py           # Build edge list từ trip data
│   ├── 2_pagerank.py              # PageRank implementation
│   ├── 3_clustering.py            # Graph clustering (Label Propagation, etc.)
│   ├── 4_visualization.py         # Vẽ đồ thị và charts
│   └── utils.py                   # Helper functions
├── config/
│   └── spark_config.py            # Spark configuration
├── results/                        # Kết quả output (local trên Master)
│   ├── graphs/
│   ├── pagerank/
│   └── clusters/
├── docs/                           # Báo cáo
│   └── report.md
└── README.md
```

---

### 3.2. Workflow thực tế

> **💡 Hiểu rõ luồng xử lý:**
```
┌─────────────────────────────────────────────────────────────┐
│  MASTER NODE (~/massive_data_mining/)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Viết code Python/Notebook                        │  │
│  │  2. Submit job: spark-submit script.py               │  │
│  │     --master spark://master:7077                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                  │
│                          ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Spark Driver (trên Master)                          │  │
│  │  - Đọc dữ liệu từ HDFS                               │  │
│  │  - Tạo execution plan                                │  │
│  │  - Phân phối tasks                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴──────────────────┐
        │                                    │
        ▼                                    ▼
┌────────────────────┐            ┌────────────────────┐
│  MASTER NODE       │            │  WORKER NODE       │
│  Spark Worker      │            │  Spark Worker      │
│  - Execute tasks   │            │  - Execute tasks   │
│  - Read HDFS data  │            │  - Read HDFS data  │
│  - Process         │            │  - Process         │
└────────────────────┘            └────────────────────┘
        │                                    │
        └─────────────────┬──────────────────┘
                          ▼
              ┌────────────────────────┐
              │  Results               │
              │  - HDFS: /results/     │
              │  - Local: ~/results/   │
              └────────────────────────┘
```

---

### 3.3. Cách chạy code

**Option 1: Chạy trực tiếp trên Master (Development)**

```bash
# SSH vào Master
ssh tiennd@master

# Navigate to project
cd ~/massive_data_mining

# comment line graphframes the run, may need creat venv:
pip install -r requirement.txt

# Đóng gói venv (bỏ cache để giảm size)
tar -czf mmds-venv.tar.gz \
    --exclude='mmds-venv/__pycache__' \
    --exclude='mmds-venv/**/__pycache__' \
    --exclude='mmds-venv/lib/python3.*/site-packages/*.dist-info' \
    mmds-venv/
# Kiểm tra kích thước
ls -lh mmds-venv.tar.gz

# Tạo thư mục trên HDFS
hdfs dfs -mkdir -p /user/taxi/python_env/

# Upload venv
hdfs dfs -put mmds-venv.tar.gz /user/taxi/python_env/

# Kiểm tra
hdfs dfs -ls /user/taxi/python_env/

# Chạy script Python
python3 src/1_build_graph.py

# Hoặc submit Spark job
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
```

**Option 2: Jupyter Notebook trên Master**

```bash
# Trên Master, cài Jupyter
pip3 install jupyter

# Khởi động Jupyter (cho phép remote access)
jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser

# Từ laptop của bạn, mở browser:
# http://master:8888
# Hoặc SSH tunnel:
ssh -L 8888:localhost:8888 tiennd@master
# Mở: http://localhost:8888
```

**Option 3: Remote Development từ Windows (VSCode)**

```bash
# Trên Windows, dùng VSCode Remote SSH
# 1. Install extension: "Remote - SSH"
# 2. Connect to Master: ssh tiennd@master
# 3. Mở folder: ~/massive_data_mining
# 4. Code và debug trực tiếp trên Master
```

---

### 3.4. Lưu ý quan trọng

**📌 Files cần ở đâu:**
| File/Folder | Location | Lý do |
|-------------|----------|-------|
| **Code Python (.py)** | Master: `~/massive_data_mining/src/` | Submit từ Master |
| **Notebooks (.ipynb)** | Master: `~/massive_data_mining/notebooks/` | Jupyter chạy trên Master |
| **Spark config** | Master: `~/massive_data_mining/config/` | Driver đọc config |
| **Input data (raw)** | HDFS: `/user/taxi/raw_data/` | Tất cả nodes đều đọc từ HDFS |
| **Output results** | HDFS: `/user/taxi/results/` HOẶC Local: `~/results/` | HDFS cho big data, Local cho reports |
| **Visualizations** | Local Master: `~/massive_data_mining/results/` | Download về để xem |

**💡 Best Practices:**
1. **Code trên Master, chạy distributed:**
   ```bash
   # Code ở: ~/massive_data_mining/src/pagerank.py
   # Data ở: hdfs://master:9000/user/taxi/raw_data/
   # Submit: spark-submit --master spark://master:7077 src/pagerank.py
   ```

2. **Không cần copy code sang Worker:**
   - Spark tự động serialize và gửi code tới Worker
   - Chỉ cần đảm bảo Worker có cài dependencies (pyspark, networkx, etc.)

3. **Kết quả nhỏ → Local, kết quả lớn → HDFS:**
   ```python
   # Kết quả nhỏ (vài MB)
   pagerank_df.toPandas().to_csv("~/results/pagerank.csv")
   
   # Kết quả lớn (vài GB)
   pagerank_df.write.parquet("hdfs://master:9000/user/taxi/results/pagerank/")
   ```

---

**📝 TÓM TẮT - AI LÀM GÌ:**

| Task | Master Node | Worker Node |
|------|-------------|-------------|
| Viết code | ✅ Có | ❌ Không |
| Submit Spark jobs | ✅ Có | ❌ Không |
| Chạy Jupyter | ✅ Có | ❌ Không |
| Execute Spark tasks | ✅ Có (Worker role) | ✅ Có |
| Đọc dữ liệu từ HDFS | ✅ Có | ✅ Có |
| Lưu results local | ✅ Có | ❌ Không cần |
| Lưu results HDFS | ✅ Driver ghi | ✅ Executors ghi (distributed) |

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
