# AttendMe

AttendMe is a comprehensive student management and attendance tracking system built with Django. It streamlines the process of managing classes, enrollments, and attendance for both teachers and students.

## Features

### For Teachers
- **Dashboard:** View upcoming and current classes, and student statistics.
- **Class Management:** Create and update class details.
- **Enrollment Management:** Easily enroll or unenroll students from classes.
- **Attendance Marking:**
    - **Manual:** Mark attendance (Present, Absent, Late) for students manually.
    - **QR Scanner:** Scan student QR codes to quickly mark them as present.
- **Attendance History:** View detailed attendance history for each class, filterable by date.

### For Students
- **Dashboard:** View enrolled classes and attendance performance.
- **QR Code Generation:** Generate a unique QR code for quick attendance scanning.
- **Attendance History:** View personal attendance records for each enrolled class.

## Tech Stack

- **Backend:** Django (Python)
- **Frontend:** HTML, Tailwind CSS (via CDN/Local), JavaScript
- **Database:** SQLite (Default)
- **Libraries:**
    - `html5-qrcode` for QR code scanning.
    - `qrcode.js` for QR code generation.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd AttendMe
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Apply migrations:**
    ```bash
    python manage.py migrate
    ```

5.  **Create a superuser (optional):**
    ```bash
    python manage.py createsuperuser
    ```

6.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```

7.  **Access the application:**
    Open your browser and go to `http://127.0.0.1:8000/`.

## Usage

- **Login:** Users must log in to access the dashboard.
- **Roles:** The system automatically redirects users to the appropriate dashboard (Teacher or Student) based on their profile.
- **Attendance Window:** Attendance can only be marked during the class's scheduled time.

## License

[MIT License](LICENSE)