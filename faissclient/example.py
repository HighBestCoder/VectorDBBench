#!/usr/bin/env python3
"""
FAISS HNSW 测试脚本
按照 VectorDBBench 的测试流程测试 FAISS HNSW 索引

用法:
    python example.py --m 32 --ef-construction 400 --ef-search 800
    python example.py --m 64 --ef-construction 1000 --ef-search 2000
    python example.py --dataset /builds/cohere/cohere_medium_1m --m 32 --ef-construction 300 --ef-search 600
"""

import argparse
import json
import pathlib
import time
from typing import Literal

import numpy as np
import polars as pl
from pyarrow.parquet import ParquetFile

from _native import FaissNativeClient, MetricKind


def parse_args():
    parser = argparse.ArgumentParser(description="Test FAISS HNSW index with VectorDBBench dataset")
    parser.add_argument(
        "--dataset",
        type=str,
        default="/builds/cohere/cohere_medium_1m",
        help="Dataset directory path (default: /builds/cohere/cohere_medium_1m)",
    )
    parser.add_argument(
        "--m",
        type=int,
        default=32,
        help="HNSW M parameter - edges per node (default: 32)",
    )
    parser.add_argument(
        "--ef-construction",
        type=int,
        default=400,
        help="HNSW ef_construction parameter (default: 400)",
    )
    parser.add_argument(
        "--ef-search",
        type=int,
        default=800,
        help="HNSW ef_search parameter (default: 800)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10000,
        help="Batch size for insertion (default: 10000)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=100,
        help="Top K for search (default: 100)",
    )
    parser.add_argument(
        "--num-threads",
        type=int,
        default=None,
        help="Number of threads for FAISS (default: use all cores)",
    )
    parser.add_argument(
        "--save-index",
        type=str,
        default=None,
        help="Path to save the index after build (optional)",
    )
    parser.add_argument(
        "--load-index",
        type=str,
        default=None,
        help="Path to load existing index (skip build phase)",
    )
    return parser.parse_args()


def detect_metric_type(dataset_dir: pathlib.Path) -> tuple[MetricKind, str]:
    """从数据集 parquet 文件的 schema 中检测 metric type"""
    # 尝试读取训练文件来检测 metric
    train_files = [
        "shuffle_train.parquet",
        "train.parquet",
    ]
    
    for train_file in train_files:
        file_path = dataset_dir / train_file
        if file_path.exists():
            pf = ParquetFile(file_path)
            schema = pf.schema_arrow
            metadata = schema.metadata
            
            # 检查 schema metadata 中是否有 metric_type
            if metadata and b"metric_type" in metadata:
                metric_str = metadata[b"metric_type"].decode().lower()
                if "cosine" in metric_str or "cos" in metric_str:
                    print(f"✓ Detected metric type from {train_file}: COSINE")
                    return MetricKind.INNER_PRODUCT, "COSINE"
                elif "l2" in metric_str or "euclidean" in metric_str:
                    print(f"✓ Detected metric type from {train_file}: L2")
                    return MetricKind.L2, "L2"
            break
    
    # 根据数据集名称推断
    dataset_name = dataset_dir.name.lower()
    if "cohere" in dataset_name or "openai" in dataset_name or "glove" in dataset_name:
        print(f"✓ Inferred metric type from dataset name '{dataset_name}': COSINE")
        return MetricKind.INNER_PRODUCT, "COSINE"
    elif "sift" in dataset_name:
        print(f"✓ Inferred metric type from dataset name '{dataset_name}': L2")
        return MetricKind.L2, "L2"
    
    # 默认使用 COSINE
    print("⚠ Could not detect metric type, defaulting to COSINE")
    return MetricKind.INNER_PRODUCT, "COSINE"


def load_dataset(dataset_dir: pathlib.Path, batch_size: int = 10000):
    """
    加载训练数据集，使用迭代器逐批读取（节省内存）
    
    返回: (iterator, total_count, dim)
    """
    # 查找训练文件
    train_files = [
        "shuffle_train.parquet",
        "train.parquet",
    ]
    
    train_file = None
    for f in train_files:
        if (dataset_dir / f).exists():
            train_file = dataset_dir / f
            break
    
    if train_file is None:
        raise FileNotFoundError(f"Training file not found in {dataset_dir}")
    
    print(f"✓ Found training file: {train_file.name}")
    
    # 获取元数据
    pf = ParquetFile(train_file, memory_map=True, pre_buffer=True)
    total_rows = pf.metadata.num_rows
    
    # 读取第一个 batch 来确定维度
    first_batch = next(pf.iter_batches(1)).to_pandas()
    vector_field = "emb" if "emb" in first_batch.columns else "vector"
    dim = len(first_batch[vector_field].iloc[0])
    
    print(f"✓ Dataset info: {total_rows:,} vectors, {dim} dimensions")
    
    # 创建迭代器
    def batch_iterator():
        pf = ParquetFile(train_file, memory_map=True, pre_buffer=True)
        for batch in pf.iter_batches(batch_size):
            df = batch.to_pandas()
            vectors = np.vstack(df[vector_field].values).astype(np.float32)
            ids = df["id"].values.astype(np.int64) if "id" in df.columns else np.arange(len(df), dtype=np.int64)
            yield vectors, ids
    
    return batch_iterator(), total_rows, dim, vector_field


