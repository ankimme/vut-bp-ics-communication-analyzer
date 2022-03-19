#!/usr/bin/env python3

# region Imports

import csv
import os
import sys
import traceback
from typing import Any
from bidict import bidict
import numpy as np
import pandas as pd

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QAbstractListModel, pyqtSlot, QAbstractItemModel
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
    QTableView,
    QTextEdit,
    QFileDialog,
    QErrorMessage,
    QToolBar,
    QGridLayout,
    QPushButton,
    QTabWidget,
    QDialog,
    QDialogButtonBox,
    QStackedLayout,
    QWizard,
    QComboBox,
    QWizardPage,
    QFormLayout,
    QCheckBox,
    QListWidget,
    QListView,
    QHBoxLayout,
    QRadioButton,
    QButtonGroup,
    QAbstractButton,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
)
from PyQt6.QtGui import QIcon, QAction, QPalette, QColor

import dsmanipulator.dsloader as dsl
import dsmanipulator.dscreator as dsc
import dsmanipulator.dsanalyzer as dsa
from dsmanipulator.utils.dataobjects import Direction, FileColumnNames, Station

# endregion


# region Models


# https://doc.qt.io/qtforpython/examples/example_external__pandas.html
class DataFrameModel(QAbstractTableModel):
    """A model to interface a Qt view with pandas dataframe"""

    def __init__(self, dataframe: pd.DataFrame, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._df = dataframe

    def rowCount(self, parent=QModelIndex()) -> int:
        """Override method from QAbstractTableModel

        Return row count of the pandas DataFrame
        """
        if parent == QModelIndex():
            return len(self._df)
        else:
            return 0

    def columnCount(self, parent=QModelIndex()) -> int:
        """Override method from QAbstractTableModel

        Return column count of the pandas DataFrame
        """
        if parent == QModelIndex():
            return len(self._df.columns)
        else:
            return 0

    def data(self, index: QModelIndex, role=Qt.ItemDataRole):
        """Override method from QAbstractTableModel

        Return data cell from the pandas DataFrame
        """
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._df.iloc[index.row(), index.column()])

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole):
        """Override method from QAbstractTableModel

        Return dataframe index as vertical header data and columns as horizontal header data.
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._df.columns[section])

            if orientation == Qt.Orientation.Vertical:
                return str(self._df.index[section])

        return None

    def sort(self, column: int, order: Qt.SortOrder = ...) -> None:
        colname = self._df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(colname, ascending=order == Qt.SortOrder.AscendingOrder, inplace=True)
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()


class ListModel(QAbstractListModel):
    """AbstractionListModel of a simple list."""

    def __init__(self, *args, items=None, **kwargs) -> None:
        """Initialize a ListModel object.

        Parameters
        ----------
        items : list[Any], optional
            List of items of any type.
        """
        super().__init__(*args, **kwargs)
        self.items = items or []

    def data(self, index, role) -> Any:
        if role == Qt.ItemDataRole.DisplayRole:
            return self.items[index.row()]

    def rowCount(self, index) -> int:
        return len(self.items)


# endregion


# region Open CSV wizard


class OpenCsvWizard(QWizard):
    """Wizard dialog used for getting the dialect and settings of a csv file.

    Attributes
    ----------
    file_name : str
        Name of CSV file.
    dialect : csv.Dialect
        Dialect of CSV.
    col_types_by_user : dict[str, TypeComboBox]
        Key : Name of column in CSV file.
        Value : Combobox object in UI.
    """

    def __init__(self, file_name: str, parent: QWidget = None) -> None:
        """Initialize OpenCsvWizard class and create button layout.

        Parameters
        ----------
        file_name : str
            Name of CSV file.
        parent : QWidget, optional
            Parent widget, by default None
        file_col_names : FileColumnNames
            Real names of predefined columns.
        """
        super().__init__(parent)

        self.setWindowTitle("Load data from CSV")

        # pages can use and update this variables
        self.file_name: str = file_name
        self.dialect: csv.Dialect = dsl.detect_dialect(file_name)  # TODO exceptions kdyz bude chybny vstup
        self.col_types_by_user: dict[str, TypeComboBox]
        self.fcn: FileColumnNames

        self.addPage(PageSetDelimiter(parent=self))
        self.addPage(PageSetDataTypes(parent=self))

        # buttons layout
        buttons_layout = []
        buttons_layout.append(QWizard.WizardButton.CancelButton)
        buttons_layout.append(QWizard.WizardButton.NextButton)
        buttons_layout.append(QWizard.WizardButton.FinishButton)
        self.setButtonLayout(buttons_layout)

    def get_csv_settings(self) -> tuple[csv.Dialect, dict[str, str], FileColumnNames]:
        """

        Returns
        -------
        dialect : csv.Dialect
            Dialect of CSV.
        col_types : dict[str, str]
            Key : Name of column in CSV file.
            Value : Data type of column. Selected by user.
        file_col_names : FileColumnNames
            Real names of predefined columns.

        """
        col_types: dict[str, str] = {key: value.currentText() for key, value in self.col_types_by_user.items()}
        return self.dialect, col_types, self.fcn


class PageSetDelimiter(QWizardPage):
    """Page used to set delimiter of csv file."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setSubTitle("Set CSV delimiter")

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

        # Columns preview #
        layout.addWidget(QLabel("Columns:"))
        self.columns_view = QListView()
        self.columns_model = ListModel()
        self.columns_view.setModel(self.columns_model)
        layout.addWidget(self.columns_view)

        # Warning #
        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("QLabel { color: red }")
        layout.addWidget(self.warning_label)

        # self.dialect.strict = True # TODO enable?
        self.setLayout(layout)

    def initializePage(self) -> None:
        self.delimiter_line_edit.setText(self.wizard().dialect.delimiter)
        # self.doublequote_check_box.setChecked(self.dialect.doublequote) # TODO delete
        # self.escape_char_line_edit.setText(self.dialect.escapechar)
        # self.quote_char_line_edit.setText(self.dialect.quotechar)
        self.update_column_preview()

    @pyqtSlot()
    def delimiter_line_edit_changed(self) -> None:
        self.wizard().dialect.delimiter = self.delimiter_line_edit.text() or None
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

    def update_column_preview(self) -> None:
        """Update preview of columns based on delimiter change."""
        try:
            self.columns_model.items = list(dsl.detect_columns(self.wizard().file_name, self.wizard().dialect).keys())
            self.warning_label.clear()
            self.completeChanged.emit()
        except (pd.errors.ParserError, TypeError):
            self.columns_model.items = []
            self.warning_label.setText("Could not parse csv columns.")
            self.completeChanged.emit()

        self.columns_model.layoutChanged.emit()

    def isComplete(self) -> bool:
        """Validates delimiter validity.

        Returns
        -------
        bool
            Columns were parsed correctly.
        """
        return bool(self.delimiter_line_edit.text()) and bool(self.columns_model.items)


