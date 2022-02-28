#!/usr/bin/env python3

import csv
import sys
from bidict import bidict
import numpy as np
import pandas as pd

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QAbstractListModel
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QWidget, QTableView, QTextEdit, QFileDialog, QErrorMessage, QToolBar, QGridLayout, QPushButton, QTabWidget, QDialog, QDialogButtonBox, QStackedLayout, QWizard, QComboBox, QWizardPage, QFormLayout, QCheckBox, QListWidget, QListView, QHBoxLayout, QRadioButton, QButtonGroup
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

        tabs = QTabWidget()
        # tabs.setTabPosition(QTabWidget.West)
        # tabs.setMovable(True)

        primary_widget = QWidget()
        primary_layout = self.create_primary_layout()
        primary_widget.setLayout(primary_layout)

        secondary_widget = QWidget()
        secondary_layout = self.create_secondary_layout()
        secondary_widget.setLayout(secondary_layout)

        tabs.addTab(primary_widget, "Primary view")
        tabs.addTab(secondary_widget, "Secondary view")
        self.setCentralWidget(tabs)

        dialog = OpenCsv()  # TODO delete
        dialog.exec()

    def create_primary_layout(self) -> QVBoxLayout:
        # TODO add vars to doc
        layout = QVBoxLayout()

        # add file name info on top
        self.file_name_label = QLabel()
        layout.addWidget(self.file_name_label)

        # LAYOUT TOP - INFORMATION PANEL #
        info_panel_layout = QGridLayout()

        self.entries = InfoLabel("Entries")
        info_panel_layout.addWidget(self.entries, 0, 0)

        self.column_count = InfoLabel("Columns")
        info_panel_layout.addWidget(self.column_count, 0, 1)

        # set maximum stretch for all columns
        for i in range(info_panel_layout.columnCount()):
            info_panel_layout.setColumnStretch(i, 1)

        info_panel_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(info_panel_layout)

        # LAYOUT BOTTOM - DATAFRAME VIEW #
        self.df_table_view = QTableView()
        self.df_table_view.horizontalHeader().setStretchLastSection(True)
        self.df_table_view.setAlternatingRowColors(True)
        self.df_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        layout.addWidget(self.df_table_view)

        return layout

    def create_secondary_layout(self) -> QVBoxLayout:
        # TODO add vars to doc
        layout = QVBoxLayout()

        layout.addWidget(QLabel("zakladni info"))
        layout.addWidget(QLabel("filtry"))
        layout.addWidget(QLabel("menu pro tvorbu grafu"))
        # layout.addWidget(QLabel("data"))
        # add file name info on top
        # self.file_name_label = QLabel() TODO duplicate label
        # layout.addWidget(self.file_name_label)

        # LAYOUT TOP - INFORMATION PANEL #
        # info_panel_layout = QGridLayout()

        # LAYOUT BOTTOM - DATAFRAME VIEW # # TODO RENAME
        self.dff_table_view = QTableView()
        # self.dff_table_view.horizontalHeader().setStretchLastSection(True)
        # self.dff_table_view.setAlternatingRowColors(True)
        # self.dff_table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        layout.addWidget(self.dff_table_view)

        return layout

    def create_actions(self) -> dict[str, QAction]:
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
            dialog = OpenCsv()
            dialog.exec()
            # try:
            #     dialog = OpenCsv()
            #     dialog.exec()

            #     self.df = dsl.load_data(file_path, FileColumnNames(
            #         "TimeStamp", "Relative Time", "srcIP", "dstIP", "srcPort", "dstPort"))
            #     model = PandasModel(self.df)
            #     self.df_table_view.setModel(model)
            #     self.file_name_label.setText(os.path.basename(file_path))
            #     self.update_stats()
            # except Exception:  # TODO odstranit tuhle nehezkou vec
            #     error_dialog = QErrorMessage()
            #     error_dialog.showMessage('An error occurred while loading data')
            #     error_dialog.exec()

    def update_stats(self) -> None:
        # TODO doc
        self.entries.set_value(len(self.df.index))
        self.column_count.set_value(len(self.df.columns))