def load_test_data(dataset_dir: pathlib.Path):
    """加载测试查询向量"""
    test_file = dataset_dir / "test.parquet"
    if not test_file.exists():
        print("⚠ test.parquet not found, skipping search phase")
        return None
    
    print(f"✓ Loading test queries from {test_file.name}")
    df = pl.read_parquet(test_file)
    
    # 确定向量字段名
    vector_field = "emb" if "emb" in df.columns else "vector"
    test_vectors = np.vstack(df[vector_field].to_list()).astype(np.float32)
    
    print(f"✓ Loaded {len(test_vectors)} test queries")
    return test_vectors


def load_ground_truth(dataset_dir: pathlib.Path):
    """加载 Ground Truth"""
    gt_file = dataset_dir / "neighbors.parquet"
    if not gt_file.exists():
        print("⚠ neighbors.parquet not found, cannot calculate recall")
        return None
    
    print(f"✓ Loading ground truth from {gt_file.name}")
    df = pl.read_parquet(gt_file)
    
    # 确定字段名 - VectorDBBench 使用 neighbors_id
    if "neighbors_id" in df.columns:
        neighbors_field = "neighbors_id"
    elif "neighbors" in df.columns:
        neighbors_field = "neighbors"
    else:
        neighbors_field = "ids"
    
    ground_truth = df[neighbors_field].to_list()
    
    print(f"✓ Loaded ground truth for {len(ground_truth)} queries")
    return ground_truth


def calculate_recall(search_results: list[np.ndarray], ground_truth: list[list[int]], k: int = 100) -> float:
    """
    计算 Recall@K
    
    Recall@K = (搜索结果与真实结果的交集) / K
    """
    if len(search_results) != len(ground_truth):
        raise ValueError(f"Results count mismatch: {len(search_results)} vs {len(ground_truth)}")
    
    total_recall = 0.0
    for i in range(len(search_results)):
        result_ids = set(search_results[i][:k])
        gt_ids = set(ground_truth[i][:k])
        overlap = len(result_ids & gt_ids)
        recall = overlap / k
        total_recall += recall
    
    return total_recall / len(search_results)


