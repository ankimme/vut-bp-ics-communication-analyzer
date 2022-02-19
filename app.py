#!/usr/bin/env python3

import sys
import pandas as pd
from PyQt6.QtCore import QAbstractTableModel
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QWidget, QTableView, QTextEdit, QFileDialog, QErrorMessage
from PyQt6.QtGui import QIcon, QAction

import dsmanipulator.dsloader as dsl
import dsmanipulator.dscreator as dsc
import dsmanipulator.dsanalyzer as dsa
from dsmanipulator.utils.dataobjects import FileColumnNames


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ICS Analyzer")

        self.init_toolbar()

    def init_toolbar(self) -> None:
        """Initialize toolbar.
        """
        self.toolbar = self.addToolBar("Main toolbar")

        # LOAD CSV #
        load_csv_act = QAction(icon=QIcon('img/file.png'), text='Load CSV', parent=self)
        # https://www.iconfinder.com/icons/290138/document_extension_file_format_paper_icon
        load_csv_act.triggered.connect(self.load_csv)
        self.toolbar.addAction(load_csv_act)

        # EXIT #
        exit_act = QAction(icon=QIcon('img/exit.png'), text='Exit', parent=self)
        # https://www.iconfinder.com/icons/352328/app_exit_to_icon
        exit_act.triggered.connect(QApplication.instance().quit)  # TODO je to spravne?
        self.toolbar.addAction(exit_act)

    def load_csv(self):
        # TODO zde se bude otvirat nove okno a bude tu detekce sloupcu

        file_name, _ = QFileDialog.getOpenFileName(parent=self, caption='Open file', filter='CSV files (*.csv *.txt)')

        if file_name:
            try:
                self.df = dsl.load_data(file_name, FileColumnNames(
                    "TimeStamp", "Relative Time", "srcIP", "dstIP", "srcPort", "dstPort"))
                print(self.df)
            except Exception:  # TODO odstranit tuhle nehezkou vec
                error_dialog = QErrorMessage()
                error_dialog.showMessage('An error occurred while loading data')
                error_dialog.exec()


if __name__ == '__main__':
    app = QApplication([])
    # app = QApplication(sys.argv) # kdyby byly potreba command line argumenty

    window = MainWindow()
    window.show()

    app.exec()
