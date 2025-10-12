import sys

def check_syntax(filename):
    try:
        with open(filename, 'r') as f:
            source = f.read()
        compile(source, filename, 'exec')
        print(f"✅ No syntax errors found in {filename}")
        return True
    except SyntaxError as e:
        line_no = e.lineno
        print(f"❌ Syntax error in {filename} at line {line_no}: {e}")
        
        # Print the problematic line and surrounding context
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        start = max(0, line_no - 3)
        end = min(len(lines), line_no + 2)
        
        print("\nContext:")
        for i in range(start, end):
            prefix = "→ " if i == line_no - 1 else "  "
            print(f"{prefix}{i+1}: {lines[i].rstrip()}")
        
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_syntax.py <filename>")
        sys.exit(1)
    
    filename = sys.argv[1]
    if not check_syntax(filename):
        sys.exit(1)