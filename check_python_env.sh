#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     KIỂM TRA MÔI TRƯỜNG PYTHON TRÊN CLUSTER               ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Check Master
echo -e "\n🔍 Kiểm tra Master Node..."
source ~/mmds-venv/bin/activate 2>/dev/null
if [ $? -eq 0 ]; then
    python3 -c "import pyspark, numpy, pandas; print('✅ Master: Python OK')" 2>/dev/null || echo "❌ Master: Python imports FAILED"
    deactivate
else
    echo "⚠️  Master: venv not found at ~/mmds-venv"
fi

# Check Worker
echo -e "\n🔍 Kiểm tra Worker Node..."
ssh worker1 "source ~/mmds-venv/bin/activate 2>/dev/null && python3 -c 'import pyspark, numpy, pandas; print(\"✅ Worker: Python OK\")' 2>/dev/null && deactivate" || echo "❌ Worker: Python FAILED"

# Check HDFS archive
echo -e "\n🔍 Kiểm tra HDFS archive..."
hdfs dfs -test -e /user/taxi/python_env/mmds-venv.tar.gz 2>/dev/null && echo "✅ HDFS archive exists" || echo "❌ HDFS archive NOT found"

echo -e "\n✅ Hoàn thành kiểm tra!"
