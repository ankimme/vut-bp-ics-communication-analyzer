"""The models are used for visualizing data in pyqt.

Author
------
Andrea Chimenti

Date
----
March 2022
"""


import pandas as pd
from PyQt6.QtCore import Qt, QModelIndex, QAbstractTableModel, QAbstractListModel


# https://doc.qt.io/qtforpython/examples/example_external__pandas.html
class DataFrameModel(QAbstractTableModel):
    """A model to interface a Qt view with pandas dataframe

    Based on the example code in Qt Documentation.
    https://doc.qt.io/qtforpython/examples/example_external__pandas.html
    """

    def __init__(self, dataframe: pd.DataFrame, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._df = dataframe

    def rowCount(self, parent=QModelIndex()) -> int:
        """Override method from QAbstractTableModel.

        Return row count of the pandas DataFrame.
        """
        if parent == QModelIndex():
            return len(self._df)
        else:
            return 0

    def columnCount(self, parent=QModelIndex()) -> int:
        """Override method from QAbstractTableModel.

        Return column count of the pandas DataFrame.
        """
        if parent == QModelIndex():
            return len(self._df.columns)
        else:
            return 0

    def data(self, index: QModelIndex, role=Qt.ItemDataRole):
        """Override method from QAbstractTableModel.

        Return data cell from the pandas DataFrame.
        """
        if not index.isValid():
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._df.iloc[index.row(), index.column()])

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole):
        """Override method from QAbstractTableModel.

        Return dataframe index as vertical header data and columns as horizontal header data.
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._df.columns[section])

            if orientation == Qt.Orientation.Vertical:
                return str(self._df.index[section])

        return None

    def sort(self, column: int, order: Qt.SortOrder = ...) -> None:
        """Override method from QAbstractTableModel.

        Sort dataframe date by column.
        """
        colname = self._df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(colname, ascending=order == Qt.SortOrder.AscendingOrder, inplace=True)
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()


class ListModel(QAbstractListModel):
    """AbstractionListModel of a simple list."""

    def __init__(self, *args, items=None, **kwargs) -> None:
        """Initialize a ListModel object.

        Parameters
        ----------
        items : list[Any], optional
            List of items of any type.
        """
        super().__init__(*args, **kwargs)
        self.items = items or []

    def data(self, index, role):
        """Override method from QAbstractListModel.

        Return data on given index from the list.
        """
        if role == Qt.ItemDataRole.DisplayRole:
            return self.items[index.row()]

    def rowCount(self, index) -> int:
        """Override method from QAbstractListModel.

        Return length of list.
        """
        return len(self.items)
