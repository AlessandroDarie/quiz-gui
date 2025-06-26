import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
import json
import time
import random
import os
import string
import glob

PRIMARY   = "#ECECEC"
SECONDARY = "#222831"
ACCENT    = "#00ADB5"
SUCCESS   = "#16C172"
ERROR     = "#F05454"
FONT_BIG = ("Segoe UI", 13)
FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_SMALL = ("Segoe UI", 11)

JSON_FILENAME = "geography.json"

class DatabaseSelector:
    def __init__(self, master):
        self.master = master
        self.master.geometry("720x600")
        self.master.title("Select Database")
        self.master.configure(bg=SECONDARY)

        self.frame = tk.Frame(master, bg=SECONDARY, padx=50, pady=50)
        self.frame.grid(row=0, column=0, sticky="nsew")
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)


        tk.Label(self.frame, text="Select the database to use:", font=FONT_TITLE, bg=SECONDARY, fg=PRIMARY, pady=30).pack()

        json_files = glob.glob("database/*.json")
        if not json_files:
            tk.Label(self.frame, text="No JSON files found in the 'database' folder!", font=FONT_BIG, bg=SECONDARY, fg=ERROR).pack()
            return

        for filename in json_files:
            base = os.path.basename(filename)
            name = os.path.splitext(base)[0]
            btn = tk.Button(
                self.frame, text=name, font=FONT_BIG, bg=ACCENT, fg="white", width=35, pady=2,
                command=lambda f=filename: self.select_db(f)
            )
            btn.pack(pady=5)

        tk.Button(self.frame, text="Exit", font=FONT_BIG, bg="#F05454", fg="white", width=35, pady=2, command=master.destroy).pack(pady=(30,0))

    def select_db(self, filename):
        self.frame.destroy()
        StartScreen(self.master, filename)

