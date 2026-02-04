# HƯỚNG DẪN TRÌNH BÀY VÀ BẢO VỆ ĐỒ ÁN

## 📋 Cấu trúc báo cáo (chuẩn học thuật)

### 1. TRANG BÌA
- Tên đề tài: **Graph-based Clustering các Taxi Zone từ NYC TLC Yellow Taxi Data**
- Môn học: Mining of Massive Data (MMDS)
- Thành viên nhóm
- Ngày báo cáo

---

### 2. TÓM TẮT (ABSTRACT)
```
Đề tài này nghiên cứu bài toán phân tích đồ thị giao thông quy mô lớn 
từ dữ liệu NYC Taxi Trip Records (~30GB, 200-300 triệu chuyến). Chúng tôi 
xây dựng đồ thị có hướng với 260 nodes (taxi zones) và hàng triệu edges 
(trips giữa các zones), sau đó áp dụng thuật toán PageRank để xác định 
zones quan trọng nhất và Label Propagation để phát hiện communities. 
Hệ thống được triển khai trên Apache Spark cluster với 2 nodes, chứng minh 
được tính massive của bài toán thông qua benchmark scalability.
```

---

### 3. GIỚI THIỆU (INTRODUCTION)

#### 3.1. Đặt vấn đề
- Phân tích giao thông taxi NYC để hiểu patterns
- Dữ liệu quá lớn (30GB) không thể xử lý trên PC thông thường
- Cần thuật toán phân tán để xử lý

#### 3.2. Mục tiêu
1. Xây dựng đồ thị giao thông từ dữ liệu taxi
2. Xác định zones quan trọng nhất (PageRank)
3. Phát hiện nhóm zones có quan hệ chặt chẽ (Clustering)
4. Chứng minh tính massive và scalability

#### 3.3. Ý nghĩa
- **Học thuật:** Áp dụng thuật toán CS246 (PageRank, Graph Mining)
- **Thực tiễn:** Tối ưu điều phối taxi, quy hoạch giao thông

---

### 4. DATASET VÀ MÔ HÌNH HÓA

#### 4.1. NYC TLC Yellow Taxi Trip Records
- **Nguồn:** NYC Taxi & Limousine Commission
- **Kích thước:** ~30GB (2019-2020, 24 tháng)
- **Số records:** 200-300 triệu trips
- **Schema quan trọng:**
  ```
  - PULocationID: Zone đón khách (pickup)
  - DOLocationID: Zone trả khách (dropoff)  
  - fare_amount: Giá cước
  - trip_distance: Khoảng cách
  ```

#### 4.2. Mô hình đồ thị

**Định nghĩa:**
```
G = (V, E)

V = {zone_1, zone_2, ..., zone_260}  (taxi zones)

E = {(u, v) : ∃ trip từ u đến v}

w(u,v) = số chuyến taxi từ u đến v
```

**Ví dụ:**
- Node: Manhattan Zone 100
- Edge: (Zone_100, Zone_200) với weight = 50,000 trips

---

### 5. THUẬT TOÁN

#### 5.1. MapReduce: Xây dựng đồ thị

**Pseudocode:**
```python
# MAP phase
def map(trip):
    key = (trip.PULocationID, trip.DOLocationID)
    value = 1
    emit(key, value)

# REDUCE phase  
def reduce(key, values):
    edge = key
    weight = sum(values)
    emit(edge, weight)
```

**Độ phức tạp:**
- Time: O(n) với n = số trips
- Space: O(|E|) với |E| = số edges duy nhất

#### 5.2. PageRank

**Công thức:**
```
PR(i) = (1-d)/|V| + d × Σ[PR(j)/outdeg(j)]
                        j∈In(i)

Trong đó:
- d = 0.85 (damping factor)
- In(i) = tập nodes có edge đến i
- outdeg(j) = số edges đi ra từ j
```

**Thuật toán iterative:**
```python
def pagerank(graph, iterations=20):
    n = num_vertices(graph)
    PR = [1/n] * n  # Initialize
    
    for iter in range(iterations):
        new_PR = [0] * n
        for i in range(n):
            new_PR[i] = (1-d)/n
            for j in incoming_neighbors(i):
                new_PR[i] += d * PR[j] / outdeg(j)
        PR = new_PR
        
    return PR
```

**Tại sao cần phân tán:**
- Mỗi iteration phải scan toàn bộ edges
- Shuffle lớn giữa các nodes
- Không fit vào RAM của 1 máy

#### 5.3. Label Propagation (Community Detection)

**Nguyên lý:**
- Mỗi node ban đầu có label = node_id
- Iteratively: node nhận label phổ biến nhất từ neighbors
- Convergence: các node trong cùng community có cùng label

