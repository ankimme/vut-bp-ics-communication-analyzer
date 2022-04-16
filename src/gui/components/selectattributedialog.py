# TODO doc

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QButtonGroup, QDialogButtonBox, QRadioButton


class SelectAttributeDialog(QDialog):
    def __init__(self, og_attribute: str, attributes: list[str], parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Select attribute")

        main_layout = QVBoxLayout()

        self.button_group = QButtonGroup(self)

        for attribute in attributes:
            button = QRadioButton(str(attribute))
            if attribute == og_attribute:
                button.setChecked(True)
            self.button_group.addButton(button)
            main_layout.addWidget(button, Qt.AlignmentFlag.AlignCenter)

        # BUTTONS #

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        self.main_layout.addWidget(buttons)
        self.setLayout(main_layout)

    def get_attribute_name(self) -> str:
        """Return the selected attribute in dialog.

        Returns
        -------
        str
            Name of selected attribute.
        """
        return self.button_group.checkedButton().text()