class QuizApp:
    def __init__(self, master, questions, mode, filename):
        self.master = master
        self.master.geometry("720x600")
        self.questions = questions
        self.mode = mode
        self.filename = filename
        self.index = 0
        self.score = 0
        self.var = tk.StringVar()
        self.check_vars = []
        self.start_time = time.time()
        self.chrono_id = None
        self.error_questions = []
        self.is_retry = False
        self.setup_ui()
        self.update_chrono()
        self.frame.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        new_wrap = max(300, event.width - 80)
        self.label.config(wraplength=new_wrap)

    def setup_ui(self):
        self.master.title("Quiz GUI")
        self.master.configure(bg=SECONDARY)
        self.container = tk.Frame(self.master, bg=SECONDARY)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        for i in range(3):
            self.container.grid_rowconfigure(i, weight=1)
            self.container.grid_columnconfigure(i, weight=1)

        self.frame = tk.Frame(self.container, bg=SECONDARY, padx=30, pady=30)
        self.frame.grid(row=1, column=1, sticky="nsew")

        self.frame.bind("<Configure>", self.on_resize)

        self.label = tk.Label(self.frame, text="", font=FONT_BIG, bg=SECONDARY, fg=PRIMARY, wraplength=600, justify="left")
        self.label.pack(pady=(0, 15), anchor="center")

        self.opts_frame = tk.Frame(self.frame, bg=SECONDARY)
        self.opts_frame.pack(pady=(0,10), anchor="center")

        self.entry = tk.Entry(self.frame, textvariable=self.var, font=FONT_BIG)

        self.next_btn = tk.Button(self.frame, text="Next question", font=FONT_SMALL, bg=PRIMARY, fg="black", command=self.next_question, activebackground=ACCENT)

        self.feedback = tk.Label(self.frame, text="", font=FONT_SMALL, bg=SECONDARY)
        self.progress = tk.Label(self.frame, text="", font=FONT_SMALL, bg=SECONDARY, fg="#00FF00")
        self.progress.pack(pady=(10,0), anchor="center")

        self.chrono_label = tk.Label(self.frame, text="Elapsed time: 0s", font=FONT_SMALL, bg=SECONDARY, fg=PRIMARY)
        self.chrono_label.pack(pady=(2,10), anchor="center")

        self.button_row = tk.Frame(self.frame, bg=SECONDARY)
        self.submit = tk.Button(
            self.button_row, text="Submit", font=FONT_SMALL, bg=ACCENT,
            fg="white", command=self.check_answer, activebackground=PRIMARY
        )
        self.menu_btn = tk.Button(
            self.button_row, text="Back to menu", font=FONT_SMALL, bg="#CCCCCC",
            fg="#222831", activebackground="#EEEEEE", command=self.back_to_menu
        )
        self.submit.pack(side="left", padx=10)
        self.menu_btn.pack(side="left", padx=10)

        self.next_question()

    def show_feedback(self, text, color):
        self.feedback.config(text=text, fg=color)
        self.feedback.pack(anchor="center")
        self.next_btn.pack(anchor="center")

    def update_chrono(self):
        elapsed = int(time.time() - self.start_time)
        m, s = divmod(elapsed, 60)
        if m:
            self.chrono_label.config(text=f"Elapsed time: {m}m {s}s")
        else:
            self.chrono_label.config(text=f"Elapsed time: {s}s")
        self.chrono_id = self.master.after(1000, self.update_chrono)

    def stop_chrono(self):
        if self.chrono_id:
            self.master.after_cancel(self.chrono_id)
            self.chrono_id = None

    def next_question(self):
        for widget in self.opts_frame.winfo_children():
            widget.destroy()
        self.entry.pack_forget()
        self.next_btn.pack_forget()
        self.button_row.pack_forget()
        self.var.set("")
        self.check_vars = []
        self.feedback.pack_forget()
        self.submit.config(state="normal")
        if self.index >= len(self.questions):
            self.stop_chrono()
            elapsed = int(time.time() - self.start_time)
            m, s = divmod(elapsed, 60)
            time_str = f"{m}m {s}s" if m else f"{s}s"
            score = self.score
            total = len(self.questions)
            errors = total - score

            dialog = EndQuizDialog(self.master, score, total, errors, time_str, errors > 0)
            self.master.wait_window(dialog)
            choice = dialog.result

            if choice == 'errors':
                self.questions = list(self.error_questions)
                self.index = 0
                self.score = 0
                self.error_questions = []
                self.is_retry = True
                self.start_time = time.time()
                self.next_question()
                return
            elif choice == 'shuffle':
                questions = self.questions[:]
                random.shuffle(questions)
                self.questions = questions
                self.index = 0
                self.score = 0
                self.error_questions = []
                self.is_retry = True
                self.start_time = time.time()
                self.next_question()
                return
            else:
                self.container.destroy()
                DatabaseSelector(self.master)
                return


        q = self.questions[self.index]
        if self.mode == "normal":
            self.label.config(text=f"{q['id']}. {q['question']}")
        else:
            self.label.config(text=f"{q['question']}")
        self.progress.config(text=f"Question {self.index+1} of {len(self.questions)} | Score: {self.score}")

        if q["type"] == "crocette":
            option_items = list(q["options"].items())
            random.shuffle(option_items)
            new_letters = list(string.ascii_uppercase)
            self.letter_map = {}
            self.answer_letters = set()
            self.check_vars = []
            for idx, (old_letter, text) in enumerate(option_items):
                new_letter = new_letters[idx]
                self.letter_map[new_letter] = old_letter
                if old_letter in [ans.strip() for ans in q["answer"].split(',')]:
                    self.answer_letters.add(new_letter)
                v = tk.IntVar()
                cb = tk.Checkbutton(
                    self.opts_frame, text=f"{new_letter}: {text}", variable=v,
                    bg=SECONDARY, fg="white", selectcolor="#000000",
                    font=FONT_SMALL, anchor="w", padx=10
                )
                cb.pack(anchor="w", pady=2)
                self.check_vars.append((new_letter, v))
            self.button_row.pack(pady=(10,0), anchor="center")
        else:
            self.entry.pack(pady=(5,5), ipadx=10, ipady=5, anchor="center")
            self.button_row.pack(pady=(10,0), anchor="center")


    def check_answer(self):
        q = self.questions[self.index]
        correct = False
        if q["type"] == "crocette":
            answers = [letter for letter, v in self.check_vars if v.get()]
            if set(answers) == self.answer_letters:
                correct = True
        else:
            if self.var.get().strip().lower() == q['answer'].lower():
                correct = True
        if correct:
            self.score += 1
            self.show_feedback("Correct!", SUCCESS)
        else:
            self.error_questions.append(q)
            if q["type"] == "crocette":
                resp = ','.join(sorted(self.answer_letters))
                text = f"Incorrect. Correct answer: {resp}"
            else:
                text = f"Incorrect. Correct answer: {q['answer']}"
            self.show_feedback(text, ERROR)
        self.submit.config(state="disabled")
        self.index += 1

    def back_to_menu(self):
        self.stop_chrono()
        self.container.destroy()
        StartScreen(self.master, self.filename)

