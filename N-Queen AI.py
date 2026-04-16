import tkinter as tk
from tkinter import ttk, messagebox
import time
import heapq

# ====================== ALGORITHM HELPERS ======================

def is_safe(board, row, col):
    """
    Check if placing a queen at (row, col) is safe.
    No other queen should be in the same row or diagonal.
    """
    for c in range(col):
        r = board[c]
        if r == row or abs(r - row) == abs(c - col):
            return False
    return True

def calculate_conflicts(state):
    """
    Calculate total number of conflicts (pairs of queens attacking each other).
    """
    conflicts = 0
    n = len(state)
    for i in range(n):
        for j in range(i + 1, n):
            if state[i] == state[j] or abs(state[i] - state[j]) == abs(i - j):
                conflicts += 1
    return conflicts

def get_neighbors(state):
    """
    Generate all possible neighboring states by moving each queen
    in its column to another row (except current row).
    """
    neighbors = []
    n = len(state)
    for col in range(n):
        for row in range(n):
            if row != state[col]:
                new_state = state.copy()
                new_state[col] = row
                neighbors.append(new_state)
    return neighbors

# ====================== CSP ======================

def solve_csp_from_initial(board, col, n, counter, steps):
    """
    Recursive backtracking CSP solver starting from an initial board.
    - board: current board state
    - col: current column to place a queen
    - n: board size
    - counter: dictionary to track number of iterations
    - steps: list to store board states for visualization
    """
    counter["iter"] += 1               # Increment iteration count
    steps.append(board.copy())          # Save current board for visualization

    if col >= n:                        # Base case: all queens placed
        return True

    user_row = board[col]               # Take user-provided initial position

    # First try initial position if valid
    if 0 <= user_row < n and is_safe(board, user_row, col):
        if solve_csp_from_initial(board, col + 1, n, counter, steps):
            return True

    # Try all other rows
    for row in range(n):
        if row == user_row:
            continue
        board[col] = row
        if is_safe(board, row, col):
            if solve_csp_from_initial(board, col + 1, n, counter, steps):
                return True

    board[col] = -1                     # Reset column if no solution
    steps.append(board.copy())          # Save for visualization
    return False

def csp_solve(initial):
    """
    Wrapper function for CSP solver.
    Returns:
        success: True/False
        iterations: number of recursive calls
        runtime: time in seconds
        steps: list of board states for visualization
        solution: final board if success, else None
    """
    n = len(initial)
    board = initial.copy()
    counter = {"iter": 0}
    steps = []

    start = time.time()
    success = solve_csp_from_initial(board, 0, n, counter, steps)
    runtime = time.time() - start
    return success, counter["iter"], runtime, steps, board if success else None

# ====================== A* ======================

def a_star_solve(initial):
    """
    A* search to solve N-Queens using heuristic = number of conflicts.
    Returns:
        success, iterations, runtime, steps, efficiency, solution
    """
    pq = []
    visited = set()
    h = calculate_conflicts(initial)
    heapq.heappush(pq, (h, 0, initial.copy()))  # f = h + g
    steps = []

    iterations = 0
    start = time.time()

    while pq:
        iterations += 1
        f, g, state = heapq.heappop(pq)
        h = calculate_conflicts(state)
        steps.append(state.copy())  # Save state for visualization

        if h == 0:                  # Solution found
            runtime = time.time() - start
            efficiency = iterations / (runtime + 1e-9)
            return True, iterations, runtime, steps, efficiency, state

        visited.add(tuple(state))

        # Explore neighbors
        for child in get_neighbors(state):
            t = tuple(child)
            if t not in visited:
                g2 = g + 1
                h2 = calculate_conflicts(child)
                f2 = g2 + h2
                heapq.heappush(pq, (f2, g2, child))

    runtime = time.time() - start
    efficiency = iterations / (runtime + 1e-9)
    return False, iterations, runtime, steps, efficiency, None

# ====================== GUI ======================

