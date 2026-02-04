**BÀI TOÁN 3B – GRAPH-BASED CLUSTERING CÁC TAXI ZONE TỪ NYC TLC YELLOW TAXI DATA
(Đề tài chính – khuyến nghị cho môn Mining of Massive Data / CS246)**

---

### 1. Phát biểu bài toán

Cho tập dữ liệu **NYC TLC Yellow Taxi Trip Records** có kích thước ~30GB, mỗi bản ghi mô tả một chuyến taxi với hai trường quan trọng:

* `PULocationID`: zone đón khách
* `DOLocationID`: zone trả khách

Xem mỗi **taxi zone** là một **đỉnh (node)** trong đồ thị có hướng.
Mỗi chuyến taxi tạo ra một **cạnh có hướng** từ `PULocationID → DOLocationID`.

Mục tiêu:

* Xây dựng **đồ thị giao thông quy mô lớn** của thành phố New York
* Phân tích cấu trúc đồ thị để:

  * xác định **các zone bận rộn nhất**
  * phát hiện **cụm zone có quan hệ giao thông chặt chẽ**
* Thực hiện bằng **thuật toán graph mining phân tán**, không thể chạy trên một máy đơn

---

### 2. Mô hình hóa dữ liệu thành đồ thị

#### 2.1. Định nghĩa đồ thị

Đồ thị có hướng, có trọng số:

[
G = (V, E)
]

Trong đó:

* ( V ): tập các taxi zones (LocationID), |V| ≈ 260
* ( E ): tập các cạnh có hướng
* Trọng số cạnh:

[
w_{ij} = \text{số chuyến taxi từ zone } i \rightarrow j
]

hoặc mở rộng:

[
w_{ij} =
\begin{cases}
\sum \text{trip_count} \
\sum \text{fare_amount} \
\sum \text{tip_amount}
\end{cases}
]

---

### 3. Thuật toán Mining of Massive Data sử dụng

#### 3.1. PageRank (thuật toán chính)

PageRank đo “tầm quan trọng” của một zone dựa trên:

* số lượng zone khác đi đến nó
* mức độ quan trọng của các zone đó

Công thức:

[
PR(i) = \frac{1-d}{|V|} + d \sum_{j \in In(i)} \frac{PR(j)}{outdeg(j)}
]

Trong đó:

* ( d ): damping factor (thường 0.85)
* Thuật toán lặp (iterative)

**Lý do chọn PageRank**

* Thuật toán kinh điển trong CS246
* Iterative + distributed
* Shuffle dữ liệu lớn ở mỗi vòng lặp
* Không thể chạy hiệu quả trên 1 máy

---

#### 3.2. HITS (mở rộng)

Mỗi node có:

* Authority score: zone được nhiều zone khác đi đến
* Hub score: zone thường đi đến nhiều zone khác

Phù hợp để:

* phân biệt zone trung chuyển vs zone đích đến

---

#### 3.3. Community Detection (clustering đồ thị)

Sau khi có đồ thị:

* Áp dụng **graph clustering** để tìm các cụm zone
* Mỗi cụm đại diện cho:

  * khu vực giao thông nội bộ mạnh
  * vùng chức năng đô thị (CBD, airport area, residential…)

Có thể dùng:

* Label Propagation (Spark GraphFrames)
* Louvain (nếu triển khai được)
* Hoặc clustering trên embedding (PageRank vector)

---

### 4. Vì sao đây là bài toán “massive”

Mặc dù số node nhỏ, **số edge rất lớn**:

* ~200–300 triệu chuyến taxi
* Edge list ban đầu > 10GB
* Graph phải build bằng MapReduce

Các điểm không thể làm trên PC thường:

* Không thể load raw edge list vào RAM
* PageRank cần:

  * nhiều iteration
  * shuffle lớn giữa các node
* Single-machine Spark:

  * disk spill liên tục
  * runtime rất dài

---

### 5. Hướng giải quyết tổng thể

#### 5.1. Giai đoạn 1: Xây dựng đồ thị (MapReduce)

* Map:

  * đọc từng trip
  * emit `(PULocationID, DOLocationID) → 1`
* Reduce:

  * cộng dồn → edge weight

Đây là bước scan toàn bộ 30GB dữ liệu.

---

#### 5.2. Giai đoạn 2: Graph Mining (Iterative)

* Load edge list vào Spark GraphX / GraphFrames
* Chạy:

  * PageRank (10–20 iterations)
  * HITS (nếu mở rộng)
* Persist graph trên disk

---

#### 5.3. Giai đoạn 3: Graph Clustering

* Dùng kết quả PageRank:

  * vector hóa mỗi zone
* Áp dụng clustering (k-means / label propagation)
* Phân tích các cluster thu được

---

### 6. Quy trình xây dựng dự án (theo học kỳ)

**Tuần 1–2**

* Hiểu schema NYC TLC
* Thiết kế graph model
* Chạy thử trên 1 tháng dữ liệu

**Tuần 3–4**

* Full data ingestion vào HDFS
* Build edge list phân tán

**Tuần 5–7**

* Cài Spark cluster (VMware)
* Chạy PageRank trên full graph

**Tuần 8–10**

* Graph clustering
* Visualization + insight

**Tuần 11–12**

* Benchmark:

  * 1 node vs 2–3 nodes
  * runtime, memory, disk I/O

**Tuần 13–14**

* Viết report
* Chuẩn bị demo

---

### 7. Chuẩn bị cần thiết

#### 7.1. Phần cứng

* 3 máy ảo VMware:

  * mỗi máy 4–8GB RAM
  * 2 CPU cores
* Tổng RAM: 12–24GB

---

#### 7.2. Phần mềm

* Apache Spark
* HDFS (pseudo hoặc fully distributed)
* Python + PySpark
* GraphX hoặc GraphFrames
* Git + GitHub
* Jupyter / LaTeX (báo cáo)

---

### 8. Deliverables bắt buộc

* Đồ thị taxi zones
* Bảng xếp hạng PageRank
* Visualization cluster zone
* So sánh runtime theo số node
* Giải thích vì sao không chạy được trên 1 PC

---

### 9. Điểm mạnh học thuật của đề tài

* Thuộc **Link Analysis & Graph Mining** (core CS246)
* Có thuật toán lặp phân tán
* Có phân tích scalability
* Không phụ thuộc deep learning
* Dataset thực, rất lớn

---

### 10. Kết luận

Bài toán 3B:

* **Đáp ứng đầy đủ tiêu chí Mining of Massive Data**
* Dễ bảo vệ trước giảng viên
* Có demo rõ ràng
* Có khả năng mở rộng nghiên cứu

Nếu cần, có thể tiếp tục:

* viết **pseudocode MapReduce + PageRank (LaTeX)**
* thiết kế **slide trình bày đúng chuẩn CS246**
* viết **phần Evaluation & Scalability** chuẩn học thuật

Về phân công cho nhóm 4 người, làm remote còn giúp tách nhiệm vụ rõ ràng và giảm xung đột môi trường. Một người phụ trách data ingestion và MapReduce build edge list. Một người phụ trách Spark GraphX hoặc GraphFrames và PageRank/HITS. Một người làm clustering, visualization và phân tích đô thị. Một người phụ trách benchmarking, scalability, viết report và slide. Các phần này tương đối độc lập, giao tiếp chủ yếu qua interface dữ liệu và kết quả trung gian, rất phù hợp làm từ xa.