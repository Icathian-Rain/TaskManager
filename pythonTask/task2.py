import argparse
import time

def main():
    parser = argparse.ArgumentParser(description='Run a command and print its output')
    parser.add_argument('--args1', type=str, help='args1')
    parser.add_argument('--args2', type=str, help='args2')
    args = parser.parse_args()

    print(f'Running command: {args}')

if __name__ == '__main__':
    main()
    time.sleep(2)