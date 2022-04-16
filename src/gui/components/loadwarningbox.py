from PyQt6.QtWidgets import QWidget, QMessageBox


class LoadWarningMessageBox(QMessageBox):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Warning")
        self.setText("Please load a CSV file before proceeding")
        self.setIcon(QMessageBox.Icon.Warning)
