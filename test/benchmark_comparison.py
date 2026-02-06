"""
So sánh hiệu năng: Single Machine vs Distributed Cluster
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class PerformanceComparison:
    def __init__(self, single_metrics_path, cluster_metrics_path):
        """
        Args:
            single_metrics_path: CSV từ test_single_machine.py
            cluster_metrics_path: CSV từ benchmark.py (cluster mode)
        """
        self.single_df = pd.read_csv(single_metrics_path)
        self.cluster_df = pd.read_csv(cluster_metrics_path)
    
    def compare_metrics(self):
        """So sánh metrics chi tiết"""
        print(f"\n{'='*60}")
        print(f"PERFORMANCE COMPARISON")
        print(f"{'='*60}")
        
        # Tìm test chung giữa 2 mode
        common_tests = set(self.single_df['test']) & set(self.cluster_df['test'])
        
        for test in common_tests:
            print(f"\n📊 Test: {test}")
            print(f"{'-'*60}")
            
            single_row = self.single_df[self.single_df['test'] == test].iloc[0]
            cluster_row = self.cluster_df[self.cluster_df['test'] == test].iloc[0]
            
            if single_row['status'] == 'SUCCESS' and cluster_row['status'] == 'SUCCESS':
                speedup = single_row['time_seconds'] / cluster_row['time_seconds']
                
                print(f"  Time:")
                print(f"    - Single Machine: {single_row['time_seconds']:.2f}s")
                print(f"    - Cluster:        {cluster_row['time_seconds']:.2f}s")
                print(f"    - Speedup:        {speedup:.2f}x")
                
                if 'memory_delta_gb' in single_row and 'memory_delta_gb' in cluster_row:
                    print(f"  Memory:")
                    print(f"    - Single Machine: {single_row['memory_delta_gb']:.2f} GB")
                    print(f"    - Cluster:        {cluster_row['memory_delta_gb']:.2f} GB")
            else:
                print(f"  ⚠️ Incomplete data (one mode failed)")
    
    def plot_comparison(self, output_path="results/comparison_plots.png"):
        """Vẽ biểu đồ so sánh"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Single Machine vs Distributed Cluster', fontsize=16)
        
        # Prepare data
        single_success = self.single_df[self.single_df['status'] == 'SUCCESS']
        cluster_success = self.cluster_df[self.cluster_df['status'] == 'SUCCESS']
        
        # Plot 1: Execution Time Comparison
        ax1 = axes[0, 0]
        tests = list(set(single_success['test']) & set(cluster_success['test']))
        
        single_times = [single_success[single_success['test'] == t]['time_seconds'].values[0] for t in tests]
        cluster_times = [cluster_success[cluster_success['test'] == t]['time_seconds'].values[0] for t in tests]
        
        x = range(len(tests))
        width = 0.35
        ax1.bar([i - width/2 for i in x], single_times, width, label='Single Machine')
        ax1.bar([i + width/2 for i in x], cluster_times, width, label='Cluster')
        ax1.set_xlabel('Test Type')
        ax1.set_ylabel('Time (seconds)')
        ax1.set_title('Execution Time Comparison')
        ax1.set_xticks(x)
        ax1.set_xticklabels(tests, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # Plot 2: Speedup Factor
        ax2 = axes[0, 1]
        speedups = [single_times[i] / cluster_times[i] for i in range(len(tests))]
        ax2.bar(tests, speedups, color='green', alpha=0.7)
        ax2.axhline(y=1, color='r', linestyle='--', label='Baseline (1x)')
        ax2.set_xlabel('Test Type')
        ax2.set_ylabel('Speedup Factor')
        ax2.set_title('Cluster Speedup over Single Machine')
        ax2.tick_params(axis='x', rotation=45)
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)
        
        # Plot 3: Success Rate
        ax3 = axes[1, 0]
        categories = ['Single Machine', 'Cluster']
        success_rates = [
            (self.single_df['status'] == 'SUCCESS').sum() / len(self.single_df) * 100,
            (self.cluster_df['status'] == 'SUCCESS').sum() / len(self.cluster_df) * 100
        ]
        colors = ['orange', 'green']
        ax3.bar(categories, success_rates, color=colors, alpha=0.7)
        ax3.set_ylabel('Success Rate (%)')
        ax3.set_title('Success Rate Comparison')
        ax3.set_ylim([0, 100])
        for i, v in enumerate(success_rates):
            ax3.text(i, v + 2, f'{v:.1f}%', ha='center', fontweight='bold')
        
        # Plot 4: Memory Usage (if available)
        ax4 = axes[1, 1]
        if 'memory_delta_gb' in single_success.columns and 'memory_delta_gb' in cluster_success.columns:
            single_mem = [single_success[single_success['test'] == t]['memory_delta_gb'].values[0] for t in tests]
            cluster_mem = [cluster_success[cluster_success['test'] == t]['memory_delta_gb'].values[0] for t in tests]
            
            ax4.bar([i - width/2 for i in x], single_mem, width, label='Single Machine')
            ax4.bar([i + width/2 for i in x], cluster_mem, width, label='Cluster')
            ax4.set_xlabel('Test Type')
            ax4.set_ylabel('Memory Delta (GB)')
            ax4.set_title('Memory Usage Comparison')
            ax4.set_xticks(x)
            ax4.set_xticklabels(tests, rotation=45, ha='right')
            ax4.legend()
        else:
            ax4.text(0.5, 0.5, 'Memory data not available', 
                    ha='center', va='center', transform=ax4.transAxes)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"\n📊 Comparison plots saved to: {output_path}")
        plt.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--single', type=str, required=True,
                       help='Path to single machine metrics CSV')
    parser.add_argument('--cluster', type=str, required=True,
                       help='Path to cluster metrics CSV')
    parser.add_argument('--output', type=str, default='results/comparison_plots.png',
                       help='Output plot path')
    
    args = parser.parse_args()
    
    comparator = PerformanceComparison(args.single, args.cluster)
    comparator.compare_metrics()
    comparator.plot_comparison(args.output)