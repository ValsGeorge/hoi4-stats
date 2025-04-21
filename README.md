# HOI4 Soviet MIO Production Reader

A simple application that allows you to read one or more HOI4 save files and extract production history for Soviet Military-Industrial Organizations (MIO).

## Features

-   Load one or more HOI4 save files
-   Efficiently analyze extremely large save files (5+ million lines)
-   Automatically extract Soviet MIO organizations and their production history
-   Display production history in a sortable table
-   Export results to CSV

## Requirements

-   Python 3.6 or higher
-   Tkinter (usually comes with Python)

## Installation

1. Make sure you have Python installed
2. No additional packages are required as this uses standard libraries

## Usage

### Windows

Simply double-click `run.bat` to start the application.

### All Platforms

1. Run the application:

    ```
    python run.py
    ```

    or directly:

    ```
    python hoi4_mio_reader.py
    ```

2. Click "Select HOI4 Save File(s)" to choose one or more HOI4 save files

3. Configure processing options:

    - Use cache (saves results for faster loading next time)
    - Use multiprocessing (parallel processing for speed)
    - Use binary search (faster scanning for large files)

4. The application will automatically process the files and display the Soviet MIO production history

    - A progress bar will show processing status for large files
    - The status bar at the bottom displays relevant information

5. You can export the results to CSV by clicking the "Export Results" button

## How It Works

The application uses multiple advanced techniques to efficiently parse very large HOI4 save files:

1. Memory mapping for efficient file access
2. Binary search to quickly identify relevant file sections
3. Multiprocessing for parallel chunk processing
4. Compiled regex patterns for faster matching
5. Caching of results for instant loading of previously processed files

The application searches for patterns in HOI4 save files that match Soviet MIO organizations (blocks that start with "SOV\_" and end with "\_organization"). It then extracts the production history from these blocks, including:

-   Organization name
-   Equipment ID and type
-   Production date (if available)
-   Number of units produced

## Performance Optimizations

-   **Memory mapping**: Uses OS-level file mapping for efficient access to very large files
-   **Binary search**: Quickly identifies sections containing Soviet data without scanning entire file
-   **Multiprocessing**: Processes multiple organization blocks in parallel using all available CPU cores
-   **Smart chunking**: Reads files in manageable chunks with optimized extraction sizes
-   **Result caching**: Stores parsed results to avoid reprocessing the same files
-   **Compiled regex patterns**: Pre-compiles all regex patterns for better performance
-   **Processing options**: User-configurable settings to optimize for specific scenarios

## Notes

-   HOI4 save files with 5+ million lines can now be processed efficiently
-   For save files you frequently access, enable caching for instant loading times
-   If you encounter any memory issues with extremely large files, try disabling multiprocessing
-   The application handles encoding issues that might occur in save files
-   If you encounter any problems, check the status bar at the bottom of the application for error messages
