import os
from dotenv import load_dotenv
import gspread
from enum import Enum

load_dotenv() # load all the variables from the env file

class Point(Enum):
    LEAD    = 8
    EVENT   = 9
    P       = 10
    D       = 11
    B       = 12
    SE      = 13

    def __int__(self):
        return self.value

gc = gspread.service_account(filename=os.getenv('GSPREAD_SA_LOC'))

sh = gc.open(os.getenv('GSPREAD_SHEET_ID'))
ws = sh.get_worksheet(0)

def update(user: int, point: Point):
    cell = ws.find(query = str(user))
    val = ws.cell(cell.row, point).value
    val = str(int(val) + 1)
    ws.update_cell(cell.row, point, val)