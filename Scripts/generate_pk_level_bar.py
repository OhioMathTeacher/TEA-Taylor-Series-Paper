#!/usr/bin/env python3
"""
Generate bar chart of PK level attainment across anchor cases.

Shows CUMULATIVE attainment - the percentage of cases that reached
AT LEAST each Pirie-Kieren layer.

Usage:
  python3 generate_pk_level_bar.py
  python3 generate_pk_level_bar.py --output figures/pk_levels.png
"""

import matplotlib.pyplot as plt
import numpy as np
import argparse
from pathlib import Path

# Full PK layer hierarchy (inner to outer) with level numbers
PK_LAYERS_ORDERED = [
    ('Primitive Knowing', 'L1'),
    ('Image Making', 'L2'),
    ('Image Having', 'L3'),
    ('Property Noticing', 'L4'),
    ('Formalising', 'L5'),
    ('Observing', 'L6'),
    ('Structuring', 'L7'),
    ('Inventising', 'L8'),
]

# CUMULATIVE attainment data - percentage of cases reaching AT LEAST this level
# Based on PK-WAP analysis of anchor cases
# Note: These percentages represent coded evidence in transcripts
PK_CUMULATIVE_ATTAINMENT = {
    'Primitive Knowing': 100,   # All cases show primitive knowing
    'Image Making': 100,        # All cases show image making evidence
    'Image Having': 100,        # All cases show image having evidence
    'Property Noticing': 97,    # 97% reached at least Property Noticing
    'Formalising': 93,          # 93% reached at least Formalising
    'Observing': 90,            # 90% reached at least Observing
    'Structuring': 83,          # 83% reached at least Structuring
    'Inventising': 77,          # 77% reached Inventising (highest level)
}

# Color scheme - dark blue for highest level, lighter blue for lower levels
LAYER_COLORS = {
    'Primitive Knowing': '#7FBFDB',
    'Image Making': '#7FBFDB',
    'Image Having': '#7FBFDB',
    'Property Noticing': '#7FBFDB',
    'Formalising': '#7FBFDB',
    'Observing': '#7FBFDB',
    'Structuring': '#7FBFDB',
    'Inventising': '#1A365D',  # Dark blue for highest level
}


def generate_bar_chart(output_path: Path = None, show_plot: bool = True):
    """Generate horizontal bar chart of PK level cumulative attainment."""
    
    # Prepare data - order from lowest (L1) at bottom to highest (L8) at top
    levels = [f"{name} ({code})" for name, code in PK_LAYERS_ORDERED]
    percentages = [PK_CUMULATIVE_ATTAINMENT[name] for name, code in PK_LAYERS_ORDERED]
    colors = [LAYER_COLORS[name] for name, code in PK_LAYERS_ORDERED]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create horizontal bars
    y_pos = np.arange(len(levels))
    
    bars = ax.barh(y_pos, percentages, color=colors, edgecolor='black', linewidth=1.2, height=0.7)
    
    # Add percentage labels on bars
    for i, (bar, pct) in enumerate(zip(bars, percentages)):
        width = bar.get_width()
        # Label at end of bar
        ax.text(width + 1, bar.get_y() + bar.get_height()/2,
               f'{pct}%', 
               ha='left', va='center', fontsize=11, fontweight='bold', color='black')
    
    # Formatting
    ax.set_yticks(y_pos)
    ax.set_yticklabels(levels, fontsize=11)
    ax.set_xlabel('Percentage of Cases', fontsize=12)
    ax.set_xlim(0, 105)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xticklabels(['0%', '20%', '40%', '60%', '80%', '100%'])
    ax.set_title('Highest Level of PK Attainment', fontsize=14, fontweight='bold')
    
    # Add grid
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    # Save if output path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✓ Bar chart saved to: {output_path}")
    
    # Show plot if requested
    if show_plot:
        plt.show()
    
    return fig, ax


def generate_vertical_bar_chart(output_path: Path = None, show_plot: bool = True):
    """Generate vertical bar chart of PK level cumulative attainment."""
    
    # Prepare data - order from lowest (L1) to highest (L8)
    levels = [f"{name}\n({code})" for name, code in PK_LAYERS_ORDERED]
    percentages = [PK_CUMULATIVE_ATTAINMENT[name] for name, code in PK_LAYERS_ORDERED]
    colors = [LAYER_COLORS[name] for name, code in PK_LAYERS_ORDERED]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create vertical bars
    x_pos = np.arange(len(levels))
    
    bars = ax.bar(x_pos, percentages, color=colors, edgecolor='black', linewidth=1.2, width=0.7)
    
    # Add percentage labels above bars
    for bar, pct in zip(bars, percentages):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + 1,
               f'{pct}%', 
               ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Formatting
    ax.set_xticks(x_pos)
    ax.set_xticklabels(levels, fontsize=9)
    ax.set_ylabel('Percentage of Cases', fontsize=12)
    ax.set_ylim(0, 110)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_title('Highest Level of PK Attainment', fontsize=14, fontweight='bold')
    
    # Add grid
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    # Save if output path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✓ Bar chart saved to: {output_path}")
    
    if show_plot:
        plt.show()
    
    return fig, ax


def print_statistics():
    """Print summary statistics."""
    print("\n" + "="*60)
    print("PK LEVEL CUMULATIVE ATTAINMENT")
    print("="*60)
    print(f"\n{'Layer':<25} {'Level':>6} {'Attainment':>12}")
    print("-"*45)
    
    for name, code in reversed(PK_LAYERS_ORDERED):
        pct = PK_CUMULATIVE_ATTAINMENT[name]
        print(f"{name:<25} {code:>6} {pct:>11}%")
    
    print("-"*45)
    print()
    
    # Key insights
    print("Key Findings:")
    print(f"  - {PK_CUMULATIVE_ATTAINMENT['Inventising']}% reached Inventising (highest level)")
    print(f"  - {PK_CUMULATIVE_ATTAINMENT['Formalising']}% reached at least Formalising")
    print("  - 100% of cases showed folding-back patterns")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Generate PK level attainment bar chart'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='Manuscript/figures/pk_level_bar.png',
        help='Output path for the figure (default: Manuscript/figures/pk_level_bar.png)'
    )
    parser.add_argument(
        '--vertical', '-v',
        action='store_true',
        help='Generate vertical bar chart instead of horizontal'
    )
    parser.add_argument(
        '--no-show',
        action='store_true',
        help='Do not display the plot (just save)'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Print statistics only (no plot)'
    )
    
    args = parser.parse_args()
    
    # Print statistics
    print_statistics()
    
    if args.stats:
        return
    
    # Generate chart
    output_path = Path(args.output)
    show = not args.no_show
    
    if args.vertical:
        generate_vertical_bar_chart(output_path, show_plot=show)
    else:
        generate_bar_chart(output_path, show_plot=show)


if __name__ == "__main__":
    main()
