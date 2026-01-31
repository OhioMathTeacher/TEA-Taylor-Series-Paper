#!/usr/bin/env python3
"""
Generate box plot of student talk percentages by section.
Creates fig3.png for the manuscript - uses data from Appendix C.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import re

# Read data directly from appendix.tex
data = []
with open('../Manuscript (LaTeX)/appendix.tex', 'r') as f:
    for line in f:
        # Match lines like: P01-G8-S4 & 3558 & 203 & 3761 & 94.6 & 5.4 \\
        match = re.match(r'(P\d+-G\w+-S\d+)\s+&\s+[\d.]+\s+&\s+[\d.]+\s+&\s+[\d.]+\s+&\s+[\d.]+\s+&\s+([\d.]+)', line)
        if match:
            participant_id = match.group(1)
            pct_student = float(match.group(2))
            data.append({'id': participant_id, 'pct_student': pct_student})

df = pd.DataFrame(data)

# Extract section from participant ID
def extract_section(participant_id):
    parts = participant_id.split('-')
    if len(parts) >= 3:
        section_part = parts[2]  # e.g., 'S4', 'S5', 'S6'
        return section_part.replace('S', '')  # Returns '3', '4', '5', '6'
    return None

df['section'] = df['id'].apply(extract_section)
df = df[df['section'].notna()]

# Define section order
section_order = ['3', '4', '5', '6']
df = df[df['section'].isin(section_order)]

# Prepare data for box plot and bar chart
data_by_section = [df[df['section'] == section]['pct_student'].values 
                   for section in section_order]

# Create single figure - reduced height for compression
fig, ax = plt.subplots(1, 1, figsize=(7, 2.5))

# Define colors - orange for sections 3 and 5, blue for 4 and 6
colors = ['#F5A642', '#1F77B4', '#F5A642', '#1F77B4']

# Section 3 has only n=2, so use bar chart instead of box plot
section3_data = data_by_section[0]
section3_mean = np.mean(section3_data)
section3_std = np.std(section3_data)

# Plot bar for Section 3
ax.bar(1, section3_mean, width=0.6, color=colors[0], edgecolor='black', linewidth=1.5, alpha=0.8)
ax.errorbar(1, section3_mean, yerr=section3_std, fmt='none', ecolor='black', 
            capsize=5, capthick=1.5, linewidth=1.5)

# Create box plots for Sections 4, 5, 6 (which have adequate sample sizes)
box_positions = [2, 3, 4]
box_data = data_by_section[1:]  # Skip Section 3
box_colors = colors[1:]  # Skip Section 3 color

bp = ax.boxplot(box_data, 
                positions=box_positions,
                patch_artist=True,
                widths=0.6,
                medianprops=dict(color='#FF6B35', linewidth=2.5),
                whiskerprops=dict(color='black', linewidth=1.5),
                capprops=dict(color='black', linewidth=1.5),
                boxprops=dict(linewidth=1.5),
                flierprops=dict(marker='o', markerfacecolor='red', markersize=6, linestyle='none'))

# Color the boxes
for patch, color in zip(bp['boxes'], box_colors):
    patch.set_facecolor(color)
    patch.set_edgecolor('black')

# Styling
ax.set_ylabel('% Student Talk', fontsize=11)
ax.set_xlabel('Section', fontsize=11)
ax.set_ylim(0, 85)
ax.set_yticks([0, 20, 40, 60, 80])
ax.set_xticks([1, 2, 3, 4])
ax.set_xticklabels(section_order)
ax.grid(True, axis='y', alpha=0.3, linewidth=0.8)
ax.set_axisbelow(True)

# Adjust layout
plt.tight_layout()

# Save the figure
output_path = '../Manuscript (LaTeX)/figures/fig3.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"Box plot saved to {output_path}")

# Print statistics
print(f"\nTotal participants: {len(df)}")
print("\nSection Statistics:")
for section in section_order:
    data = df[df['section'] == section]['pct_student'].values
    if len(data) > 0:
        print(f"Section {section}: n={len(data)}, median={np.median(data):.1f}%, "
              f"mean={np.mean(data):.1f}%, range=[{np.min(data):.1f}%, {np.max(data):.1f}%]")
