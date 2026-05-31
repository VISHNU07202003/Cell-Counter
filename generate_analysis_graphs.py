import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)

# Read the comparison CSV
df = pd.read_csv('outputs/model_vs_gt_counts.csv')

# Extract model and GT counts
model_counts = df['model_count'].values
gt_counts = df['gt_count'].values

# Calculate metrics
mae = mean_absolute_error(gt_counts, model_counts)
rmse = np.sqrt(mean_squared_error(gt_counts, model_counts))
mape = np.mean(np.abs((gt_counts - model_counts) / gt_counts)) * 100
r2 = r2_score(gt_counts, model_counts)

# Calculate additional metrics
errors = model_counts - gt_counts
absolute_errors = np.abs(errors)
mean_error = np.mean(errors)
std_error = np.std(errors)

# Calculate precision, recall, and F1 (adapted for regression)
# Using threshold-based approach: predictions within 10% of GT are considered "correct"
threshold = 0.1
correct_predictions = np.sum(absolute_errors <= (gt_counts * threshold))
total_predictions = len(gt_counts)
adapted_precision = (correct_predictions / total_predictions) * 100

# Absolute Percentage Error for each sample
ape = (absolute_errors / gt_counts) * 100

print("="*60)
print("MODEL PERFORMANCE ANALYSIS")
print("="*60)
print(f"\nBasic Metrics:")
print(f"  Mean Absolute Error (MAE): {mae:.2f} cells")
print(f"  Root Mean Square Error (RMSE): {rmse:.2f} cells")
print(f"  Mean Absolute Percentage Error (MAPE): {mape:.2f}%")
print(f"  R² Score: {r2:.4f}")
print(f"\nError Statistics:")
print(f"  Mean Error: {mean_error:.2f} cells")
print(f"  Std Dev Error: {std_error:.2f} cells")
print(f"  Min Error: {np.min(errors):.2f} cells")
print(f"  Max Error: {np.max(errors):.2f} cells")
print(f"\nAccuracy Metrics:")
print(f"  Predictions within ±10% of GT: {adapted_precision:.2f}%")
print(f"  Mean Absolute Percentage Error per sample: {np.mean(ape):.2f}%")
print(f"  Median Absolute Percentage Error: {np.median(ape):.2f}%")

# Create comprehensive visualization
fig = plt.figure(figsize=(16, 12))

