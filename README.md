# URL Status Checker 🌐

A modern and beginner-friendly Python application that checks whether websites are online or offline using HTTP requests.

This project supports:
- Multithreading
- Retry handling
- Response time measurement
- Exporting reports
- Professional GUI using Tkinter

---

# 🚀 Features

- Check single or multiple URLs
- HTTP status code detection
- Online / Redirect / Error classification
- Multithreaded URL checking
- Retry failed requests automatically
- Response time monitoring
- Invalid URL validation
- Export reports as CSV or TXT
- Real-time progress tracking
- Continuous monitoring mode
- Professional dark-themed GUI
- Beginner-friendly Python structure

---

# 🛠 Technologies Used

- Python
- requests
- tkinter
- threading
- concurrent.futures
- csv
- colorama

---

# 📂 Project Structure

```bash
url-status-checker/
│
├── checker_gui.py        # Main GUI application
├── requirements.txt      # Project dependencies
├── reports/              # Exported reports
└── README.md             # Documentation
```

---

# 📦 Installation

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/url-status-checker.git
cd url-status-checker
```

---

## 2. Create Virtual Environment (Optional)

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

---

# 📥 Install Dependencies

```bash
pip install -r requirements.txt
```

---

# ▶ Run the Project

```bash
python checker_gui.py
```

---

# 🌐 Example URLs

```text
https://www.google.com
https://github.com
https://openai.com
https://example.com
```

---

# 📊 Status Categories

| Status Type | Meaning |
|---|---|
| ✅ Online | Website is working properly |
| 🔄 Redirected | Website redirects to another page |
| ⚠️ Client Error | 4xx errors like 404 |
| ❌ Server Error | 5xx server-side errors |
| 🚫 Invalid URL | Incorrect URL format |
| 💥 Unreachable | Connection or timeout error |

---

# 📄 Export Reports

The application supports exporting results into:

- `.csv`
- `.txt`

Reports include:
- URL
- Status Code
- Status Label
- Response Time
- Error Message
- Checked Time

---

# 🧠 Core Concepts Learned

This project helps you practice:

- HTTP Requests
- GUI Development with Tkinter
- Multithreading
- Exception Handling
- File Exporting
- Regex Validation
- Real-time UI updates
- Clean Python Architecture

---

# ⚙ Example Workflow

1. Enter URLs
2. Click **Check URLs**
3. Monitor live results
4. Export report if needed

---

# 📌 requirements.txt

```txt
requests>=2.31.0
colorama>=0.4.6
```

---

# 💡 Future Improvements

- Add charts and analytics
- Add website uptime history
- Add API mode
- Add dark/light theme switch
- Add database storage
- Add notification system
- Add ping and DNS lookup
- Add mobile app version

---

# 🖥 GUI Preview Features

- Dark modern UI
- Live logging system
- Progress bar
- Status table
- Summary dashboard
- Continuous monitoring mode

---

# 🔒 Error Handling

The project handles:
- Invalid URLs
- Connection errors
- Timeout errors
- Redirect loops
- Unexpected exceptions

---

# 👨‍💻 Beginner Tips

If you're new to Python:

- Start by understanding `requests.get()`
- Learn threading slowly
- Practice exception handling
- Try modifying the GUI colors and layout

---

# 📚 Learning Outcome

After building this project, you will understand:

- Real-world HTTP request handling
- Building professional desktop applications
- Working with APIs and networking
- Writing scalable Python code

---

# 📜 License

This project is open-source and free to use for learning purposes.

---

# ❤️ Author

Developed with Python for learning networking, GUI development, and real-world programming concepts.
