import tkinter
import random
import time
import sys
from threading import Thread
from PIL import Image, ImageTk

master=tkinter.Tk()
master.title("Minesweeper")
master.geometry("1000x1000")

NUM_ROWS = 30
NUM_COLS = 20
NUM_MINES = 150
BUTTONS = []
SQUARES = []
CLICKED = []
SLEEP_TIME = 0.1
TRACKED_MINES = []

image = Image.open("flag.png")
image = image.resize((10, 10), Image.Resampling.LANCZOS)
flag = ImageTk.PhotoImage(image)

is_first_click = True

def is_in_bounds(row, col):
    return row >= 0 and row < NUM_ROWS and col >= 0 and col < NUM_COLS

def get_neighbors(row, col):
    neighbors = []
    for i in range(-1, 2):
        for j in range(-1, 2):
            if i == 0 and j == 0:
                continue
            new_row = row + i
            new_col = col + j
            if not is_in_bounds(new_row, new_col):
                continue
            neighbors.append((new_row, new_col))
    return neighbors

def get_neighbors_no_diagonals(row, col):
    neighbors = []
    for i in range(-1, 2):
        for j in range(-1, 2):
            if not ((i != 0 and j == 0) or (i == 0 and j != 0)):
                continue
            new_row = row + i
            new_col = col + j
            if not is_in_bounds(new_row, new_col):
                continue
            neighbors.append((new_row, new_col))
    return neighbors

def count_around(row, col):
    count = 0
    for new_row, new_col in get_neighbors(row, col):
        is_mine = SQUARES[new_row][new_col]
        if is_mine:
            count += 1
    return count

def handle_first_click(row, col):
    is_mine = SQUARES[row][col]
    mine_count = count_around(row, col)
    while is_mine or mine_count > 0:
        setup_squares()
        is_mine = SQUARES[row][col]
        mine_count = count_around(row, col)
    on_click(row, col)

def on_click(row, col):
    global is_first_click
    if is_first_click:
        is_first_click = False
        handle_first_click(row, col)
        return

    if CLICKED[row][col]:
        return
    CLICKED[row][col] = True
    button = BUTTONS[row][col]
    is_mine = SQUARES[row][col]

    if is_mine:
       button.configure(text="M")
       sys.exit("You lose!")
    else:
        mine_count = count_around(row, col)
        button.configure(text=str(mine_count))
        if mine_count == 0:
            for new_row, new_col in get_neighbors_no_diagonals(row, col):
                if not SQUARES[new_row][new_col]:
                    on_click(new_row, new_col)

def create_on_click_lambda(i, j):
    return lambda: on_click(i, j)

def setup_grid():
    for i in range(NUM_ROWS):
        BUTTONS.append([])
        for j in range(NUM_COLS):
            button = tkinter.Button(master, text=" ", command=create_on_click_lambda(i, j))
            button.grid(row=i, column=j)
            BUTTONS[i].append(button)

def setup_squares():
    global SQUARES
    global CLICKED
    global TRACKED_MINES
    SQUARES = []
    CLICKED = []
    num_mines_left = NUM_MINES
    num_squares_left = NUM_ROWS * NUM_COLS

    for i in range(NUM_ROWS):
        SQUARES.append([])
        CLICKED.append([])
        TRACKED_MINES.append([])
        for j in range(NUM_COLS):
            is_mine = random.uniform(0, 1) <= num_mines_left / num_squares_left
            if is_mine:
                SQUARES[i].append(True)
                num_mines_left -= 1
            else:
                SQUARES[i].append(False)
            num_squares_left -= 1
            CLICKED[i].append(False)
            TRACKED_MINES[i].append(False)

def predict_mine(row, col):
    TRACKED_MINES[row][col] = True
    BUTTONS[row][col].configure(image = flag)

def sleep():
    pass
    #time.sleep(SLEEP_TIME)

def is_tracked_mines_consistent():
    for row in range(NUM_ROWS):
        for col in range(NUM_COLS):
            if not CLICKED[row][col]:
                continue
            mine_count = count_around(row, col)
            neighbors = get_neighbors(row, col)
            tracked_mine_count = 0
            free_square_count = 0
            for i, j in neighbors:
                if not CLICKED[i][j]:
                    free_square_count += 1
                elif TRACKED_MINES[i][j]:
                    tracked_mine_count += 1
            if tracked_mine_count > mine_count or tracked_mine_count + free_square_count < mine_count:
                return False
    return True

def get_all_combos(candidates, combo_size):
    if combo_size == 0:
        return [[]]
    if len(candidates) == 0:
        return []
    if len(candidates) == combo_size:
        return [candidates.copy()]
    if len(candidates) < combo_size:
        return []

    combos = []
    combos.extend(get_all_combos(candidates[1:], combo_size))

    sub_combos = get_all_combos(candidates[1:], combo_size - 1)
    for c in sub_combos:
        combos.append([candidates[0]] + c)
    return combos

