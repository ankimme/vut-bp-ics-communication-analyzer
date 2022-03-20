"""Representation of the main toolbar.

Author
------
Andrea Chimenti

Date
----
March 2022
"""

# from PyQt6.QtWidgets import QWidget, QToolBar
# from PyQt6.QtGui import QAction


# class MainToolbar(QToolBar):
#     def __init__(self, actions: dict[str, QAction], title: str = "Main Toolbar", parent: QWidget = None):
#         """Initialize main toolbar and add all actions.

#         Parameters
#         ----------
#         actions : dict[str, QAction]
#             Key : Action name.
#             Value : QAction object.

#         title : str, optional
#             Title of toolbar.
#         parent : QWidget, optional
#             Parent of toolbar.
#         """
#         super().__init__(title=title, parent=parent)

#         for action in actions.values():
#             self.addAction(action)
