import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
from scipy import signal
from scipy.ndimage import gaussian_filter1d

# Set style for better-looking plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_and_process_data(file_path='Lin Lab AMI data.xlsx'):
    """
    Load and process Haley's data from Excel file
    """
    print("Loading Haley's data from Excel file...")
    df = pd.read_excel(file_path, sheet_name='Haley', header=None)
    
    # Extract data starting from row 20
    data_start_row = 20
    time_seconds = pd.to_numeric(df.iloc[data_start_row:, 0], errors='coerce').values
    values = pd.to_numeric(df.iloc[data_start_row:, 2], errors='coerce').values
    
    # Clean data - remove NaN values
    valid_indices = ~(np.isnan(time_seconds) | np.isnan(values))
    time_seconds = time_seconds[valid_indices].astype(int)
    values = values[valid_indices]
    
    print(f"Loaded {len(values)} data points")
    print(f"Time range: {time_seconds[0]} to {time_seconds[-1]} seconds\n")
    
    return time_seconds, values


def find_peaks_scipy(values, height_percentile=75):
    """
    Find peaks using scipy's peak detection algorithm
    """
    # Set minimum height as percentile of data
    min_height = np.percentile(values, height_percentile)
    
    # Find peaks
    peaks, properties = signal.find_peaks(values, 
                                         height=min_height,
                                         distance=3,  # Minimum distance between peaks
                                         prominence=50)  # Minimum prominence
    
    # Sort peaks by height and return top peaks
    if len(peaks) > 0:
        peak_heights = properties['peak_heights']
        sorted_indices = np.argsort(peak_heights)[::-1]
        return peaks[sorted_indices], peak_heights[sorted_indices]
    return np.array([]), np.array([])


def analyze_periods(time_seconds, values):
    """
    Analyze each time period for peaks and statistics
    """
    # Define time periods (in seconds)
    time_periods = {
        'No weight (1:30-2:30)': {'start': 90, 'end': 150, 'color': '#FF6B6B'},
        '2.5 lbs (3:10-4:10)': {'start': 190, 'end': 250, 'color': '#4ECDC4'},
        '5 lbs (5:15-6:15)': {'start': 315, 'end': 375, 'color': '#45B7D1'},
        '7.5 lbs (7:40-8:40)': {'start': 460, 'end': 520, 'color': '#96CEB4'},
        '10 lbs (9:40-10:40)': {'start': 580, 'end': 640, 'color': '#FECA57'}
    }
    
    results = {}
    
    for period_name, period_info in time_periods.items():
        # Extract data for this period
        mask = (time_seconds >= period_info['start']) & (time_seconds <= period_info['end'])
        period_values = values[mask]
        period_times = time_seconds[mask]
        
        if len(period_values) == 0:
            print(f"Warning: No data found for {period_name}")
            continue
        
        # Calculate statistics
        period_avg = np.mean(period_values)
        period_std = np.std(period_values)
        period_median = np.median(period_values)
        
        # Find peaks using two methods
        # Method 1: Simple top 3 values
        sorted_indices = np.argsort(period_values)[::-1]
        top_3_indices = sorted_indices[:3]
        top_3_values = period_values[top_3_indices]
        top_3_times = period_times[top_3_indices]
        
        # Method 2: Scientific peak detection
        peaks_sci, heights_sci = find_peaks_scipy(period_values)
        
        # Calculate metrics
        peak_above_avg = top_3_values - period_avg
        peak_above_avg_percent = (peak_above_avg / period_avg) * 100
        
        # Store results
        results[period_name] = {
            'average': period_avg,
            'std': period_std,
            'median': period_median,
            'peak_values': top_3_values,
            'peak_times': top_3_times,
            'peak_above_avg': peak_above_avg,
            'peak_above_avg_percent': peak_above_avg_percent,
            'all_values': period_values,
            'all_times': period_times,
            'color': period_info['color'],
            'scientific_peaks': peaks_sci[:3] if len(peaks_sci) > 0 else np.array([]),
            'scientific_heights': heights_sci[:3] if len(heights_sci) > 0 else np.array([])
        }
        
        # Print results
        print(f"\n{'='*60}")
        print(f"{period_name}")
        print(f"{'='*60}")
        print(f"Statistics:")
        print(f"  Average: {period_avg:.2f} μA")
        print(f"  Median: {period_median:.2f} μA")
        print(f"  Std Dev: {period_std:.2f} μA")
        print(f"  Data points: {len(period_values)}")
        print(f"\nTop 3 peaks:")
        for i in range(3):
            print(f"  Peak {i+1}: {top_3_values[i]:.2f} μA")
            print(f"          Above avg: +{peak_above_avg[i]:.2f} ({peak_above_avg_percent[i]:.1f}%)")
    
    return results, time_periods


