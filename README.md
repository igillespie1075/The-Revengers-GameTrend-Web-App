Install Python, MySQL Server, and MySQL Workbench.

Download or clone this GitHub Repo

Make sure MySQL Server is running

Run database_setup.sql in MySQL Workbench.

Copy .env.example and rename the copy to .env.

Enter your MySQL username and password in .env.

Install dependencies:
pip install -r requirements.txt

Start the application:
python ProjectBe.py
Open http://127.0.0.1:5000

Ctrl + C in terminal to stop the flask server
