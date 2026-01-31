#!/usr/bin/env python3
"""
Web-based transcript reviewer for identifying noteworthy cases.

Creates a simple Flask app to display original student submissions (PDF/DOCX)
and collect annotations about what makes them noteworthy.

Usage:
  python3 transcript_reviewer.py
  Then open http://localhost:5000 in your browser
"""

import csv
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
import webbrowser
import threading
import time

app = Flask(__name__)

# Store selections
SELECTIONS_FILE = Path('noteworthy_selections.json')
selections = {}

if SELECTIONS_FILE.exists():
    with open(SELECTIONS_FILE, 'r') as f:
        selections = json.load(f)


def load_middle_candidates():
    """Load middle-range candidates from Phase I results."""
    with open('../simple_mode_final_127/summary.csv', 'r') as f:
        reader = csv.DictReader(f)
        data = [row for row in reader]
    
    # Filter valid cases
    valid = [row for row in data 
             if 10.0 < float(row['pct_student']) < 100.0]
    
    # Sort and exclude top/bottom 10
    sorted_valid = sorted(valid, key=lambda x: float(x['pct_student']), reverse=True)
    middle = sorted_valid[10:-10]
    
    # Sort by word count for review
    middle_sorted = sorted(middle, key=lambda x: int(x['total']), reverse=True)
    
    # Add file paths - search recursively in Original Data
    orig_data_path = Path('../Original Data')
    
    for row in middle_sorted:
        transcript_id = row['filename'].replace('.txt', '').replace('.docx', '')
        row['transcript_id'] = transcript_id
        
        # Extract group/section from transcript_id (e.g., P70-G13-S4 -> G13, S4)
        parts = transcript_id.split('-')
        if len(parts) >= 3:
            group = parts[1]  # e.g., G13
            section = parts[2]  # e.g., S4
            
            # Search for files matching pattern "Group *, Section *"
            pattern = f"*Group*{group.replace('G', '')}*Section*{section.replace('S', '')}*.pdf"
            candidates = list(orig_data_path.rglob(pattern))
            
            # Also try without section (GX or SX cases)
            if not candidates:
                pattern = f"*Group*{group.replace('G', '')}*.pdf"
                candidates = list(orig_data_path.rglob(pattern))
            
            # Try .docx too
            if not candidates:
                pattern = f"*Group*{group.replace('G', '')}*Section*{section.replace('S', '')}*.docx"
                candidates = list(orig_data_path.rglob(pattern))
        else:
            candidates = []
        
        if candidates:
            # Take first match
            row['file_path'] = str(candidates[0])
            row['file_type'] = candidates[0].suffix
        else:
            row['file_path'] = None
            row['file_type'] = None
    
    return middle_sorted


candidates = load_middle_candidates()


@app.route('/')
def index():
    """Main review interface."""
    return render_template('reviewer.html', 
                         total=len(candidates),
                         selections=selections)


@app.route('/api/candidate/<int:index>')
def get_candidate(index):
    """Get candidate info by index."""
    if 0 <= index < len(candidates):
        candidate = candidates[index].copy()
        candidate['index'] = index
        candidate['selected'] = candidate['transcript_id'] in selections
        candidate['tags'] = selections.get(candidate['transcript_id'], {}).get('tags', [])
        candidate['notes'] = selections.get(candidate['transcript_id'], {}).get('notes', '')
        return jsonify(candidate)
    return jsonify({'error': 'Invalid index'}), 404


@app.route('/api/file/<int:index>')
def get_file(index):
    """Serve the original file."""
    if 0 <= index < len(candidates):
        file_path = candidates[index].get('file_path')
        if file_path and Path(file_path).exists():
            return send_file(file_path)
    return "File not found", 404


@app.route('/api/select', methods=['POST'])
def select_candidate():
    """Mark a candidate as noteworthy."""
    data = request.json
    transcript_id = data.get('transcript_id')
    tags = data.get('tags', [])
    notes = data.get('notes', '')
    
    selections[transcript_id] = {
        'tags': tags,
        'notes': notes,
        'pct_student': data.get('pct_student'),
        'total_words': data.get('total_words')
    }
    
    # Save to file
    with open(SELECTIONS_FILE, 'w') as f:
        json.dump(selections, f, indent=2)
    
    return jsonify({'status': 'saved', 'count': len(selections)})


@app.route('/api/unselect', methods=['POST'])
def unselect_candidate():
    """Remove a candidate from noteworthy list."""
    data = request.json
    transcript_id = data.get('transcript_id')
    
    if transcript_id in selections:
        del selections[transcript_id]
        
        # Save to file
        with open(SELECTIONS_FILE, 'w') as f:
            json.dump(selections, f, indent=2)
    
    return jsonify({'status': 'removed', 'count': len(selections)})


@app.route('/api/export')
def export_selections():
    """Export selections to CSV."""
    output_path = Path('noteworthy_selections.csv')
    
    with open(output_path, 'w', newline='') as f:
        fieldnames = ['transcript_id', 'pct_student', 'total_words', 'tags', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for transcript_id, data in selections.items():
            writer.writerow({
                'transcript_id': transcript_id,
                'pct_student': data.get('pct_student', ''),
                'total_words': data.get('total_words', ''),
                'tags': ', '.join(data.get('tags', [])),
                'notes': data.get('notes', '')
            })
    
    return send_file(output_path, as_attachment=True)


@app.route('/api/summary')
def get_summary():
    """Get summary of selections."""
    return jsonify({
        'total_candidates': len(candidates),
        'selected_count': len(selections),
        'selections': selections
    })


def open_browser():
    """Open browser after short delay."""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')


if __name__ == '__main__':
    print("="*70)
    print("TRANSCRIPT REVIEWER - Starting...")
    print("="*70)
    print(f"\nLoaded {len(candidates)} middle-range candidates")
    print(f"Current selections: {len(selections)}")
    print("\nOpening browser at http://localhost:5000")
    print("Press Ctrl+C to stop the server\n")
    
    # Open browser in background
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run Flask app
    app.run(debug=False, port=5000)
