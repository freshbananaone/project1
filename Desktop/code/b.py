with open("input.txt", "r", encoding="utf-8") as f:
    lines = [line.rstrip("\n") for line in f if line.strip()]

with open("output.txt", "w", encoding="utf-8") as f:
    for i, line in enumerate(lines, 1):
        f.write(f"{i}|{line}\n")