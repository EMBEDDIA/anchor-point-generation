import argparse


def filterout_multiwords(read_path, write_path):
    with open(write_path, 'w') as w_file:
        with open(read_path, "r") as r_file:
            for line in r_file:
                if len(line.split()) == 2:
                    w_file.write(line)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Merge two separated finalized dictionaries.')
    parser.add_argument('--read_path', help='Path to read file.')
    parser.add_argument('--write_path', help='Path to write file.')
    args = parser.parse_args()

    filterout_multiwords(args.read_path, args.write_path)
