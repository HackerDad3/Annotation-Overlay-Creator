from time import time

def get_current_timestamp():
    # Get the current time in milliseconds
    current_timestamp_ms = int(time() * 1000)
    print(f"Current timestamp in milliseconds: {current_timestamp_ms}")

if __name__ == "__main__":
    get_current_timestamp()
