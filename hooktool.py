#!/usr/bin/env python3
import sys
import os
import re
import shutil
import time
import threading
from typing import List, Tuple, Dict
from datetime import datetime

# ========== DEBUG CONFIG ==========
DEBUG_LEVEL = 2  # 0: OFF, 1: BASIC, 2: VERBOSE, 3: EXTREME (từng key)
LOG_TO_FILE = True
LOG_FILE = f"xor_tool_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

# Colors cho terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def debug_print(level, *args, **kwargs):
    """In debug log ra terminal và file"""
    if level <= DEBUG_LEVEL:
        # In ra terminal
        print(*args, **kwargs)
        # Ghi ra file
        if LOG_TO_FILE:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                msg = ' '.join(str(arg) for arg in args)
                # Loại bỏ màu sắc khi ghi file
                for color in [Colors.HEADER, Colors.BLUE, Colors.CYAN, Colors.GREEN, 
                              Colors.YELLOW, Colors.RED, Colors.END, Colors.BOLD, Colors.DIM]:
                    msg = msg.replace(color, '')
                f.write(f"[{timestamp}] {msg}\n")

def log_system_info(filepath):
    """Log thông tin hệ thống"""
    debug_print(1, f"{Colors.HEADER}{'='*70}{Colors.END}")
    debug_print(1, f"{Colors.BOLD}🖥️  THÔNG TIN HỆ THỐNG & FILE{Colors.END}")
    debug_print(1, f"  Python: {sys.version.split()[0]}")
    debug_print(1, f"  File: {os.path.basename(filepath)}")
    debug_print(1, f"  Size: {os.path.getsize(filepath):,} bytes ({os.path.getsize(filepath)/1024:.2f} KB)")
    debug_print(1, f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    debug_print(1, f"  Debug level: {DEBUG_LEVEL}")
    debug_print(1, f"{Colors.HEADER}{'='*70}{Colors.END}")

# ========== XOR FUNCTIONS ==========
DEFAULT_KEY = 0x2E

def xor_crypt(data: bytes, key: int) -> bytes:
    return bytes([b ^ (key & 0xFF) for b in data])

def find_urls(data: bytes) -> List[Tuple[int, str]]:
    url_pattern = re.compile(rb"https?://[A-Za-z0-9\./_\-\?\=&%:#]+")
    return [(m.start(), m.group().decode(errors="ignore")) for m in url_pattern.finditer(data)]

def find_urls_aggressive(data: bytes) -> List[Tuple[int, str]]:
    patterns = [
        rb"https?://[A-Za-z0-9\./_\-\?\=&%:#]+",
        rb"www\.[A-Za-z0-9\./_\-\?\=&%:#]+",
        rb"[A-Za-z0-9\-]+\.(com|net|org|io|vn|edu|gov)[A-Za-z0-9\./_\-\?\=&%:#]*"
    ]
    urls = []
    seen = set()
    for pattern in patterns:
        for match in re.finditer(pattern, data):
            try:
                url = match.group().decode(errors='ignore')
                if url not in seen:
                    urls.append((match.start(), url))
                    seen.add(url)
            except:
                continue
    return urls

def brute_force_urls(data: bytes, start_key: int = 0x00, end_key: int = 0xFF, 
                     max_urls_per_key: int = 10, aggressive: bool = False) -> Dict[int, List[Tuple[int, str]]]:
    results = {}
    total_keys = end_key - start_key + 1
    
    debug_print(1, f"{Colors.CYAN}🔍 Brute-force XOR key từ 0x{start_key:02X} → 0x{end_key:02X}{Colors.END}")
    debug_print(1, f"📊 Tổng số key: {total_keys}")
    
    start_time = time.time()
    found_count = 0
    
    for idx, key in enumerate(range(start_key, end_key + 1)):
        # Progress bar (level 1, mỗi 16 keys)
        if idx % 16 == 0:
            percent = (idx / total_keys) * 100
            bar_len = 40
            filled = int(bar_len * idx // total_keys)
            bar = '█' * filled + '░' * (bar_len - filled)
            debug_print(1, f"\r  ⏳ Tiến độ: [{bar}] {percent:.1f}% ({idx}/{total_keys})", end="")
        
        # Debug chi tiết từng key (level 3)
        if DEBUG_LEVEL >= 3:
            debug_print(3, f"{Colors.DIM}    [DEBUG] Thử key 0x{key:02X}...{Colors.END}")
        
        try:
            decrypted = xor_crypt(data, key)
            urls = find_urls_aggressive(decrypted) if aggressive else find_urls(decrypted)
            
            if urls:
                found_count += 1
                debug_print(1, f"\n{Colors.GREEN}✅ [FOUND] Key 0x{key:02X} ({key}): {len(urls)} URL(s){Colors.END}")
                
                # Log chi tiết URL (level 2)
                if DEBUG_LEVEL >= 2:
                    for ui, (offset, url) in enumerate(urls[:5]):
                        debug_print(2, f"     {ui+1}. {Colors.YELLOW}{url}{Colors.END} (offset: 0x{offset:08X})")
                    if len(urls) > 5:
                        debug_print(2, f"     ... và {len(urls)-5} URL khác")
                
                results[key] = urls[:max_urls_per_key]
                if len(urls) > max_urls_per_key:
                    results[key].append((0, f"... và {len(urls) - max_urls_per_key} URL(s) khác"))
                    
        except Exception as e:
            if DEBUG_LEVEL >= 3:
                debug_print(3, f"{Colors.RED}    [ERROR] Key 0x{key:02X}: {e}{Colors.END}")
            continue
    
    # Hoàn tất progress bar
    debug_print(1, f"\r  ⏳ Tiến độ: [{'█'*40}] 100% ({total_keys}/{total_keys})")
    
    elapsed = time.time() - start_time
    debug_print(1, f"\n{Colors.GREEN}✅ Hoàn thành! Thời gian: {elapsed:.2f}s | Tìm thấy: {found_count}/{total_keys} keys có URL{Colors.END}")
    
    return results

# ========== HIỂN THỊ KẾT QUẢ ==========
def display_bruteforce_results(results: Dict[int, List[Tuple[int, str]]], 
                               data_length: int, start_key: int, end_key: int):
    clear_screen()
    print(f"{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}                    BRUTE-FORCE XOR KEY RESULTS{Colors.END}")
    print(f"{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"📊 Tổng số key đã thử: {end_key - start_key + 1}")
    print(f"🔑 Số key tìm thấy URL(s): {len(results)}")
    print(f"📁 Kích thước file: {data_length} bytes")
    print(f"{Colors.HEADER}{'='*80}{Colors.END}")
    
    if not results:
        print(f"{Colors.RED}❌ Không tìm thấy URL nào với bất kỳ key nào!{Colors.END}")
        return
    
    sorted_results = sorted(results.items(), key=lambda x: len(x[1]), reverse=True)
    
    for idx, (key, urls) in enumerate(sorted_results[:10], 1):
        print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}🔑 KEY 0x{key:02X} ({key} decimal):{Colors.END}")
        print(f"📊 Tổng URL tìm thấy: {len(urls)}")
        print(f"{Colors.DIM}{'-'*40}{Colors.END}")
        
        for url_idx, (offset, url) in enumerate(urls[:5], 1):
            if offset == 0 and url.startswith("..."):
                print(f"   {url}")
            else:
                print(f"   {url_idx}. {Colors.YELLOW}{url}{Colors.END}")
                print(f"      Offset: {Colors.DIM}0x{offset:08X}{Colors.END}")
        
        if len(urls) > 5:
            print(f"   ... và {len(urls) - 5} URL(s) khác")
    
    if len(sorted_results) > 10:
        print(f"\n{Colors.DIM}... và {len(sorted_results)-10} keys khác{Colors.END}")
    
    print(f"\n{Colors.HEADER}{'='*80}{Colors.END}")
    
    # Thống kê
    print(f"\n{Colors.BOLD}📈 TOP 5 KEYS:{Colors.END}")
    key_counts = {key: len(urls) for key, urls in results.items()}
    top_keys = sorted(key_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for key, count in top_keys:
        print(f"  • 0x{key:02X}: {count} URL(s)")
    
    if top_keys:
        best_key = top_keys[0][0]
        print(f"\n{Colors.GREEN}💡 KEY CÓ KHẢ NĂNG NHẤT: 0x{best_key:02X} ({best_key} decimal){Colors.END}")

# ========== CÁC HÀM KHÁC (giữ nguyên) ==========
def save_results_to_file(results: Dict[int, List[Tuple[int, str]]], 
                        filename: str, start_key: int, end_key: int):
    output_file = f"{filename}_bruteforce_results.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("                    BRUTE-FORCE XOR KEY RESULTS\n")
        f.write("=" * 80 + "\n")
        f.write(f"File: {filename}\n")
        f.write(f"Key range: 0x{start_key:02X} - 0x{end_key:02X}\n")
        f.write(f"Total keys tested: {end_key - start_key + 1}\n")
        f.write(f"Keys with URLs: {len(results)}\n")
        f.write("=" * 80 + "\n\n")
        
        sorted_results = sorted(results.items(), key=lambda x: len(x[1]), reverse=True)
        for key, urls in sorted_results:
            f.write(f"\n{'='*60}\n")
            f.write(f"KEY 0x{key:02X} ({key} decimal) - {len(urls)} URL(s):\n")
            f.write('-' * 60 + "\n")
            for offset, url in urls:
                if offset == 0 and url.startswith("..."):
                    f.write(f"{url}\n")
                else:
                    f.write(f"Offset: 0x{offset:08X}\n")
                    f.write(f"URL: {url}\n")
                    f.write("-" * 40 + "\n")
    
    debug_print(1, f"{Colors.GREEN}📄 Kết quả đã lưu vào: {output_file}{Colors.END}")

def patch_by_offset(data: bytearray, offset: int, old_bytes: bytes, new_bytes: bytes) -> bool:
    end = offset + len(old_bytes)
    if offset < 0 or end > len(data):
        return False
    if bytes(data[offset:end]) != old_bytes:
        return False
    data[offset:offset+len(new_bytes)] = new_bytes
    if len(new_bytes) < len(old_bytes):
        pad_len = len(old_bytes) - len(new_bytes)
        data[offset+len(new_bytes):end] = b"\x00" * pad_len
    return True

def backup_file(path: str) -> str:
    bak = path + ".bak"
    shutil.copy2(path, bak)
    return bak

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_menu():
    print(f"{Colors.HEADER}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}           URL PATCHER & BRUTE-FORCE TOOL (DEBUG MODE){Colors.END}")
    print(f"{Colors.HEADER}{'='*60}{Colors.END}")
    print(f"1. Chọn file để phân tích")
    print(f"2. Đặt XOR key (hiện tại: 0x{current_key:02X})")
    print(f"3. Liệt kê URLs với key hiện tại")
    print(f"4. Thay thế URLs")
    print(f"5. BRUTE-FORCE: Tìm key XOR tự động")
    print(f"6. Thoát")
    print(f"{Colors.HEADER}{'='*60}{Colors.END}")
    print(f"{Colors.DIM}📝 Debug level: {DEBUG_LEVEL} | Log file: {LOG_FILE}{Colors.END}")

# Biến toàn cục
current_file = ""
current_key = DEFAULT_KEY

def select_file():
    global current_file
    filename = input("Nhập đường dẫn file: ").strip()
    if not os.path.isfile(filename):
        print(f"{Colors.RED}❌ File không tồn tại!{Colors.END}")
        return False
    current_file = filename
    log_system_info(current_file)
    print(f"{Colors.GREEN}✅ Đã chọn file: {filename}{Colors.END}")
    return True

def set_key():
    global current_key
    try:
        key_input = input("Nhập XOR key (hex: 0x2E, decimal: 46): ").strip()
        if key_input.startswith('0x'):
            key = int(key_input, 16)
        else:
            key = int(key_input)
        current_key = key & 0xFF
        debug_print(1, f"{Colors.GREEN}✅ XOR key mới: 0x{current_key:02X} ({current_key}){Colors.END}")
    except ValueError:
        print(f"{Colors.RED}❌ Key không hợp lệ!{Colors.END}")

def list_urls():
    if not current_file:
        print(f"{Colors.RED}❌ Chưa chọn file!{Colors.END}")
        return
    try:
        with open(current_file, "rb") as f:
            encrypted = f.read()
        decrypted = xor_crypt(encrypted, key=current_key)
        urls = find_urls_aggressive(decrypted)
        if not urls:
            print(f"{Colors.YELLOW}❌ Không tìm thấy URL nào.{Colors.END}")
            return
        print(f"\n{Colors.GREEN}🔎 Tìm thấy {len(urls)} URL(s) với key 0x{current_key:02X}:{Colors.END}")
        for i, (pos, url) in enumerate(urls, 1):
            print(f"{i}. {Colors.YELLOW}{url}{Colors.END}")
            print(f"   Offset: {Colors.DIM}{hex(pos)}{Colors.END}")
        input("\nNhấn Enter để tiếp tục...")
    except Exception as e:
        print(f"{Colors.RED}❌ Lỗi: {e}{Colors.END}")

def replace_urls():
    if not current_file:
        print(f"{Colors.RED}❌ Chưa chọn file!{Colors.END}")
        return
    try:
        with open(current_file, "rb") as f:
            encrypted = f.read()
        decrypted = xor_crypt(encrypted, key=current_key)
        urls = find_urls_aggressive(decrypted)
        if not urls:
            print(f"{Colors.YELLOW}❌ Không tìm thấy URL nào để thay thế.{Colors.END}")
            return
        print(f"\n{Colors.GREEN}🔎 Tìm thấy {len(urls)} URL(s):{Colors.END}")
        for i, (pos, url) in enumerate(urls, 1):
            print(f"{i}. {Colors.YELLOW}{url}{Colors.END}")
        choice = input("\nChọn số URL để thay thế (ví dụ: 1 hoặc 1,3,4): ").strip()
        try:
            selected = [int(x.strip()) - 1 for x in choice.split(",") if x.strip()]
        except Exception:
            print(f"{Colors.RED}❌ Lựa chọn không hợp lệ.{Colors.END}")
            return
        confirm = input("Bạn có chắc muốn thay thế các URL này? (y/N): ").strip().lower()
        if confirm != 'y':
            print(f"{Colors.YELLOW}⚠️ Đã hủy thao tác.{Colors.END}")
            return
        bak_file = backup_file(current_file)
        debug_print(1, f"{Colors.CYAN}ℹ️ Đã tạo backup: {bak_file}{Colors.END}")
        patched = bytearray(decrypted)
        replacements_made = 0
        for idx in selected:
            if idx < 0 or idx >= len(urls):
                print(f"{Colors.RED}❌ Chỉ số không hợp lệ: {idx+1}{Colors.END}")
                continue
            offset, old_url = urls[idx]
            old_bytes = old_url.encode()
            new_url = input(f"\nNhập URL mới cho '{old_url}': ").strip()
            if not new_url:
                print("⚠️ Bỏ qua, không có URL mới.")
                continue
            new_bytes = new_url.encode()
            if len(new_bytes) > len(old_bytes):
                print(f"{Colors.RED}⚠️ URL mới dài hơn URL cũ! Bỏ qua.{Colors.END}")
                continue
            ok = patch_by_offset(patched, offset, old_bytes, new_bytes)
            if not ok:
                print(f"{Colors.RED}❌ Không thể patch tại offset {hex(offset)}{Colors.END}")
                continue
            debug_print(1, f"{Colors.GREEN}✅ Đã thay thế: '{old_url}' → '{new_url}'{Colors.END}")
            replacements_made += 1
        if replacements_made == 0:
            print(f"{Colors.YELLOW}⚠️ Không có thay thế nào được thực hiện.{Colors.END}")
            return
        encrypted_out = xor_crypt(bytes(patched), key=current_key)
        out_file = current_file.replace(".so", "_patched.so") if current_file.endswith('.so') else current_file + "_patched"
        with open(out_file, "wb") as f:
            f.write(encrypted_out)
        try:
            shutil.copystat(current_file, out_file)
        except Exception:
            pass
        print(f"\n{Colors.GREEN}📂 File mới đã được lưu: {out_file}{Colors.END}")
        print(f"{Colors.GREEN}✅ Đã thay thế {replacements_made} URL(s){Colors.END}")
    except Exception as e:
        print(f"{Colors.RED}❌ Lỗi: {e}{Colors.END}")

def brute_force_menu():
    global current_key
    if not current_file:
        print(f"{Colors.RED}❌ Chưa chọn file!{Colors.END}")
        input("Nhấn Enter để tiếp tục...")
        return
    try:
        with open(current_file, "rb") as f:
            data = f.read()
        print(f"\n{Colors.HEADER}⚙️  CẤU HÌNH BRUTE-FORCE{Colors.END}")
        print("-" * 40)
        start_input = input("Key bắt đầu (hex) [mặc định: 0x00]: ").strip()
        start_key = 0x00
        if start_input:
            start_key = int(start_input, 16) if start_input.startswith('0x') else int(start_input)
        end_input = input("Key kết thúc (hex) [mặc định: 0xFF]: ").strip()
        end_key = 0xFF
        if end_input:
            end_key = int(end_input, 16) if end_input.startswith('0x') else int(end_input)
        start_key = max(0, min(start_key, 0xFF))
        end_key = max(start_key, min(end_key, 0xFF))
        print("\n🔍 CHẾ ĐỘ TÌM KIẾM:")
        print("1. Cơ bản (http/https)")
        print("2. Nâng cao (cả domain)")
        mode = input("Chọn (1/2) [mặc định: 1]: ").strip()
        aggressive = (mode == '2')
        limit_input = input("Giới hạn URLs mỗi key [mặc định: 10]: ").strip()
        max_urls = 10 if not limit_input else int(limit_input)
        
        results = brute_force_urls(data, start_key, end_key, max_urls, aggressive)
        display_bruteforce_results(results, len(data), start_key, end_key)
        
        save_choice = input("\n💾 Lưu kết quả ra file? (y/N): ").strip().lower()
        if save_choice == 'y':
            save_results_to_file(results, current_file, start_key, end_key)
        if results:
            use_key = input("\n🔑 Dùng key từ kết quả? (y/N): ").strip().lower()
            if use_key == 'y':
                try:
                    key_input = input("Nhập key: ").strip()
                    new_key = int(key_input, 16) if key_input.startswith('0x') else int(key_input)
                    current_key = new_key & 0xFF
                    debug_print(1, f"{Colors.GREEN}✅ Đã đặt key: 0x{current_key:02X}{Colors.END}")
                except ValueError:
                    print(f"{Colors.RED}❌ Key không hợp lệ!{Colors.END}")
        input("\nNhấn Enter để tiếp tục...")
    except Exception as e:
        print(f"{Colors.RED}❌ Lỗi: {e}{Colors.END}")
        input("Nhấn Enter để tiếp tục...")

def main():
    clear_screen()
    while True:
        display_menu()
        choice = input("Lựa chọn (1-6): ").strip()
        if choice == '1':
            clear_screen()
            select_file()
        elif choice == '2':
            clear_screen()
            set_key()
        elif choice == '3':
            clear_screen()
            list_urls()
            clear_screen()
        elif choice == '4':
            clear_screen()
            replace_urls()
            input("\nNhấn Enter...")
            clear_screen()
        elif choice == '5':
            clear_screen()
            brute_force_menu()
            clear_screen()
        elif choice == '6':
            print(f"{Colors.GREEN}👋 Tạm biệt!{Colors.END}")
            debug_print(1, f"\n{Colors.CYAN}📝 Log file: {LOG_FILE}{Colors.END}")
            break
        else:
            print(f"{Colors.RED}❌ Lựa chọn không hợp lệ!{Colors.END}")
            input("Nhấn Enter...")
            clear_screen()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}✋ Đã dừng bởi người dùng.{Colors.END}")