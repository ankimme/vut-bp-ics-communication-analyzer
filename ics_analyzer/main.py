#!/usr/bin/env python3

"""This file is used for starting up the application.

Author
------
Andrea Chimenti

Date
----
March 2022
"""

import sys
from PyQt6.QtWidgets import QApplication
from app import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
