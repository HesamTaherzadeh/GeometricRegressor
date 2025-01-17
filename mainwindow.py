import sys
from PySide6.QtWidgets import QApplication
from ui.maintoolbox import ToolBoxMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ToolBoxMainWindow()
    window.show()
    sys.exit(app.exec())