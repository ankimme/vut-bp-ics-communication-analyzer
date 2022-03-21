"""Representation of the Original Dataframe tab.

Author
------
Andrea Chimenti

Date
----
March 2022
"""

import pandas as pd

from PyQt6.QtWidgets import QWidget, QTableView

from gui.utils import DataFrameModel, EventData


class OriginalDfTab(QTableView):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.df_model: DataFrameModel

        self.setSortingEnabled(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    def update_model(self, data: EventData) -> None:
        tmpdf = data.df.loc[:, data.original_cols]
        self.df_model = DataFrameModel(tmpdf)
        self.setModel(self.df_model)