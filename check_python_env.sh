#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     KIỂM TRA MÔI TRƯỜNG PYTHON TRÊN CLUSTER               ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Check Master
echo -e "\n🔍 Kiểm tra Master Node..."
source ~/mmds-venv/bin/activate
python3 -c "import pyspark, numpy, pandas; print('✅ Master: Python OK')" || echo "❌ Master: Python FAILED"
deactivate

# Check Worker
echo -e "\n🔍 Kiểm tra Worker Node..."
ssh worker1 "source ~/mmds-venv/bin/activate && python3 -c 'import pyspark, numpy, pandas; print(\"✅ Worker: Python OK\")' && deactivate" || echo "❌ Worker: Python FAILED"

# Check HDFS archive
echo -e "\n🔍 Kiểm tra HDFS archive..."
hdfs dfs -test -e /user/taxi/python_env/mmds-venv.tar.gz && echo "✅ HDFS archive exists" || echo "❌ HDFS archive NOT found"

echo -e "\n✅ Hoàn thành kiểm tra!"
