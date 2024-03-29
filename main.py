from PyQt6.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QTableWidget,
    QSlider,
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtCore import Qt
import atexit
import sys
from numpy.random import choice

TABLE_ITEM_WIDTH: int = 183
TABLE_ITEM_HEIGHT: int = 150

WINDOW_WIDTH: int = 600
WINDOW_HEIGHT: int = 630

BET_MIN: int = 25
BET_MAX: int = 50000

# To allow for images in tables
# Credit: https://www.mail-archive.com/pyqt@riverbankcomputing.com/msg01259.html
#         https://stackoverflow.com/questions/5553342/adding-images-to-a-qtablewidget-in-pyqt
class ImageWidget(QWidget):
    def __init__(self, imagePath, parent):
        super(ImageWidget, self).__init__(parent)
        self.picture = QPixmap(imagePath)
        self.picture = self.picture.scaled(TABLE_ITEM_WIDTH, TABLE_ITEM_HEIGHT)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.picture)


def format_number(n: int) -> str:
    s: str = str(n)
    l: list = list(s)
    intermediary_res: list = []
    index: int = len(l) -1
    counter: int = 0
    while (index >= 0):
        if (counter == 3):
            counter = 0
            intermediary_res.insert(0, ',')
        intermediary_res.insert(0, l[index])
        index -= 1
        counter += 1
    return ''.join(intermediary_res)

class TableWidget(QTableWidget):
    def setImage(self, row, col, imagePath):
        image = ImageWidget(imagePath, self)
        self.setCellWidget(row, col, image)

# Main class, contains all logic
class Window(QWidget):
    # Set up the variables we know we need
    def __init__(self):
        super().__init__()
        self.slots: list = [
            "gfx/cherry.png",
            "gfx/melon.png",
            "gfx/banana.png",
            "gfx/bell.png",
            "gfx/money.png",
            "gfx/seven.png",
            "gfx/gem.png",
        ]
        self.lifetime_gain: int = 0
        self.balance: int = 0
        self.setup()
        self.ui()
    
    # Reads in stored player data to make balance and lifetime gain/loss persistent
    def setup(self):
        with open("data/playerdata.crypt", "r") as data:
            b: str = data.readline()
            lt: str = data.readline()
            self.balance = int(b)
            self.lifetime_gain = int(lt)
        print("Read player data")

    # Make sure to save the player data when the program closes
    def exit_handler(self):
        with open("data/playerdata.crypt", "w") as clear:
            clear.write("")
        with open("data/playerdata.crypt", "a") as data:
            data.write(str(self.balance))
            data.write("\n")
            data.write(str(self.lifetime_gain))
        print("Wrote player data")

    # Draws the UI elements
    def ui(self):
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowTitle("Zlot")
        self.setWindowIcon(QIcon("gfx/icon.png"))

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.table = TableWidget()
        self.table.setHorizontalHeaderLabels([" ", " ", " "])
        self.table.setVerticalHeaderLabels([" ", " ", " "])
        self.table.setRowCount(3)
        self.table.setColumnCount(3)
        for _ in range(3):
            self.table.setColumnWidth(_, TABLE_ITEM_WIDTH)
            self.table.setRowHeight(_, TABLE_ITEM_HEIGHT)
        layout.addWidget(self.table)
        for i in range(3):
            for j in range(3):
                self.table.setImage(i, j, "gfx/question.png")

        self.label = QLabel("Lifetime Gain/Loss: {}¤".format(format_number(self.lifetime_gain)))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.adjustSize()
        layout.addWidget(self.label)

        self.balance_label = QLabel("Balance: {}¤".format(format_number(self.balance)))
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.adjustSize()
        layout.addWidget(self.balance_label)

        roll_button = QPushButton("Roll", self)
        roll_button.move(250, 550)
        roll_button.clicked.connect(self.roll)
        layout.addWidget(roll_button)

        self.bet_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.bet_slider.setMinimum(BET_MIN)
        self.bet_slider.setMaximum(BET_MAX)
        self.bet_slider.setTickInterval(int(BET_MAX / BET_MIN))
        self.bet_slider.valueChanged.connect(self.update)
        layout.addWidget(self.bet_slider)
        self.bet_label = QLabel("Current bet: {}¤".format(self.bet_slider.value()))
        self.bet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bet_label.adjustSize()
        layout.addWidget(self.bet_label)

    # Just here to update the label that reads your current betting amount
    def update(self):
        self.bet_label.setText("Current bet: {}¤".format(self.bet_slider.value()))
        self.bet_label.adjustSize()

    # Handles rolling logic for the slot machine itself
    def roll(self):
        bet: int = self.bet_slider.value()
        self.lifetime_gain -= bet
        self.balance -= bet
        rolls: list = [["", "", ""], ["", "", ""], ["", "", ""]]
        used: list = []
        for i in range(3):
            for j in range(3):
                r: str = str(choice(self.slots,  p=[0.4, 0.25, 0.15, 0.07, 0.05, 0.05, 0.03]))
                while (r in used):
                    r = str(choice(self.slots,  p=[0.4, 0.25, 0.15, 0.07, 0.05, 0.05, 0.03]))
                rolls[j][i] = r
                used.append(r)
                self.table.setImage(j, i, r)
            used = []
        winnings: int = 0
        # Handle winning scenarios - three of a kind and x number of consolation prize
        if rolls[1][0] == rolls[1][1] == rolls[1][2]:
            winning_roll: str = rolls[1][0]
            k: int = 0
            while self.slots[k] != winning_roll:
                k += 1
            winnings = bet + ((bet * (k + 1)) * ((k + 1) ** 4))
        else:
            if (
                (rolls[1][0] == self.slots[4])
                ^ (rolls[1][1] == self.slots[4])
                ^ (rolls[1][2] == self.slots[4])
            ):
                winnings = bet
            if (
                (rolls[1][0] == self.slots[4] and rolls[1][1] == self.slots[4])
                ^ (rolls[1][0] == self.slots[4] and rolls[1][2] == self.slots[4])
                ^ (rolls[1][1] == self.slots[4] and rolls[1][2] == self.slots[4])
            ):
                winnings = bet * 2
        # Check if we won anything or not, and update display info accordingly
        if winnings != 0:
            self.lifetime_gain += winnings
            self.label.setText(
                "Result: +{}¤, Lifetime Gain/Loss: {}¤".format(
                    format_number((winnings - bet)), format_number(self.lifetime_gain)
                )
            )
            self.balance += winnings
            self.balance_label.setText("Balance: {}¤".format(format_number(self.balance)))
        else:
            self.label.setText(
                "Result: -{}¤, Lifetime Gain/Loss: {}¤".format(bet, format_number(self.lifetime_gain))
            )
            self.balance_label.setText("Balance: {}¤".format(format_number(self.balance)))


def main() -> None:
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    atexit.register(window.exit_handler)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
