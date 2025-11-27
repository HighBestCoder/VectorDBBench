#!/usr/bin/env python3
"""
Compare VectorDBBench Results and Generate Charts

This script reads test results from VDSS and Qdrant, then generates
comparison charts for QPS, latency, and other metrics.
"""

import json
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Set matplotlib to use non-interactive backend
plt.switch_backend('Agg')

RESULTS_DIR = Path("/builds/VectorDBBench/vectordb_bench/results")
OUTPUT_DIR = Path("/builds/VectorDBBench/benchmark_comparison")


def load_latest_result(db_name):
    """Load the latest result file for a database"""
    db_dir = RESULTS_DIR / db_name
    if not db_dir.exists():
        print(f"❌ No results found for {db_name}")
        return None
    
    # Find all result files
    result_files = list(db_dir.glob("result_*.json"))
    if not result_files:
        print(f"❌ No result files found in {db_dir}")
        return None
    
    # Get the latest file
    latest_file = max(result_files, key=lambda p: p.stat().st_mtime)
    print(f"📂 Loading {db_name}: {latest_file.name}")
    
    with open(latest_file, 'r') as f:
        return json.load(f)


def extract_metrics(result_data):
    """Extract key metrics from result data"""
    if not result_data or 'results' not in result_data:
        return None
    
    results = result_data['results'][0]  # Get first test case
    
    metrics = {
        'db_name': results.get('db', 'Unknown'),
        'db_label': results.get('db_label', ''),
        'case_name': results.get('case_name', ''),
        'load_duration': results.get('load_duration', 0),
        'optimize_duration': results.get('optimize_duration', 0),
        'serial_qps': [],
        'serial_latency_p99': [],
        'serial_latency_p95': [],
        'serial_recall': [],
        'concurrent_qps': {},
        'concurrent_latency_p99': {},
        'max_load_count': results.get('max_load_count', 0),
    }
    
    # Extract serial search metrics
    if 'serial_search_results' in results:
        for sr in results['serial_search_results']:
            metrics['serial_qps'].append(sr.get('qps', 0))
            metrics['serial_latency_p99'].append(sr.get('latency_p99', 0) * 1000)  # Convert to ms
            metrics['serial_latency_p95'].append(sr.get('latency_p95', 0) * 1000)
            metrics['serial_recall'].append(sr.get('recall', 0))
    
    # Extract concurrent search metrics
    if 'concurrent_search_results' in results:
        for cr in results['concurrent_search_results']:
            concurrency = cr.get('concurrency', 0)
            metrics['concurrent_qps'][concurrency] = cr.get('qps', 0)
            metrics['concurrent_latency_p99'][concurrency] = cr.get('latency_p99', 0) * 1000
    
    return metrics