def create_comprehensive_visualization(time_seconds, values, results):
    """
    Create a comprehensive multi-panel visualization
    """
    # Create figure with custom layout
    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    # Main title
    fig.suptitle('Haley\'s AMI Data - Comprehensive Peak Analysis', fontsize=20, fontweight='bold')
    
    # 1. Full time series with highlighted periods
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(time_seconds, values, 'b-', alpha=0.5, linewidth=0.8, label='Raw Signal')
    
    # Apply smoothing for trend visualization
    smoothed = gaussian_filter1d(values, sigma=3)
    ax1.plot(time_seconds, smoothed, 'navy', linewidth=1.5, alpha=0.7, label='Smoothed Trend')
    
    # Highlight each period with different colors
    for period_name, data in results.items():
        period_mask = np.isin(time_seconds, data['all_times'])
        ax1.fill_between(time_seconds[period_mask], 0, values[period_mask], 
                         alpha=0.3, color=data['color'], label=period_name.split('(')[0])
    
    ax1.set_title('Complete Time Series with Weight Conditions', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Time (seconds)', fontsize=12)
    ax1.set_ylabel('AMI Value (μA)', fontsize=12)
    ax1.legend(loc='upper right', ncol=3, fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # 2-6. Individual period analysis
    period_axes = []
    positions = [(1, 0), (1, 1), (1, 2), (2, 0), (2, 1)]
    
    for idx, (period_name, data) in enumerate(results.items()):
        if idx >= 5:
            break
        
        ax = fig.add_subplot(gs[positions[idx][0], positions[idx][1]])
        period_axes.append(ax)
        
        # Plot signal for this period
        ax.plot(data['all_times'], data['all_values'], 
                color=data['color'], alpha=0.6, linewidth=1.5)
        
        # Fill area under curve
        ax.fill_between(data['all_times'], 0, data['all_values'], 
                        color=data['color'], alpha=0.2)
        
        # Mark average and standard deviation bands
        ax.axhline(y=data['average'], color='green', linestyle='--', 
                  linewidth=2, label=f'Avg: {data["average"]:.1f}')
        ax.axhspan(data['average'] - data['std'], data['average'] + data['std'],
                  alpha=0.1, color='green', label='±1 SD')
        
        # Mark the top 3 peaks with enhanced visibility
        ax.scatter(data['peak_times'], data['peak_values'], 
                  color='red', s=150, zorder=5, edgecolor='darkred', 
                  linewidth=2, label='Top 3 Peaks')
        
        # Add value annotations for peaks
        for i in range(3):
            ax.annotate(f'+{data["peak_above_avg_percent"][i]:.1f}%\n({data["peak_values"][i]:.0f})',
                       xy=(data['peak_times'][i], data['peak_values'][i]),
                       xytext=(10, 10), textcoords='offset points',
                       fontsize=9, color='darkred', fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                               edgecolor='red', alpha=0.8),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3',
                                     color='darkred', linewidth=1.5))
        
        # Styling
        weight = period_name.split('(')[0].strip()
        ax.set_title(f'{weight}', fontsize=12, fontweight='bold', color=data['color'])
        ax.set_xlabel('Time (s)', fontsize=10)
        ax.set_ylabel('AMI (μA)', fontsize=10)
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    # 7. Summary statistics comparison
    ax7 = fig.add_subplot(gs[2, 2])
    
    periods = list(results.keys())
    weights = [p.split('(')[0].strip() for p in periods]
    averages = [results[p]['average'] for p in periods]
    stds = [results[p]['std'] for p in periods]
    colors = [results[p]['color'] for p in periods]
    
    x_pos = np.arange(len(weights))
    bars = ax7.bar(x_pos, averages, yerr=stds, capsize=5, 
                   color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for i, (bar, avg) in enumerate(zip(bars, averages)):
        ax7.text(bar.get_x() + bar.get_width()/2., avg + stds[i] + 20,
                f'{avg:.0f}', ha='center', va='bottom', fontweight='bold')
    
    ax7.set_title('Average AMI Values by Weight', fontsize=12, fontweight='bold')
    ax7.set_xlabel('Weight Condition', fontsize=10)
    ax7.set_ylabel('Average AMI (μA)', fontsize=10)
    ax7.set_xticks(x_pos)
    ax7.set_xticklabels(weights, rotation=45, ha='right')
    ax7.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('haley_comprehensive_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()


def create_peak_analysis_charts(results):
    """
    Create focused charts for peak analysis
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Peak Analysis - Detailed Comparison', fontsize=18, fontweight='bold')
    
    periods = list(results.keys())
    weights = [p.split('(')[0].strip() for p in periods]
    colors = [results[p]['color'] for p in periods]
    
    # 1. Grouped bar chart - All peaks comparison
    ax1 = axes[0, 0]
    x = np.arange(len(weights))
    width = 0.25
    
    peak1 = [results[p]['peak_above_avg_percent'][0] for p in periods]
    peak2 = [results[p]['peak_above_avg_percent'][1] for p in periods]
    peak3 = [results[p]['peak_above_avg_percent'][2] for p in periods]
    
    bars1 = ax1.bar(x - width, peak1, width, label='Peak 1', color='#FF6B6B', edgecolor='black')
    bars2 = ax1.bar(x, peak2, width, label='Peak 2', color='#4ECDC4', edgecolor='black')
    bars3 = ax1.bar(x + width, peak3, width, label='Peak 3', color='#45B7D1', edgecolor='black')
    
    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
    
    ax1.set_title('Peak Elevation Above Average (%)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Weight Condition', fontsize=12)
    ax1.set_ylabel('Percentage Above Average (%)', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(weights)
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. Line plot - Peak trends
    ax2 = axes[0, 1]
    weight_values = [0, 2.5, 5, 7.5, 10]  # Actual weight values
    
    # Plot trends for each peak
    for i in range(3):
        peak_percentages = [results[p]['peak_above_avg_percent'][i] for p in periods]
        ax2.plot(weight_values, peak_percentages, 
                marker='o', markersize=10, linewidth=2.5,
                label=f'Peak {i+1}', alpha=0.8)
    
    ax2.set_title('Peak Elevation Trends with Weight', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Weight (lbs)', fontsize=12)
    ax2.set_ylabel('Percentage Above Average (%)', fontsize=12)
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    # 3. Box plot - Distribution comparison
    ax3 = axes[1, 0]
    
    # Prepare data for box plot
    all_elevations = []
    labels = []
    positions = []
    
    for i, (period_name, data) in enumerate(results.items()):
        # Calculate all values above average
        above_avg = (data['all_values'] - data['average']) / data['average'] * 100
        all_elevations.append(above_avg[above_avg > 0])  # Only positive values
        labels.append(weights[i])
        positions.append(i)
    
    bp = ax3.boxplot(all_elevations, positions=positions, widths=0.6,
                     patch_artist=True, showfliers=False)
    
    # Color the box plots
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Customize box plot
    ax3.set_title('Distribution of Values Above Average', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Weight Condition', fontsize=12)
    ax3.set_ylabel('Percentage Above Average (%)', fontsize=12)
    ax3.set_xticks(positions)
    ax3.set_xticklabels(labels)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Heatmap - Peak characteristics
    ax4 = axes[1, 1]
    
    # Create matrix for heatmap
    heatmap_data = []
    for period in periods:
        row = []
        row.append(results[period]['peak_values'][0])  # Highest peak
        row.append(results[period]['peak_above_avg_percent'][0])  # % above avg
        row.append(results[period]['average'])  # Average
        row.append(results[period]['std'])  # Std dev
        heatmap_data.append(row)
    
    # Normalize each column separately for better visualization
    heatmap_array = np.array(heatmap_data)
    heatmap_norm = (heatmap_array - heatmap_array.min(axis=0)) / (heatmap_array.max(axis=0) - heatmap_array.min(axis=0))
    
    im = ax4.imshow(heatmap_norm, cmap='YlOrRd', aspect='auto')
    
    # Set ticks and labels
    ax4.set_xticks(np.arange(4))
    ax4.set_yticks(np.arange(len(weights)))
    ax4.set_xticklabels(['Max Peak\nValue', 'Max Peak\n% Above Avg', 'Period\nAverage', 'Std Dev'])
    ax4.set_yticklabels(weights)
    
    # Add text annotations
    for i in range(len(weights)):
        for j in range(4):
            text = ax4.text(j, i, f'{heatmap_data[i][j]:.1f}',
                          ha="center", va="center", color="black", fontsize=10)
    
    ax4.set_title('Peak Characteristics Heatmap', fontsize=14, fontweight='bold')
    plt.colorbar(im, ax=ax4, label='Normalized Value')
    
    plt.tight_layout()
    plt.savefig('haley_peak_analysis_charts.png', dpi=300, bbox_inches='tight')
    plt.show()


def create_statistical_summary(results):
    """
    Create statistical summary and export to DataFrame
    """
    summary_data = []
    
    for period_name, data in results.items():
        weight = period_name.split('(')[0].strip()
        
        # Period statistics
        summary_data.append({
            'Weight Condition': weight,
            'Metric': 'Period Statistics',
            'Average (μA)': data['average'],
            'Median (μA)': data['median'],
            'Std Dev (μA)': data['std'],
            'Peak 1 Value': data['peak_values'][0],
            'Peak 1 Above Avg (%)': data['peak_above_avg_percent'][0],
            'Peak 2 Value': data['peak_values'][1],
            'Peak 2 Above Avg (%)': data['peak_above_avg_percent'][1],
            'Peak 3 Value': data['peak_values'][2],
            'Peak 3 Above Avg (%)': data['peak_above_avg_percent'][2],
        })
    
    df_summary = pd.DataFrame(summary_data)
    
    # Format the dataframe
    numeric_columns = df_summary.select_dtypes(include=[np.number]).columns
    df_summary[numeric_columns] = df_summary[numeric_columns].round(2)
    
    return df_summary


def create_interactive_timeline(time_seconds, values, results):
    """
    Create an interactive-style timeline visualization
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 10), 
                                   gridspec_kw={'height_ratios': [3, 1]})
    
    fig.suptitle('AMI Signal Timeline with Peak Detection', fontsize=18, fontweight='bold')
    
    # Top panel - Main signal with annotations
    ax1.plot(time_seconds, values, 'b-', alpha=0.4, linewidth=1, label='Raw Signal')
    
    # Add smoothed signal
    smoothed = gaussian_filter1d(values, sigma=5)
    ax1.plot(time_seconds, smoothed, 'navy', linewidth=2, alpha=0.7, label='Smoothed Signal')
    
    # Annotate each period
    for period_name, data in results.items():
        # Highlight period
        period_mask = np.isin(time_seconds, data['all_times'])
        ax1.fill_between(time_seconds[period_mask], 
                         np.min(values) - 100, 
                         np.max(values) + 100,
                         alpha=0.15, color=data['color'])
        
        # Mark peaks
        global_peak_indices = [np.where(time_seconds == t)[0][0] for t in data['peak_times']]
        ax1.scatter(data['peak_times'], data['peak_values'], 
                   color='red', s=200, zorder=5, 
                   edgecolor='darkred', linewidth=2)
        
        # Add period label
        mid_time = np.mean(data['all_times'])
        ax1.text(mid_time, np.max(values) + 50, 
                period_name.split('(')[0].strip(),
                ha='center', fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', 
                         facecolor=data['color'], alpha=0.7))
    
    ax1.set_ylabel('AMI Value (μA)', fontsize=12)
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([time_seconds[0], time_seconds[-1]])
    
    # Bottom panel - Weight timeline
    ax2.set_xlim([time_seconds[0], time_seconds[-1]])
    
    # Create weight timeline bars
    timeline_data = [
        {'name': 'Baseline', 'start': 0, 'end': 60, 'color': '#95a5a6'},
        {'name': 'No weight', 'start': 90, 'end': 150, 'color': '#FF6B6B'},
        {'name': '2.5 lbs', 'start': 190, 'end': 250, 'color': '#4ECDC4'},
        {'name': '5 lbs', 'start': 315, 'end': 375, 'color': '#45B7D1'},
        {'name': '7.5 lbs', 'start': 460, 'end': 520, 'color': '#96CEB4'},
        {'name': '10 lbs', 'start': 580, 'end': 640, 'color': '#FECA57'}
    ]
    
    for period in timeline_data:
        ax2.barh(0, period['end'] - period['start'], 
                left=period['start'], height=0.5,
                color=period['color'], edgecolor='black', 
                linewidth=2, alpha=0.8)
        
        # Add label
        mid_point = (period['start'] + period['end']) / 2
        ax2.text(mid_point, 0, period['name'], 
                ha='center', va='center', 
                fontsize=10, fontweight='bold', color='white')
    
    ax2.set_ylim([-0.5, 0.5])
    ax2.set_xlabel('Time (seconds)', fontsize=12)
    ax2.set_yticks([])
    ax2.set_title('Experimental Timeline', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig('haley_timeline_visualization.png', dpi=300, bbox_inches='tight')
    plt.show()


# Main execution
if __name__ == "__main__":
    # Load data
    time_seconds, values = load_and_process_data('Lin Lab AMI data.xlsx')
    
    # Analyze periods
    results, time_periods = analyze_periods(time_seconds, values)
    
    # Create visualizations
    print("\n" + "="*70)
    print("GENERATING VISUALIZATIONS")
    print("="*70)
    
    print("\nCreating comprehensive visualization...")
    create_comprehensive_visualization(time_seconds, values, results)
    
    print("Creating peak analysis charts...")
    create_peak_analysis_charts(results)
    
    print("Creating interactive timeline...")
    create_interactive_timeline(time_seconds, values, results)
    
    # Generate statistical summary
    print("\nGenerating statistical summary...")
    summary_df = create_statistical_summary(results)
    
    # Display summary
    print("\n" + "="*70)
    print("STATISTICAL SUMMARY TABLE")
    print("="*70)
    print(summary_df.to_string(index=False))
    
    # Save to CSV
    summary_df.to_csv('haley_analysis_summary.csv', index=False)
    print("\nSummary saved to 'haley_analysis_summary.csv'")
    
    # Calculate overall trends
    print("\n" + "="*70)
    print("OVERALL TRENDS ANALYSIS")
    print("="*70)
    
    weights = [0, 2.5, 5, 7.5, 10]
    avg_peak_elevations = []
    
    for period in results.keys():
        avg_elevation = np.mean(results[period]['peak_above_avg_percent'])
        avg_peak_elevations.append(avg_elevation)
    
    # Check for correlation
    correlation = np.corrcoef(weights, avg_peak_elevations)[0, 1]
    
    print(f"Correlation between weight and peak elevation: {correlation:.3f}")
    
    if correlation > 0.5:
        print("Strong positive correlation: Peak elevations tend to increase with weight")
    elif correlation < -0.5:
        print("Strong negative correlation: Peak elevations tend to decrease with weight")
    else:
        print("Weak correlation: No clear linear relationship between weight and peak elevation")
    
    print(f"\nAverage peak elevation across all conditions: {np.mean(avg_peak_elevations):.1f}%")
    print(f"Maximum peak elevation observed: {np.max([np.max(r['peak_above_avg_percent']) for r in results.values()]):.1f}%")
    print(f"Minimum peak elevation observed: {np.min([np.min(r['peak_above_avg_percent']) for r in results.values()]):.1f}%")
    
    print("\n" + "="*70)
    print("Analysis complete! Three visualization files have been saved:")
    print("1. haley_comprehensive_analysis.png")
    print("2. haley_peak_analysis_charts.png") 
    print("3. haley_timeline_visualization.png")
    print("="*70)