# 1. Actual vs Predicted scatter plot
ax1 = plt.subplot(2, 3, 1)
ax1.scatter(gt_counts, model_counts, alpha=0.6, s=100, color='steelblue')
# Add perfect prediction line
min_val = min(gt_counts.min(), model_counts.min())
max_val = max(gt_counts.max(), model_counts.max())
ax1.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
ax1.set_xlabel('Ground Truth Count', fontsize=11, fontweight='bold')
ax1.set_ylabel('Model Predicted Count', fontsize=11, fontweight='bold')
ax1.set_title('Actual vs Predicted Cell Counts', fontsize=12, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. Error Distribution (Histogram)
ax2 = plt.subplot(2, 3, 2)
ax2.hist(errors, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
ax2.axvline(mean_error, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_error:.2f}')
ax2.axvline(0, color='green', linestyle='--', linewidth=2, label='Zero Error')
ax2.set_xlabel('Prediction Error (Model - GT)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Frequency', fontsize=11, fontweight='bold')
ax2.set_title('Error Distribution', fontsize=12, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3, axis='y')

# 3. Residual Plot
ax3 = plt.subplot(2, 3, 3)
ax3.scatter(gt_counts, errors, alpha=0.6, s=100, color='coral')
ax3.axhline(0, color='red', linestyle='--', linewidth=2)
ax3.set_xlabel('Ground Truth Count', fontsize=11, fontweight='bold')
ax3.set_ylabel('Residuals (Error)', fontsize=11, fontweight='bold')
ax3.set_title('Residual Plot', fontsize=12, fontweight='bold')
ax3.grid(True, alpha=0.3)

# 4. Absolute Percentage Error
ax4 = plt.subplot(2, 3, 4)
ax4.hist(ape, bins=20, color='lightgreen', edgecolor='black', alpha=0.7)
ax4.axvline(np.mean(ape), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(ape):.2f}%')
ax4.set_xlabel('Absolute Percentage Error (%)', fontsize=11, fontweight='bold')
ax4.set_ylabel('Frequency', fontsize=11, fontweight='bold')
ax4.set_title('Absolute Percentage Error Distribution', fontsize=12, fontweight='bold')
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')

# 5. Box Plot of Errors
ax5 = plt.subplot(2, 3, 5)
box_data = [errors, ape]
bp = ax5.boxplot(box_data, labels=['Error (cells)', 'APE (%)'], patch_artist=True)
for patch, color in zip(bp['boxes'], ['steelblue', 'lightgreen']):
    patch.set_facecolor(color)
ax5.set_ylabel('Value', fontsize=11, fontweight='bold')
ax5.set_title('Error Statistics - Box Plot', fontsize=12, fontweight='bold')
ax5.grid(True, alpha=0.3, axis='y')

# 6. Metrics Summary (Text)
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')
metrics_text = f"""
MODEL PERFORMANCE METRICS

Basic Statistics:
  • MAE: {mae:.2f} cells
  • RMSE: {rmse:.2f} cells
  • MAPE: {mape:.2f}%
  • R² Score: {r2:.4f}

Error Characteristics:
  • Mean Error: {mean_error:.2f} cells
  • Std Dev: {std_error:.2f} cells
  • Min Error: {np.min(errors):.0f} cells
  • Max Error: {np.max(errors):.0f} cells

Accuracy:
  • Within ±10% GT: {adapted_precision:.2f}%
  • Median APE: {np.median(ape):.2f}%
  • Mean APE: {np.mean(ape):.2f}%

Sample Size: {len(gt_counts)} images
"""
ax6.text(0.1, 0.5, metrics_text, fontsize=10, verticalalignment='center',
         fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('outputs/model_analysis_complete.png', dpi=300, bbox_inches='tight')
print("\n[OK] Complete analysis graph saved to: outputs/model_analysis_complete.png")

# Create additional detailed graphs
fig2, axes = plt.subplots(2, 2, figsize=(14, 10))

# Comparison of counts
ax = axes[0, 0]
x_pos = np.arange(len(df))
width = 0.35
ax.bar(x_pos - width/2, gt_counts, width, label='Ground Truth', alpha=0.8, color='steelblue')
ax.bar(x_pos + width/2, model_counts, width, label='Model Prediction', alpha=0.8, color='coral')
ax.set_ylabel('Cell Count', fontsize=11, fontweight='bold')
ax.set_title('GT vs Predicted Counts (All Images)', fontsize=12, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')
ax.set_xticks([])

# Error by image category
ax = axes[0, 1]
csm_errors = errors[df['image'].str.contains('csm')]
project_errors = errors[df['image'].str.contains('Project')]
simple_errors = errors[df['image'].str.contains('Simple')]

categories = ['CSM Images', 'Project Images', 'Simple Images']
mean_errors_by_cat = [np.mean(csm_errors), np.mean(project_errors), np.mean(simple_errors)]
colors_cat = ['steelblue', 'coral', 'lightgreen']

bars = ax.bar(categories, mean_errors_by_cat, color=colors_cat, alpha=0.7, edgecolor='black')
ax.axhline(0, color='red', linestyle='--', linewidth=2)
ax.set_ylabel('Mean Error (cells)', fontsize=11, fontweight='bold')
ax.set_title('Mean Error by Image Category', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bar, val in zip(bars, mean_errors_by_cat):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{val:.1f}', ha='center', va='bottom' if val > 0 else 'top', fontweight='bold')

# Absolute error distribution by category
ax = axes[1, 0]
csm_abs_errors = absolute_errors[df['image'].str.contains('csm')]
project_abs_errors = absolute_errors[df['image'].str.contains('Project')]
simple_abs_errors = absolute_errors[df['image'].str.contains('Simple')]

mean_abs_errors_by_cat = [np.mean(csm_abs_errors), np.mean(project_abs_errors), np.mean(simple_abs_errors)]
bars = ax.bar(categories, mean_abs_errors_by_cat, color=colors_cat, alpha=0.7, edgecolor='black')
ax.set_ylabel('Mean Absolute Error (cells)', fontsize=11, fontweight='bold')
ax.set_title('Mean Absolute Error by Image Category', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

for bar, val in zip(bars, mean_abs_errors_by_cat):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{val:.1f}', ha='center', va='bottom', fontweight='bold')

# Percentage error by category
ax = axes[1, 1]
csm_ape = ape[df['image'].str.contains('csm')]
project_ape = ape[df['image'].str.contains('Project')]
simple_ape = ape[df['image'].str.contains('Simple')]

mean_ape_by_cat = [np.mean(csm_ape), np.mean(project_ape), np.mean(simple_ape)]
bars = ax.bar(categories, mean_ape_by_cat, color=colors_cat, alpha=0.7, edgecolor='black')
ax.set_ylabel('Mean Absolute Percentage Error (%)', fontsize=11, fontweight='bold')
ax.set_title('Mean APE by Image Category', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

for bar, val in zip(bars, mean_ape_by_cat):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig('outputs/model_analysis_by_category.png', dpi=300, bbox_inches='tight')
print("[OK] Category analysis graph saved to: outputs/model_analysis_by_category.png")

# Save metrics to CSV
metrics_df = pd.DataFrame({
    'Metric': ['MAE', 'RMSE', 'MAPE (%)', 'R² Score', 'Mean Error', 'Std Dev Error',
               'Min Error', 'Max Error', 'Mean APE (%)', 'Median APE (%)', 
               'Predictions within ±10% of GT (%)'],
    'Value': [mae, rmse, mape, r2, mean_error, std_error, 
              np.min(errors), np.max(errors), np.mean(ape), np.median(ape), adapted_precision]
})

metrics_df.to_csv('outputs/model_metrics_summary.csv', index=False)
print("[OK] Metrics summary saved to: outputs/model_metrics_summary.csv")

print("\n" + "="*60)
print("Analysis complete! Generated files:")
print("  1. model_analysis_complete.png - Comprehensive 6-panel analysis")
print("  2. model_analysis_by_category.png - Category-based performance")
print("  3. model_metrics_summary.csv - All metrics in CSV format")
print("="*60)
