filename = input("Enter file path: ")
with open(filename, "r") as f:
    print(f.read())  # Path Traversal 취약점 예시
