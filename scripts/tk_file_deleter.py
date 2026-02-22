#!/usr/bin/env python

from tkinter import *
from tkinter import messagebox
import os

root = None
e = None
errors = None


def handler():
    path = e.get()
    remove_non_dwg_files(path)
    remove_empty_dirs(path)


def remove_empty_dirs(path):
    if not os.path.isdir(path):
        return

    files = os.listdir(path)
    if len(files):
        for f in files:
            full_path = os.path.join(path, f)
            if os.path.isdir(full_path):
                remove_empty_dirs(full_path)

    files = os.listdir(path)
    if len(files) == 0:
        try:
            print("Removing empty folder: " + path)
            os.rmdir(path)
        except Exception as e:
            with open("errors.txt", "a") as fl:
                fl.write("Error: " + str(e) + "\n")
                fl.write(path + "\n")


def remove_non_dwg_files(path):
    for d, dirs, files in os.walk(path):
        for f in files:
            file_path = os.path.join(d, f)
            if not file_path.endswith(".dwg"):
                try:
                    print("Deleting file: " + file_path)
                    os.remove(file_path)
                except Exception as e:
                    with open("errors.txt", "a") as fl:
                        fl.write("Error: " + str(e) + "\n")
                        fl.write(file_path + "\n")


def quit():
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()


def on_closing():
    quit()


# Main program
def main():
    global root, e

    root = Tk()
    if root is not None:
        root.title("Non-dwg file deleter")

    e = Entry(root)
    e.pack(side="top", pady=20)

    e.delete(0, END)
    e.insert(0, "Enter full path to folder")

    b = Button(root, text="Go!", command=handler, takefocus=False, height=4, width=10)
    b.pack(side="top", pady=5)

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.resizable(width=FALSE, height=FALSE)
    root.geometry("{}x{}".format(320, 240))

    root.focus_set()
    root.mainloop()


if __name__ == "__main__":
    main()