class EndQuizDialog(tk.Toplevel):
    def __init__(self, parent, score, total, errors, elapsed, has_errors):
        super().__init__(parent)
        self.result = None
        self.title("Quiz finished")
        self.configure(bg=SECONDARY)
        self.geometry("380x280")
        msg = f"Quiz finished!\nYou scored {score}/{total}.\nTotal time: {elapsed}\n"
        if has_errors:
            msg += f"You made {errors} mistake{'s' if errors != 1 else ''}."
        else:
            msg += "All answers are correct!"

        label = tk.Label(self, text=msg, font=FONT_BIG, bg=SECONDARY, fg=PRIMARY, wraplength=340, justify="center")
        label.pack(pady=(25,18))

        btn_frame = tk.Frame(self, bg=SECONDARY)
        btn_frame.pack(pady=5)

        if has_errors:
            tk.Button(btn_frame, text="Retry only wrong answers", width=28, font=FONT_SMALL, bg=ACCENT, fg="white",
                      command=lambda: self._set_and_close('errors')).pack(pady=4)
        tk.Button(btn_frame, text="Retry all questions (shuffle)", width=28, font=FONT_SMALL, bg=ACCENT, fg="white",
                  command=lambda: self._set_and_close('shuffle')).pack(pady=4)
        tk.Button(btn_frame, text="Back to menu", width=28, font=FONT_SMALL, bg="#CCCCCC", fg="#222831",
                  command=lambda: self._set_and_close('menu')).pack(pady=4)

        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: self._set_and_close('menu'))

    def _set_and_close(self, result):
        self.result = result
        self.grab_release()
        self.destroy()

