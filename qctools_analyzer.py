#!/usr/bin/env python3
"""
QCTools XML Report Analyzer
Extracts and calculates average values for all signal statistics from QCTools XML reports.
"""

import xml.etree.ElementTree as ET
import sys
from collections import defaultdict
from pathlib import Path


def parse_single_qctools_xml(xml_file_path, metrics_data):
    """
    Parse a single QCTools XML file and add its data to the metrics collection.
    
    Args:
        xml_file_path (str): Path to the QCTools XML file
        metrics_data (defaultdict): Existing metrics data to append to
        
    Returns:
        tuple: (frame_count, success_flag)
    """
    try:
        # Parse the XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        # Handle namespace - QCTools uses ffprobe namespace
        namespace = {'ffprobe': 'http://www.ffmpeg.org/schema/ffprobe'}
        
        frame_count = 0
        
        # Find all frame elements
        frames = root.findall('.//frame[@media_type="video"]', namespace)
        if not frames:
            # Try without namespace if not found
            frames = root.findall('.//frame[@media_type="video"]')
        
        print(f"  Processing {len(frames)} frames from {Path(xml_file_path).name}")
        
        # Extract data from each frame
        for frame in frames:
            frame_count += 1
            
            # Find all tag elements within this frame
            tags = frame.findall('tag')
            
            for tag in tags:
                key = tag.get('key')
                value_str = tag.get('value')
                
                # Skip if key or value is missing
                if not key or not value_str:
                    continue
                
                try:
                    # Convert value to float
                    value = float(value_str)
                    metrics_data[key].append(value)
                except ValueError:
                    # Skip non-numeric values (only show warning for first file)
                    continue
        
        return frame_count, True
        
    except ET.ParseError as e:
        print(f"  Error parsing XML file {xml_file_path}: {e}")
        return 0, False
    except FileNotFoundError:
        print(f"  File not found: {xml_file_path}")
        return 0, False
    except Exception as e:
        print(f"  Unexpected error processing {xml_file_path}: {e}")
        return 0, False


def parse_multiple_qctools_xml(xml_file_paths):
    """
    Parse multiple QCTools XML files and calculate combined average values.
    
    Args:
        xml_file_paths (list): List of paths to QCTools XML files
        
    Returns:
        tuple: (averages_dict, total_frames, successful_files)
    """
    # Dictionary to store all values for each metric across all files
    metrics_data = defaultdict(list)
    total_frames = 0
    successful_files = 0
    
    print(f"Processing {len(xml_file_paths)} XML files...")
    print("-" * 60)
    
    for xml_file in xml_file_paths:
        if not Path(xml_file).exists():
            print(f"  Skipping missing file: {xml_file}")
            continue
            
        frame_count, success = parse_single_qctools_xml(xml_file, metrics_data)
        
        if success:
            total_frames += frame_count
            successful_files += 1
        else:
            print(f"  Failed to process: {xml_file}")
    
    print("-" * 60)
    
    # Calculate averages across all files
    averages = {}
    for metric, values in metrics_data.items():
        if values:  # Only calculate if we have values
            averages[metric] = sum(values) / len(values)
    
    print(f"Successfully processed {successful_files}/{len(xml_file_paths)} files")
    print(f"Total frames analyzed: {total_frames}")
    print(f"Found {len(averages)} unique metrics")
    
    return averages, total_frames, successful_files


