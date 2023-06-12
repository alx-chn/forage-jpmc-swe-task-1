# JPMC Task 1
Starter repo for task 1 of the JPMC software engineering program

python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt

python server3.py
python client3.py

netstat -ano | findstr :8080
for /f "tokens=5" %a in ('netstat -ano ^| findstr :8080') do taskkill /f /pid %a
