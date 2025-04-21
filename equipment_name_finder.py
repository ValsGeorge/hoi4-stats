import re
import sys

def find_equipment_mappings(file_path) -> dict[str, tuple[int, int]]:
    # Pattern for text_text={ followed by nested id structure with type=70
    pattern = r'([a-zA-Z0-9_]+)=\{\s*id=\{\s*id=(\d+)\s*type=70\s*\}'
    equipment_mappings = {}
    
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

                equipment_mappings[prefix] = (int(id_num), 70)
                
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
    except Exception as e:
        print(f"Error: {str(e)}")

    return equipment_mappings

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python equipment_name_finder.py <file_path>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    mappings = find_equipment_mappings(file_path)
    
    # Print findings in a readable format
    print("\nEquipment Mappings Found:")
    print("-" * 50)
    for name, (id_num, type_num) in sorted(mappings.items()):
        print(f"{name} -> (ID:{id_num}, Type:{type_num})")