def main():
    args = parse_args()
    
    dataset_dir = pathlib.Path(args.dataset)
    if not dataset_dir.exists():
        print(f"✗ Dataset directory not found: {dataset_dir}")
        return 1
    
    print("=" * 70)
    print("FAISS HNSW Index Test")
    print("=" * 70)
    print(f"Dataset: {dataset_dir}")
    print(f"Parameters: M={args.m}, ef_construction={args.ef_construction}, ef_search={args.ef_search}")
    print(f"Batch size: {args.batch_size}, Top-K: {args.top_k}")
    print("=" * 70)
    print()
    
    # 检测 metric type
    metric_kind, metric_name = detect_metric_type(dataset_dir)
    
    client = None
    
    # 自动检测是否存在预构建的索引文件
    auto_index_path = None
    if not args.load_index:
        # 生成默认索引文件名
        index_filename = f"faiss_index_m{args.m}_efc{args.ef_construction}.index"
        potential_index = dataset_dir.parent / index_filename
        if potential_index.exists():
            auto_index_path = potential_index
            print(f"✓ Found existing index: {auto_index_path}")
            print(f"  Will load index instead of rebuilding")
            print()
    
    try:
        # ============================================================
        # Phase 1: Load Index or Build Index
        # ============================================================
        if args.load_index or auto_index_path:
            index_path = args.load_index or auto_index_path
            print(f"[Phase 1] Loading existing index from {index_path}")
            print("-" * 70)
            
            # 先需要确定维度来创建客户端
            _, _, dim, _ = load_dataset(dataset_dir, batch_size=1)
            
            client = FaissNativeClient(
                dim=dim,
                m=args.m,
                ef_construction=args.ef_construction,
                ef_search=args.ef_search,
                metric=metric_kind,
                num_threads=args.num_threads,
            )
            
            start = time.time()
            client.load(index_path)
            load_time = time.time() - start
            
            info = client.info()
            print(f"✓ Index loaded successfully in {load_time:.2f}s")
            print(f"  - Vectors: {info['ntotal']:,}")
            print(f"  - Dimension: {info['dim']}")
            print(f"  - M: {info['m']}")
            print(f"  - ef_search: {info['ef_search']}")
            print()
            
        else:
            print("[Phase 1] Building Index from Dataset")
            print("-" * 70)
            
            # 加载数据集
            batch_iter, total_count, dim, vector_field = load_dataset(dataset_dir, args.batch_size)
            
            # 创建 FAISS 客户端
            client = FaissNativeClient(
                dim=dim,
                m=args.m,
                ef_construction=args.ef_construction,
                ef_search=args.ef_search,
                metric=metric_kind,
                num_threads=args.num_threads,
            )
            
            print(f"✓ FAISS client created (metric={metric_name})")
            print(f"Starting batch insertion...")
            
            # 批量插入
            total_inserted = 0
            batch_count = 0
            start_time = time.time()
            
            for vectors, ids in batch_iter:
                batch_start = time.time()
                count = client.add(vectors, ids)
                batch_time = time.time() - batch_start
                
                total_inserted += count
                batch_count += 1
                progress = (total_inserted / total_count) * 100
                
                print(f"  Batch {batch_count}: inserted {count} vectors in {batch_time:.2f}s "
                      f"({total_inserted:,}/{total_count:,} = {progress:.1f}%)")
            
            build_time = time.time() - start_time
            
            info = client.info()
            print()
            print(f"✓ Index built successfully!")
            print(f"  - Total vectors: {info['ntotal']:,}")
            print(f"  - Build time: {build_time:.2f}s")
            print(f"  - Throughput: {info['ntotal'] / build_time:.0f} vectors/sec")
            print()
            
            # 自动保存索引（如果没有指定 save_index 且没有使用 auto_index_path）
            if not auto_index_path:
                if args.save_index:
                    save_path = pathlib.Path(args.save_index)
                else:
                    # 使用默认文件名
                    save_filename = f"faiss_index_m{args.m}_efc{args.ef_construction}.index"
                    save_path = dataset_dir.parent / save_filename
                
                # 确保目录存在
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                print(f"Saving index to {save_path}...")
                save_start = time.time()
                client.save(save_path)
                save_time = time.time() - save_start
                print(f"✓ Index saved in {save_time:.2f}s")
                print(f"  (Next time this index will be loaded automatically)")
                print()
        
        # ============================================================
        # Phase 2: Search and Calculate Recall
        # ============================================================
        print("[Phase 2] Search and Evaluate Recall")
        print("-" * 70)
        
        # 加载测试数据
        test_vectors = load_test_data(dataset_dir)
        if test_vectors is None:
            print("⚠ Skipping search phase (no test data)")
            return 0
        
        # 加载 Ground Truth
        ground_truth = load_ground_truth(dataset_dir)
        can_calculate_recall = ground_truth is not None
        
        # 执行搜索
        print(f"Running search for {len(test_vectors)} queries (top_k={args.top_k})...")
        search_results = []
        search_times = []
        
        for i, query in enumerate(test_vectors):
            start = time.time()
            ids, distances = client.search(query, args.top_k)
            search_time = time.time() - start
            
            search_results.append(ids)
            search_times.append(search_time)
            
            if (i + 1) % 100 == 0:
                avg_time = np.mean(search_times[-100:])
                print(f"  Progress: {i + 1}/{len(test_vectors)} queries, "
                      f"avg latency: {avg_time * 1000:.2f}ms")
        
        # 统计搜索性能
        avg_latency = np.mean(search_times) * 1000  # ms
        p50_latency = np.percentile(search_times, 50) * 1000
        p95_latency = np.percentile(search_times, 95) * 1000
        p99_latency = np.percentile(search_times, 99) * 1000
        qps = 1.0 / np.mean(search_times)
        
        print()
        print(f"✓ Search completed!")
        print(f"  - Total queries: {len(test_vectors)}")
        print(f"  - Avg latency: {avg_latency:.2f}ms")
        print(f"  - P50 latency: {p50_latency:.2f}ms")
        print(f"  - P95 latency: {p95_latency:.2f}ms")
        print(f"  - P99 latency: {p99_latency:.2f}ms")
        print(f"  - QPS (serial): {qps:.2f}")
        print()
        
        # 计算 Recall
        if can_calculate_recall:
            print(f"Calculating Recall@{args.top_k}...")
            recall = calculate_recall(search_results, ground_truth, k=args.top_k)
            print()
            print("=" * 70)
            print(f"📊 Final Results")
            print("=" * 70)
            print(f"Recall@{args.top_k}: {recall:.4f} ({recall * 100:.2f}%)")
            print()
            
            # 评价
            if recall > 0.99:
                grade = "优秀 ✓"
            elif recall > 0.95:
                grade = "良好"
            elif recall > 0.90:
                grade = "一般"
            else:
                grade = "差 ✗"
            
            print(f"评价: {grade}")
            print()
        
        # 输出摘要 JSON
        summary = {
            "dataset": str(dataset_dir),
            "metric_type": metric_name,
            "parameters": {
                "m": args.m,
                "ef_construction": args.ef_construction,
                "ef_search": args.ef_search,
            },
            "index_info": client.info(),
            "search_performance": {
                "avg_latency_ms": float(avg_latency),
                "p50_latency_ms": float(p50_latency),
                "p95_latency_ms": float(p95_latency),
                "p99_latency_ms": float(p99_latency),
                "qps": float(qps),
                "num_queries": len(test_vectors),
            },
        }
        
        if can_calculate_recall:
            summary["recall"] = {
                f"recall@{args.top_k}": float(recall),
            }
        
        summary_file = dataset_dir.parent / f"faiss_test_results_{args.m}_{args.ef_construction}_{args.ef_search}.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"Results saved to: {summary_file}")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    exit(main())