class PageSetDataTypes(QWizardPage):
    """_summary_

    Attributes
    ----------
    goups : bidict[str, QButtonGroup]
        Key : Group name.
        Value : Assigned group.
    csv_cols : dict[str, dtype]
        Key : CSV column name.
        Value : Automatically detected CSV column data type.
    cols_ids : dict[int, str]
        Key : ID of column in UI.
        Value : Column name in CSV.
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.grid_layout = QGridLayout(self)

        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("QLabel { color: red }")

        self.layout.addLayout(self.grid_layout)
        self.layout.addWidget(self.warning_label)
        self.setLayout(self.layout)

        self.groups = bidict(
            {
                "timestamp": QButtonGroup(self),
                "rel_time": QButtonGroup(self),
                "src_ip": QButtonGroup(self),
                "src_port": QButtonGroup(self),
                "dst_ip": QButtonGroup(self),
                "dst_port": QButtonGroup(self),
            }
        )

        for group in self.groups.values():
            group.buttonToggled.connect(self.radio_button_changed)
            # group.buttonClicked.connect(self.radio_button_changed)
            # group.buttonClicked.connect(self.completeChanged.emit)

    def initializePage(self) -> None:
        self.wizard().fcn = FileColumnNames()

        # grid header
        self.grid_layout.addWidget(QLabel("Name"), 0, 0, Qt.AlignmentFlag.AlignCenter)
        self.grid_layout.addWidget(QLabel("Data type"), 0, 1, Qt.AlignmentFlag.AlignCenter)

        self.grid_layout.addWidget(QLabel("Time stamp"), 0, 2, Qt.AlignmentFlag.AlignCenter)
        b = QPushButton("Reset")
        b.clicked.connect(lambda: self.deselect_group(self.groups["timestamp"]))
        b.clicked.connect(lambda: self.clear_file_col_names(self.groups["timestamp"]))
        self.grid_layout.addWidget(b, 1, 2, Qt.AlignmentFlag.AlignCenter)

        self.grid_layout.addWidget(QLabel("Rel time"), 0, 3, Qt.AlignmentFlag.AlignCenter)
        b = QPushButton("Reset")
        b.clicked.connect(lambda: self.deselect_group(self.groups["rel_time"]))
        b.clicked.connect(lambda: self.clear_file_col_names(self.groups["rel_time"]))
        self.grid_layout.addWidget(b, 1, 3, Qt.AlignmentFlag.AlignCenter)

        self.grid_layout.addWidget(QLabel("SRC IP"), 0, 4, Qt.AlignmentFlag.AlignCenter)
        b = QPushButton("Reset")
        b.clicked.connect(lambda: self.deselect_group(self.groups["src_ip"]))
        b.clicked.connect(lambda: self.clear_file_col_names(self.groups["src_ip"]))
        self.grid_layout.addWidget(b, 1, 4, Qt.AlignmentFlag.AlignCenter)

        self.grid_layout.addWidget(QLabel("SRC Port"), 0, 5, Qt.AlignmentFlag.AlignCenter)
        b = QPushButton("Reset")
        b.clicked.connect(lambda: self.deselect_group(self.groups["src_port"]))
        b.clicked.connect(lambda: self.clear_file_col_names(self.groups["src_port"]))
        self.grid_layout.addWidget(b, 1, 5, Qt.AlignmentFlag.AlignCenter)

        self.grid_layout.addWidget(QLabel("DST IP"), 0, 6, Qt.AlignmentFlag.AlignCenter)
        b = QPushButton("Reset")
        b.clicked.connect(lambda: self.deselect_group(self.groups["dst_ip"]))
        b.clicked.connect(lambda: self.clear_file_col_names(self.groups["dst_ip"]))
        self.grid_layout.addWidget(b, 1, 6, Qt.AlignmentFlag.AlignCenter)

        self.grid_layout.addWidget(QLabel("DST Port"), 0, 7, Qt.AlignmentFlag.AlignCenter)
        b = QPushButton("Reset")
        b.clicked.connect(lambda: self.deselect_group(self.groups["dst_port"]))
        b.clicked.connect(lambda: self.clear_file_col_names(self.groups["dst_port"]))
        self.grid_layout.addWidget(b, 1, 7, Qt.AlignmentFlag.AlignCenter)

        # grid rest
        self.csv_cols = dsl.detect_columns(self.wizard().file_name, self.wizard().dialect)
        self.cols_ids = {}
        self.wizard().col_types_by_user = {}
        row_offset, col_offset = 2, 2
        for i, (col_name, col_type) in enumerate(self.csv_cols.items(), 2):
            self.grid_layout.addWidget(QLabel(col_name), i, 0)

            type_combo_box = TypeComboBox(col_type)
            # type_combo_box.currentTextChanged.connect(self.validate_user_settings)

            type_combo_box.currentTextChanged.connect(self.completeChanged.emit)

            self.grid_layout.addWidget(type_combo_box, i, 1)

            self.wizard().col_types_by_user[col_name] = type_combo_box

            # for radio buttons
            self.cols_ids[i - 2] = col_name

            for j, group in enumerate(self.groups.values()):
                b = QRadioButton()
                group.addButton(b, i - 2)
                self.grid_layout.addWidget(b, i, j + 2, Qt.AlignmentFlag.AlignCenter)  # magic offset for columns

        self.autodetect_file_col_names()
        self.grid_layout.update()
        self.completeChanged.emit()

    def autodetect_file_col_names(self):
        for col_id, name in reversed(self.cols_ids.items()):
            name = name.lower()
            group = None

            if "stamp" in name:
                group = self.groups["timestamp"]
            elif "rel" in name:
                group = self.groups["rel_time"]
            elif "time" in name:
                group = self.groups["timestamp"]
            elif any(x in name for x in ["src", "source"]):
                if any(x in name for x in ["ip", "internet", "address"]):
                    group = self.groups["src_ip"]
                elif "port" in name:
                    group = self.groups["src_port"]
            elif any(x in name for x in ["dst", "destination"]):
                if any(x in name for x in ["ip", "internet", "address"]):
                    group = self.groups["dst_ip"]
                elif "port" in name:
                    group = self.groups["dst_port"]

            if group:
                group.buttons()[col_id].setChecked(True)

    # def validatePage(self) -> bool:
    #     try:
    #         col_types = {key: value.currentText() for key, value in self.wizard().col_types_by_user.items()}

    #         dsl.load_data(self.wizard().file_name, col_types, self.fcn, self.wizard().dialect, 100)

    #         return True
    #     except Exception as e:
    #         return False

    # @pyqtSlot()
    # def validate_user_settings(self):
    #     pass
    # try:
    #     col_types = {key: value.currentText() for key, value in self.wizard().col_types_by_user.items()}

    #     dsl.load_data(self.wizard().file_name, col_types, self.fcn, self.wizard().dialect, 100)

    #     self.warning_label.clear()
    # except Exception as e:
    #     print(traceback.format_exc())
    #     self.warning_label.setText("Could not parse csv. (Based on first 100 rows)")

    @pyqtSlot(QAbstractButton)
    def radio_button_changed(self, button: QRadioButton) -> None:
        """Change the real column name of given group in file_col_names.

        Parameters
        ----------
        button : QRadioButton
            Triggered button.
        """
        if button.isChecked():
            csv_col_name = self.cols_ids[button.group().id(button)]
            attribute_name = self.groups.inv[button.group()]

            self.wizard().fcn.__dict__[attribute_name] = csv_col_name

            self.completeChanged.emit()

    @pyqtSlot()
    def deselect_group(self, group: QButtonGroup) -> None:
        """Deselect all buttons in button group and update file_col_names.

        Parameters
        ----------
        group : QButtonGroup
            Button group.
        """
        group.setExclusive(False)
        for button in group.buttons():
            if button.isChecked():
                button.setChecked(False)
        group.setExclusive(True)

        attribute_name = self.groups.inv[group]
        self.wizard().fcn.__dict__[attribute_name] = None

        self.completeChanged.emit()

    @pyqtSlot()
    def clear_file_col_names(self, group: QButtonGroup) -> None:
        """Update the given group in file_col_names to None.

        Parameters
        ----------
        group : QButtonGroup
            Button group.
        """
        attribute_name = self.groups.inv[group]
        self.wizard().fcn.__dict__[attribute_name] = None

    def isComplete(self) -> bool:
        try:

            mandatory_groups = [self.groups["timestamp"], self.groups["src_ip"], self.groups["dst_ip"]]
            assert all(group.checkedButton() for group in mandatory_groups)

            col_types = {key: value.currentText() for key, value in self.wizard().col_types_by_user.items()}

            dsl.load_data(self.wizard().file_name, col_types, self.wizard().dialect, 100)

            self.warning_label.clear()

            return True
        except (AssertionError) as e:  # todo filter errors
            self.warning_label.setText("Could not parse csv. (Based on first 100 rows)")
            print(traceback.format_exc())
            return False
        except Exception as e:
            # TODO DELETE
            print(traceback.format_exc())
            return False


class TypeComboBox(QComboBox):
    """ComboBox used for selecting data type of column."""

    def __init__(self, type, parent: QWidget = None) -> None:
        super().__init__(parent)
        types = ["object", "int", "float", "bool", "datetime", "timedelta", "category"]  # TODO review
        self.insertItems(0, types)
        self.setCurrentIndex(types.index(type))


# endregion


# region Custom Qt components


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


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=300) -> None:
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.set_tight_layout(True)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)


class SelectMasterStationsDialog(QDialog):
    """A simple dialog used for selecting the master station.
    """

    def __init__(self, station_ids: bidict[int, Station], master_station_id: int = None):
        """Initialize the dialog window.

        Parameters
        ----------
        station_ids : bidict[int, Station]
            Key : ID of station.
            Value : Station.
        master_station_id : int, optional
            Id of current master station.
        """
        super().__init__()

        self.setWindowTitle("Select master station")

        self.layout = QVBoxLayout()

        self.button_group = QButtonGroup(self)

        for station_id, station in station_ids.items():
            print(f"added {station}")
            button = QRadioButton(str(station))
            if station_id == master_station_id:
                button.setChecked(True)
            self.button_group.addButton(button, id=station_id)
            self.layout.addWidget(button, Qt.AlignmentFlag.AlignCenter)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)

    def get_selected_station_id(self) -> int:
        """Return the id of the selected station in dialog.

        Returns
        -------
        int
            ID of selected station.
        """
        return self.button_group.checkedId()

    # def click_box(self, state):

    #     if state == Qt.CheckState.Checked:
    #         print("Checked")
    #     else:
    #         print("Unchecked")


# endregion


# region Main

MASTER_STATION_PORT = 2404


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
    stat_widgets : dict[str, InfoLabel]
        Key : Statistic name.
        Value : Assigned label.
    df : pd.DataFrame
        Main dataframe.
    df_model : DataFrameModel
        Model of original data.
    self.master_station_id : int
        ID of station that should be treated as master.
    self.station_ids: bidict[int, Station]
        Key : ID of station.
        Value : Station.
    self.pair_ids: bidict[int, frozenset]
        Key : ID of station.
        Value : Pair of station ids.
        Direction does not matter.
    self.direction_ids: bidict[int, Direction]
        Key : ID of station.
        Value : Pair of station ids. Source and destination.
        Direction does matter.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ICS Analyzer")
        self.setMinimumSize(800, 500)

        self.df: pd.DataFrame = None
        self.df_model: DataFrameModel
        self.fcn: FileColumnNames
        self.stat_widgets: dict[str, InfoLabel] = {}
        self.actions = self.create_actions()
        self.master_station_id: int
        self.station_ids: bidict[int, Station]
        self.pair_ids: bidict[int, frozenset]
        self.direction_ids: bidict[int, Direction]

        self.init_toolbar()

        tabs = QTabWidget()
        # tabs.setTabPosition(QTabWidget.West)
        # tabs.setMovable(True)

        # primary_widget = QWidget()
        # primary_layout = self.create_primary_layout()
        # primary_widget.setLayout(primary_layout)
        primary_widget = self.create_original_df_view()

        secondary_widget = QWidget()
        self.secondary_layout = self.create_secondary_layout()
        secondary_widget.setLayout(self.secondary_layout)

        self.tertiary_scroll_area = QScrollArea(self)
        # self.tertiary_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.tertiary_scroll_area.setWidgetResizable(True)
        self.tertiary_scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # tertiary_widget = QWidget()
        # self.tertiary_layout = QVBoxLayout()
        # tertiary_widget.setLayout(self.tertiary_layout)
        # w = QWidget()
        # w.setLayout(self.tertiary_layout)
        # tertiary_scroll_area.setWidget(w)

        tabs.addTab(primary_widget, "Original Dataframe")
        tabs.addTab(secondary_widget, "Secondary view")
        tabs.addTab(self.tertiary_scroll_area, "Tertiary view")
        self.setCentralWidget(tabs)

    def create_original_df_view(self) -> QTableView:
        # LAYOUT BOTTOM - DATAFRAME VIEW #
        self.table_view = QTableView()
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

        return self.table_view

    def create_secondary_layout(self) -> QVBoxLayout:
        # TODO add vars to doc, rename
        layout = QVBoxLayout()

        # BASIC STATS #
        stat_names = ["File name", "Row count", "Column count", "Time span", "Pairs count"]

        for stat in stat_names:
            w = InfoLabel(stat)
            self.stat_widgets[stat] = w
            layout.addWidget(w)

        return layout

    def update_secondary_layout(self, file_path: str) -> None:
        self.stat_widgets["File name"].set_value(os.path.basename(file_path))
        self.stat_widgets["Row count"].set_value(len(self.df.index))
        self.stat_widgets["Column count"].set_value(len(self.df.columns))
        self.stat_widgets["Time span"].set_value(dsa.compute_time_span(self.df, self.fcn))
        self.stat_widgets["Pairs count"].set_value(dsa.pairs_count(self.df, self.fcn))

    # def create_tertiary_layout(self) -> QVBoxLayout:
    #     layout = QVBoxLayout()

    #     return layout

    def update_tertiary_layout(self) -> None:
        assert self.fcn.pair_id in self.df.columns
        assert all(col in self.df.columns for col in [self.fcn.timestamp, self.fcn.pair_id])

        # remove old widgets
        # for i in reversed(range(self.tertiary_layout.count())):
        #     self.tertiary_layout.itemAt(i).widget().setParent(None)

        # for pair_id in self.pair_ids.keys():
        #     sc = MplCanvas(self, width=3, height=2, dpi=100)
        #     dsa.plot_pair_flow(self.df, self.fcn, sc.axes, pair_id, self.station_ids, self.direction_ids)
        #     self.tertiary_layout.addWidget(sc)

        parent_widget = QWidget(parent=self.tertiary_scroll_area)
        # w = QWidget()

        parent_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        vbox_layout = QVBoxLayout(parent_widget)

        master_station_label = InfoLabel("Master station")
        master_station_label.set_value(self.station_ids[self.master_station_id])
        vbox_layout.addWidget(master_station_label)

        # compute xlimits of axes
        datetime_index = pd.DatetimeIndex(self.df[self.fcn.timestamp])
        left_xlim = min(datetime_index)
        right_xlim = max(datetime_index)

        for pair_id, pair in self.pair_ids.items():
            sc = MplCanvas(parent=parent_widget, width=7, height=3.5, dpi=100)
            sc.axes.set_xlim([left_xlim, right_xlim])
            dsa.plot_pair_flow(self.df, self.fcn, sc.axes, pair_id, self.station_ids, self.direction_ids)

            l1 = QLabel(f"Stations")
            x, y = pair
            l2 = QLabel(str(self.station_ids[x]))
            l3 = QLabel(str(self.station_ids[y]))
            vbox_layout.addWidget(l1)
            vbox_layout.addWidget(l2)
            vbox_layout.addWidget(l3)

            vbox_layout.addWidget(sc)
        parent_widget.setLayout(vbox_layout)

        self.tertiary_scroll_area.setWidget(parent_widget)
        self.tertiary_scroll_area.update()
        # self.tertiary_layout.update()

    def create_actions(self) -> dict[str, QAction]:
        """Define QActions.

        Returns
        -------
        dict[str, QAction]
            Actions used in menu and toolbar.
        """
        actions = dict()

        # LOAD CSV #
        name = "Load CSV"
        actions[name] = QAction(icon=QIcon("img/file.png"), text=name, parent=self)
        # https://www.iconfinder.com/icons/290138/document_extension_file_format_paper_icon
        actions[name].triggered.connect(self.load_csv)

        # SELECT MASTER STATIONS #
        name = "Select master stations"
        actions[name] = QAction(icon=QIcon("img/computa.png"), text=name, parent=self)
        actions[name].triggered.connect(self.select_master_station)

        # EXIT #
        name = "Exit"
        actions[name] = QAction(icon=QIcon("img/exit.png"), text=name, parent=self)
        # https://www.iconfinder.com/icons/352328/app_exit_to_icon
        actions[name].triggered.connect(QApplication.instance().quit)  # TODO je to spravne?

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

        # TODO delete test

        if True:
            # file_path = "data/mega104-14-12-18-ioa.csv"
            # self.df = dsl.load_data(file_path, dtype, dialect)
            self.df = pd.read_pickle("save/df.pkl")
            self.df_model = DataFrameModel(self.df)
            self.table_view.setModel(self.df_model)
            import pickle

            with open("save/fcn.pkl", "rb") as f:
                self.fcn = pickle.load(f)

            self.prepare_df()
            self.update_secondary_layout("placeholder")
            self.update_tertiary_layout()

            self.df.to_pickle("save/dfb.pkl")
            return

        file_path, _ = QFileDialog.getOpenFileName(parent=self, caption="Open file", filter="CSV files (*.csv *.txt)")

        if file_path:
            dialog = OpenCsvWizard(file_path)
            if dialog.exec():
                # TODO exception
                dialect, dtype, self.fcn = dialog.get_csv_settings()
                print(self.fcn)
                self.df = dsl.load_data(file_path, dtype, dialect)
                self.df_model = DataFrameModel(self.df)
                self.table_view.setModel(self.df_model)

                import pickle

                # TODO delete
                self.df.to_pickle("save/df.pkl")
                with open("save/fcn.pkl", "wb") as f:
                    pickle.dump(self.fcn, f)

                self.prepare_df()
                self.update_secondary_layout(file_path)
                self.update_tertiary_layout()

    def prepare_df(self) -> None:
        dsc.add_relative_days(self.df, self.fcn, inplace=True)
        # self.df = dsc.convert_to_timeseries(self.df, self.fcn) TODO delete
        # self.comm_pairs = dsc.find_communication_pairs(self.df, self.fcn)
        # dsc.add_communication_id(self.df, self.fcn, self.comm_pairs, inplace=True)
        # dsc.add_pair_id(self.df, self.fcn, inplace=True)
        self.station_ids = dsc.create_station_ids(self.df, self.fcn)
        dsc.add_station_id(self.df, self.fcn, self.station_ids, inplace=True)

        self.pair_ids = dsc.create_pair_ids(self.df, self.fcn)
        dsc.add_pair_id(self.df, self.fcn, self.pair_ids, inplace=True)

        self.direction_ids = dsc.create_direction_ids(self.df, self.fcn)
        dsc.add_direction_id(self.df, self.fcn, self.direction_ids, inplace=True)

        self.master_station_id = self.detect_master_staion()

    def detect_master_staion(self) -> int | None:
        """Try to detect the master station by its port. Return the first found with corresponding port.

        Returns
        -------
        int | None
            ID of master station. None if not found.
        """
        for station_id, station in self.station_ids.items():
            if self.fcn.double_column_station:
                if station.port == MASTER_STATION_PORT:
                    return station_id
            else:
                if str(MASTER_STATION_PORT) in station.ip:
                    return station_id
        else:
            return None

    def select_master_station(self) -> None:
        if self.df is not None:
            dlg = SelectMasterStationsDialog(self.station_ids, self.master_station_id)
            if dlg.exec():
                self.master_station_id = dlg.get_selected_station_id()
                # TODO trigger event
        else:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Warning")
            dlg.setText("Pleas load a CSV file before proceeding")
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()


# endregion
