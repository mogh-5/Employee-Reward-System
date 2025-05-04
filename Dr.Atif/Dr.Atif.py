import tkinter as tk #GUI library name it as tk
from tkinter import messagebox, ttk #Getting tools from library
from datetime import datetime, timedelta, date #Getting date and time from library
import json #save employees data in it
import os #check file exist in computer?

# Enable this during testing to bypass work-hour restriction
TEST_MODE = False  # Set to False in production

DATA_FILE = "employees.json"
HISTORY_FILE = "login_history.txt"

#class employee to give him a username, pass....
class Employee:
    #employee object for info
    def __init__(self, username, password, points=0, redeemed=None, last_login=None):
        self.username = username
        self.password = password
        self.points = points
        self.redeemed = redeemed or []
        self.last_login = last_login


# return employee info in JASON file by this format and save it there
    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
            "points": self.points,
            "redeemed": self.redeemed,
            "last_login": self.last_login
        }

# check if JASON file exist in computer
def load_employees():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f: #open jason file read mode call file f
        data = json.load(f)
        return {u: Employee(**info) for u, info in data.items()}


#function to save employees data in jason file
def save_employees():
    with open(DATA_FILE, "w") as f: #open jason file and write the new employee in the next line
        json.dump({u: e.to_dict() for u, e in employees.items()}, f, indent=4)   # related to how data formated in jason file


#function for login and checking staus(on time, late..)
def log_login(username, status):
    with open(HISTORY_FILE, "a") as f: #open history file to add data
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {username} - {status}\n")   #history file format


#function to detect employee absent
def detect_absences(employee):
    if not employee.last_login: #check if this the employee first time?
        return
    last_date = datetime.strptime(employee.last_login, "%Y-%m-%d").date() #convert it to data so it can be used for calc
    today = date.today() #get today's date

    current = last_date + timedelta(days=1)
    missed_days = 0

    while current < today:
        if current.weekday() < 5:  # Monday to Friday
            missed_days += 1
        current += timedelta(days=1)

    if missed_days > 0:
        penalty = 10 * missed_days
        employee.points -= penalty
        log_login(employee.username, f"Missed {missed_days} day(s) (-{penalty} points)")
        messagebox.showinfo("Absence Detected", f"{missed_days} missed workday(s). -{penalty} points.")

employees = load_employees()
current_employee = None


#login function to get info from user
def login():
    global current_employee, TEST_MODE
    username = entry_username.get()
    password = entry_password.get()

    now = datetime.now().time()

    # Restrict login on weekends (Friday and Saturday) — only if not in test mode
    if not TEST_MODE and date.today().weekday() in [4, 5]:
        messagebox.showwarning("Weekend Login Blocked", "Logins are not allowed on weekends (Friday and Saturday).")
        log_login(username, "Weekend login blocked")
        return

    work_start = datetime.strptime("09:00", "%H:%M").time()
    work_end = datetime.strptime("17:00", "%H:%M").time()

    if not TEST_MODE and not (work_start <= now <= work_end):
        messagebox.showwarning("Out of Work Time", "Login is only allowed between 09:00 and 17:00.")
        log_login(username, "Attempted login outside work hours")
        return

    # (continue with the rest of login logic...)
    employee = employees.get(username) #check if the user exist?
    if employee and employee.password == password: #user found
        current_employee = employee
        today_str = date.today().strftime("%Y-%m-%d")  #check if already logged in today

        if employee.last_login != today_str:
            detect_absences(employee)

            early_start = datetime.strptime("07:00", "%H:%M").time()
            early_end = datetime.strptime("09:30", "%H:%M").time()

            if early_start <= now <= early_end:
                employee.points += 5
                lbl_status.config(text="On time! +5 points")
                log_login(username, "On time")
            else:
                employee.points -= 5
                lbl_status.config(text="Late! -5 points")
                log_login(username, "Late")

            employee.last_login = today_str
            save_employees()
        else:
            lbl_status.config(text="Already logged in today")
            log_login(username, "Already logged in today")

        update_points() #update points in the GUI
    else:
        messagebox.showerror("Login Failed", "Invalid username or password")
        log_login(username, "Failed login")


#Registe func is for new employees
def register():
    #get name and pass written in textboxes
    username = entry_username.get()
    password = entry_password.get()

    if username in employees:
        messagebox.showwarning("User Exists", "This username is already taken.")
    elif not username or not password:
        messagebox.showwarning("Missing Info", "Username and password cannot be empty.")
    else:
        employees[username] = Employee(username, password) #creat new employee object
        save_employees()
        messagebox.showinfo("Success", f"User '{username}' registered.")


#redeem func check for login first and then check points finally redeem
def redeem():
    if not current_employee:
        messagebox.showwarning("Warning", "Please login first.")
        return

    reward = reward_combo.get() #reads what user selected
    costs = {
        "Coffee": 10,
        "Remove Late": 20,
        "Remote Day": 30,
        "Off Day": 50
    }

    cost = costs.get(reward, 0)
    if current_employee.points >= cost:
        current_employee.points -= cost
        current_employee.redeemed.append(reward) #add to employee rewarded list
        messagebox.showinfo("Redeemed", f"You redeemed: {reward}")
        update_points()
        save_employees() #save redeemed items in JASON file
    else:
        messagebox.showerror("Not Enough Points", "You don't have enough points.")


#function to show redeemed list
def view_redeemed():
    if not current_employee:
        messagebox.showwarning("Warning", "Please login first.")
        return

    history = current_employee.redeemed
    if history: # if list not empty
        messagebox.showinfo("Redeemed Rewards", "\n".join(history))
    else:
        messagebox.showinfo("Redeemed Rewards", "No rewards redeemed yet.")


#func for update points
def update_points():
    if current_employee: #check for logged in
        lbl_points.config(text=f"Points: {current_employee.points}") #points format

# GUI setup
root = tk.Tk()
root.title("Employee Login Reward System")
root.geometry("400x420")

tk.Label(root, text="Username:").pack(pady=2)
entry_username = tk.Entry(root)
entry_username.pack()

tk.Label(root, text="Password:").pack(pady=2)
entry_password = tk.Entry(root, show="*")
entry_password.pack()

tk.Button(root, text="Login", command=login).pack(pady=5)
tk.Button(root, text="Register", command=register).pack(pady=5)
tk.Button(root, text="Exit").pack(pady=5)

lbl_points = tk.Label(root, text="Points: 0")
lbl_points.pack()

tk.Label(root, text="Select Reward:").pack(pady=2)
reward_combo = ttk.Combobox(root, values=["Coffee", "Remove Late", "Remote Day", "Off Day"])
reward_combo.pack()

tk.Button(root, text="Redeem Reward", command=redeem).pack(pady=5)
tk.Button(root, text="View Redeemed", command=view_redeemed).pack(pady=5)

lbl_status = tk.Label(root, text="Status: Not logged in")
lbl_status.pack(pady=10)

root.mainloop()