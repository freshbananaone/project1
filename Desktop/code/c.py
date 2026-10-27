from pathlib import Path

input_file = "input.txt"
output_file = "output.txt"

text = Path(input_file).read_text(encoding="utf-8")

# Tách theo dòng phân cách dài
blocks = text.split("=" * 20)

results = []

for block in blocks:
    lines = [line.strip() for line in block.splitlines() if line.strip()]

    # Lấy dòng cuối cùng của mỗi block
    if lines:
        results.append(lines[-1])

Path(output_file).write_text("\n".join(results), encoding="utf-8")

print(f"Đã xử lý {len(results)} dòng.")