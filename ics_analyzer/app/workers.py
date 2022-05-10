"""Workers.

Author
------
Andrea Chimenti

Date
----
March 2022
"""

import pandas as pd
import csv

from dsmanipulator import dsloader as dsl

from PyQt6.QtCore import QObject, pyqtSignal


class LoadCsvWorker(QObject):

    csv_loaded = pyqtSignal(pd.DataFrame)
    finished = pyqtSignal()
    exception_raised = pyqtSignal()

    def __init__(
        self, file_name: str, data_types: dict[str, str], dialect: csv.Dialect, parent: QObject = None
    ) -> None:
        super().__init__(parent)
        self.file_name = file_name
        self.data_types = data_types
        self.dialect = dialect

    def load_csv(self):
        try:
            df = dsl.load_data(self.file_name, self.data_types, self.dialect)
            self.csv_loaded.emit(df)
        except Exception:
            self.exception_raised.emit()
        finally:
            self.finished.emit()
