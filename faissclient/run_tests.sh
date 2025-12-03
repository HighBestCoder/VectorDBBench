#!/bin/bash

# FAISS HNSW 参数测试脚本
# 测试不同的 M, ef_construction, ef_search 组合

DATASET="/builds/cohere/cohere_medium_1m"
BATCH_SIZE=10000
TOP_K=100

echo "======================================================================"
echo "FAISS HNSW Parameter Tests"
echo "======================================================================"
echo "Dataset: $DATASET"
echo "Batch Size: $BATCH_SIZE"
echo "Top-K: $TOP_K"
echo ""


apt update && apt install -y libgomp1
mkdir -p /builds/VectorDBBench/faiss1m/

# 测试配置数组
# 格式: "M ef_construction ef_search 描述"
configs=(
    "32 300 300 baseline_small"
    "32 400 800 recommended_1m"
    "64 1000 2000 current_vdss"
    "48 500 1000 balanced"
)

for config in "${configs[@]}"; do
    read -r M EF_C EF_S DESC <<< "$config"
    
    echo ""
    echo "======================================================================"
    echo "Test: $DESC"
    echo "Parameters: M=$M, ef_construction=$EF_C, ef_search=$EF_S"
    echo "======================================================================"
    echo ""
    
    # 运行测试
    python3 example.py \
        --dataset "$DATASET" \
        --m "$M" \
        --ef-construction "$EF_C" \
        --ef-search "$EF_S" \
        --batch-size "$BATCH_SIZE" \
        --top-k "$TOP_K" \
        --save-index "/builds/VectorDBBench/faiss1m/index_${DESC}.faiss"
    
    if [ $? -ne 0 ]; then
        echo "✗ Test failed: $DESC"
        exit 1
    fi
    
    echo ""
    echo "✓ Test completed: $DESC"
    echo ""
done

echo ""
echo "======================================================================"
echo "All tests completed!"
echo "======================================================================"
echo ""
echo "Result files saved in: /builds/VectorDBBench/faiss1m/"
ls -lh /builds/VectorDBBench/faiss1m/
