"""主程序入口"""
from gui import ManosabaGUI
# from tui import ManosabaTUI

if __name__ == "__main__":
    app = ManosabaGUI()
    # app = ManosabaTUI()
    app.run()
