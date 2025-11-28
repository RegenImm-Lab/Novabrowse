from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
import os
import time
import threading
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil
from datetime import datetime

# Add GTK/Cairo to PATH for Windows
import sys
if sys.platform == "win32":
    # Common GTK installation paths on Windows
    gtk_paths = [
        r"C:\Program Files\GTK3-Runtime Win64\bin",
        r"C:\Program Files (x86)\GTK3-Runtime Win32\bin",
        r"C:\msys64\mingw64\bin",
        r"C:\gtk\bin",
    ]

    for gtk_path in gtk_paths:
        if os.path.exists(gtk_path):
            print(f"Found GTK at: {gtk_path}")
            os.environ['PATH'] = gtk_path + ';' + os.environ['PATH']
            # Also set for DLL loading
            if hasattr(os, 'add_dll_directory'):
                os.add_dll_directory(gtk_path)
            break

# Image comparison libraries
try:
    import cairosvg
    from PIL import Image, ImageChops
    import numpy as np
except ImportError:
    print("Installing required packages for image comparison...")
    import subprocess
    subprocess.check_call(["pip", "install", "cairosvg", "pillow", "numpy"])
    import cairosvg
    from PIL import Image, ImageChops
    import numpy as np

# Configuration
WAIT_TIME = 0.2  # Wait time in seconds after page load and each click
DOWNLOAD_WAIT = 1  # Wait time for download to complete

# Directory for test downloads
TEST_DOWNLOAD_DIR = os.path.abspath("test_downloads")
os.makedirs(TEST_DOWNLOAD_DIR, exist_ok=True)

# Directory for image comparisons
TEST_IMAGE_COMPARE_DIR = os.path.abspath("test_image_compare")
os.makedirs(TEST_IMAGE_COMPARE_DIR, exist_ok=True)

def svg_to_png_cairo(svg_path, png_path):
    """
    Convert SVG file to PNG using Cairo (via cairosvg).

    Args:
        svg_path: Path to the SVG file
        png_path: Path where PNG should be saved

    Returns:
        True if conversion successful, False otherwise
    """
    try:
        print(f"Converting {os.path.basename(svg_path)} to PNG using Cairo...")

        # Read the SVG file
        with open(svg_path, 'rb') as svg_file:
            svg_data = svg_file.read()

        # Convert SVG to PNG using cairosvg
        png_data = cairosvg.svg2png(
            bytestring=svg_data,
            write_to=png_path
        )

        # Verify the PNG was created
        if os.path.exists(png_path):
            file_size = os.path.getsize(png_path)
            print(f"Successfully converted to PNG ({file_size:,} bytes)")
            return True
        else:
            print(f"Failed to create PNG file")
            return False

    except Exception as e:
        print(f"Cairo conversion error: {str(e)}")
        return False

def compare_images(image1_path, image2_path, diff_path):
    """
    Compare two PNG images and calculate similarity.

    Args:
        image1_path: Path to first image (NEW)
        image2_path: Path to second image (ORIGINAL)
        diff_path: Path to save difference image

    Returns:
        dict with comparison results (match=True only if 100% identical)
    """
    result = {
        'match': False,
        'similarity': 0.0,
        'differences': [],
        'image1_exists': os.path.exists(image1_path),
        'image2_exists': os.path.exists(image2_path),
        'new_dimensions': None,
        'original_dimensions': None,
        'max_pixel_diff': 0,
        'diff_image_saved': False
    }

    if not result['image1_exists']:
        result['differences'].append(f"Image 1 not found: {image1_path}")
        return result

    if not result['image2_exists']:
        result['differences'].append(f"Image 2 not found: {image2_path}")
        return result

    try:
        # Open both images
        img1 = Image.open(image1_path).convert('RGBA')
        img2 = Image.open(image2_path).convert('RGBA')

        # Store dimensions
        result['new_dimensions'] = img1.size
        result['original_dimensions'] = img2.size

        # Report dimensions
        print(f"  NEW PNG:      {img1.size[0]}x{img1.size[1]} pixels")
        print(f"  ORIGINAL PNG: {img2.size[0]}x{img2.size[1]} pixels")

        # Check if dimensions match
        if img1.size != img2.size:
            result['differences'].append(
                f"Image dimensions differ: NEW {img1.size} vs ORIGINAL {img2.size}"
            )
            # Resize the second image to match the first for comparison
            img2 = img2.resize(img1.size, Image.LANCZOS)
            print(f"  Resized ORIGINAL image for comparison")

        # Convert to numpy arrays
        arr1 = np.array(img1)
        arr2 = np.array(img2)

        # Method 1: Calculate pixel-wise difference
        pixel_diff = np.sum(arr1 != arr2)
        total_pixels = arr1.size
        pixel_similarity = 1.0 - (pixel_diff / total_pixels)

        # Method 2: Calculate mean squared error
        mse = np.mean((arr1.astype(float) - arr2.astype(float)) ** 2)
        # Normalize MSE to 0-1 scale (inverse for similarity)
        mse_similarity = 1.0 - min(mse / (255.0 ** 2), 1.0)

        # Method 3: Use PIL's difference
        diff_img = ImageChops.difference(img1, img2)
        diff_array = np.array(diff_img)
        mean_diff = np.mean(diff_array)
        pil_similarity = 1.0 - (mean_diff / 255.0)

        # Average all three methods for final similarity
        result['similarity'] = (pixel_similarity + mse_similarity + pil_similarity) / 3

        # Calculate max pixel difference
        result['max_pixel_diff'] = int(np.max(diff_array))

        # Determine if images match - must be 100% identical (or very close due to floating point)
        if result['similarity'] >= 0.9999:
            result['match'] = True
            result['differences'].append(
                f"Images are identical (100% match)"
            )
        else:
            result['match'] = False
            result['differences'].append(
                f"Images differ ({result['similarity']*100:.2f}% similarity)"
            )

        # Always save difference image (even if identical, for reference)
        # Create a visual difference image
        # Convert difference to grayscale and enhance contrast
        diff_gray = diff_img.convert('L')
        diff_enhanced = Image.eval(diff_gray, lambda x: min(x * 10, 255))
        diff_enhanced.save(diff_path)
        result['diff_image_saved'] = True
        print(f"  Difference image saved to: {diff_path}")

        if result['similarity'] < 1.0:
            result['differences'].append(f"Difference image saved to: {os.path.basename(diff_path)}")
            result['differences'].append(f"Maximum pixel difference: {result['max_pixel_diff']}")

    except Exception as e:
        result['differences'].append(f"Error comparing images: {str(e)}")

    return result

