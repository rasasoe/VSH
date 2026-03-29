import subprocess
filename = input("Enter filename: ")
subprocess.run(["cat", filename], shell=True)  # Command Injection 취약점 예시