class NQueensGUI:
    def __init__(self, root):
        """
        Initialize GUI:
        - Input fields
        - CSP & A* boards
        - Information text box
        """
        self.root = root
        self.root.title("N-Queens CSP & A* Visualizer")
        self.root.geometry("950x700")
        self.root.resizable(True, True)
        self.n_var = tk.StringVar()
        self.positions_var = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        """Create all Tkinter widgets: input, boards, info."""
        # ------------------ Main scrollable canvas ------------------
        self.canvas_main = tk.Canvas(self.root)
        self.canvas_main.pack(side="left", fill="both", expand=True)

        scrollbar_main = tk.Scrollbar(self.root, orient="vertical", command=self.canvas_main.yview)
        scrollbar_main.pack(side="right", fill="y")
        self.canvas_main.configure(yscrollcommand=scrollbar_main.set)

        self.frame_main = tk.Frame(self.canvas_main)
        self.canvas_main.create_window((0, 0), window=self.frame_main, anchor="nw")

        def on_frame_configure(event):
            self.canvas_main.configure(scrollregion=self.canvas_main.bbox("all"))
        self.frame_main.bind("<Configure>", on_frame_configure)

        # ------------------ Input Frame ------------------
        frame_input = tk.LabelFrame(self.frame_main, text="Input Configuration", font=("Arial", 12, "bold"))
        frame_input.pack(pady=10, padx=10, fill="x")

        tk.Label(frame_input, text="Board Size (N):", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(frame_input, textvariable=self.n_var, width=5, font=("Arial", 10)).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_input, text="Initial Positions (0-based, space-separated):", font=("Arial", 10)).grid(row=0, column=2, padx=5, pady=5)
        tk.Entry(frame_input, textvariable=self.positions_var, width=30, font=("Arial", 10)).grid(row=0, column=3, padx=5, pady=5)

        tk.Button(frame_input, text="Run Algorithms", command=self.run, font=("Arial", 10, "bold"),
                  bg="#4CAF50", fg="white").grid(row=0, column=4, padx=10)

        # ------------------ Boards Frame ------------------
        self.frame_boards = tk.Frame(self.frame_main)
        self.frame_boards.pack(pady=10)

        self.canvas_csp = None
        self.canvas_astar = None

        # ------------------ Info Frame (scrollable) ------------------
        frame_info = tk.Frame(self.frame_main)
        frame_info.pack(pady=5, padx=10, fill="both", expand=True)

        scrollbar_info = tk.Scrollbar(frame_info)
        scrollbar_info.pack(side="right", fill="y")

        self.info_text = tk.Text(frame_info, height=8, width=115, font=("Arial", 10), yscrollcommand=scrollbar_info.set)
        self.info_text.pack(side="left", fill="both", expand=True, pady=5)
        scrollbar_info.config(command=self.info_text.yview)
        self.info_text.configure(state='normal')

    # ------------------ Board Drawing ------------------
    def draw_board(self, canvas, board, n):
        """Draw chessboard and queens on the canvas."""
        canvas.delete("all")
        size = 35
        colors = ["#F0D9B5", "#B58863"]

        # Draw squares
        for r in range(n):
            for c in range(n):
                color = colors[(r+c)%2]
                canvas.create_rectangle(c*size, r*size, (c+1)*size, (r+1)*size, fill=color, outline="black")

        # Draw queens
        for c, r in enumerate(board):
            if r >= 0:
                x = c*size + size//2
                y = r*size + size//2
                canvas.create_text(x, y, text="♛", font=("Arial", size//2), fill="red")

    def visualize_steps(self, canvas, steps, n, delay=400):
        """Visualize all steps sequentially with delay."""
        if not steps:
            return
        step = steps.pop(0)
        self.draw_board(canvas, step, n)
        self.root.after(delay, lambda: self.visualize_steps(canvas, steps, n, delay))

    # ------------------ Run Algorithms ------------------
    def run(self):
        """Run CSP and A* algorithms, display results and visualize."""
        self.info_text.delete('1.0', tk.END)

        try:
            n = int(self.n_var.get())
            if n < 4 or n > 12:
                messagebox.showerror("Error", "Board size N must be between 4 and 12.")
                return

            initial = list(map(int, self.positions_var.get().strip().split()))
            if len(initial) != n:
                messagebox.showerror("Error", "Initial positions length must equal N.")
                return

        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {e}")
            return

        # Clear previous boards
        for widget in self.frame_boards.winfo_children():
            widget.destroy()

        # Create CSP board
        tk.Label(self.frame_boards, text="CSP Board", font=("Arial", 12, "bold")).grid(row=0, column=0)
        self.canvas_csp = tk.Canvas(self.frame_boards, width=50*n, height=50*n)
        self.canvas_csp.grid(row=1, column=0, padx=20)

        # Create A* board
        tk.Label(self.frame_boards, text="A* Board", font=("Arial", 12, "bold")).grid(row=0, column=1)
        self.canvas_astar = tk.Canvas(self.frame_boards, width=50*n, height=50*n)
        self.canvas_astar.grid(row=1, column=1, padx=20)

        # ------------------ Run CSP ------------------
        success_csp, iters_csp, time_csp, steps_csp, solution_csp = csp_solve(initial)
        self.info_text.insert(tk.END, "==== CSP Results ====\n")
        self.info_text.insert(tk.END, f"Success: {success_csp}\nIterations: {iters_csp}\nTime: {time_csp:.5f} s\nSolution: {solution_csp}\n\n")
        self.visualize_steps(self.canvas_csp, steps_csp.copy(), n, delay=400)

        # ------------------ Run A* ------------------
        success_astar, iters_astar, time_astar, steps_astar, efficiency_astar, solution_astar = a_star_solve(initial)
        self.info_text.insert(tk.END, "==== A* Results ====\n")
        self.info_text.insert(tk.END, f"Success: {success_astar}\nIterations: {iters_astar}\nTime: {time_astar:.5f} s\nSolution: {solution_astar}\n\n")
        self.visualize_steps(self.canvas_astar, steps_astar.copy(), n, delay=400)

# ------------------ Main Program ------------------
if __name__ == "__main__":
    root = tk.Tk()
    gui = NQueensGUI(root)
    root.mainloop()




















