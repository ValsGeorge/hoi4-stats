# HOI4 Save File Tools

This repository contains a collection of tools for working with Hearts of Iron IV save files, including parsing, melting binary files, and extracting data.

## Requirements

-   Python 3.7 or higher
-   `melt.exe` - The Paradox save game melter executable (should be available in the project directory)
-   Pyradox library - Used for parsing save files (included as a submodule or directory)

## Tools

### 1. Melter Utility (`melt_files.py`)

A simple command-line utility for converting binary HOI4 save files to text format.

#### Usage

```bash
python melt_files.py save1.hoi4 save2.hoi4 save3.hoi4
```

#### Options

-   `--output-dir` or `-o`: Directory to save melted files (default: `./melted_saves/`)
-   `--check` or `-c`: Check if files are binary or text without melting them
-   `--verbose` or `-v`: Enable verbose output

#### Examples

```bash
# Melt a single file
python melt_files.py path/to/save.hoi4

# Melt multiple files
python melt_files.py path/to/save1.hoi4 path/to/save2.hoi4

# Melt to a specific directory
python melt_files.py --output-dir ./my_melted_files/ path/to/save.hoi4

# Check if files are binary or text
python melt_files.py --check path/to/save1.hoi4 path/to/save2.hoi4
```

### 2. Save Parser (`read_with_pyradox.py`)

A tool for parsing and analyzing HOI4 save files using the Pyradox library.

#### Usage

```bash
python read_with_pyradox.py [save_path] [options]
```

#### Options

-   `save_path`: Path to the HOI4 save file to parse (optional, default provided)
-   `--output` or `-o`: Path to save the output JSON file
-   `--melt-only`: Only melt the file, do not parse it

#### Examples

```bash
# Parse a save file
python read_with_pyradox.py path/to/save.hoi4

# Parse and save to JSON
python read_with_pyradox.py path/to/save.hoi4 --output save_data.json

# Only melt a binary save file without parsing
python read_with_pyradox.py path/to/save.hoi4 --melt-only
```

### 3. GUI Production Reader (`hoi4_mio_reader.py`)

A GUI application for reading Soviet MIO production from save files.

#### Usage

```bash
python hoi4_mio_reader.py
```

## How It Works

1. **File Detection**: The tools first check if a save file is in binary format.
2. **Melting Process**: Binary files are processed using `melt.exe` to convert them to readable text format.
3. **Parsing**: The text save files are parsed using Pyradox to extract game data.
4. **Data Extraction**: The tools can extract specific data (such as Soviet MIO production) or provide the entire save game structure.

## Troubleshooting

-   Make sure `melt.exe` is available in the project directory or in your system PATH.
-   Some very large save files may require increased memory or timeout settings.
-   If you encounter encoding issues, try using the `--encoding` option in the appropriate tool.

## Technical Notes

-   The melter utility has been extracted to a reusable module in `src/utils/melter.py`.
-   The tools are designed to work on Windows with HOI4 installed, but may work on other platforms with appropriate modifications.
-   Binary save files are converted to text using temporary files to avoid path-related issues.
