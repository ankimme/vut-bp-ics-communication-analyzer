"""Dialog used to change the timespan of resampling.

Author
------
Andrea Chimenti

Date
----
March 2022
"""

import pandas as pd

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QWidget, QDialog, QSpinBox, QVBoxLayout, QLabel, QDialogButtonBox

from gui.components import InfoLabel


class ChangeResampleRate(QDialog):
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
