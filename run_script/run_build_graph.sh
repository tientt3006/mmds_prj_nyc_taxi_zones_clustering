#!/bin/bash

# Script wrapper để chạy 1_build_graph.py với đúng PYTHONPATH

cd ~/massive_data_mining

export PYTHONPATH="${PWD}:${PYTHONPATH}"

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
    src/1_build_graph.py "$@"