class StartScreen:
    def __init__(self, master, filename):
        self.master = master
        self.master.geometry("720x600")
        self.filename = filename
        self.questions = self.load_questions()
        self.master.title("Quiz - Select mode")
        self.master.configure(bg=SECONDARY)
        self.container = tk.Frame(self.master, bg=SECONDARY)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        for i in range(3):
            self.container.grid_rowconfigure(i, weight=1)
            self.container.grid_columnconfigure(i, weight=1)

        self.frame = tk.Frame(self.container, bg=SECONDARY, padx=50, pady=50)
        self.frame.grid(row=1, column=1, sticky="nsew")

        name = os.path.splitext(os.path.basename(filename))[0]
        self.title = tk.Label(self.frame, text=name, font=FONT_TITLE, bg=SECONDARY, fg=PRIMARY, pady=40, wraplength=600)
        self.title.pack(anchor="center")
        self.frame.bind("<Configure>", self.on_resize)

        self.normal_btn = tk.Button(self.frame, text="Ordered mode", font=FONT_BIG, bg=ACCENT, fg="white", width=25, pady=1, command=self.start_normal, activebackground=PRIMARY)
        self.normal_btn.pack(pady=(30,10), anchor="center")
        self.shuffle_btn = tk.Button(self.frame, text="Shuffle mode", font=FONT_BIG, bg=ACCENT, fg="white", width=25, pady=1, command=self.start_shuffle, activebackground=PRIMARY)
        self.shuffle_btn.pack(pady=(0,10), anchor="center")
        self.crocette_btn = tk.Button(self.frame, text="Multiple choice only (ordered)", font=FONT_BIG, bg=ACCENT, fg="white", width=25, pady=1, command=self.start_crocette, activebackground=PRIMARY)
        self.crocette_btn.pack(pady=(0,10), anchor="center")
        self.crocette_shuffle_btn = tk.Button(self.frame,text="Multiple choice only (shuffle)",font=FONT_BIG,bg=ACCENT,fg="white",width=25,pady=1,command=self.start_crocette_shuffle,activebackground=PRIMARY)
        self.crocette_shuffle_btn.pack(pady=(0,10), anchor="center")
        self.dariempire_btn = tk.Button(self.frame, text="Fill in the blank only (ordered)", font=FONT_BIG, bg=ACCENT, fg="white", width=25, pady=1, command=self.start_dariempire, activebackground=PRIMARY)
        self.dariempire_btn.pack(pady=(0,10), anchor="center")
        self.dariempire_shuffle_btn = tk.Button(self.frame,text="Fill in the blank only (shuffle)",font=FONT_BIG,bg=ACCENT,fg="white",width=25,pady=1,command=self.start_dariempire_shuffle,activebackground=PRIMARY)
        self.dariempire_shuffle_btn.pack(pady=(0,10), anchor="center")
        self.back_btn = tk.Button(self.frame, text="Back", font=FONT_BIG, bg="#F05454", fg="white", width=25, pady=1, command=self.back_to_dbselect, activebackground="#B22222")
        self.back_btn.pack(pady=(2, 0), anchor="center")

    def on_resize(self, event):
        new_wrap = max(300, event.width - 80)
        self.title.config(wraplength=new_wrap)

    def load_questions(self):
        with open(self.filename, "r", encoding="utf-8") as f:
            return json.load(f)

    def start_normal(self):
        self.frame.destroy()
        tot = len(self.questions)
        interval = simpledialog.askstring(
            "Question range",
            f"There are {tot} questions in the database.\nEnter the desired range (e.g., 1-30, or leave empty for all):",
            parent=self.master,
        )
        if interval:
            try:
                if "-" in interval:
                    start, end = [int(x) for x in interval.split("-")]
                    start = max(1, start)
                    end = min(tot, end)
                    if start <= end:
                        selected = self.questions[start-1:end]
                    else:
                        selected = self.questions
                else:
                    n = int(interval)
                    selected = self.questions[:n]
            except:
                selected = self.questions
        else:
            selected = self.questions
        QuizApp(self.master, selected, "normal", self.filename)

    def start_shuffle(self):
        self.frame.destroy()
        tot = len(self.questions)
        n = simpledialog.askinteger(
            "How many questions?",
            f"There are {tot} questions in the database. How many do you want to do?",
            parent=self.master,
            minvalue=1, maxvalue=tot
        )
        questions = self.questions[:]
        random.shuffle(questions)
        if n is not None and n < tot:
            selected = questions[:n]
        else:
            selected = questions
        QuizApp(self.master, selected, "shuffle", self.filename)

    def start_crocette(self):
        self.frame.destroy()
        crocette = [q for q in self.questions if q.get("type") == "crocette"]
        tot = len(crocette)
        interval = simpledialog.askstring(
            "Range of multiple choice questions",
            f"There are {tot} multiple choice questions in the database.\nEnter the desired range (e.g., 1-30, or leave empty for all):",
            parent=self.master,
        )
        if interval:
            try:
                if "-" in interval:
                    start, end = [int(x) for x in interval.split("-")]
                    start = max(1, start)
                    end = min(tot, end)
                    if start <= end:
                        selected = crocette[start-1:end]
                    else:
                        selected = crocette
                else:
                    n = int(interval)
                    selected = crocette[:n]
            except:
                selected = crocette
        else:
            selected = crocette
        QuizApp(self.master, selected, "normal", self.filename)

    def start_crocette_shuffle(self):
        self.frame.destroy()
        crocette = [q for q in self.questions if q.get("type") == "crocette"]
        tot = len(crocette)
        n = simpledialog.askinteger(
            "How many questions?",
            f"There are {tot} multiple choice questions in the database. How many do you want to do?",
            parent=self.master,
            minvalue=1, maxvalue=tot
        )
        random.shuffle(crocette)
        if n is not None and n < tot:
            selected = crocette[:n]
        else:
            selected = crocette
        QuizApp(self.master, selected, "shuffle", self.filename)

    def start_dariempire(self):
        self.frame.destroy()
        dariempire = [q for q in self.questions if q.get("type") == "dariempire"]
        tot = len(dariempire)
        n = simpledialog.askinteger(
            "How many questions?",
            f"There are {tot} fill-in-the-blank questions in the database. How many do you want to do?",
            parent=self.master,
            minvalue=1, maxvalue=tot
        )
        if n is not None and n < tot:
            selected = dariempire[:n]
        else:
            selected = dariempire
        QuizApp(self.master, selected, "normal", self.filename)

    def start_dariempire_shuffle(self):
        self.frame.destroy()
        dariempire = [q for q in self.questions if q.get("type") == "dariempire"]
        tot = len(dariempire)
        n = simpledialog.askinteger(
            "How many questions?",
            f"There are {tot} fill-in-the-blank questions in the database. How many do you want to do?",
            parent=self.master,
            minvalue=1, maxvalue=tot
        )
        random.shuffle(dariempire)
        if n is not None and n < tot:
            selected = dariempire[:n]
        else:
            selected = dariempire
        QuizApp(self.master, selected, "shuffle", self.filename)

    def back_to_dbselect(self):
        self.container.destroy()
        DatabaseSelector(self.master)

if __name__ == "__main__":
    root = tk.Tk()
    DatabaseSelector(root)
    root.mainloop()
