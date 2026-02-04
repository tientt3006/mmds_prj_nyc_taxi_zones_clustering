"""
Spark Configuration cho NYC Taxi Graph Mining
Tối ưu cho cluster 2 nodes với RAM hạn chế
"""

from pyspark.sql import SparkSession

def create_spark_session(app_name="NYC_Taxi_Graph_Mining"):
    """
    Tạo Spark Session với cấu hình tối ưu cho cluster nhỏ
    
    Args:
        app_name: Tên application
        
    Returns:
        SparkSession object
    """
    
    spark = SparkSession.builder \
        .appName(app_name) \
        .master("spark://master:7077") \
        .config("spark.driver.memory", "2g") \
        .config("spark.executor.memory", "2g") \
        .config("spark.executor.cores", "2") \
        .config("spark.cores.max", "4") \
        .config("spark.default.parallelism", "8") \
        .config("spark.sql.shuffle.partitions", "200") \
        .config("spark.memory.fraction", "0.8") \
        .config("spark.memory.storageFraction", "0.3") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
        .config("spark.kryoserializer.buffer.max", "512m") \
        .config("spark.driver.maxResultSize", "1g") \
        .config("spark.rpc.message.maxSize", "256") \
        .config("spark.network.timeout", "600s") \
        .config("spark.executor.heartbeatInterval", "60s") \
        .getOrCreate()
    
    # Set log level
    spark.sparkContext.setLogLevel("WARN")
    
    return spark

def create_local_spark_session(app_name="NYC_Taxi_Local"):
    """
    Tạo Spark Session cho test local (không cần cluster)
    """
    
    spark = SparkSession.builder \
        .appName(app_name) \
        .master("local[*]") \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.shuffle.partitions", "8") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    
    return spark


# HDFS Configuration
HDFS_NAMENODE = "hdfs://master:9000"
HDFS_RAW_DATA = f"{HDFS_NAMENODE}/user/taxi/raw_data/"
HDFS_PROCESSED_DATA = f"{HDFS_NAMENODE}/user/taxi/processed/"
HDFS_GRAPH_DATA = f"{HDFS_NAMENODE}/user/taxi/graph/"
HDFS_RESULTS = f"{HDFS_NAMENODE}/user/taxi/results/"

# Local paths for results
LOCAL_RESULTS_DIR = "../results/"
LOCAL_VISUALIZATIONS_DIR = "../results/visualizations/"

# Graph parameters
DAMPING_FACTOR = 0.85
PAGERANK_ITERATIONS = 20
PAGERANK_TOLERANCE = 1e-6

# Data schema constants
PICKUP_LOCATION = "PULocationID"
DROPOFF_LOCATION = "DOLocationID"
TRIP_DISTANCE = "trip_distance"
FARE_AMOUNT = "fare_amount"
TIP_AMOUNT = "tip_amount"