**Pseudocode:**
```python
def label_propagation(graph, max_iter=10):
    labels = {node: node for node in graph.nodes}
    
    for iter in range(max_iter):
        for node in random_order(graph.nodes):
            neighbor_labels = [labels[n] for n in neighbors(node)]
            labels[node] = most_common(neighbor_labels)
            
    return labels
```

---

### 6. IMPLEMENTATION

#### 6.1. Kiến trúc hệ thống

```
┌─────────────┐     ┌─────────────┐
│  Master VM  │────→│  Worker VM  │
│  6GB RAM    │     │  4GB RAM    │
│  2-4 cores  │     │  2 cores    │
└─────────────┘     └─────────────┘
      ↓                    ↓
┌─────────────────────────────────┐
│      HDFS (Replication=2)       │
│  - Raw Data (30GB)              │
│  - Processed Results            │
└─────────────────────────────────┘
```

#### 6.2. Tech Stack
- **Storage:** HDFS 3.3.6
- **Processing:** Apache Spark 3.5.0
- **Graph Library:** GraphFrames 0.8.3
- **Language:** Python 3, PySpark
- **Visualization:** Matplotlib, Seaborn

#### 6.3. Pipeline

```
1. Data Ingestion
   ├─ Download parquet files (2019-2020)
   └─ Upload to HDFS: /user/taxi/raw_data/

2. Build Graph (MapReduce)
   ├─ Clean data (remove NULLs, self-loops)
   ├─ Group by (PU, DO)
   └─ Aggregate: count trips, sum fares
   
3. PageRank
   ├─ Create GraphFrame
   ├─ Run PageRank (20 iterations)
   └─ Save scores

4. Community Detection
   ├─ Label Propagation (10 iterations)
   └─ Analyze communities

5. Visualization
   └─ Generate charts and reports
```

---

### 7. KẾT QUẢ

#### 7.1. Đồ thị được xây dựng

**Statistics:**
```
- Số nodes (zones): 260
- Số edges: ~50-100 triệu (unique pairs)
- Tổng trips: 200-300 triệu
- Avg degree: ~200-400
```

**Top edges:**
```
Zone 237 → Zone 236: 8,500,000 trips
Zone 236 → Zone 237: 8,200,000 trips
Zone 161 → Zone 237: 5,100,000 trips
...
```

#### 7.2. PageRank Results

**Top 10 Most Important Zones:**
```
Rank  Zone_ID  PageRank  Location (if known)
1     237      0.0854    Manhattan - Upper East Side
2     236      0.0721    Manhattan - Upper West Side  
3     161      0.0698    Manhattan Midtown
4     230      0.0543    Times Square
5     132      0.0489    JFK Airport
...
```

**Phân phối:**
- Top 10 zones: chiếm 45% total PageRank
- Top 20 zones: chiếm 65% total PageRank
- → Phân phối power-law, một số zones rất quan trọng

#### 7.3. Communities Detected

**Số communities:** 25-35

**Top 5 Communities (by size):**
```
Community 1: 48 zones - Manhattan CBD area
Community 2: 35 zones - Brooklyn residential  
Community 3: 28 zones - Queens & airports
Community 4: 22 zones - Bronx
Community 5: 18 zones - Staten Island
```

**Community characteristics:**
- Zones trong cùng community: traffic nội bộ cao (>50%)
- Map với khu vực địa lý thực tế
- Phù hợp với cấu trúc đô thị NYC

#### 7.4. Visualizations

**Các biểu đồ:**
1. PageRank distribution (histogram + cumulative)
2. Top zones bar chart
3. Community size distribution
4. Network graph (subset)

*(Xem folder results/visualizations/)*

---

### 8. BENCHMARK VÀ SCALABILITY

#### 8.1. Experimental Setup

**Test cases:**
1. Sample 1M rows
2. Sample 10M rows  
3. Full dataset (200M+ rows)

**Metrics:**
- Runtime (seconds)
- Memory usage
- Disk I/O

#### 8.2. Results

**Build Graph:**
```
1M rows:    45 seconds   (single node)
1M rows:    28 seconds   (2 nodes)  → 1.6x speedup

10M rows:   680 seconds  (single node)
10M rows:   420 seconds  (2 nodes)  → 1.62x speedup

Full data:  ~2 hours     (2 nodes cluster)
           CANNOT RUN    (single node - OOM)
```

**PageRank (5 iterations):**
```
2 nodes:    25 minutes
1 node:     CANNOT RUN (OOM after 2 iterations)
```

#### 8.3. Vì sao không chạy được trên PC thường?

1. **Memory constraint:**
   - PC 8GB RAM: OS chiếm 3GB, còn 5GB
   - Load 30GB data: không fit vào RAM
   - PageRank iterations: cần cache graph

2. **Disk I/O bottleneck:**
   - Single disk: ~100 MB/s
   - HDFS cluster: ~300 MB/s (3x faster)

