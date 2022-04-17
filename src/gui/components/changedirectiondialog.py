from PyQt6.QtWidgets import QWidget, QDialog, QRadioButton, QVBoxLayout, QButtonGroup, QDialogButtonBox

from dsmanipulator.utils.dataobjects import DirectionEnum


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
