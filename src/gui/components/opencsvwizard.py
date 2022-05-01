"""Dialog used to create a dataframe from a csv file.

Provides data type (int, str...) and column type (timestamp, srcip ...) settings.

Author
------
Andrea Chimenti

Date
----
March 2022
"""

import csv
import pandas as pd
from bidict import bidict
import traceback  # TODO delete


from PyQt6.QtWidgets import (
    QWidget,
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListView,
    QGridLayout,
    QButtonGroup,
    QRadioButton,
    QPushButton,
    QAbstractButton,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSlot


from gui.utils import ListModel
from dsmanipulator import dsloader as dsl
from dsmanipulator import FileColumnNames


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
    fcn : FileColumnNames
        Real names of mandatory columns.
    """

    def __init__(self, file_name: str, parent: QWidget = None) -> None:
        """Initialize OpenCsvWizard class and create button layout.

        Parameters
        ----------
        file_name : str
            Name of CSV file.
        parent : QWidget, optional
            Parent widget, by default None
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
        """Get settings for loading the csv file that the user selected in the dialog.

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
    """Page used to set delimiter of csv file.

    Attributes
    ----------
    delimiter_line_edit : QLineEdit()
        User input for changing delimiter.
    columns_model : ListModel()
        List model containing detected columns.
    warning_label : QLabel()
        A warning label on the bottom fo the page.
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setSubTitle("Set CSV delimiter")

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Delimiter #
        self.delimiter_line_edit = QLineEdit()
        self.delimiter_line_edit.setMaxLength(1)
        self.delimiter_line_edit.textChanged.connect(self.delimiter_line_edit_changed)
        form_layout.addRow(QLabel("Delimiter:"), self.delimiter_line_edit)

        layout.addLayout(form_layout)

        # Columns preview #
        layout.addWidget(QLabel("Columns:"))
        columns_view = QListView()
        self.columns_model = ListModel()
        columns_view.setModel(self.columns_model)
        layout.addWidget(columns_view)

        # Warning #
        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("QLabel { color: red }")
        layout.addWidget(self.warning_label)

        self.setLayout(layout)

    def initializePage(self) -> None:
        """Set delimiter to automatically detected."""
        self.delimiter_line_edit.setText(self.wizard().dialect.delimiter)

    @pyqtSlot()
    def delimiter_line_edit_changed(self) -> None:
        """Update preview of columns based on delimiter change."""
        self.wizard().dialect.delimiter = self.delimiter_line_edit.text() or None

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
        return bool(self.columns_model.items)


class PageSetDataTypes(QWizardPage):
    """Page used to set the data type (int, str...) and column type (timestamp, srcip ...) of detected columns.


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
    grid_layout : QGridLayout(self)
        Layout containing column type selection buttons.
    warning_label : QLabel()
        A warning label on the bottom fo the page.
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setSubTitle(
            "Set column data types and their functionality. Timestamp, source and destination IPs are mandatory."
        )

        layout = QVBoxLayout(self)
        self.grid_layout = QGridLayout(self)

        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("QLabel { color: red }")

        layout.addLayout(self.grid_layout)
        layout.addWidget(self.warning_label)

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
        self.setLayout(layout)

    def initializePage(self) -> None:
        """Create widgets."""
        self.wizard().fcn = FileColumnNames()

        # grid header
        self.grid_layout.addWidget(QLabel("Name"), 0, 0, Qt.AlignmentFlag.AlignCenter)
        self.grid_layout.addWidget(QLabel("Data type"), 0, 1, Qt.AlignmentFlag.AlignCenter)

        self.grid_layout.addWidget(QLabel("Time stamp"), 0, 2, Qt.AlignmentFlag.AlignCenter)
        # b = QPushButton("Reset")
        # b.clicked.connect(lambda: self.deselect_group(self.groups["timestamp"]))
        # b.clicked.connect(lambda: self.clear_file_col_names(self.groups["timestamp"]))
        # self.grid_layout.addWidget(b, 1, 2, Qt.AlignmentFlag.AlignCenter)

        self.grid_layout.addWidget(QLabel("Rel time"), 0, 3, Qt.AlignmentFlag.AlignCenter)
        b = QPushButton("None")
        b.clicked.connect(lambda: self.deselect_group(self.groups["rel_time"]))
        b.clicked.connect(lambda: self.clear_file_col_names(self.groups["rel_time"]))
        self.grid_layout.addWidget(b, 1, 3, Qt.AlignmentFlag.AlignCenter)

        self.grid_layout.addWidget(QLabel("SRC IP"), 0, 4, Qt.AlignmentFlag.AlignCenter)
        # b = QPushButton("Reset")
        # b.clicked.connect(lambda: self.deselect_group(self.groups["src_ip"]))
        # b.clicked.connect(lambda: self.clear_file_col_names(self.groups["src_ip"]))
        # self.grid_layout.addWidget(b, 1, 4, Qt.AlignmentFlag.AlignCenter)

        self.grid_layout.addWidget(QLabel("SRC Port"), 0, 5, Qt.AlignmentFlag.AlignCenter)
        b = QPushButton("None")
        b.clicked.connect(lambda: self.deselect_group(self.groups["src_port"]))
        b.clicked.connect(lambda: self.clear_file_col_names(self.groups["src_port"]))
        self.grid_layout.addWidget(b, 1, 5, Qt.AlignmentFlag.AlignCenter)

        self.grid_layout.addWidget(QLabel("DST IP"), 0, 6, Qt.AlignmentFlag.AlignCenter)
        # b = QPushButton("Reset")
        # b.clicked.connect(lambda: self.deselect_group(self.groups["dst_ip"]))
        # b.clicked.connect(lambda: self.clear_file_col_names(self.groups["dst_ip"]))
        # self.grid_layout.addWidget(b, 1, 6, Qt.AlignmentFlag.AlignCenter)

        self.grid_layout.addWidget(QLabel("DST Port"), 0, 7, Qt.AlignmentFlag.AlignCenter)
        b = QPushButton("None")
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
        """Autodetect mandatory file column names and select them in UI."""
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
        """Validate user settings.

        Returns
        -------
        bool
            True if it is possible to load the csv file with given settings.
        """
        try:

            # check that mandatory groups are selected
            mandatory_groups = [self.groups["timestamp"], self.groups["src_ip"], self.groups["dst_ip"]]
            assert all(
                group.checkedButton() for group in mandatory_groups
            ), "Timstamp, source ip and destination ip are mandatory"

            # check databypes of mandatory groups
            assert (
                self.wizard().col_types_by_user[self.wizard().fcn.timestamp].currentText() == "datetime"
            ), "Timestamp column should be of datetime type"
            assert (
                self.wizard().col_types_by_user[self.wizard().fcn.src_ip].currentText() == "object"
            ), "Source ip column should be of string type"
            assert (
                self.wizard().col_types_by_user[self.wizard().fcn.dst_ip].currentText() == "object"
            ), "Destination ip column should be of string type"

            # both ports must be assigned
            assert bool(self.groups["src_port"].checkedButton()) == bool(
                self.groups["dst_port"].checkedButton()
            ), "Cannot use only one port"

            if self.groups["src_port"].checkedButton():
                assert (
                    self.wizard().col_types_by_user[self.wizard().fcn.src_port].currentText() == "float"
                ), "Source port column should be of numeric type"
                assert (
                    self.wizard().col_types_by_user[self.wizard().fcn.dst_port].currentText() == "float"
                ), "Destination port column should be of numeric type"

            # check relative time is numeric
            if self.groups["rel_time"].checkedButton():
                assert (
                    self.wizard().col_types_by_user[self.wizard().fcn.rel_time].currentText() == "float"
                ), "Relative time column should be of numeric type"

            # try loading the csv with given settings
            col_types = {key: value.currentText() for key, value in self.wizard().col_types_by_user.items()}
            dsl.load_data(self.wizard().file_name, col_types, self.wizard().dialect, row_limit=15000)

            self.warning_label.clear()

            return True
        except AssertionError as e:  # TODO filter errors
            self.warning_label.setText(str(e))
            return False
        except ValueError as e:
            self.warning_label.setText(f"Cannot parse. Please check the datatypes of columns.")
            print(traceback.format_exc())
            return False
        except Exception as e:
            # TODO DELETE
            self.warning_label.setText("Unknown error")
            print(traceback.format_exc())
            return False


class TypeComboBox(QComboBox):
    """ComboBox used for selecting data type of column.

    Show 'string' instead of 'object'. But return 'object'.
    Show 'numeric' instead of 'float'. But return 'float'.
    """

    def __init__(self, preselected_type, parent: QWidget = None) -> None:
        super().__init__(parent)
        if preselected_type == "object":
            preselected_type = "string"
        if preselected_type == "float":
            preselected_type = "numeric"
        types = ["string", "numeric", "datetime"]
        self.insertItems(0, types)
        self.setCurrentIndex(types.index(preselected_type))

    def currentText(self) -> str:
        """Return selected dtype value.

        Return 'object' instead of 'string'.

        Returns
        -------
        str
            Selected value.
        """
        if super().currentText() == "string":
            return "object"
        if super().currentText() == "numeric":
            return "float"
        else:
            return super().currentText()