def generate_html_report(svg_name, comparison_result, new_png, original_png, diff_png, output_dir, svg_display_name=None, new_svg=None, original_svg=None):
    """
    Generate an HTML report for the comparison results.

    Args:
        svg_name: Name of the SVG file being compared (used for file naming)
        comparison_result: Dictionary with comparison results
        new_png: Path to the NEW PNG file
        original_png: Path to the ORIGINAL PNG file
        diff_png: Path to the difference PNG file
        output_dir: Directory to save the HTML report
        svg_display_name: Full name to display in report (defaults to svg_name)
        new_svg: Path to the NEW SVG file (optional, for SVG comparison section)
        original_svg: Path to the ORIGINAL SVG file (optional, for SVG comparison section)
    """
    # Use full display name if provided, otherwise use svg_name
    display_name = svg_display_name if svg_display_name else svg_name
    # Calculate file size difference
    file_size_diff = abs(comparison_result.get('new_size', 0) - comparison_result.get('original_size', 0))
    file_size_ok = file_size_diff < 1024  # Less than 1KB is OK

    # Determine overall test status (visual must be 100% identical, file size diff < 1KB)
    test_passed = comparison_result['structure_match'] and comparison_result['visual_match'] and file_size_ok

    # Get relative paths for images
    new_png_name = os.path.basename(new_png)
    original_png_name = os.path.basename(original_png)
    diff_png_name = os.path.basename(diff_png)

    # Check if diff image exists
    diff_exists = os.path.exists(diff_png)

    # Handle SVG files - use original paths (convert to file:// URLs for the browser)
    svg_comparison_html = ""

    if new_svg and original_svg and os.path.exists(new_svg) and os.path.exists(original_svg):
        # Copy only the NEW SVG to output directory, use original path for ORIGINAL SVG
        new_svg_name = f"{svg_name}_NEW.svg"
        new_svg_dest = os.path.join(output_dir, new_svg_name)

        # Convert original SVG path to file:// URL format
        original_svg_url = "file:///" + original_svg.replace("\\", "/")

        try:
            shutil.copy2(new_svg, new_svg_dest)
            print(f"  Copied NEW SVG to output directory for HTML report")
            print(f"  Using original path for ORIGINAL SVG: {original_svg}")

            # Generate SVG comparison section HTML
            svg_comparison_html = f'''
            <h3 style="margin-top: 30px; margin-bottom: 15px; color: #636e72; font-size: 1em;">Original SVG Files</h3>
            <div class="comparison-grid">
                <div class="image-container">
                    <h3>NEW SVG</h3>
                    <a href="{new_svg_name}" target="_blank" class="image-wrapper svg-wrapper">
                        <object data="{new_svg_name}" type="image/svg+xml" class="main-image svg-object">
                            <img src="{new_png_name}" alt="NEW SVG (fallback to PNG)">
                        </object>
                        <object data="{original_svg_url}" type="image/svg+xml" class="hover-image svg-object">
                            <img src="{original_png_name}" alt="ORIGINAL SVG (fallback to PNG)">
                        </object>
                    </a>
                    <p class="hover-hint">Hover to see ORIGINAL | Click to open NEW SVG</p>
                </div>
                <div class="image-container">
                    <h3>ORIGINAL SVG</h3>
                    <a href="{original_svg_url}" target="_blank" class="image-wrapper svg-wrapper">
                        <object data="{original_svg_url}" type="image/svg+xml" class="main-image svg-object">
                            <img src="{original_png_name}" alt="ORIGINAL SVG (fallback to PNG)">
                        </object>
                        <object data="{new_svg_name}" type="image/svg+xml" class="hover-image svg-object">
                            <img src="{new_png_name}" alt="NEW SVG (fallback to PNG)">
                        </object>
                    </a>
                    <p class="hover-hint">Hover to see NEW | Click to open ORIGINAL SVG</p>
                </div>
            </div>
'''
        except Exception as e:
            print(f"  Warning: Could not copy NEW SVG file: {e}")

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SVG Comparison Report - {svg_name}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f6fa;
            color: #2d3436;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 20px;
            color: #2d3436;
            font-size: 1.5em;
        }}
        .status-box {{
            padding: 20px 30px;
            border-radius: 10px;
            text-align: center;
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .status-success {{
            background: linear-gradient(135deg, #00b894, #00cec9);
            color: #fff;
        }}
        .status-failed {{
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            color: #fff;
        }}
        .section {{
            background: #ffffff;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            border: 1px solid #dfe6e9;
        }}
        .section h2 {{
            color: #0984e3;
            margin-bottom: 15px;
            font-size: 1.2em;
            border-bottom: 1px solid #dfe6e9;
            padding-bottom: 10px;
        }}
        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .image-container {{
            position: relative;
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            border: 1px solid #dfe6e9;
        }}
        .image-container h3 {{
            margin-bottom: 10px;
            color: #2d3436;
        }}
        .image-wrapper {{
            position: relative;
            display: inline-block;
            cursor: pointer;
        }}
        .image-wrapper img {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            transition: opacity 0.2s;
            border: 1px solid #dfe6e9;
        }}
        .image-wrapper .hover-image {{
            position: absolute;
            top: 0;
            left: 0;
            opacity: 0;
            transition: opacity 0.2s;
        }}
        .image-wrapper:hover .hover-image {{
            opacity: 1;
        }}
        .image-wrapper:hover .main-image {{
            opacity: 0;
        }}
        /* SVG object styling */
        .svg-wrapper {{
            display: block;
            width: 100%;
        }}
        .svg-object {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            border: 1px solid #dfe6e9;
            pointer-events: none;
        }}
        .svg-wrapper .hover-image.svg-object {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            opacity: 0;
            transition: opacity 0.2s;
        }}
        .svg-wrapper:hover .hover-image.svg-object {{
            opacity: 1;
        }}
        .svg-wrapper:hover .main-image.svg-object {{
            opacity: 0;
        }}
        .hover-hint {{
            font-size: 0.8em;
            color: #636e72;
            margin-top: 8px;
        }}
        .diff-container {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            margin-top: 20px;
            border: 1px solid #dfe6e9;
        }}
        .diff-container h3 {{
            margin-bottom: 10px;
            color: #2d3436;
        }}
        .diff-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            border: 1px solid #dfe6e9;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .stat-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #dfe6e9;
        }}
        .stat-label {{
            color: #636e72;
            font-size: 0.85em;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 1.3em;
            font-weight: bold;
            color: #0984e3;
        }}
        .stat-value.success {{
            color: #00b894;
        }}
        .stat-value.warning {{
            color: #e17055;
        }}
        .stat-value.error {{
            color: #d63031;
        }}
        .details-list {{
            list-style: none;
        }}
        .details-list li {{
            padding: 8px 12px;
            background: #f8f9fa;
            margin-bottom: 8px;
            border-radius: 5px;
            font-family: monospace;
            border: 1px solid #dfe6e9;
        }}
        .details-list li.success {{
            border-left: 3px solid #00b894;
        }}
        .details-list li.error {{
            border-left: 3px solid #d63031;
        }}
        .details-list li.info {{
            border-left: 3px solid #0984e3;
        }}
        .timestamp {{
            text-align: center;
            color: #636e72;
            font-size: 0.85em;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>SVG Comparison Report</h1>
        <p style="text-align: center; color: #636e72; margin-bottom: 20px; word-break: break-all;">{display_name}</p>

        <!-- Status Box -->
        <div class="status-box {'status-success' if test_passed else 'status-failed'}">
            {'TEST PASSED' if test_passed else 'TEST FAILED'}
        </div>

        <!-- Summary Stats -->
        <div class="section">
            <h2>Summary</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">Structure Match</div>
                    <div class="stat-value {'success' if comparison_result['structure_match'] else 'error'}">
                        {'Match' if comparison_result['structure_match'] else 'Differs'}
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Visual Similarity</div>
                    <div class="stat-value {'success' if comparison_result['visual_similarity'] >= 0.9999 else 'error'}">
                        {comparison_result['visual_similarity']*100:.2f}%
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">File Size Difference</div>
                    <div class="stat-value {'success' if file_size_diff == 0 else 'warning' if file_size_diff < 1024 else 'error'}">
                        {file_size_diff:,} bytes
                    </div>
                </div>
            </div>
        </div>

        <!-- Structural Comparison -->
        <div class="section">
            <h2>1. Structural Comparison</h2>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">NEW SVG Elements</div>
                    <div class="stat-value">{comparison_result.get('new_elements', 'N/A')}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">ORIGINAL SVG Elements</div>
                    <div class="stat-value">{comparison_result.get('original_elements', 'N/A')}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">NEW File Size</div>
                    <div class="stat-value">{comparison_result.get('new_size', 0):,} bytes</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">ORIGINAL File Size</div>
                    <div class="stat-value">{comparison_result.get('original_size', 0):,} bytes</div>
                </div>
            </div>
        </div>

        <!-- Visual Comparison -->
        <div class="section">
            <h2>2. Visual Comparison</h2>
            <div class="stats-grid" style="margin-bottom: 20px;">
                <div class="stat-item">
                    <div class="stat-label">NEW PNG Dimensions</div>
                    <div class="stat-value">{comparison_result.get('new_png_dimensions', 'N/A')}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">ORIGINAL PNG Dimensions</div>
                    <div class="stat-value">{comparison_result.get('original_png_dimensions', 'N/A')}</div>
                </div>
            </div>

            <h3 style="margin-bottom: 15px; color: #636e72; font-size: 1em;">PNG Renders</h3>
            <div class="comparison-grid">
                <div class="image-container">
                    <h3>NEW</h3>
                    <a href="{new_png_name}" target="_blank" class="image-wrapper">
                        <img src="{new_png_name}" alt="NEW" class="main-image">
                        <img src="{original_png_name}" alt="ORIGINAL" class="hover-image">
                    </a>
                    <p class="hover-hint">Hover to see ORIGINAL | Click to open NEW</p>
                </div>
                <div class="image-container">
                    <h3>ORIGINAL</h3>
                    <a href="{original_png_name}" target="_blank" class="image-wrapper">
                        <img src="{original_png_name}" alt="ORIGINAL" class="main-image">
                        <img src="{new_png_name}" alt="NEW" class="hover-image">
                    </a>
                    <p class="hover-hint">Hover to see NEW | Click to open ORIGINAL</p>
                </div>
            </div>

            {svg_comparison_html}

            {'<div class="diff-container"><h3>Difference Image</h3><a href="' + diff_png_name + '" target="_blank"><img src="' + diff_png_name + '" alt="Difference"></a></div>' if diff_exists else ''}
        </div>

        <!-- Details -->
        <div class="section">
            <h2>3. Details</h2>
            <ul class="details-list">
'''

    # Add detail items
    for diff in comparison_result.get('differences', []):
        if '✓' in diff or 'match' in diff.lower():
            css_class = 'success'
        elif '✗' in diff or 'differ' in diff.lower() or 'mismatch' in diff.lower():
            css_class = 'error'
        else:
            css_class = 'info'
        html_content += f'                <li class="{css_class}">{diff}</li>\n'

    html_content += f'''            </ul>
        </div>

        <p class="timestamp">Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
'''

    # Write HTML file
    html_path = os.path.join(output_dir, f"{svg_name}_report.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"HTML report saved to: {html_path}")
    return html_path  # Return path so it can be opened in browser

def compare_svg_files(downloaded_svg, reference_svg, output_dir=None):
    """
    Compare two SVG files by converting them to PNG and comparing visually.

    Args:
        downloaded_svg: Path to the downloaded SVG file
        reference_svg: Path to the reference SVG file
        output_dir: Directory for output files (PNG, HTML). Defaults to TEST_IMAGE_COMPARE_DIR.

    Returns:
        dict with comparison results
    """
    if output_dir is None:
        output_dir = TEST_IMAGE_COMPARE_DIR
    os.makedirs(output_dir, exist_ok=True)
    result = {
        'structure_match': False,
        'visual_match': False,
        'visual_similarity': 0.0,
        'differences': [],
        'downloaded_exists': os.path.exists(downloaded_svg),
        'reference_exists': os.path.exists(reference_svg),
        'new_elements': 0,
        'original_elements': 0,
        'new_size': 0,
        'original_size': 0,
        'new_png_dimensions': 'N/A',
        'original_png_dimensions': 'N/A',
        'max_pixel_diff': 0,
        'html_report_path': None,  # Path to generated HTML report
        'new_svg_path': downloaded_svg,  # Store SVG paths for report
        'original_svg_path': reference_svg
    }

    print(f"\n{'='*60}")
    print("SVG COMPARISON PROCESS")
    print(f"{'='*60}")

    if not result['downloaded_exists']:
        result['differences'].append(f"Downloaded file not found: {downloaded_svg}")
        return result

    if not result['reference_exists']:
        result['differences'].append(f"Reference file not found: {reference_svg}")
        return result

    # First, do a basic structural comparison
    try:
        print("\n1. Structural Comparison:")

        # Parse both SVG files
        tree1 = ET.parse(downloaded_svg)
        tree2 = ET.parse(reference_svg)
        root1 = tree1.getroot()
        root2 = tree2.getroot()

        # Count elements
        elements1 = list(root1.iter())
        elements2 = list(root2.iter())

        result['new_elements'] = len(elements1)
        result['original_elements'] = len(elements2)

        print(f"   NEW SVG:      {len(elements1)} elements")
        print(f"   ORIGINAL SVG: {len(elements2)} elements")

        if len(elements1) == len(elements2):
            result['structure_match'] = True
            print(f"   Element count matches")
        else:
            diff = abs(len(elements1) - len(elements2))
            print(f"   Element count differs by {diff}")
            result['differences'].append(
                f"Element count mismatch: NEW={len(elements1)}, ORIGINAL={len(elements2)}"
            )

        # Compare file sizes
        size1 = os.path.getsize(downloaded_svg)
        size2 = os.path.getsize(reference_svg)

        result['new_size'] = size1
        result['original_size'] = size2

        print(f"   NEW size:      {size1:,} bytes")
        print(f"   ORIGINAL size: {size2:,} bytes")

        if abs(size1 - size2) > 100:  # Allow 100 bytes difference
            result['differences'].append(
                f"File size differs by {abs(size1 - size2):,} bytes"
            )

    except Exception as e:
        result['differences'].append(f"Error in structural comparison: {str(e)}")

    # Now do visual comparison using Cairo
    try:
        print("\n2. Visual Comparison (Cairo Rendering):")

        # Get SVG filename for naming PNG files
        svg_name = Path(downloaded_svg).stem
        svg_full_name = Path(downloaded_svg).name  # Full filename with extension for display

        # Define PNG paths with NEW and ORIGINAL naming (all caps)
        new_png = os.path.join(output_dir, f"{svg_name}_NEW.png")
        original_png = os.path.join(output_dir, f"{svg_name}_ORIGINAL.png")
        diff_png = os.path.join(output_dir, f"{svg_name}_DIFF.png")

        # Convert both SVGs to PNG using Cairo
        print(f"   Converting NEW SVG to PNG...")
        downloaded_converted = svg_to_png_cairo(downloaded_svg, new_png)

        print(f"   Converting ORIGINAL SVG to PNG...")
        reference_converted = svg_to_png_cairo(reference_svg, original_png)

        if downloaded_converted and reference_converted:
            # Compare the PNG images
            print(f"\n3. Image Comparison:")
            img_result = compare_images(new_png, original_png, diff_png)

            result['visual_match'] = img_result['match']
            result['visual_similarity'] = img_result['similarity']
            result['max_pixel_diff'] = img_result.get('max_pixel_diff', 0)
            result['differences'].extend(img_result['differences'])

            # Store dimensions
            if img_result['new_dimensions']:
                result['new_png_dimensions'] = f"{img_result['new_dimensions'][0]}x{img_result['new_dimensions'][1]}"
            if img_result['original_dimensions']:
                result['original_png_dimensions'] = f"{img_result['original_dimensions'][0]}x{img_result['original_dimensions'][1]}"

            # Generate HTML report with SVG file paths
            print(f"\n4. Generating HTML Report...")
            html_path = generate_html_report(
                svg_name, result, new_png, original_png, diff_png, output_dir, svg_full_name,
                new_svg=downloaded_svg, original_svg=reference_svg
            )
            result['html_report_path'] = html_path

        else:
            result['differences'].append("Failed to convert one or both SVGs to PNG")

    except Exception as e:
        result['differences'].append(f"Error in visual comparison: {str(e)}")

    return result

def wait_for_download(download_dir, timeout=10):
    """
    Wait for a file to appear in the download directory.

    Args:
        download_dir: Directory to monitor
        timeout: Maximum time to wait in seconds

    Returns:
        Path to the downloaded file or None
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        files = list(Path(download_dir).glob("*.svg"))
        # Filter out temporary download files
        files = [f for f in files if not str(f).endswith('.crdownload') and not str(f).endswith('.tmp')]

        if files:
            # Return the most recently created file
            latest_file = max(files, key=os.path.getctime)
            return str(latest_file)

        time.sleep(0.5)

    return None

def parse_selector(driver, selector):
    """
    Parse a selector string and return the corresponding element.

    Args:
        driver: Selenium WebDriver instance
        selector: Selector string (id="...", class="...", xpath="...", or css="...")

    Returns:
        tuple: (element, description) or (None, error_message)
    """
    if selector.startswith('id="') and selector.endswith('"'):
        element_id = selector[4:-1]
        element = driver.find_element(By.ID, element_id)
        return element, f"id: {element_id}"
    elif selector.startswith('class="') and selector.endswith('"'):
        element_classes = selector[7:-1]
        css_selector = '.' + element_classes.replace(' ', '.')
        element = driver.find_element(By.CSS_SELECTOR, css_selector)
        return element, f"class: {element_classes}"
    elif selector.startswith('xpath="') and selector.endswith('"'):
        xpath = selector[7:-1]
        element = driver.find_element(By.XPATH, xpath)
        return element, f"xpath: {xpath}"
    elif selector.startswith('css="') and selector.endswith('"'):
        css = selector[5:-1]
        element = driver.find_element(By.CSS_SELECTOR, css)
        return element, f"css: {css}"
    else:
        return None, f"Invalid selector format: {selector}"


def click_elements(driver, click_list, wait_time):
    """
    Perform actions on elements from the click_list.

    Args:
        driver: Selenium WebDriver instance
        click_list: List of selector strings or tuples for actions
        wait_time: Time to wait after each action in seconds

    Supported actions:
        - String selector: Click the element
        - ('input', selector, value): Input text into element
        - ('drag', source_selector, target_selector): Drag source to target
        - ('set_value', selector, value): Set value via JavaScript (for color pickers, etc.)
    """
    for item in click_list:
        # Check if item is a tuple for special actions
        if isinstance(item, tuple) and len(item) == 3:
            action = item[0]

            # Input action (uses send_keys)
            if action == 'input':
                _, selector, value = item
                element, desc = parse_selector(driver, selector)
                if element is None:
                    print(desc)  # Print error message
                    continue
                print(f"Inputting '{value}' into element with {desc}")
                element.clear()
                element.send_keys(value)
                time.sleep(wait_time)

            # Set value action (uses JavaScript - works for color pickers, date inputs, etc.)
            elif action == 'set_value':
                _, selector, value = item
                element, desc = parse_selector(driver, selector)
                if element is None:
                    print(desc)
                    continue
                print(f"Setting value '{value}' on element with {desc} (via JavaScript)")
                driver.execute_script(
                    "arguments[0].value = arguments[1]; "
                    "arguments[0].dispatchEvent(new Event('input', { bubbles: true })); "
                    "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                    element, value
                )
                time.sleep(wait_time)

            # Drag action
            elif action == 'drag':
                _, source_selector, target_selector = item
                source, source_desc = parse_selector(driver, source_selector)
                if source is None:
                    print(source_desc)
                    continue
                target, target_desc = parse_selector(driver, target_selector)
                if target is None:
                    print(target_desc)
                    continue
                print(f"Dragging element with {source_desc} to element with {target_desc}")
                ActionChains(driver)\
                    .click_and_hold(source)\
                    .move_to_element(target)\
                    .release()\
                    .perform()
                time.sleep(wait_time)

            else:
                print(f"Unknown action: {action}")
                continue

        # String selector = click action
        elif isinstance(item, str):
            element, desc = parse_selector(driver, item)
            if element is None:
                print(desc)
                continue
            print(f"Clicking element with {desc}")
            element.click()
            time.sleep(wait_time)

        else:
            print(f"Invalid item format: {item}")
            continue

def open_and_click(file_name, click_list, window_x_position, window_y_position=0, reference_svg=None):
    """
    Open a browser instance, load a file, click elements, and optionally compare downloaded SVG.

    Args:
        file_name: Name of the HTML file to open
        click_list: List of selector strings to click
        window_x_position: X position for the browser window
        window_y_position: Y position for the browser window (default 0)
        reference_svg: Path to reference SVG file for comparison (optional)
    """
    # Create a unique download directory for this instance based on the file name
    # This prevents parallel tests from interfering with each other
    instance_name = Path(file_name).stem
    instance_download_dir = os.path.abspath(os.path.join("test_downloads", instance_name))
    os.makedirs(instance_download_dir, exist_ok=True)

    # Clear this instance's download directory before starting
    for f in Path(instance_download_dir).glob("*.svg"):
        f.unlink()

    # Configure Chrome with custom download directory
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option("detach", True)

    # Set download preferences - use instance-specific directory
    prefs = {
        "download.default_directory": instance_download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)

    # Move window to specified position
    driver.set_window_position(window_x_position, window_y_position)

    # Open local HTML file
    file_path = os.path.abspath(file_name)
    driver.get(f"file:///{file_path}")

    # Wait for page to render
    time.sleep(WAIT_TIME)

    # Click all elements in the list
    click_elements(driver, click_list, WAIT_TIME)

    print(f"Opened: {file_path}")
    print(f"Clicked {len(click_list)} elements")

    # If we clicked saveSvg button and have a reference file, compare
    if reference_svg and any('saveSvg' in str(item) for item in click_list):
        print(f"\nWaiting for SVG download...")
        time.sleep(DOWNLOAD_WAIT)  # Wait for download to complete

        downloaded_file = wait_for_download(instance_download_dir, timeout=10)

        if downloaded_file:
            print(f"NEW (Downloaded): {os.path.basename(downloaded_file)}")
            print(f"ORIGINAL (Reference): {os.path.basename(reference_svg)}")

            # Create instance-specific output directory for comparison images
            instance_output_dir = os.path.abspath(os.path.join("test_image_compare", instance_name))
            os.makedirs(instance_output_dir, exist_ok=True)

            # Perform comparison with Cairo conversion
            result = compare_svg_files(downloaded_file, reference_svg, instance_output_dir)

            # Display final results
            print(f"\n{'='*60}")
            print("COMPARISON RESULTS")
            print(f"{'='*60}")

            if result['structure_match']:
                print("STRUCTURE: Element counts match")
            else:
                print("STRUCTURE: Element counts differ")

            if result['visual_match']:
                print(f"VISUAL: Images match ({result['visual_similarity']*100:.1f}% similarity)")
            else:
                print(f"VISUAL: Images differ ({result['visual_similarity']*100:.1f}% similarity)")

            if result['differences']:
                print(f"\nDetails:")
                for diff in result['differences']:
                    print(f"  • {diff}")

            print(f"\nPNG files saved to: {instance_output_dir}")
            print(f"{'='*60}\n")

            # Open the HTML report in a new tab in the same browser window
            if result.get('html_report_path') and os.path.exists(result['html_report_path']):
                print("Opening HTML report in new tab...")
                # Open new tab using JavaScript
                driver.execute_script("window.open('');")
                # Switch to the new tab
                driver.switch_to.window(driver.window_handles[-1])
                # Navigate to the report
                report_url = f"file:///{result['html_report_path'].replace(chr(92), '/')}"
                driver.get(report_url)
                print(f"Report opened: {report_url}")
        else:
            print("ERROR: Could not find downloaded SVG file")

    print("Browser will remain open. Close manually when done.")

# ==============================================================================
# DOCUMENTATION: How to define test instances
# ==============================================================================
#
# FORMAT: [html_file, reference_svg_path, x_position, action1, action2, ...]
#
# REQUIRED PARAMETERS:
#   - html_file:         Name of the HTML file to open (in current directory)
#   - reference_svg_path: Full path to the reference SVG file for comparison
#                         Use raw string r"..." for Windows paths with backslashes
#   - x_position:        X position for browser window (use 0 for primary monitor,
#                        or monitor width like 1920, 2560 for secondary monitors)
#
# ACTIONS (after the 3 required parameters):
#
#   1. CLICK - Click on an element (string selector)
#      Format: 'selector_type="selector_value"'
#
#      Selector types:
#        - id="elementId"           Click element by ID
#        - class="class1 class2"    Click element by CSS class(es)
#        - xpath="/html/body/..."   Click element by XPath
#        - css="button.primary"     Click element by CSS selector
#
#      Examples:
#        'id="submitButton"'
#        'id="toggleHighlighter"'
#        'xpath="/html/body/table/tbody/tr[2]/th[2]/button[1]"'
#        'css="button[data-action=save]"'
#
#   2. INPUT - Type text into an input field
#      Format: ('input', 'selector', 'value')
#
#      Examples:
#        ('input', 'id="username"', 'john_doe')
#        ('input', 'xpath="/html/body/form/input[1]"', '12345')
#
#   3. SET_VALUE - Set value via JavaScript (for color pickers, date inputs, sliders)
#      Format: ('set_value', 'selector', 'value')
#
#      Examples:
#        ('set_value', 'id="colorPicker"', '#ff0000')
#        ('set_value', 'xpath="//input[@type=\"color\"]"', '#00ff00')
#        ('set_value', 'id="dateInput"', '2024-01-15')
#
#   4. DRAG - Drag and drop / reorder elements
#      Format: ('drag', 'source_selector', 'target_selector')
#
#      Examples:
#        ('drag', 'id="item1"', 'id="item2"')
#        ('drag', 'xpath="//button[@data-species=\"3\"]"', 'xpath="//button[@data-species=\"0\"]"')
#
#   5. CHECKBOX - Click to toggle (same as regular click)
#      Format: 'id="checkboxId"' or 'xpath="..."'
#
#      Examples:
#        'id="ribbon_keep_top"'
#        'xpath="//input[@type=\"checkbox\"]"'
#
#   6. LABEL / RADIO - Click to select (same as regular click)
#      Format: 'xpath="//label[4]"' or 'id="labelId"'
#
#      Examples:
#        'xpath="/html/body/div/label[2]"'
#
#   7. SELECT/DROPDOWN - Click to open, then click option
#      Format: Two clicks - one to open dropdown, one to select option
#
#      Examples:
#        'xpath="//select[@id=\"dropdown\"]"',           # Open dropdown
#        'xpath="//select[@id=\"dropdown\"]/option[2]"'  # Select option
#
# IMPORTANT NOTES:
#   - The last action should be 'id="saveSvg"' to trigger SVG download and comparison
#   - XPath selectors must have properly escaped quotes if using quotes inside
#   - All selectors must end with closing quote: 'id="example"' (not 'id="example')
#   - Reference SVG path must be a file path, NOT a file:/// URL
#
# ==============================================================================
# SAMPLE TEST INSTANCE (commented out):
# ==============================================================================
#
# [
#     "my_test_page.html",                              # HTML file to open
#     r"C:\path\to\reference\image.svg",               # Reference SVG for comparison
#     2560,                                             # X position (secondary monitor)
#
#     # Click a dropdown to open it
#     'xpath="/html/body/div/select"',
#
#     # Select an option from dropdown
#     'xpath="/html/body/div/select/option[3]"',
#
#     # Type into an input field
#     ('input', 'id="searchBox"', 'search term'),
#
#     # Set a color picker value
#     ('set_value', 'id="colorInput"', '#ff5500'),
#
#     # Click a checkbox
#     'id="enableFeature"',
#
#     # Click toggle buttons
#     'id="toggleOption1"',
#     'id="toggleOption2"',
#
#     # Drag to reorder elements
#     ('drag', 'xpath="/html/body/div[3]/div[2]/div[2]/div[4]/button[4]"', 'xpath="/html/body/div[3]/div[2]/div[2]/div[4]/button[3]"'),
#
#     # Save SVG (triggers download and comparison)
#     'id="saveSvg"'
# ],
#
# ==============================================================================

# Define instances to run
# Format: [html_file, reference_svg_path, x_position, action1, action2, ...]
instances = [
    [
        "Novabrowse_Figure_9B_Xtropicalis_AIRE_transcript_vs_Pwaltl_genome_xenopus_tblastx_all_matches.html",
        r"H:\genome\blast\mhc\article_illustrations\Figure 9B\Novabrowse_Figure_9B_Xtropicalis_AIRE_transcript_vs_Pwaltl_genome_xenopus_tblastx_all_matches.svg",
        2560,  # X position for window on monitor
        'xpath="/html/body/table/tbody/tr[2]/th[2]/div/button"',
        'xpath="/html/body/table/tbody/tr[2]/th[2]/div/div/label[4]"',
        ('input', 'xpath="/html/body/table/tbody/tr[2]/th[2]/input[1]"', '493786787'),
        ('input', 'xpath="/html/body/table/tbody/tr[2]/th[2]/input[2]"', '556489871'),
        'xpath="/html/body/table/tbody/tr[2]/th[2]/button[1]"',
        'xpath="/html/body/table/tbody/tr[2]/th[2]/button[1]"',
        'id="toggleHighlighter"',
        'id="toggleNumber"',
        'id="toggleNormalize"',
        'id="toggleChrmNum"',
        'id="toggleScore"',
        'id="toggleEvalue"',
        'id="toggleStart"',
        'id="toggleEnd"',
        'id="toggleABCInfo"',
        'id="saveSvg"'
    ],
    [
        "Novabrowse_Figure_5B_human_FOXP3_7up_7down_transcripts_vs_Pwaltl_mouse_frog_gar_transcriptomes_human_tblastx_best_matches.html",
        r"H:\genome\blast\mhc\article_illustrations\figure 5B\Novabrowse_Figure_5B_human_FOXP3_7up_7down_transcripts_vs_Pwaltl_mouse_frog_gar_transcriptomes_human_tblastx_best_matches.svg",
        2560,  # X position for window on monitor
        'id="toggleNormalize"',
        'xpath="/html/body/table/tbody/tr[3]/th[2]/div/div[2]/button[2]"',
        'id="toggleRibbon"',
        ('drag', 'xpath="/html/body/div[3]/div[2]/div[2]/div[4]/button[4]"', 'xpath="/html/body/div[3]/div[2]/div[2]/div[4]/button[3]"'),
        'id="toggleCoverage"',
        'id="toggleScore"',
        'id="toggleEvalue"',
        'id="toggleChrmNum"',
        'id="toggleTranscriptsInfo"',
        'id="toggleABCInfo"',
        'xpath="/html/body/table/tbody/tr[2]/th[3]/div/button"',
        'xpath="/html/body/table/tbody/tr[2]/th[3]/div/div/label[4]"',
        'xpath="/html/body/table/tbody/tr[2]/th[3]/button[1]"',
        'xpath="/html/body/table/tbody/tr[2]/th[3]/button[2]"',
        'xpath="/html/body/table/tbody/tr[2]/th[4]/div/button"',
        'xpath="/html/body/table/tbody/tr[2]/th[4]/div/div/label[4]"',
        'xpath="/html/body/table/tbody/tr[2]/th[4]/button[1]"',
        'xpath="/html/body/table/tbody/tr[2]/th[4]/button[2]"',
        'xpath="/html/body/table/tbody/tr[2]/th[5]/div/button"',
        'xpath="/html/body/table/tbody/tr[2]/th[5]/div/div/label[2]"',
        'xpath="/html/body/table/tbody/tr[2]/th[5]/button[1]"',
        'xpath="/html/body/table/tbody/tr[2]/th[5]/button[2]"',
        'id="toggleHighlighter"',
        'id="toggleRibbonSettings"',
        'xpath="/html/body/table/tr[8]/td[2]/div/button"',
        'xpath="/html/body/table/tr[8]/td[2]/div/div/div[1]/select"',
        'xpath="/html/body/table/tr[8]/td[2]/div/div/div[1]/select/option[2]"',
        ('set_value', 'xpath="/html/body/table/tr[8]/td[2]/div/div/div[2]/div[2]/input[1]"', '#ff0000'),
        ('set_value', 'xpath="/html/body/table/tr[8]/td[2]/div/div/div[2]/div[2]/input[3]"', '1'),
        'xpath="/html/body/table/tr[8]/td[2]/div/div/div[2]/div[2]/div[1]/input"',
        'xpath="/html/body/table/tr[1]/td[2]/div/button"',
        ('set_value', 'xpath="/html/body/table/tr[1]/td[2]/div/div/div[2]/div[2]/input[1]"', '#ff3dc2'),
        'xpath="/html/body/table/tr[1]/td[2]/div/div/button"',
        'xpath="/html/body/table/tr[2]/td[2]/div/button"',
        ('set_value', 'xpath="/html/body/table/tr[2]/td[2]/div/div/div[2]/div[2]/input[1]"', '#ff6741'),
        'xpath="/html/body/table/tr[2]/td[2]/div/div/button"',
        'id="toggleRibbonSettings"',
        'id="saveSvg"',
    ],
    [
        "Novabrowse_Figure_6B_human_AIRE_7up_7down_transcripts_vs_mouse_lizard_chicken_frog_Pwaltl_gar_transcriptomes_human_tblastx_best_matches.html",
        r"H:\genome\blast\mhc\article_illustrations\figure 6B\Novabrowse_Figure_6B_human_AIRE_7up_7down_transcripts_vs_mouse_lizard_chicken_frog_Pwaltl_gar_transcriptomes_human_tblastx_best_matches.svg",
        2560,  # X position for window on monitor
        'id="toggleNormalize"',
        'id="toggleCoverage"',
        'id="toggleScore"',
        'id="toggleEvalue"',
        'id="toggleChrmNum"',
        'id="toggleTranscriptsInfo"',
        'xpath="/html/body/table/tbody/tr[3]/th[2]/div/div[2]/button[2]"',
        'id="toggleABCInfo"',
        'id="toggleRibbon"',
        ('drag', 'xpath="/html/body/div[3]/div[2]/div[2]/div[4]/button[5]"', 'xpath="/html/body/div[3]/div[2]/div[2]/div[4]/button[2]"'),
        ('drag', 'xpath="/html/body/div[3]/div[2]/div[2]/div[4]/button[5]"', 'xpath="/html/body/div[3]/div[2]/div[2]/div[4]/button[3]"'),
        ('drag', 'xpath="/html/body/div[3]/div[2]/div[2]/div[4]/button[7]"', 'xpath="/html/body/div[3]/div[2]/div[2]/div[4]/button[4]"'),
        ('drag', 'xpath="/html/body/div[3]/div[2]/div[2]/div[4]/button[6]"', 'xpath="/html/body/div[3]/div[2]/div[2]/div[4]/button[5]"'),
        ('input', 'xpath="/html/body/table/tbody/tr[2]/th[2]/input[1]"', '69302468'),
        ('input', 'xpath="/html/body/table/tbody/tr[2]/th[2]/input[2]"', '87469134'),
        'xpath="/html/body/table/tbody/tr[2]/th[2]/div/button"',
        'xpath="/html/body/table/tbody/tr[2]/th[2]/div/div/label[2]"',
        'xpath="/html/body/table/tbody/tr[2]/th[3]/div/button"',
        'xpath="/html/body/table/tbody/tr[2]/th[3]/div/div/label[3]"',
        'xpath="/html/body/table/tbody/tr[2]/th[3]/button[2]"',
        ('input', 'xpath="/html/body/table/tbody/tr[2]/th[3]/input[1]"', '220447010'),
        ('input', 'xpath="/html/body/table/tbody/tr[2]/th[3]/input[2]"', '257684681'),
        'xpath="/html/body/table/tbody/tr[2]/th[4]/div/button"',
        'xpath="/html/body/table/tbody/tr[2]/th[4]/div/div/label[4]"',
        'xpath="/html/body/table/tbody/tr[2]/th[4]/button[2]"',
        ('input', 'xpath="/html/body/table/tbody/tr[2]/th[4]/input[1]"', '1'),
        ('input', 'xpath="/html/body/table/tbody/tr[2]/th[4]/input[2]"', '1835050'),
        'xpath="/html/body/table/tbody/tr[2]/th[5]/div/button"',
        'xpath="/html/body/table/tbody/tr[2]/th[5]/div/div/label[4]"',
        'xpath="/html/body/table/tbody/tr[2]/th[5]/button[2]"',
        ('input', 'xpath="/html/body/table/tbody/tr[2]/th[5]/input[1]"', '116260910'),
        ('input', 'xpath="/html/body/table/tbody/tr[2]/th[5]/input[2]"', '137822024'),
        ('input', 'xpath="/html/body/table/tbody/tr[2]/th[6]/input[1]"', '1'),
        ('input', 'xpath="/html/body/table/tbody/tr[2]/th[6]/input[2]"', '2372146345'),
        'xpath="/html/body/table/tbody/tr[2]/th[6]/div/button"',
        'xpath="/html/body/table/tbody/tr[2]/th[6]/div/div/label[6]"',
        'xpath="/html/body/table/tbody/tr[2]/th[7]/div/button"',
        'xpath="/html/body/table/tbody/tr[2]/th[7]/div/div/label[5]"',
        'xpath="/html/body/table/tbody/tr[2]/th[7]/button[2]"',
        ('input', 'xpath="/html/body/table/tbody/tr[2]/th[7]/input[1]"', '1'),
        ('input', 'xpath="/html/body/table/tbody/tr[2]/th[7]/input[2]"', '78916909'),
        'id="toggleHighlighter"',
        'xpath="/html/body/table/tbody/tr[3]/th[2]/div/div[1]/div"',
        'xpath="/html/body/table/tr[8]/td[2]/div/input"',
        'id="toggleRibbonSettings"',
        'xpath="/html/body/table/tr[8]/td[2]/div/button"',
        'xpath="/html/body/table/tr[8]/td[2]/div/div/div[1]/select"',
        'xpath="/html/body/table/tr[8]/td[2]/div/div/div[1]/select/option[2]"',
        ('set_value', 'xpath="/html/body/table/tr[8]/td[2]/div/div/div[2]/div[2]/input[1]"', '#ff0000'),
        ('set_value', 'xpath="/html/body/table/tr[8]/td[2]/div/div/div[2]/div[2]/input[3]"', '1'),
        'xpath="/html/body/table/tr[8]/td[2]/div/div/button"',
        'id="toggleRibbonSettings"',
        'id="saveSvg"',
    ],
]

# Run all instances in parallel
threads = []
for instance in instances:
    file_name = instance[0]      # 1st: HTML file to open
    reference_svg = instance[1]  # 2nd: Reference SVG path for comparison
    x_position = instance[2]     # 3rd: X position for browser window
    click_list = instance[3:]    # 4th+: Actions (clicks, inputs, drags, etc.)

    # Create and start a thread for each instance
    thread = threading.Thread(
        target=open_and_click,
        args=(file_name, click_list, x_position, 0, reference_svg)
    )
    thread.start()
    threads.append(thread)

# Wait for all threads to complete
for thread in threads:
    thread.join()

print("All instances completed successfully.")
print(f"Downloaded SVG files can be found in: {TEST_DOWNLOAD_DIR}")
print(f"Image comparison files can be found in: {TEST_IMAGE_COMPARE_DIR}")
