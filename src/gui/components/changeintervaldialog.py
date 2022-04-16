from datetime import datetime

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QDateTimeEdit, QDialogButtonBox, QPushButton

from gui.components import InfoLabel


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