def plot_comparison(vdss_metrics, qdrant_metrics):
    """Generate comparison charts"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')
    colors = {'VDSS': '#FF6B6B', 'Qdrant': '#4ECDC4'}
    
    print("\n📊 Generating comparison charts...")
    
    # 1. Load & Optimize Duration Comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    
    databases = ['VDSS', 'Qdrant']
    load_times = [vdss_metrics['load_duration'], qdrant_metrics['load_duration']]
    optimize_times = [vdss_metrics['optimize_duration'], qdrant_metrics['optimize_duration']]
    
    x = np.arange(len(databases))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, load_times, width, label='Load Duration', color=['#FF6B6B', '#4ECDC4'])
    bars2 = ax.bar(x + width/2, optimize_times, width, label='Optimize Duration', color=['#FFB6B6', '#9EEEE4'])
    
    ax.set_ylabel('Time (seconds)', fontsize=12)
    ax.set_title('Load & Optimize Duration Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(databases)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}s',
                   ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'load_optimize_comparison.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved: load_optimize_comparison.png")
    plt.close()
    
    # 2. Serial Search QPS Comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    
    vdss_qps = np.mean(vdss_metrics['serial_qps']) if vdss_metrics['serial_qps'] else 0
    qdrant_qps = np.mean(qdrant_metrics['serial_qps']) if qdrant_metrics['serial_qps'] else 0
    
    bars = ax.bar(databases, [vdss_qps, qdrant_qps], color=[colors['VDSS'], colors['Qdrant']], width=0.6)
    
    ax.set_ylabel('Queries Per Second (QPS)', fontsize=12)
    ax.set_title('Serial Search QPS Comparison', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.1f}',
               ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'serial_qps_comparison.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved: serial_qps_comparison.png")
    plt.close()
    
    # 3. Serial Search Latency Comparison (P99)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    vdss_p99 = np.mean(vdss_metrics['serial_latency_p99']) if vdss_metrics['serial_latency_p99'] else 0
    qdrant_p99 = np.mean(qdrant_metrics['serial_latency_p99']) if qdrant_metrics['serial_latency_p99'] else 0
    
    bars = ax.bar(databases, [vdss_p99, qdrant_p99], color=[colors['VDSS'], colors['Qdrant']], width=0.6)
    
    ax.set_ylabel('Latency (ms)', fontsize=12)
    ax.set_title('Serial Search Latency P99 Comparison', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.2f}ms',
               ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'serial_latency_p99_comparison.png', dpi=300, bbox_inches='tight')
    print(f"  ✓ Saved: serial_latency_p99_comparison.png")
    plt.close()
    
    # 4. Concurrent Search QPS Comparison
    if vdss_metrics['concurrent_qps'] and qdrant_metrics['concurrent_qps']:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        concurrencies = sorted(set(list(vdss_metrics['concurrent_qps'].keys()) + 
                                  list(qdrant_metrics['concurrent_qps'].keys())))
        
        vdss_concurrent_qps = [vdss_metrics['concurrent_qps'].get(c, 0) for c in concurrencies]
        qdrant_concurrent_qps = [qdrant_metrics['concurrent_qps'].get(c, 0) for c in concurrencies]
        
        x = np.arange(len(concurrencies))
        width = 0.35
        
        ax.bar(x - width/2, vdss_concurrent_qps, width, label='VDSS', color=colors['VDSS'])
        ax.bar(x + width/2, qdrant_concurrent_qps, width, label='Qdrant', color=colors['Qdrant'])
        
        ax.set_xlabel('Concurrency Level', fontsize=12)
        ax.set_ylabel('QPS', fontsize=12)
        ax.set_title('Concurrent Search QPS Comparison', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(concurrencies)
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / 'concurrent_qps_comparison.png', dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: concurrent_qps_comparison.png")
        plt.close()
    
    # 5. Recall Comparison
    if vdss_metrics['serial_recall'] and qdrant_metrics['serial_recall']:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        vdss_recall = np.mean(vdss_metrics['serial_recall']) * 100
        qdrant_recall = np.mean(qdrant_metrics['serial_recall']) * 100
        
        bars = ax.bar(databases, [vdss_recall, qdrant_recall], 
                     color=[colors['VDSS'], colors['Qdrant']], width=0.6)
        
        ax.set_ylabel('Recall (%)', fontsize=12)
        ax.set_title('Search Recall Comparison', fontsize=14, fontweight='bold')
        ax.set_ylim([0, 105])
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}%',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / 'recall_comparison.png', dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: recall_comparison.png")
        plt.close()
    
    print(f"\n✅ All charts saved to: {OUTPUT_DIR}")


def generate_summary_report(vdss_metrics, qdrant_metrics):
    """Generate a text summary report"""
    report_file = OUTPUT_DIR / 'performance_summary.txt'
    
    with open(report_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("VectorDBBench Performance Comparison: VDSS vs Qdrant\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Test Case: {vdss_metrics['case_name']}\n")
        f.write(f"Dataset: {vdss_metrics.get('max_load_count', 0):,} vectors\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("Load & Index Building Performance\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Metric':<30} {'VDSS':>20} {'Qdrant':>20}\n")
        f.write(f"{'-'*30} {'-'*20} {'-'*20}\n")
        f.write(f"{'Load Duration (s)':<30} {vdss_metrics['load_duration']:>20.2f} {qdrant_metrics['load_duration']:>20.2f}\n")
        f.write(f"{'Optimize Duration (s)':<30} {vdss_metrics['optimize_duration']:>20.2f} {qdrant_metrics['optimize_duration']:>20.2f}\n")
        f.write(f"{'Total Time (s)':<30} {vdss_metrics['load_duration']+vdss_metrics['optimize_duration']:>20.2f} {qdrant_metrics['load_duration']+qdrant_metrics['optimize_duration']:>20.2f}\n")
        
        f.write("\n" + "-" * 80 + "\n")
        f.write("Serial Search Performance\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Metric':<30} {'VDSS':>20} {'Qdrant':>20}\n")
        f.write(f"{'-'*30} {'-'*20} {'-'*20}\n")
        
        vdss_qps = np.mean(vdss_metrics['serial_qps']) if vdss_metrics['serial_qps'] else 0
        qdrant_qps = np.mean(qdrant_metrics['serial_qps']) if qdrant_metrics['serial_qps'] else 0
        f.write(f"{'Average QPS':<30} {vdss_qps:>20.2f} {qdrant_qps:>20.2f}\n")
        
        vdss_p99 = np.mean(vdss_metrics['serial_latency_p99']) if vdss_metrics['serial_latency_p99'] else 0
        qdrant_p99 = np.mean(qdrant_metrics['serial_latency_p99']) if qdrant_metrics['serial_latency_p99'] else 0
        f.write(f"{'P99 Latency (ms)':<30} {vdss_p99:>20.2f} {qdrant_p99:>20.2f}\n")
        
        vdss_p95 = np.mean(vdss_metrics['serial_latency_p95']) if vdss_metrics['serial_latency_p95'] else 0
        qdrant_p95 = np.mean(qdrant_metrics['serial_latency_p95']) if qdrant_metrics['serial_latency_p95'] else 0
        f.write(f"{'P95 Latency (ms)':<30} {vdss_p95:>20.2f} {qdrant_p95:>20.2f}\n")
        
        if vdss_metrics['serial_recall'] and qdrant_metrics['serial_recall']:
            vdss_recall = np.mean(vdss_metrics['serial_recall']) * 100
            qdrant_recall = np.mean(qdrant_metrics['serial_recall']) * 100
            f.write(f"{'Average Recall (%)':<30} {vdss_recall:>20.2f} {qdrant_recall:>20.2f}\n")
        
        f.write("\n" + "=" * 80 + "\n")
    
    print(f"  ✓ Saved: performance_summary.txt")


def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║     VectorDBBench Performance Comparison Tool                   ║")
    print("║     VDSS vs Qdrant                                              ║")
    print("╚══════════════════════════════════════════════════════════════════╝\n")
    
    # Check if matplotlib is installed
    try:
        import matplotlib
    except ImportError:
        print("❌ matplotlib is not installed")
        print("Install with: pip install matplotlib")
        return 1
    
    # Load results
    vdss_data = load_latest_result("VDSS")
    qdrant_data = load_latest_result("QdrantLocal")
    
    if not vdss_data or not qdrant_data:
        print("\n❌ Could not load results for both databases")
        print("Make sure both benchmarks have completed successfully")
        return 1
    
    # Extract metrics
    print("\n📈 Extracting metrics...")
    vdss_metrics = extract_metrics(vdss_data)
    qdrant_metrics = extract_metrics(qdrant_data)
    
    if not vdss_metrics or not qdrant_metrics:
        print("❌ Failed to extract metrics from results")
        return 1
    
    print(f"  ✓ VDSS: {vdss_metrics['case_name']}")
    print(f"  ✓ Qdrant: {qdrant_metrics['case_name']}")
    
    # Generate charts
    plot_comparison(vdss_metrics, qdrant_metrics)
    
    # Generate summary report
    print("\n📄 Generating summary report...")
    generate_summary_report(vdss_metrics, qdrant_metrics)
    
    print("\n" + "=" * 70)
    print("✅ Performance comparison completed successfully!")
    print(f"📁 Results saved to: {OUTPUT_DIR}")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
