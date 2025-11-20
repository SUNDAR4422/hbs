with open('students/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the problematic line
for i, line in enumerate(lines):
    if 'errors.append(f"Row {idx}: Error parsing data' in line and 'if errors:' in line:
        # Split the line
        lines[i] = '                    errors.append(f"Row {idx}: Error parsing data - {str(e)}")\n'
        lines.insert(i + 1, '\n')
        lines.insert(i + 2, '            if errors:\n')
        break

with open('students/views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Fixed indentation issue')