def check_if_anything_has_too_many_tracked_mines():
    for row in range(NUM_ROWS):
        for col in range(NUM_COLS):
            mine_count = count_around(row, col)
            tracked_count = 0
            for i, j in get_neighbors(row, col):
                if TRACKED_MINES[i][j]:
                    tracked_count += 1
            if tracked_count > mine_count:
                return True
    return False

# Returns true if try_track_mines is possible
def oracle_recurse_is_combo_possible(try_track_mines):
    print('oracle_recurse_is_combo_possible', try_track_mines)

    for i, j in try_track_mines:
        TRACKED_MINES[i][j] = True

    if check_if_anything_has_too_many_tracked_mines():
        for i, j in try_track_mines:
            TRACKED_MINES[i][j] = False
        return False

    anything_all_combos_invalid = oracle_check_if_anything_has_all_combos_invalid()

    for i, j in try_track_mines:
        TRACKED_MINES[i][j] = False

    return not anything_all_combos_invalid

def oracle_check_if_anything_has_all_combos_invalid():
    print('oracle_check_if_anything_has_all_combos_invalid')

    for row in range(NUM_ROWS):
        for col in range(NUM_COLS):
            if not CLICKED[row][col]:
                return []
            mine_count = count_around(row, col)
            if mine_count == 0:
                continue

            num_mines_left = mine_count
            candidates = []
            for i, j in get_neighbors(row, col):
                if TRACKED_MINES[i][j]:
                    num_mines_left -= 1
                elif not CLICKED[i][j]:
                    candidates.append((i, j))

            if num_mines_left == 0:
                continue
            combos = get_all_combos(candidates, num_mines_left)
            any_possible = False
            for combo in combos:
                if oracle_recurse_is_combo_possible(combo):
                    any_possible = True
                    break

            if not any_possible:
                return True
    return False
            

# If row, col is clicked with non-zero mine count, return whether we know for sure
# what the mines around it are
def oracle_predict_mines(row, col):
    print('oracle_predict_mines', row, col)

    if not CLICKED[row][col]:
        return []
    mine_count = count_around(row, col)
    if mine_count == 0:
        return []

    num_mines_left = mine_count
    candidates = []
    for i, j in get_neighbors(row, col):
        if TRACKED_MINES[i][j]:
            num_mines_left -= 1
        elif not CLICKED[i][j]:
            candidates.append((i, j))

    if num_mines_left == 0:
        return []
    if len(candidates) == num_mines_left:
        return candidates
    if len(candidates) < num_mines_left:
        raise Exception("Impossible situation")

    combos = get_all_combos(candidates, num_mines_left)
    possible_combos = []

    for combo in combos:
        result = oracle_recurse_is_combo_possible(combo)
        print(combo, "is possible ? ", result)
        if result:
            possible_combos.append(combo)

    if len(possible_combos) == 1:
        return possible_combos[0]
    return []


def oracle_predict_safe(row, col):
    if not CLICKED[row][col]:
        return []
    mine_count = count_around(row, col)
    if mine_count == 0:
        return []
    num_mines_left = mine_count
    candidates = []
    for i, j in get_neighbors(row, col):
        if TRACKED_MINES[i][j]:
            num_mines_left -= 1
        elif not CLICKED[i][j]:
            candidates.append((i, j))
    if num_mines_left == 0:
        return candidates
    return []


def is_game_done():
    for row in range(NUM_ROWS):
        for col in range(NUM_COLS):
            if CLICKED[row][col] or TRACKED_MINES[row][col]:
                continue
            return False
    return True


def check_win():
    for row in range(NUM_ROWS):
        for col in range(NUM_COLS):
            if TRACKED_MINES[row][col] != SQUARES[row][col]:
                return False
    return True
        

def minesweeper_ai():
    sleep()
    row, col = random.randint(0, NUM_ROWS-1), random.randint(0, NUM_COLS-1)
    print(row, col)
    on_click(row, col)
    sleep()

    while not is_game_done():
        predicted_something = False

        for row in range(NUM_ROWS):
            for col in range(NUM_COLS):
                predict_mines = oracle_predict_mines(row, col)
                for i, j in predict_mines:
                    print("Predicting mine", i, j)
                    predict_mine(i, j)
                    predicted_something = True
                    sleep()

                predict_safe = oracle_predict_safe(row, col)
                for i, j in predict_safe:
                    print("Predicting safe", i, j)
                    on_click(i, j)
                    predicted_something = True
                    sleep()

        if not predicted_something:
            print("I don't know anything, random guessing")
            row, col = random.randint(0, NUM_ROWS-1), random.randint(0, NUM_COLS-1)
            print(row, col)
            on_click(row, col)
            sleep()

    print("Done game")
    if check_win():
        print("You win!")
    else:
        print("You lose!")
                    
            
def main():
    setup_grid()
    setup_squares()

    thread = Thread(target=lambda: minesweeper_ai())
    thread.start()

    master.mainloop()
    thread.join()
    
    
random.seed(125)
main()