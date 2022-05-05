import pandas as pd
from datetime import datetime
from bidict import bidict

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget,
    QDialog,
    QVBoxLayout,
    QButtonGroup,
    QDialogButtonBox,
    QRadioButton,
    QScrollArea,
    QPushButton,
    QMessageBox,
    QCheckBox,
    QSpinBox,
    QLabel,
    QDateTimeEdit,
)

from dsmanipulator.dataobjects import DirectionEnum, Station

from gui.widgets import InfoLabel


class WarningMessageBox(QMessageBox):
    def __init__(self, message: str, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Warning")
        self.setText(message)
        self.setIcon(QMessageBox.Icon.Warning)


class SelectMasterStationsDialog(QDialog):
    """A simple dialog used for selecting the master station."""

    def __init__(self, station_ids: bidict[int, Station], og_master_station_id: int = None, parent: QWidget = None):
        """Initialize the dialog window.

        Parameters
        ----------
        station_ids : bidict[int, Station]
            Key : ID of station.
            Value : Station.
        master_station_id : int, optional
            Id of current master station.
        """
        super().__init__(parent)

        self.setWindowTitle("Select master station")

        # QScrollArea -> QWidget -> layout -> content widgets
        dialog_layout = QVBoxLayout()
        scroll_area = QScrollArea()
        parent_widget = QWidget(self)

        self.layout = QVBoxLayout()

        self.button_group = QButtonGroup(self)

        for station_id, station in station_ids.items():
            button = QRadioButton(str(station))
            if station_id == og_master_station_id:
                button.setChecked(True)
            self.button_group.addButton(button, id=station_id)
            self.layout.addWidget(button, Qt.AlignmentFlag.AlignCenter)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        parent_widget.setLayout(self.layout)

        scroll_area.setWidget(parent_widget)
        dialog_layout.addWidget(scroll_area)
        dialog_layout.addWidget(self.buttons)
        self.setLayout(dialog_layout)

    def get_master_station_id(self) -> int:
        """Return the id of the selected station in dialog.

        Returns
        -------
        int
            ID of master station.
        """
        return self.button_group.checkedId()


class SelectSlavesDialog(QDialog):
    """Select slaves dialog.

    Attributes
    ----------
    layout : QVBoxLayout
        Main dialog layout.
    boxes : dict[int, QCheckBox]
        Key : ID of station.
        Value : Assigned checkbox.
    buttons : QDialogButtonBox
        Dialog control buttons
    """

    def __init__(
        self,
        master_station_id: int,
        og_slave_station_ids: list[int],
        station_ids: bidict[int, Station],
        pair_ids: bidict[int, frozenset],
        parent: QWidget = None,
    ) -> None:
        """Initialize dialog.

        Parameters
        ----------
        master_station_id : int
            ID of master station.
        og_slave_station_ids : list[int]
           IDs of stations that will be preselected.
        station_ids : bidict[int, Station]
            Key : ID of station.
            Value : Station.
        pair_ids : bidict[int, frozenset]
            Key : ID of station.
            Value : Pair of station ids.
        parent : QWidget, optional
            Parent widget.
        """
        super().__init__(parent)

        self.setWindowTitle("Select slaves")

        # QScrollArea -> QWidget -> layout -> content widgets
        dialog_layout = QVBoxLayout()
        scroll_area = QScrollArea()
        parent_widget = QWidget(self)

        self.layout = QVBoxLayout()

        # select all button
        select_all_button = QPushButton("Select all")
        select_all_button.clicked.connect(self.select_all)
        dialog_layout.addWidget(select_all_button)

        # deselect all button
        deselect_all_button = QPushButton("Deselect all")
        deselect_all_button.clicked.connect(self.deselect_all)
        dialog_layout.addWidget(deselect_all_button)

        # ids of stations that communicate with the master station
        all_slave_ids = dsa.get_connected_stations(pair_ids, master_station_id)

        self.boxes: dict[int, QCheckBox] = {}

        for station_id, station in station_ids.items():
            if station_id in all_slave_ids:
                box = QCheckBox(str(station), self)

                if station_id in og_slave_station_ids:
                    box.setChecked(True)

                self.boxes[station_id] = box
                self.layout.addWidget(box)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        parent_widget.setLayout(self.layout)

        scroll_area.setWidget(parent_widget)
        dialog_layout.addWidget(scroll_area)
        dialog_layout.addWidget(self.buttons)
        self.setLayout(dialog_layout)

    @pyqtSlot()
    def select_all(self) -> None:
        """Check all buttons in dialog."""
        for box in self.boxes.values():
            box.setChecked(True)

    @pyqtSlot()
    def deselect_all(self) -> None:
        """Uncheck all buttons in dialog."""
        for box in self.boxes.values():
            box.setChecked(False)

    def get_slave_stations_ids(self) -> list[int]:
        """Return the ids of selected stations in dialog.

        Returns
        -------
        list[int]
            List of IDs of selected slave stations.
        """
        return [station_id for station_id, box in self.boxes.items() if box.isChecked()]


class ChangeDirectionDialog(QDialog):
    def __init__(self, og_direction: DirectionEnum, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Change direction")

        vbox_layout = QVBoxLayout()

        self.button_group = QButtonGroup(self)

        both_button = QRadioButton("Both")
        m2s_button = QRadioButton("Master to slave")
        s2m_button = QRadioButton("Slave to master")

        self.button_group.addButton(both_button, id=int(DirectionEnum.BOTH))
        self.button_group.addButton(m2s_button, id=int(DirectionEnum.M2S))
        self.button_group.addButton(s2m_button, id=int(DirectionEnum.S2M))

        match og_direction:
            case DirectionEnum.BOTH:
                both_button.setChecked(True)
            case DirectionEnum.M2S:
                m2s_button.setChecked(True)
            case DirectionEnum.S2M:
                s2m_button.setChecked(True)

        vbox_layout.addWidget(both_button)
        vbox_layout.addWidget(m2s_button)
        vbox_layout.addWidget(s2m_button)

        # BUTTONS #

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        vbox_layout.addWidget(buttons)

        self.setLayout(vbox_layout)

    def get_direction(self) -> DirectionEnum:
        return DirectionEnum(self.button_group.checkedId())


class ChangeIntervalDialog(QDialog):
    def __init__(
        self, start: datetime, end: datetime, low_limit: datetime, upper_limit: datetime, parent: QWidget = None
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Change interval")

        vbox_layout = QVBoxLayout()

        display_format = "yyyy-MM-dd hh:mm:ss.zzz"
        self.low_limit = low_limit
        self.upper_limit = upper_limit

        # START TIME EDIT #

        self.start_time_edit = QDateTimeEdit()
        self.start_time_edit.setDisplayFormat(display_format)
        self.start_time_edit.setDateTime(start)
        # self.start_time_edit.setMinimumDateTime(self.low_limit)
        # self.start_time_edit.setMaximumDateTime(self.upper_limit)
        self.start_time_edit.dateTimeChanged.connect(self.update_ui)

        start_reset_button = QPushButton("Reset start datetime")
        start_reset_button.clicked.connect(self.reset_start_time)

        vbox_layout.addWidget(self.start_time_edit)
        vbox_layout.addWidget(start_reset_button)

        # END TIME EDIT #

        self.end_time_edit = QDateTimeEdit()
        self.end_time_edit.setDisplayFormat(display_format)
        self.end_time_edit.setDateTime(end)
        # self.end_time_edit.setMinimumDateTime(self.low_limit)
        # self.end_time_edit.setMaximumDateTime(self.upper_limit)
        self.end_time_edit.dateTimeChanged.connect(self.update_ui)

        end_reset_button = QPushButton("Reset end datetime")
        end_reset_button.clicked.connect(self.reset_end_time)

        vbox_layout.addWidget(self.end_time_edit)
        vbox_layout.addWidget(end_reset_button)

        self.interval_len_label = InfoLabel("Interval length")
        vbox_layout.addWidget(self.interval_len_label)

        # BUTTONS #

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        vbox_layout.addWidget(self.buttons)

        self.setLayout(vbox_layout)

        self.update_ui()

    def get_new_interval(self) -> tuple[datetime, datetime]:

        return self.start_time_edit.dateTime().toPyDateTime(), self.end_time_edit.dateTime().toPyDateTime()

    @pyqtSlot()
    def reset_start_time(self) -> None:
        self.start_time_edit.setDateTime(self.low_limit)

    @pyqtSlot()
    def reset_end_time(self) -> None:
        self.end_time_edit.setDateTime(self.upper_limit)

    @pyqtSlot()
    def update_ui(self) -> None:

        start_ok = self.low_limit <= self.start_time_edit.dateTime().toPyDateTime() <= self.upper_limit
        end_ok = self.low_limit <= self.end_time_edit.dateTime().toPyDateTime() <= self.upper_limit
        chrono_ok = self.start_time_edit.dateTime().toPyDateTime() < self.end_time_edit.dateTime().toPyDateTime()

        # change colors
        if start_ok and chrono_ok:
            self.start_time_edit.setStyleSheet("color: black")
        else:
            self.start_time_edit.setStyleSheet("color: red")

        if end_ok and chrono_ok:
            self.end_time_edit.setStyleSheet("color: black")
        else:
            self.end_time_edit.setStyleSheet("color: red")

        if start_ok and end_ok and chrono_ok:
            self.interval_len_label.set_value(
                str(self.end_time_edit.dateTime().toPyDateTime() - self.start_time_edit.dateTime().toPyDateTime())
            )
            self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        else:
            self.interval_len_label.set_value("")
            self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)


class ChangeResampleRateDialog(QDialog):
    """Dialog used for changing the sample rate.

    Attributes
    ----------
    day_spin_box : QSpinBox
        Used for setting days.
    hour_spin_box : QSpinBox
        Used for setting hours.
    minute_spin_box : QSpinBox
        Used for setting minutes.
    second_spin_box : QSpinBox
        Used for setting seconds.
    timedelta_preview : InfoLabel
        A preview of selected timedelta value.
    """

    def __init__(self, og_resample_rate: pd.Timedelta, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Change resample rate")

        layout = QVBoxLayout()

        self.day_spin_box = QSpinBox(self)
        self.hour_spin_box = QSpinBox(self)
        self.minute_spin_box = QSpinBox(self)
        self.second_spin_box = QSpinBox(self)

        self.day_spin_box.setValue(og_resample_rate.days)
        x = og_resample_rate.seconds
        self.hour_spin_box.setValue(x // 3600)
        self.minute_spin_box.setValue((x % 3600) // 60)
        self.second_spin_box.setValue(x % 60)

        self.day_spin_box.valueChanged.connect(self.timedelta_changed)
        self.hour_spin_box.valueChanged.connect(self.timedelta_changed)
        self.minute_spin_box.valueChanged.connect(self.timedelta_changed)
        self.second_spin_box.valueChanged.connect(self.timedelta_changed)

        # spin boxes
        layout.addWidget(QLabel("Days"))
        layout.addWidget(self.day_spin_box)

        layout.addWidget(QLabel("Hours"))
        layout.addWidget(self.hour_spin_box)

        layout.addWidget(QLabel("Minutes"))
        layout.addWidget(self.minute_spin_box)

        layout.addWidget(QLabel("Seconds"))
        layout.addWidget(self.second_spin_box)

        # info
        self.timedelta_preview = InfoLabel("That is: ")
        self.timedelta_preview.set_value(og_resample_rate)
        layout.addWidget(self.timedelta_preview)

        # buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    @pyqtSlot()
    def timedelta_changed(self) -> None:
        """Update the timedelta preview."""

        self.timedelta_preview.set_value(str(self.get_resample_rate()))

    def get_resample_rate(self) -> pd.Timedelta:
        """Return the timedelta chosen by the user in the dialog.

        Returns
        -------
        pd.Timedelta
            Chosen timedelta value.
        """

        return pd.Timedelta(
            days=self.day_spin_box.value(),
            hours=self.hour_spin_box.value(),
            minutes=self.minute_spin_box.value(),
            seconds=self.second_spin_box.value(),
        )


class SelectAttributeDialog(QDialog):
    def __init__(self, og_attribute: str, attributes: list[str], parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Select attribute")

        # QScrollArea -> QWidget -> layout -> content widgets
        dialog_layout = QVBoxLayout()
        scroll_area = QScrollArea()
        parent_widget = QWidget(self)

        vbox_layout = QVBoxLayout()

        deselect_button = QPushButton("None")
        deselect_button.clicked.connect(self.deselect_all)

        self.button_group = QButtonGroup(self)

        for attribute in attributes:
            button = QRadioButton(str(attribute))
            if attribute == og_attribute:
                button.setChecked(True)
            self.button_group.addButton(button)
            vbox_layout.addWidget(button, Qt.AlignmentFlag.AlignCenter)

        # BUTTONS #

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        parent_widget.setLayout(vbox_layout)

        scroll_area.setWidget(parent_widget)
        dialog_layout.addWidget(deselect_button)
        dialog_layout.addWidget(scroll_area)
        dialog_layout.addWidget(buttons)
        self.setLayout(dialog_layout)

    def get_attribute_name(self) -> str:
        """Return the selected attribute in dialog.

        Returns
        -------
        str
            Name of selected attribute.
        """

        # check that a button is checked
        if self.button_group.checkedId() != -1:
            return self.button_group.checkedButton().text()
        else:
            return None

    @pyqtSlot()
    def deselect_all(self) -> None:
        """Uncheck all buttons in dialog."""
        self.button_group.setExclusive(False)
        for button in self.button_group.buttons():
            if button.isChecked():
                button.setChecked(False)
        self.button_group.setExclusive(True)


class SelectAttributeValuesDialog(QDialog):
    def __init__(
        self,
        og_attribute_values: list[str | int | float],
        all_attribute_values: list[str | int | float],
        parent: QWidget = None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Select attribute values")

        self.layout = QVBoxLayout()

        # select all button
        select_all_button = QPushButton("Select all")
        select_all_button.clicked.connect(self.select_all)
        self.layout.addWidget(select_all_button)

        # deselect all button
        deselect_all_button = QPushButton("Deselect all")
        deselect_all_button.clicked.connect(self.deselect_all)
        self.layout.addWidget(deselect_all_button)

        self.boxes: dict[str, QCheckBox] = {}

        for attribute in all_attribute_values:
            box = QCheckBox(str(attribute), self)

            if attribute in og_attribute_values:
                box.setChecked(True)

            self.boxes[attribute] = box
            self.layout.addWidget(box)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)

    @pyqtSlot()
    def select_all(self) -> None:
        """Check all buttons in dialog."""
        for box in self.boxes.values():
            box.setChecked(True)

    @pyqtSlot()
    def deselect_all(self) -> None:
        """Uncheck all buttons in dialog."""
        for box in self.boxes.values():
            box.setChecked(False)

    def get_attribute_values(self) -> list[str | int | float]:
        return [attribute for attribute, box in self.boxes.items() if box.isChecked()]
