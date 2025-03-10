import psutil

def is_powershell_running():
    for process in psutil.process_iter(['pid', 'name']):
        if "powershell" in process.info['name'].lower():
            return True  # PowerShell is still running
    return False  # PowerShell has finished

if is_powershell_running():
    print("PowerShell script is still running.")
else:
    print("PowerShell script has finished.")