def print_results(averages, total_frames, successful_files, total_files, output_file=None):
    """
    Print the results in a formatted way, optionally save to file.
    
    Args:
        averages (dict): Dictionary of metric averages
        total_frames (int): Total number of frames processed
        successful_files (int): Number of successfully processed files
        total_files (int): Total number of input files
        output_file (str, optional): Path to output CSV file
    """
    if not averages:
        print("No data to display")
        return
    
    # Group metrics by category for better organization
    categories = {
        'Y (Luma)': [],
        'U (Chroma)': [],
        'V (Chroma)': [],
        'Saturation': [],
        'Hue': [],
        'Other': [],
        'PSNR': [],
        'Bit Depth': []
    }
    
    # Categorize metrics
    for metric, value in averages.items():
        if 'YMIN' in metric or 'YMAX' in metric or 'YLOW' in metric or 'YHIGH' in metric or 'YAVG' in metric or 'YDIF' in metric:
            categories['Y (Luma)'].append((metric, value))
        elif 'UMIN' in metric or 'UMAX' in metric or 'ULOW' in metric or 'UHIGH' in metric or 'UAVG' in metric or 'UDIF' in metric:
            categories['U (Chroma)'].append((metric, value))
        elif 'VMIN' in metric or 'VMAX' in metric or 'VLOW' in metric or 'VHIGH' in metric or 'VAVG' in metric or 'VDIF' in metric:
            categories['V (Chroma)'].append((metric, value))
        elif 'SAT' in metric:
            categories['Saturation'].append((metric, value))
        elif 'HUE' in metric:
            categories['Hue'].append((metric, value))
        elif 'psnr' in metric.lower() or 'mse' in metric.lower():
            categories['PSNR'].append((metric, value))
        elif 'BITDEPTH' in metric:
            categories['Bit Depth'].append((metric, value))
        else:
            categories['Other'].append((metric, value))
    
    # Print results by category
    print("\n" + "="*80)
    print("QCTOOLS ANALYSIS RESULTS - COMBINED AVERAGE VALUES")
    print("="*80)
    print(f"Files processed: {successful_files}/{total_files}")
    print(f"Total frames analyzed: {total_frames:,}")
    print(f"Metrics found: {len(averages)}")
    
    for category, metrics in categories.items():
        if metrics:
            print(f"\n{category}:")
            print("-" * len(category))
            for metric, value in sorted(metrics):
                # Clean up metric name for display
                display_name = metric.replace('lavfi.signalstats.', '').replace('lavfi.psnr.', 'PSNR_')
                print(f"  {display_name:<25}: {value:>10.6f}")
    
    # Save to CSV if requested
    if output_file:
        try:
            with open(output_file, 'w') as f:
                # Write header with metadata
                f.write("# QCTools Combined Analysis Results\n")
                f.write(f"# Files processed: {successful_files}/{total_files}\n")
                f.write(f"# Total frames: {total_frames}\n")
                f.write("# \n")
                f.write("Metric,Average_Value\n")
                for metric, value in sorted(averages.items()):
                    f.write(f"{metric},{value:.6f}\n")
            print(f"\nResults saved to: {output_file}")
        except Exception as e:
            print(f"Error saving to file: {e}")


def main():
    """Main function to handle command line arguments and run analysis."""
    if len(sys.argv) < 2:
        print("Usage: python qctools_analyzer.py <xml_file1> [xml_file2] [...] [--output output.csv]")
        print("Examples:")
        print("  python qctools_analyzer.py video1.xml")
        print("  python qctools_analyzer.py video1.xml video2.xml video3.xml")
        print("  python qctools_analyzer.py *.xml --output combined_results.csv")
        print("  python qctools_analyzer.py video1.xml video2.xml --output results.csv")
        return
    
    # Parse command line arguments
    args = sys.argv[1:]
    xml_files = []
    output_file = None
    
    # Check for --output flag
    if '--output' in args:
        output_index = args.index('--output')
        if output_index + 1 < len(args):
            output_file = args[output_index + 1]
            # Remove --output and filename from args
            args = args[:output_index] + args[output_index + 2:]
        else:
            print("Error: --output flag requires a filename")
            return
    
    # Remaining args should be XML files
    xml_files = args
    
    if not xml_files:
        print("Error: No XML files specified")
        return
    
    # Check if files exist
    missing_files = [f for f in xml_files if not Path(f).exists()]
    if missing_files:
        print("Warning: The following files were not found:")
        for f in missing_files:
            print(f"  {f}")
        print()
    
    if len(xml_files) == 1:
        print(f"Analyzing single QCTools XML file: {xml_files[0]}")
    else:
        print(f"Analyzing {len(xml_files)} QCTools XML files for combined averages")
    
    # Parse and analyze
    averages, total_frames, successful_files = parse_multiple_qctools_xml(xml_files)
    
    # Display results
    print_results(averages, total_frames, successful_files, len(xml_files), output_file)


if __name__ == "__main__":
    main()