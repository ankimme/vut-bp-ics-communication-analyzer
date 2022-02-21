#!/usr/bin/env python3

import sys
import os
import pandas as pd
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QWidget, QTableView, QTextEdit, QFileDialog, QErrorMessage, QToolBar, QGridLayout, QPushButton
from PyQt6.QtGui import QIcon, QAction, QPalette, QColor

import dsmanipulator.dsloader as dsl
import dsmanipulator.dscreator as dsc
import dsmanipulator.dsanalyzer as dsa
from dsmanipulator.utils.dataobjects import FileColumnNames


# https://doc.qt.io/qtforpython/examples/example_external__pandas.html
class PandasModel(QAbstractTableModel):
    """A model to interface a Qt view with pandas dataframe """

    def __init__(self, dataframe: pd.DataFrame, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._dataframe = dataframe

    def rowCount(self, parent=QModelIndex()) -> int:
        """ Override method from QAbstractTableModel

        Return row count of the pandas DataFrame
        """
        if parent == QModelIndex():
            return len(self._dataframe)
        else:
            return 0

    def columnCount(self, parent=QModelIndex()) -> int:
        """Override method from QAbstractTableModel

        Return column count of the pandas DataFrame
        """
        if parent == QModelIndex():
            return len(self._dataframe.columns)
        else:
            return 0

    def data(self, index: QModelIndex, role=Qt.ItemDataRole):
        """Override method from QAbstractTableModel

        Return data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._dataframe.iloc[index.row(), index.column()])

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole):
        """Override method from QAbstractTableModel

        Return dataframe index as vertical header data and columns as horizontal header data.
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._dataframe.columns[section])

            if orientation == Qt.Orientation.Vertical:
                return str(self._dataframe.index[section])

        return None


class InfoLabel(QLabel):
    """A label showing formatted information."""

    def __init__(self, property: str, parent: QWidget = None):
        """Init InfoLabel class with empty value.

        Parameters
        ----------
        property : str
            Property name.
        parent : QWidget, optional
            Parent.
        """
        super().__init__(parent)
        self._property = property

        self.set_value("")

    # TODO prepsat na python 3.10 case matching a multiple types int | str
    def set_value(self, new_value):
        """Set value of label without changing property.

        Parameters
        ----------
        new_value : str | int | float
            A new value the label will display.
        """
        new_value = 2.498746546987  # TODO delete

        if type(new_value) == float:
            self.setText(f"{self._property}: {new_value:.3f}")
        else:
            self.setText(f"{self._property}: {new_value}")


class MainWindow(QMainWindow):
    """Main application window.

    Attributes
    ----------
    actions : dict[str, QAction]
        Actions used in menu and toolbar.
    toolbar : QToolBar
        Toolbar object.
    file_name_label : QLabel
        Label in the top left corner with file name.
    df : pd.DataFrame
        Main dataframe.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ICS Analyzer")
        self.setMinimumSize(800, 500)

        self.actions = self.create_actions()

        self.init_toolbar()

        main_layout = QVBoxLayout()

        self.file_name_label = QLabel()
        main_layout.addWidget(self.file_name_label)

        # LAYOUT TOP #
        info_panel_layout = QGridLayout()

        # info_panel_layout.setHorizontalSpacing(20)

        info_panel_layout.addWidget(InfoLabel("a"), 0, 0)

        for i in range(info_panel_layout.columnCount()):
            info_panel_layout.setColumnStretch(i, 1)

        # info_panel_layout.addWidget(QPushButton("Button at (2, 0)"), 2, 0)

        # info_panel_layout.addWidget(QPushButton("Button at (2, 1)"), 2, 1)

        # info_panel_layout.addWidget(QPushButton("Button at (2, 2)"), 2, 2)

        info_panel_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addLayout(info_panel_layout)

        # LAYOUT BOTTOM #
        self.df_table_view = QTableView()
        self.df_table_view.horizontalHeader().setStretchLastSection(True)
        self.df_table_view.setAlternatingRowColors(True)
        self.df_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        main_layout.addWidget(self.df_table_view)

        centralWidget = QWidget()
        centralWidget.setLayout(main_layout)
        self.setCentralWidget(centralWidget)

    # def create_actions(self) -> dict[str, QAction]: # TODO uncomment on python 3.9

    def create_actions(self):
        """Define QActions.

        Returns
        -------
        dict[str, QAction]
            Actions used in menu and toolbar.
        """
        actions = dict()

        # LOAD CSV #
        actions['Load CSV'] = QAction(icon=QIcon('img/file.png'), text='Load CSV', parent=self)
        # https://www.iconfinder.com/icons/290138/document_extension_file_format_paper_icon
        actions["Load CSV"].triggered.connect(self.load_csv)

        # EXIT #
        actions["Exit"] = QAction(icon=QIcon('img/exit.png'), text='Exit', parent=self)
        # https://www.iconfinder.com/icons/352328/app_exit_to_icon
        actions["Exit"].triggered.connect(QApplication.instance().quit)  # TODO je to spravne?

        return actions

    def init_toolbar(self) -> None:
        """Initialize toolbar.

        Add all defined actions to toolbar.

        Notes
        -----
        Should be called after create_actions().
        """
        self.toolbar = QToolBar("Main toolbar")
        self.addToolBar(self.toolbar)

        for action in self.actions.values():
            self.toolbar.addAction(action)

    def load_csv(self) -> None:
        # TODO zde se bude otvirat nove okno a bude tu detekce sloupcu

        file_path, _ = QFileDialog.getOpenFileName(parent=self, caption='Open file', filter='CSV files (*.csv *.txt)')

        if file_path:
            try:
                self.df = dsl.load_data(file_path, FileColumnNames(
                    "TimeStamp", "Relative Time", "srcIP", "dstIP", "srcPort", "dstPort"))
                model = PandasModel(self.df)
                self.df_table_view.setModel(model)
                self.file_name_label.setText(os.path.basename(file_path))
            except Exception:  # TODO odstranit tuhle nehezkou vec
                error_dialog = QErrorMessage()
                error_dialog.showMessage('An error occurred while loading data')
                error_dialog.exec()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
