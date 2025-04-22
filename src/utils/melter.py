import os
import subprocess
import tempfile
import shutil
import uuid
import logging
from pathlib import Path
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_binary_file(file_path: str) -> bool:
    """
    Determine if a file is binary by checking the first few bytes.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file appears to be binary, False if it appears to be text
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(10)
            is_text = all(b >= 32 and b <= 126 or b in (9, 10, 13) for b in header)
            return not is_text
    except Exception as e:
        logger.error(f"Error checking if file is binary: {str(e)}")
        # If we can't check, assume it's binary to be safe
        return True

def find_melt_executable() -> Optional[str]:
    """
    Find the melt.exe executable in various locations.
    
    Returns:
        Path to melt.exe if found, None otherwise
    """
    # Check in current directory
    melt_path = os.path.abspath("melt.exe")
    if os.path.exists(melt_path):
        logger.info(f"Found melt.exe in current directory: {melt_path}")
        return melt_path
    
    # Check in script directory
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    melt_path = os.path.join(script_dir, "melt.exe")
    if os.path.exists(melt_path):
        logger.info(f"Found melt.exe in script directory: {melt_path}")
        return melt_path
    
    # Check in system PATH
    from shutil import which
    melt_in_path = which("melt.exe") or which("melt")
    if melt_in_path:
        logger.info(f"Found melt.exe in PATH: {melt_in_path}")
        return melt_in_path
    
    logger.error("melt.exe not found in application directory or PATH")
    return None

def melt_save_file(file_path: str, output_path: Optional[str] = None, temp_dir: Optional[str] = None) -> Tuple[bool, str]:
    """
    Melt a HOI4 save file using melt.exe.
    
    Args:
        file_path: Path to the save file to melt
        output_path: Path where the melted file should be saved (optional)
        temp_dir: Directory to use for temporary files (optional)
        
    Returns:
        Tuple of (success, path) where:
          - success: True if melting was successful, False otherwise
          - path: Path to the melted file if successful, original path if not
    """
    # Check if the file needs melting (is binary)
    if not is_binary_file(file_path):
        logger.info(f"File appears to be text already, no melting needed: {file_path}")
        return True, file_path
    
    logger.info(f"File appears to be binary, attempting to melt: {file_path}")
    
    # Find melt.exe
    melt_path = find_melt_executable()
    if not melt_path:
        return False, file_path
    
    # Create output file path if not provided
    if not output_path:
        # Use temp directory if provided, otherwise create one
        if not temp_dir:
            temp_dir = tempfile.mkdtemp(prefix="hoi4_melted_")
        
        output_path = os.path.join(temp_dir, os.path.basename(file_path) + ".melted")
    
    try:
        # Create temporary files with unique names to avoid path issues
        temp_input_file = os.path.join(tempfile.gettempdir(), f"hoi4_melt_input_{uuid.uuid4().hex}.hoi4")
        temp_output_file = os.path.join(tempfile.gettempdir(), f"hoi4_melt_output_{uuid.uuid4().hex}.txt")
        
        # Copy original file to temp location
        logger.info(f"Copying file to temp location: {temp_input_file}")
        shutil.copy2(file_path, temp_input_file)
        
        # Fix file paths - convert forward slashes to backslashes for Windows
        win_melt_path = os.path.normpath(melt_path).replace('/', '\\')
        win_temp_input = os.path.normpath(temp_input_file).replace('/', '\\')
        win_temp_output = os.path.normpath(temp_output_file).replace('/', '\\')
        
        # Create a temporary batch file to run the command
        batch_file = os.path.join(tempfile.gettempdir(), f"run_melt_{uuid.uuid4().hex}.bat")
        with open(batch_file, 'w') as f:
            # The command in batch format
            f.write(f'@echo off\n')
            f.write(f'"{win_melt_path}" melt --unknown-key stringify --to-stdout "{win_temp_input}" > "{win_temp_output}"\n')
            f.write(f'exit %ERRORLEVEL%\n')
        
        # Log the batch file contents
        logger.info(f"Created batch file: {batch_file}")
        with open(batch_file, 'r') as f:
            logger.debug(f"Batch file contents:\n{f.read()}")
        
        # Run the batch file
        logger.info(f"Running batch file: {batch_file}")
        
        result = subprocess.run(batch_file, shell=True, capture_output=True, text=True)
        
        # Log detailed subprocess results
        logger.debug(f"Return code: {result.returncode}")
        logger.debug(f"STDOUT: {result.stdout}")
        logger.debug(f"STDERR: {result.stderr}")
        
        # Check if there was an error code (accept both 0 and 1 as success based on Java code)
        if result.returncode != 0 and result.returncode != 1:
            error_msg = f"Melt.exe returned error code {result.returncode}. Error: {result.stderr}"
            logger.error(error_msg)
            
            # Clean up temp files
            try:
                os.remove(temp_input_file)
                os.remove(batch_file)
                if os.path.exists(temp_output_file):
                    os.remove(temp_output_file)
            except Exception as e:
                logger.warning(f"Error cleaning up temp files: {str(e)}")
                
            return False, file_path
        
        # If the temp output file exists, copy it to the final destination
        if os.path.exists(temp_output_file) and os.path.getsize(temp_output_file) > 0:
            logger.info(f"Melting successful. Copying from temp file to final destination: {output_path}")
            
            # Create the directory for the output file if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            shutil.copy2(temp_output_file, output_path)
            
            # Clean up temp files
            try:
                os.remove(temp_input_file)
                os.remove(temp_output_file)
                os.remove(batch_file)
            except Exception as e:
                logger.warning(f"Error cleaning up temp files: {str(e)}")
            
            return True, output_path
        else:
            error_msg = f"Melt didn't produce output. Stderr: {result.stderr}"
            logger.error(error_msg)
            logger.error(f"Expected output file {temp_output_file} not found or empty")
            
            # Clean up temp files
            try:
                os.remove(temp_input_file)
                os.remove(batch_file)
                if os.path.exists(temp_output_file):
                    os.remove(temp_output_file)
            except Exception as e:
                logger.warning(f"Error cleaning up temp files: {str(e)}")
                
            return False, file_path
                
    except Exception as e:
        error_msg = f"Error executing melt.exe: {str(e)}"
        logger.exception(error_msg)
        return False, file_path

def ensure_melted_saves_dir(base_dir: Optional[str] = None) -> str:
    """
    Ensure the melted_saves directory exists.
    
    Args:
        base_dir: Base directory where melted_saves should be created (optional)
        
    Returns:
        Path to the melted_saves directory
    """
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    melted_saves_dir = os.path.join(base_dir, "melted_saves")
    if not os.path.exists(melted_saves_dir):
        os.makedirs(melted_saves_dir)
    
    return melted_saves_dir

def melt_to_directory(file_path: str, output_dir: Optional[str] = None) -> Tuple[bool, str]:
    """
    Melt a HOI4 save file and save it to a specific directory.
    
    Args:
        file_path: Path to the save file to melt
        output_dir: Directory where the melted file should be saved (optional)
        
    Returns:
        Tuple of (success, path) where:
          - success: True if melting was successful, False otherwise
          - path: Path to the melted file if successful, original path if not
    """
    if output_dir is None:
        output_dir = ensure_melted_saves_dir()
    
    # Create output file path
    output_path = os.path.join(output_dir, os.path.basename(file_path) + ".txt")
    
    return melt_save_file(file_path, output_path)

def melt_multiple_files(file_paths: list, output_dir: Optional[str] = None) -> dict:
    """
    Melt multiple HOI4 save files and save them to a specific directory.
    
    Args:
        file_paths: List of paths to the save files to melt
        output_dir: Directory where the melted files should be saved (optional)
        
    Returns:
        Dictionary mapping original file paths to result tuples (success, melted_path)
    """
    if output_dir is None:
        output_dir = ensure_melted_saves_dir()
    
    results = {}
    for file_path in file_paths:
        logger.info(f"Processing file: {file_path}")
        
        # Skip if file is already text
        if not is_binary_file(file_path):
            logger.info(f"Skipping {file_path}: already in text format")
            results[file_path] = (True, file_path)
            continue
        
        # Melt the file
        output_path = os.path.join(output_dir, os.path.basename(file_path) + ".txt")
        success, melted_path = melt_save_file(file_path, output_path)
        results[file_path] = (success, melted_path)
    
    return results

# Command-line interface if run directly
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Melt HOI4 save files to text format")
    parser.add_argument("files", nargs="+", help="HOI4 save files to melt")
    parser.add_argument("--output-dir", "-o", help="Directory to save melted files")
    
    args = parser.parse_args()
    
    output_dir = args.output_dir or ensure_melted_saves_dir()
    
    for file_path in args.files:
        success, melted_path = melt_to_directory(file_path, output_dir)
        if success:
            print(f"Successfully melted {file_path} to {melted_path}")
        else:
            print(f"Failed to melt {file_path}")
