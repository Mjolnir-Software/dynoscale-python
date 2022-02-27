#!/usr/bin/env python3
import os
import sys
import time


def print_help():
    print("Usage: delay.py [delay in seconds] commands to run")
    print("Examples:")
    print('\tdelay.py 1.5 echo "One and half seconds later..."')
    print("\tdelay.py 10 curl https://httpbin.org/get")


if __name__ == '__main__':
    try:
        delay: float = float(sys.argv[1])
        command: str = ' '.join(sys.argv[2:])
        print(f"Will run `{command}` in {delay} seconds.")
        if os.fork() != 0:
            exit(0)
        time.sleep(delay)
        os.system(command)
    except Exception as e:
        print(f"Error parsing arguments: {e}", file=sys.stderr)
        print_help()
        exit(1)
