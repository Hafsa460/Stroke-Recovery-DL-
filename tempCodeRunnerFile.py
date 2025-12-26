# stroke_recovery_game/main.py

import tkinter as tk
from level1 import run_level1
from level2 import run_level2
from level3 import run_level3
from level4 import run_level4
from level5 import run_game , GripStrengthGame
from level6 import run_level6
from level7 import run_game,BalanceAndHold

root = tk.Tk()
root.title("Stroke Recovery Game")
root.geometry("640x480")

level_unlocked = {1: True, 2: False, 3: False, 4: False, 5: False, 6: False, 7: False}
# Accuracy tracking
level_accuracy = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}

def run_level1_wrapper():
    run_level1(root, level_unlocked, show_main_menu, run_level2_wrapper,run_level1_wrapper)

def run_level2_wrapper():
    run_level2(root, level_unlocked, show_main_menu, run_level3_wrapper,run_level2_wrapper)

def run_level3_wrapper():
    print("Running Level 3")
    run_level3(root, level_unlocked, show_main_menu, run_level4_wrapper,run_level3_wrapper)

def run_level4_wrapper():
    print("Running Level 4")
    run_level4(root, level_unlocked, show_main_menu, run_level5_wrapper,run_level4_wrapper)

def run_level5_wrapper():
    run_game(root,GripStrengthGame, level_unlocked, show_main_menu, run_level6_wrapper,run_level5_wrapper)

def run_level6_wrapper():
     run_level6(root, level_unlocked, show_main_menu, run_level1_wrapper,run_level6_wrapper)

def run_level7_wrapper():
    run_game(root,BalanceAndHold, level_unlocked, show_main_menu, run_level2_wrapper,run_level7_wrapper)
# ─────────────────────────────────────────────────────────────────────────────

def show_main_menu():
    for widget in root.winfo_children():
        widget.destroy()

    tk.Label(root, text="Stroke Recovery Game", font=("Arial", 24)).pack(pady=20)
    tk.Button(root, text="Play", font=("Arial", 16), command=show_level_menu).pack(pady=10)
    tk.Button(root, text="How to Play", font=("Arial", 16), command=show_how_to_play).pack(pady=10)
    tk.Button(root, text="About", font=("Arial", 16), command=show_about).pack(pady=10)

def show_level_menu():
    for widget in root.winfo_children():
        widget.destroy()

    tk.Label(root, text="Select Level", font=("Arial", 24)).pack(pady=20)

    # Level wrapper map
    level_wrappers = {
        1: run_level7_wrapper, 
        2: run_level2_wrapper,
        3: run_level3_wrapper,
        4: run_level4_wrapper,
        5 : run_level5_wrapper,
        6 : run_level6_wrapper,
        7:  run_level1_wrapper,
    }
    
    for lvl in range(1, 8):
        if level_unlocked[lvl]:
            tk.Button(root, text=f"Level {lvl}", font=("Arial", 16),
                      command=level_wrappers.get(lvl, lambda: None)).pack(pady=5)
        else:
            tk.Label(root, text=f"Level {lvl} (Locked)", font=("Arial", 14)).pack(pady=5)

    tk.Button(root, text="Back", font=("Arial", 14), command=show_main_menu).pack(pady=20)

def show_how_to_play():
    for widget in root.winfo_children():
        widget.destroy()

    tk.Label(root, text="How to Play", font=("Arial", 24)).pack(pady=20)
    tk.Label(root, text=(
        "Level 1: Grab the green ball using your index and thumb and place it on the red circle.\n"
        "Level 2: Drag shapes from the left side and place them into the correct outlines on the right.\n"
        "Level 3: Drag colored balls into matching baskets."
    ), font=("Arial", 14), wraplength=600, justify="left").pack(pady=10)
    tk.Button(root, text="Back", font=("Arial", 14), command=show_main_menu).pack(pady=20)

def show_about():
    for widget in root.winfo_children():
        widget.destroy()

    tk.Label(root, text="About the Game", font=("Arial", 24)).pack(pady=20)
    tk.Label(root, text=(
        "This stroke recovery game helps patients practice precise hand movements.\n"
        "Developed by a dedicated team to aid rehabilitation through interactive gameplay."
    ), font=("Arial", 14), wraplength=600, justify="left").pack(pady=10)
    tk.Button(root, text="Back", font=("Arial", 14), command=show_main_menu).pack(pady=20)

# Start the game
show_main_menu()
root.mainloop()
