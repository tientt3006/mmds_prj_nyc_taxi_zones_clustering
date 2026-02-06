#!/bin/bash

###############################################################################
# CHECK_SETUP.SH - Kiểm tra xem hệ thống đã sẵn sàng chưa
# 
# Sử dụng: bash check_setup.sh
###############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASS=0
FAIL=0
WARN=0

check_command() {
    local cmd=$1
    local name=$2
    
    if command -v $cmd &> /dev/null; then
        echo -e "${GREEN}✅ $name installed${NC}"
        PASS=$((PASS + 1))
        return 0
    else
        echo -e "${RED}❌ $name NOT installed${NC}"
        FAIL=$((FAIL + 1))
        return 1
    fi
}

check_java() {
    if command -v java &> /dev/null; then
        version=$(java -version 2>&1 | head -n 1)
        echo -e "${GREEN}✅ Java installed: $version${NC}"
        PASS=$((PASS + 1))
        
        # Check if Java 11
        if [[ $version == *"11."* ]]; then
            echo "   Java 11 detected ✓"
        else
            echo -e "${YELLOW}   ⚠️  Recommended: Java 11${NC}"
            WARN=$((WARN + 1))
        fi
    else
        echo -e "${RED}❌ Java NOT installed${NC}"
        FAIL=$((FAIL + 1))
    fi
}

check_env_var() {
    local var=$1
    local name=$2
    
    if [ -n "${!var}" ]; then
        echo -e "${GREEN}✅ $name set: ${!var}${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}❌ $name NOT set${NC}"
        FAIL=$((FAIL + 1))
    fi
}

check_service() {
    local service=$1
    local port=$2
    local name=$3
    
    if curl -s http://localhost:$port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name is running (port $port)${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${YELLOW}⚠️  $name may not be running (port $port)${NC}"
        WARN=$((WARN + 1))
    fi
}

check_hdfs_connection() {
    if hdfs dfs -ls / > /dev/null 2>&1; then
        echo -e "${GREEN}✅ HDFS is accessible${NC}"
        PASS=$((PASS + 1))
        
        # Check data directory
        if hdfs dfs -test -d /user/taxi/raw_data; then
            file_count=$(hdfs dfs -ls /user/taxi/raw_data | grep -c "\.parquet" || echo "0")
            if [ "$file_count" -gt 0 ]; then
                echo -e "${GREEN}   Found $file_count data files${NC}"
                PASS=$((PASS + 1))
            else
                echo -e "${YELLOW}   ⚠️  No data files found in /user/taxi/raw_data${NC}"
                WARN=$((WARN + 1))
            fi
        else
            echo -e "${YELLOW}   ⚠️  /user/taxi/raw_data directory not found${NC}"
            WARN=$((WARN + 1))
        fi
    else
        echo -e "${RED}❌ HDFS is NOT accessible${NC}"
        FAIL=$((FAIL + 1))
    fi
}

check_python_package() {
    local package=$1
    local name=$2
    
    if python3 -c "import $package" 2>/dev/null; then
        version=$(python3 -c "import $package; print($package.__version__)" 2>/dev/null || echo "unknown")
        echo -e "${GREEN}✅ Python $name installed ($version)${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}❌ Python $name NOT installed${NC}"
        FAIL=$((FAIL + 1))
    fi
}

check_ssh() {
    local host=$1
    
    if ssh -o BatchMode=yes -o ConnectTimeout=5 $host "echo 2>&1" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ SSH to $host works (passwordless)${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${YELLOW}⚠️  SSH to $host may require password or not configured${NC}"
        WARN=$((WARN + 1))
    fi
}

main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║           NYC TAXI GRAPH MINING - SETUP CHECKER               ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    echo "================================"
    echo "1. CHECKING BASIC COMMANDS"
    echo "================================"
    check_java
    check_command python3 "Python 3"
    check_command pip3 "pip3"
    check_command ssh "SSH"
    check_command hdfs "HDFS CLI"
    check_command spark-submit "Spark Submit"
    
    echo ""
    echo "================================"
    echo "2. CHECKING ENVIRONMENT VARIABLES"
    echo "================================"
    check_env_var HADOOP_HOME "HADOOP_HOME"
    check_env_var SPARK_HOME "SPARK_HOME"
    check_env_var JAVA_HOME "JAVA_HOME"
    
    echo ""
    echo "================================"
    echo "3. CHECKING SERVICES"
    echo "================================"
    check_service "hdfs" 9870 "HDFS NameNode"
    check_service "spark" 8080 "Spark Master"
    check_service "yarn" 8088 "YARN ResourceManager"
    
    echo ""
    echo "================================"
    echo "4. CHECKING HDFS"
    echo "================================"
    check_hdfs_connection
    
    echo ""
    echo "================================"
    echo "5. CHECKING PYTHON PACKAGES"
    echo "================================"
    check_python_package pyspark "PySpark"
    check_python_package pandas "Pandas"
    check_python_package numpy "NumPy"
    check_python_package matplotlib "Matplotlib"
    check_python_package seaborn "Seaborn"
    
    echo ""
    echo "================================"
    echo "6. CHECKING SSH CONNECTIVITY"
    echo "================================"
    check_ssh "localhost"
    
    # Try to check workers if hosts file exists
    if grep -q "worker1" /etc/hosts 2>/dev/null; then
        check_ssh "worker1"
    fi
    
    echo ""
    echo "================================"
    echo "7. CHECKING PROJECT STRUCTURE"
    echo "================================"
    
    if [ -d "src" ]; then
        echo -e "${GREEN}✅ src/ directory exists${NC}"
        PASS=$((PASS + 1))
        
        # Check key files
        for file in "1_build_graph.py" "2_pagerank.py" "3_clustering.py"; do
            if [ -f "src/$file" ]; then
                echo -e "${GREEN}   ✅ $file exists${NC}"
                PASS=$((PASS + 1))
            else
                echo -e "${RED}   ❌ $file missing${NC}"
                FAIL=$((FAIL + 1))
            fi
        done
    else
        echo -e "${RED}❌ src/ directory not found${NC}"
        FAIL=$((FAIL + 1))
    fi
    
    if [ -d "config" ]; then
        echo -e "${GREEN}✅ config/ directory exists${NC}"
        PASS=$((PASS + 1))
    else
        echo -e "${RED}❌ config/ directory not found${NC}"
        FAIL=$((FAIL + 1))
    fi
    
    # Summary
    echo ""
    echo "════════════════════════════════"
    echo "SUMMARY"
    echo "════════════════════════════════"
    echo -e "${GREEN}Passed:  $PASS${NC}"
    echo -e "${YELLOW}Warnings: $WARN${NC}"
    echo -e "${RED}Failed:  $FAIL${NC}"
    echo ""
    
    if [ $FAIL -eq 0 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║  ✅ SYSTEM IS READY!                   ║${NC}"
        echo -e "${GREEN}║  You can run: bash run_all.sh         ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
        exit 0
    else
        echo -e "${RED}╔════════════════════════════════════════╗${NC}"
        echo -e "${RED}║  ❌ SETUP INCOMPLETE                   ║${NC}"
        echo -e "${RED}║  Please fix the issues above          ║${NC}"
        echo -e "${RED}║  See setup_guide.md for help          ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════╝${NC}"
        exit 1
    fi
}

main
