#!/usr/bin/env python3
"""
Mobile Sales SQL Log Analyzer
Analyze and filter SQL execution logs
"""

import sys
import re
from datetime import datetime
import argparse

def analyze_sql_log(log_file_path, filter_operation=None, filter_table=None, show_errors_only=False, show_slow_queries=False, min_results=None):
    """Analyze SQL log file with various filters"""
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Log file {log_file_path} not found")
        return
    
    # Split log entries (each entry can span multiple lines)
    log_entries = []
    current_entry = ""
    
    for line in content.split('\n'):
        if line.strip() == "":
            continue
            
        # Check if this line starts a new log entry
        if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line):
            if current_entry:
                log_entries.append(current_entry)
            current_entry = line
        else:
            # Continue previous entry
            current_entry += "\n" + line
    
    # Add last entry
    if current_entry:
        log_entries.append(current_entry)
    
    print(f"Total log entries found: {len(log_entries)}")
    print("=" * 80)
    
    filtered_entries = []
    error_count = 0
    
    for entry in log_entries:
        # Extract information from entry
        is_error = "ERROR" in entry
        if is_error:
            error_count += 1
        
        # Apply filters
        if show_errors_only and not is_error:
            continue
            
        if filter_operation and f"[{filter_operation.upper()}]" not in entry:
            continue
            
        if filter_table and filter_table.upper() not in entry.upper():
            continue
            
        if min_results:
            result_match = re.search(r'--> (\d+) rows', entry)
            if result_match:
                result_count = int(result_match.group(1))
                if result_count < min_results:
                    continue
            elif not is_error:  # Skip if no result count and not error
                continue
        
        filtered_entries.append(entry)
    
    print(f"Filtered entries: {len(filtered_entries)}")
    if error_count > 0:
        print(f"Errors found: {error_count}")
    print("=" * 80)
    
    for i, entry in enumerate(filtered_entries, 1):
        print(f"\n--- Entry {i} ---")
        print(entry)
        
        if i % 10 == 0 and i < len(filtered_entries):
            input("\nPress Enter to continue (or Ctrl+C to stop)...")

def show_statistics(log_file_path):
    """Show statistics about SQL operations"""
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Log file {log_file_path} not found")
        return
    
    # Count operations
    operations = {}
    errors = 0
    total_results = 0
    result_queries = 0
    
    for line in content.split('\n'):
        if '[SELECT]' in line:
            operations['SELECT'] = operations.get('SELECT', 0) + 1
        elif '[INSERT]' in line:
            operations['INSERT'] = operations.get('INSERT', 0) + 1
        elif '[UPDATE]' in line:
            operations['UPDATE'] = operations.get('UPDATE', 0) + 1
        elif '[DELETE]' in line:
            operations['DELETE'] = operations.get('DELETE', 0) + 1
        elif 'ERROR' in line:
            errors += 1
        
        # Count results
        result_match = re.search(r'--> (\d+) rows', line)
        if result_match:
            total_results += int(result_match.group(1))
            result_queries += 1
    
    print("SQL LOG STATISTICS")
    print("=" * 40)
    print(f"Total operations: {sum(operations.values())}")
    print(f"Errors: {errors}")
    print(f"Average results per query: {total_results/result_queries:.1f}" if result_queries > 0 else "Average results per query: N/A")
    print("\nOperations breakdown:")
    for op, count in sorted(operations.items()):
        print(f"  {op}: {count}")

def main():
    parser = argparse.ArgumentParser(description='Analyze Mobile Sales SQL logs')
    parser.add_argument('log_file', nargs='?', default='/var/log/apache2/mobile_sales_sql.log', 
                       help='Path to SQL log file')
    parser.add_argument('--operation', '-o', help='Filter by operation (SELECT, INSERT, UPDATE, DELETE)')
    parser.add_argument('--table', '-t', help='Filter by table name')
    parser.add_argument('--errors', '-e', action='store_true', help='Show only errors')
    parser.add_argument('--min-results', '-m', type=int, help='Show only queries with minimum result count')
    parser.add_argument('--stats', '-s', action='store_true', help='Show statistics only')
    parser.add_argument('--live', '-l', action='store_true', help='Live monitoring (tail -f)')
    
    args = parser.parse_args()
    
    if args.live:
        print(f"Live monitoring {args.log_file} (Ctrl+C to stop)...")
        import subprocess
        try:
            subprocess.run(['tail', '-f', args.log_file])
        except KeyboardInterrupt:
            print("\nStopped monitoring")
        return
    
    if args.stats:
        show_statistics(args.log_file)
    else:
        analyze_sql_log(
            args.log_file, 
            args.operation, 
            args.table, 
            args.errors,
            False,  # show_slow_queries not implemented yet
            args.min_results
        )

if __name__ == '__main__':
    main()