import re
import sys

def find_nested_patterns(file_path):
    # Pattern for text_text={ followed by nested id structure with type=70
    pattern = r'([a-zA-Z0-9_]+)=\{\s*id=\{\s*id=(\d+)\s*type=70\s*\}'
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            matches = re.finditer(pattern, content)
            
            for match in matches:
                prefix = match.group(1)  # The text_text part
                # Skip if prefix is exactly 'equipment'
                if prefix == 'equipment':
                    continue
                    
                id_num = match.group(2)  # The inner id number
                print(f"Found: {prefix}={{\n\tid={{\n\t\tid={id_num}\n\t\ttype=70\n\t}}\n}}")
                
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test.py <file_path>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    find_nested_patterns(file_path)
