from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, QPushButton


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
