# HealthPlus
CS-310 Software Engineering II 
1. Set up environment/ clone repo / download libararies/ run server
2. Set up IDE:
3.   Download and install VS Code: https://code.visualstudio.com/download
       Install Python, must be version 3.13 or later: https://www.python.org/downloads/ | Use command: python --version | to double check
       Install Git: https://github.com/git-guides/install-git | Use command: git --version | to double check
       Install Postgre SQL: https://www.postgresql.org/download/
     
6. Cloning Repository:
   Open a new project folder in VS Code
   Open the command terminal using CTRL+`
   Use command: git clone <Repo Link>
   
7. Set Environment and Dependencies:
     In the terminal, cd into the project you cloned
     Create a python environment using the command: python -m venv venv
     Activate the environment using the command: .\venv\Scripts\Activate
     You should see (venv) on the left side of the terminal if it worked
     Use the command: pip install -r requirements.txt | to install all libraries and dependencies
     Copy the contents of .env.example into your own .env file, I can supply keys

8. Prepare Database and Groups:
     Use the command: pythone manage.py migrate
     Use the command: python manage.py createsuperuser | follow the prompts and remember your user and password
     Use the command: python manage.py runserver, at the end of IP it provides, add /admin/
     Log into this admin panel using the credentials you created with the superuser command. Navigate to the 'Groups' page
     Create 3 seperate groups named 'Patient', 'Doctor', and 'Receptionist'
    
12. Create a new user and add them to the 'Doctor' group you created.
13. Create a new user and add them to the 'Receptionist' group you created.
