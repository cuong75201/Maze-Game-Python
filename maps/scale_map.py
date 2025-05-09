import json

# Đọc tệp JSON
try:
    with open('map1.json', 'r') as file:
        map_data = json.load(file)
except FileNotFoundError:
    print("Lỗi: Không tìm thấy tệp 'map1.json'. Vui lòng kiểm tra lại.")
    exit(1)
except json.JSONDecodeError:
    print("Lỗi: Tệp 'map1.json' không đúng định dạng JSON.")
    exit(1)

# Nhân đôi kích thước của tile_size
map_data['tile_size'] = [size * 2 for size in map_data['tile_size']]

# Nhân đôi kích thước scale của mỗi vật thể trong tilemap
for key in map_data['tilemap']:
    map_data['tilemap'][key]['scale'] = [size * 2 for size in map_data['tilemap'][key]['scale']]

# Lưu lại vào tệp mới
try:
    with open('map1_scaled.json', 'w') as file:
        json.dump(map_data, file, indent=2)
    print("Đã tăng kích thước các vật thể lên 2 lần và lưu vào 'map1_scaled.json'.")
except Exception as e:
    print(f"Lỗi khi lưu tệp: {e}")