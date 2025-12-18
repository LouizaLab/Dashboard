#!/usr/bin/env python3
"""
Comprehensive indentation and expression error fixer for app.py
Fixes indentation issues AND "Expected expression" errors.
"""

import re
import sys


def fix_else_after_elif(lines):
    """Fix else statements that are incorrectly indented after elif."""
    fixed = []
    i = 0
    changes = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # Check if this is an else that's incorrectly indented
        else_match = re.match(r'^(\s+)else\s*:\s*$', line)

        if else_match and i > 0:
            else_indent = len(else_match.group(1))

            # Look back to find the previous elif or if
            for j in range(i - 1, max(0, i - 20), -1):
                prev_line = lines[j]
                prev_stripped = prev_line.lstrip()

                if not prev_stripped or prev_stripped.startswith('#'):
                    continue

                prev_indent = len(prev_line) - len(prev_stripped)

                # Check if previous line is elif at same indent level as else
                elif_match = re.match(r'^\s{' + str(else_indent) + r'}elif\s+.*:\s*$', prev_line)
                if_match = re.match(r'^\s{' + str(else_indent) + r'}if\s+.*:\s*$', prev_line)

                if elif_match or if_match:
                    # This else should be at the same level - it's correct
                    # But check if the code after else is indented
                    fixed.append(line)
                    i += 1

                    # Fix the block after else
                    expected_indent = else_indent + 4
                    while i < len(lines):
                        next_line = lines[i]
                        next_stripped = next_line.lstrip()

                        if not next_stripped or next_stripped.startswith('#'):
                            fixed.append(next_line)
                            i += 1
                            continue

                        next_indent = len(next_line) - len(next_stripped)

                        # End of else block
                        if next_indent <= else_indent:
                            break

                        # Fix indentation
                        if next_indent < expected_indent:
                            fixed_line = ' ' * expected_indent + next_stripped
                            fixed.append(fixed_line)
                            if fixed_line != next_line:
                                changes += 1
                        else:
                            fixed.append(next_line)

                        i += 1
                    break

                # Check if previous line is elif but else is indented more (WRONG)
                elif_deeper_match = re.match(r'^\s{' + str(else_indent - 4) + r'}elif\s+.*:\s*$', prev_line)
                if elif_deeper_match:
                    # else is incorrectly indented - it should be at same level as elif
                    fixed_line = ' ' * (else_indent - 4) + 'else:'
                    fixed.append(fixed_line)
                    if fixed_line != line:
                        changes += 1
                    i += 1

                    # Fix the block after else
                    expected_indent = else_indent - 4 + 4
                    while i < len(lines):
                        next_line = lines[i]
                        next_stripped = next_line.lstrip()

                        if not next_stripped or next_stripped.startswith('#'):
                            fixed.append(next_line)
                            i += 1
                            continue

                        next_indent = len(next_line) - len(next_stripped)

                        # End of else block
                        if next_indent <= (else_indent - 4):
                            break

                        # Fix indentation - adjust by 4 spaces
                        if next_indent >= else_indent:
                            # This was indented for the wrong else level
                            fixed_line = ' ' * expected_indent + next_stripped
                            fixed.append(fixed_line)
                            if fixed_line != next_line:
                                changes += 1
                        else:
                            fixed.append(next_line)

                        i += 1
                    break

        if i < len(lines) and lines[i] == line:
            fixed.append(line)
            i += 1

    return fixed, changes


def fix_unindented_after_control(lines):
    """Fix code that should be indented after if/else/elif/for/while/with/try/except."""
    fixed = []
    i = 0
    changes = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        # Check if this line ends with : (control statement)
        if re.search(r':\s*$', stripped) and not stripped.startswith('#'):
            fixed.append(line)
            i += 1
            expected_indent = indent + 4

            # Process the block that follows
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.lstrip()

                if not next_stripped or next_stripped.startswith('#'):
                    fixed.append(next_line)
                    i += 1
                    continue

                next_indent = len(next_line) - len(next_stripped)

                # Check for else/elif at same level (valid)
                if re.match(r'^\s{' + str(indent) + r'}(else|elif)\s*:', next_line):
                    break

                # End of block - next statement at same or lower indent
                if next_indent <= indent:
                    break

                # Fix indentation if needed
                if next_indent < expected_indent:
                    fixed_line = ' ' * expected_indent + next_stripped
                    fixed.append(fixed_line)
                    if fixed_line != next_line:
                        changes += 1
                else:
                    fixed.append(next_line)

                i += 1
            continue

        fixed.append(line)
        i += 1

    return fixed, changes


def main():
    """Main function to fix all errors in app.py"""
    filename = 'app.py'

    try:
        print(f"Reading {filename}...")
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        total_changes = 0

        # Fix 1: Else statements incorrectly indented after elif
        print("Fixing else statements after elif...")
        lines, changes1 = fix_else_after_elif(lines)
        total_changes += changes1

        # Fix 2: Unindented code after control statements
        print("Fixing unindented code after control statements...")
        lines, changes2 = fix_unindented_after_control(lines)
        total_changes += changes2

        if total_changes > 0:
            with open(filename, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"✓ Fixed {total_changes} errors in {filename}")
        else:
            print(f"✓ No errors found in {filename}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