class OpenCsv(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Load data from CSV")

        stacked_layout = QStackedLayout()

        # PAGE 1 - set delimiter #

        self.page1 = QWidget()
        layout1 = QVBoxLayout()
        layout1.addWidget(QLabel("ahoj"))
        layout1.addWidget(QLabel("ahoj"))
        self.page1.setLayout(layout1)

        # delimiter = dsl.detect_delimiter()

        # PAGE 2 - set column data types #

        self.page2 = QWidget()
        layout2 = QVBoxLayout()
        layout2.addWidget(QLabel("ahoj"))
        layout2.addWidget(QLabel("ahoj"))
        layout2.addWidget(QLabel("ahoj"))
        self.page2.setLayout(layout2)

        # Add pages to stacked widget #
        stacked_layout.addWidget(self.page1)
        stacked_layout.addWidget(self.page2)

        self.setLayout(stacked_layout)

        # QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel

        # self.buttonBox = QDialogButtonBox(QBtn)
        # self.buttonBox.accepted.connect(self.accept)
        # self.buttonBox.rejected.connect(self.reject)

        # self.layout = QVBoxLayout()

        # dsl.

        # message = QLabel("Something happened, is that OK?")
        # self.layout.addWidget(message)
        # self.layout.addWidget(self.buttonBox)
        # self.setLayout(self.layout)


class OpenCsvWizard(QWizard):

    def __init__(self, file_name: str, parent: QWidget = None):
        super().__init__(parent)

        self.setWindowTitle("Load data from CSV")
        self.dialect = dsl.detect_dialect(file_name)
        self.addPage(Page1(file_name=file_name, dialect=self.dialect, parent=self))
        self.addPage(Page2(file_name=file_name, dialect=self.dialect, parent=self))


class Page1(QWizardPage):

    def __init__(self, file_name: str, dialect: csv.Dialect, parent: QWidget = None):
        super().__init__(parent)
        self.file_name = file_name
        self.dialect = dialect

        self.setSubTitle("Set CSV dialect")

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # Delimiter #
        self.delimiter_line_edit = QLineEdit()
        self.delimiter_line_edit.setMaxLength(1)
        self.delimiter_line_edit.textEdited.connect(self.delimiter_line_edit_changed)
        form_layout.addRow(QLabel("Delimiter:"), self.delimiter_line_edit)

        """ TODO uncomment
        # Quote char #
        self.quote_char_line_edit = QLineEdit()
        self.quote_char_line_edit.setMaxLength(1)
        self.quote_char_line_edit.textEdited.connect(self.quote_char_line_edit_changed)
        form_layout.addRow(QLabel("Quote character:"), self.quote_char_line_edit)

        # Escape char #
        self.escape_char_line_edit = QLineEdit()
        self.escape_char_line_edit.setMaxLength(1)
        self.escape_char_line_edit.textEdited.connect(self.escape_char_line_edit_changed)
        form_layout.addRow(QLabel("Escape character:"), self.escape_char_line_edit)

        # Doublequote #
        self.doublequote_check_box = QCheckBox()
        self.doublequote_check_box.toggled.connect(self.doublequote_check_box_changed)
        form_layout.addRow(QLabel("Double quote:"), self.doublequote_check_box)

        # TODO engine selection c/python
        """

        layout.addLayout(form_layout)

        layout.addWidget(QLabel("Columns:"))

        self.columns_view = QListView()
        self.columns_model = ListModel()
        self.columns_view.setModel(self.columns_model)

        layout.addWidget(self.columns_view)

        # Warning #
        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("QLabel { color: red }")
        layout.addWidget(self.warning_label)

        self.setLayout(layout)

        # self.dialect.strict = True # TODO enable?

    def initializePage(self):
        self.delimiter_line_edit.setText(self.dialect.delimiter)
        """ TODO uncomment
        self.doublequote_check_box.setChecked(self.dialect.doublequote)
        self.escape_char_line_edit.setText(self.dialect.escapechar)
        self.quote_char_line_edit.setText(self.dialect.quotechar)
        """
        self.update_column_preview()

    def delimiter_line_edit_changed(self):
        self.dialect.delimiter = self.delimiter_line_edit.text() or None
        self.update_column_preview()

    """ TODO uncomment
    def quote_char_line_edit_changed(self):
        self.dialect.quotechar = self.quote_char_line_edit.text() or None
        self.update_column_preview()

    def escape_char_line_edit_changed(self):
        self.dialect.escapechar = self.escape_char_line_edit.text() or None
        self.update_column_preview()

    def doublequote_check_box_changed(self):
        self.dialect.doublequote = self.doublequote_check_box.isChecked()
        self.update_column_preview()
    """

    def update_column_preview(self):
        try:
            self.columns_model.items = list(dsl.detect_columns(self.file_name, self.dialect).keys())
            self.warning_label.clear()
            self.completeChanged.emit()
        except (pd.errors.ParserError, TypeError):
            self.columns_model.items = []
            self.warning_label.setText("Could not parse csv columns with given dialect.")
            self.completeChanged.emit()

        self.columns_model.layoutChanged.emit()

    def isComplete(self) -> bool:
        return bool(self.delimiter_line_edit.text()) and bool(self.columns_model.items)


class ListModel(QAbstractListModel):
    def __init__(self, *args, items=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = items or []

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.items[index.row()]

    def rowCount(self, index):
        return len(self.items)


class Page2(QWizardPage):
    def __init__(self, file_name: str, dialect: csv.Dialect, parent: QWidget = None):
        super().__init__(parent)
        self.file_name = file_name
        self.dialect = dialect
        self.layout = QVBoxLayout()

        # self.warning_label = QLabel()
        # self.warning_label.setStyleSheet("QLabel { color: red }")
        # self.layout.addWidget(self.warning_label)

        self.setLayout(self.layout)

    def initializePage(self) -> None:
        g1 = QButtonGroup(self)
        g2 = QButtonGroup(self)
        for col_name, col_type in dsl.detect_columns(self.file_name, self.dialect).items():
            row = QHBoxLayout()
            row.addWidget(QLabel(col_name))

            # w = TypeComboBox(col_type)
            # w.currentIndexChanged.connect(self.type_changed)
            row.addWidget(TypeComboBox(col_type))

            row.addWidget(QLabel(str(col_type)))

            r1 = QRadioButton()
            g1.addButton(r1)
            row.addWidget(r1)

            r2 = QRadioButton()
            g2.addButton(r2)
            row.addWidget(r2)

            self.layout.addLayout(row)

    def cleanupPage(self) -> None:
        self.layout = QVBoxLayout()

    def type_changed(self):
        try:
            dsl.load_data(self.file_name, self.dialect)

            self.warning_label.clear()
        except:
            self.warning_label.setText("Invalid based on first 100 rows")


class TypeComboBox(QComboBox):
    def __init__(self, type, parent: QWidget = None):
        super().__init__(parent)
        types = ['object', 'int', 'float', 'bool', 'datetime', 'timedelta', 'category']
        self.insertItems(0, types)  # TODO and so on
        self.setCurrentIndex(types.index(type))


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # window = MainWindow()
    # window.show()

    wizard = OpenCsvWizard("data/mega104-14-12-18-ioa.csv")
    wizard.show()

    app.exec()
