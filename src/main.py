"""Shell emulator with CLI configuration, XML logging and VFS support."""

import argparse
import getpass
import os
import socket
import sys
import tkinter as tk
from tkinter import font
import xml.etree.ElementTree as ET

from vfs import VirtualFileSystem

WINDOW_WIDTH = 720
WINDOW_HEIGHT = 450
FONT_SIZE = 11


class XmlCommandLogger:
    """Handles XML logging of executed emulator commands."""

    def __init__(self, log_path: str | None) -> None:
        """Initialize logger with optional file path."""
        self.log_path = log_path
        self.root_elem = ET.Element("history")

    def log_action(
        self,
        command_line: str,
        error_message: str | None = None,
    ) -> None:
        """Append command event to XML tree and save to disk if configured."""
        if not self.log_path:
            return

        entry = ET.SubElement(self.root_elem, "entry")
        cmd_elem = ET.SubElement(entry, "command")
        cmd_elem.text = command_line

        status_elem = ET.SubElement(entry, "status")
        status_elem.text = "error" if error_message else "success"

        err_elem = ET.SubElement(entry, "error")
        err_elem.text = error_message if error_message else "none"

        tree = ET.ElementTree(self.root_elem)
        ET.indent(tree, space="  ")
        tree.write(self.log_path, encoding="utf-8", xml_declaration=True)


class ShellEmulatorGUI:
    """GUI representation of the UNIX shell emulator."""

    def __init__(
        self,
        root: tk.Tk,
        vfs_path: str | None,
        log_path: str | None,
        script_path: str | None,
    ) -> None:
        """Initialize main window, widgets and parameters."""
        self.root = root
        self.vfs_path = vfs_path
        self.log_path = log_path
        self.script_path = script_path
        self.logger = XmlCommandLogger(log_path)
        self.vfs = VirtualFileSystem(vfs_path)

        self._setup_window_title()
        self._init_ui()
        self._print_debug_info()
        self._execute_start_script()

    def _setup_window_title(self) -> None:
        """Set window title according to current system credentials."""
        user = getpass.getuser()
        host = socket.gethostname()
        self.root.title(f"Эмулятор [{user}@{host}]")

    def _init_ui(self) -> None:
        """Construct terminal-like graphical interface."""
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg="#1e1e1e")

        text_font = font.Font(family="Consolas", size=FONT_SIZE)

        self.output_text = tk.Text(
            self.root,
            bg="#1e1e1e",
            fg="#cccccc",
            insertbackground="#ffffff",
            font=text_font,
            wrap=tk.WORD,
            state=tk.DISABLED,
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))

        input_frame = tk.Frame(self.root, bg="#1e1e1e")
        input_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        self.prompt_label = tk.Label(
            input_frame,
            text="$ ",
            fg="#00ff66",
            bg="#1e1e1e",
            font=text_font,
        )
        self.prompt_label.pack(side=tk.LEFT)

        self.entry = tk.Entry(
            input_frame,
            bg="#2d2d2d",
            fg="#ffffff",
            insertbackground="#ffffff",
            font=text_font,
            relief=tk.FLAT,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self._handle_input)
        self.entry.focus_set()

    def _print_debug_info(self) -> None:
        """Display configuration parameters and VFS load status."""
        self._print_line("--- Emulator Startup Configuration ---")
        self._print_line(f"VFS Path: {self.vfs_path}")
        self._print_line(f"Log Path: {self.log_path}")
        self._print_line(f"Script Path: {self.script_path}")
        if self.vfs.load_error:
            self._print_line(f"VFS Error: {self.vfs.load_error}")
            self._print_line("Fallback to in-memory default VFS hierarchy.")
        else:
            self._print_line("VFS mounted successfully.")
        self._print_line("--------------------------------------")

    def _execute_start_script(self) -> None:
        """Execute commands from start script skipping erroneous ones."""
        if not self.script_path:
            return
        if not os.path.exists(self.script_path):
            self._print_line(f"Warning: script not found: {self.script_path}")
            return

        with open(self.script_path, "r", encoding="utf-8") as script_file:
            for line in script_file:
                clean_line = line.strip()
                if not clean_line:
                    continue
                self._run_command_line(clean_line)

    def _print_line(self, text: str) -> None:
        """Append a new line to output area."""
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
        self.output_text.configure(state=tk.DISABLED)

    def _handle_input(self, event: tk.Event) -> None:
        """Read input string from entry field and process command."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self._run_command_line(line)

    def _run_command_line(self, line: str) -> None:
        """Simulate shell dialogue and log results."""
        self._print_line(f"$ {line}")
        tokens = line.strip().split()
        if not tokens:
            return

        command = tokens[0]
        args = tokens[1:]
        err = self._dispatch_command(command, args)
        self.logger.log_action(line, err)

    def _dispatch_command(
        self,
        command: str,
        args: list[str],
    ) -> str | None:
        """Route command to handler. Return error message if any."""
        if command == "exit":
            self.root.destroy()
            sys.exit(0)
        elif command in ("ls", "cd"):
            self._print_line(f"Stub: command '{command}' called with: {args}")
            return None

        err_msg = f"command not found: {command}"
        self._print_line(f"Error: {err_msg}")
        return err_msg


def parse_arguments() -> argparse.Namespace:
    """Parse CLI arguments for emulator configuration."""
    parser = argparse.ArgumentParser(description="UNIX Shell Emulator")
    parser.add_argument("--vfs", dest="vfs", help="Path to VFS archive")
    parser.add_argument("--log", dest="log", help="Path to XML log file")
    parser.add_argument(
        "--script",
        dest="script",
        help="Path to startup script",
    )
    return parser.parse_args()


def main() -> None:
    """Run GUI shell application loop with parsed CLI arguments."""
    args = parse_arguments()
    root = tk.Tk()
    ShellEmulatorGUI(
        root=root,
        vfs_path=args.vfs,
        log_path=args.log,
        script_path=args.script,
    )
    root.mainloop()


if __name__ == "__main__":
    main()