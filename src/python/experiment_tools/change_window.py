__author__ = 'mauricio'
import sys

def change_file(filename, new_window):
    # read input file
    in_file = open(filename, "r", encoding='utf-8')
    lines = in_file.readlines()
    in_file.close()

    for idx, line in enumerate(lines):
        if line[0] == "W":
            lines[idx] = "W\t" + str(new_window) + "\n"
            break

    # write results ...
    out_file = open(filename, "w", encoding='utf-8')
    out_file.writelines(lines)
    out_file.close()


def main():
    if len(sys.argv) < 2:
        print("Usage")
        print("\tpython3 change_window.py window [input_files]")
        print("")
        print("Where:")
        print("\twindow:\t\tNew value for window parameter")
        print("\tinput_files:\tInput files to modify")
        return

    try:
        new_window = int(sys.argv[1])
    except:
        print("Invalid window parameter")
        return

    for filename in sys.argv[2:]:
        print("Processing: " + filename)
        change_file(filename, new_window)

main()