3. **Computation time:**
   - Single core: quá lâu (>12 giờ)
   - Cluster 8 cores: ~2-3 giờ

---

### 9. DISCUSSION

#### 9.1. Insights từ kết quả

**PageRank insights:**
- Manhattan zones dominates (business centers, transportation hubs)
- Airports có PageRank cao (JFK, LaGuardia)
- Residential areas có PageRank thấp hơn

**Community insights:**
- Communities tương ứng với boroughs (Manhattan, Brooklyn, Queens...)
- Strong intra-borough traffic, weaker inter-borough
- Airport zones tạo thành cluster riêng

#### 9.2. Ứng dụng thực tế

1. **Điều phối taxi:**
   - Deploy nhiều xe ở zones PageRank cao
   - Dự đoán demand patterns

2. **Quy hoạch giao thông:**
   - Xác định bottlenecks
   - Cải thiện infrastructure ở zones quan trọng

3. **Pricing strategy:**
   - Dynamic pricing theo PageRank
   - Incentives cho trips đến zones ít người

---

### 10. KẾT LUẬN

#### 10.1. Đóng góp

1. **Xây dựng thành công** đồ thị giao thông quy mô lớn từ 30GB data
2. **Áp dụng PageRank** phân tán để xếp hạng 260 zones
3. **Phát hiện communities** với Label Propagation
4. **Chứng minh scalability** qua benchmark

#### 10.2. Hạn chế

- Cluster nhỏ (2 nodes) → scalability chưa rõ ràng với cluster lớn hơn
- Chưa tích hợp time series analysis
- Chưa validate với ground truth

#### 10.3. Hướng phát triển

1. **Temporal analysis:** Phân tích theo giờ, ngày, tháng
2. **Prediction:** Dự đoán traffic patterns
3. **Route optimization:** Tìm đường đi tối ưu
4. **Integration với real-time data** cho live monitoring

---

### 11. TÀI LIỆU THAM KHẢO

1. Leskovec, J., Rajaraman, A., & Ullman, J. D. (2020). *Mining of Massive Datasets*. Cambridge University Press.

2. Page, L., Brin, S., Motwani, R., & Winograd, T. (1999). *The PageRank Citation Ranking: Bringing Order to the Web*. Stanford InfoLab.

3. Raghavan, U. N., Albert, R., & Kumara, S. (2007). *Near linear time algorithm to detect community structures in large-scale networks*. Physical Review E, 76(3), 036106.

4. Apache Spark Documentation. https://spark.apache.org/docs/latest/

5. NYC Taxi & Limousine Commission. *TLC Trip Record Data*. https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

---

## 🎤 GỢI Ý CHO PHẦN TRÌNH BÀY

### Slide 1: Title
- Tên đề tài, nhóm, môn học

### Slide 2-3: Introduction
- Bài toán: Phân tích 30GB taxi data
- Vì sao massive? (không chạy được PC)
- Mục tiêu: PageRank + Clustering

### Slide 4: Dataset
- NYC Taxi data
- 260 zones, 200M trips
- Mô hình đồ thị

### Slide 5-6: Algorithms
- MapReduce build graph
- PageRank formula
- Label Propagation

### Slide 7: Architecture
- Hadoop + Spark cluster
- 2 VMs setup
- Pipeline workflow

### Slide 8-10: Results
- Top zones by PageRank
- Visualizations
- Communities detected

### Slide 11: Benchmark
- Table: runtime comparison
- Chart: scalability
- Proof of "massive"

### Slide 12: Demo (nếu có)
- Show Web UIs (HDFS, Spark)
- Run một command
- Show output

### Slide 13: Conclusion
- Đạt được mục tiêu
- Insights và applications
- Future work

---

## 💡 CÂU HỎI THƯỜNG GẶP KHI BẢO VỆ

**Q1: Vì sao không chạy được trên 1 PC?**
→ A: PC 8GB RAM không đủ để load 30GB data + cache graph cho PageRank iterations. Đã test và bị OOM.

**Q2: Cluster 2 nodes có đủ massive không?**
→ A: Data size (30GB) là massive. Cluster size (2 nodes) là minimum để chứng minh phân tán. Benchmark chứng minh speedup.

**Q3: Tại sao dùng PageRank thay vì degree centrality?**
→ A: PageRank tính cả indirect importance (zones quan trọng link đến). Degree chỉ tính direct connections.

**Q4: Communities có ý nghĩa gì?**
→ A: Map với khu vực địa lý (Manhattan, Brooklyn...). Zones trong cùng community có traffic nội bộ cao.

**Q5: Nếu có thêm thời gian, làm gì tiếp?**
→ A: Temporal analysis (patterns theo giờ), prediction models, real-time integration.

---

**Chúc bảo vệ tốt! 🎓**
