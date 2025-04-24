print("Testing imports...")

try:
    from src.utils.melter import melt_save_file, is_binary_file, ensure_melted_saves_dir
    print("Successfully imported melter module")
except Exception as e:
    print(f"Error importing melter module: {e}")

try:
    from read_with_pyradox import load_save_file, save_to_json
    print("Successfully imported read_with_pyradox module")
except Exception as e:
    print(f"Error importing read_with_pyradox module: {e}")

try:
    from compare_view import CompareView
    print("Successfully imported CompareView class")
except Exception as e:
    print(f"Error importing CompareView class: {e}")

print("Import test completed") 