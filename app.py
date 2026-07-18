from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from datetime import datetime
import os
import math
import certifi

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret-for-local-use")
bcrypt = Bcrypt(app)
client = MongoClient(os.getenv("MONGODB_URI"), tlsCAFile=certifi.where())
db = client["finance_tracker"]

try:
    client.admin.command('ping')
    print("MongoDB Connected Successfully!")
except Exception as e:
    print("Connection Failed:", e)


def is_logged_in():
    return 'username' in session


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/income')
def income_page():
    if not is_logged_in():
        return redirect('/login')
    return render_template('income.html')


@app.route('/add_income', methods=['POST'])
def add_income():
    if not is_logged_in():
        return redirect('/login')

    source = request.form['source']
    amount = request.form['amount']
    month = request.form['month']

    db.income.insert_one({
        "username": session['username'],
        "source": source,
        "amount": float(amount),
        "month": month
    })

    return redirect('/income')


@app.route('/expenses')
def expenses_page():
    if not is_logged_in():
        return redirect('/login')
    return render_template('expenses.html')


@app.route('/add_expense', methods=['POST'])
def add_expense():
    if not is_logged_in():
        return redirect('/login')

    category = request.form['category']
    amount = request.form['amount']
    month = request.form['month']

    db.expenses.insert_one({
        "username": session['username'],
        "category": category,
        "amount": float(amount),
        "month": month
    })

    return redirect('/expenses')


@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        return redirect('/login')

    username = session['username']

    income_data = list(db.income.find({"username": username}))
    expense_data = list(db.expenses.find({"username": username}))

    total_income = sum(item['amount'] for item in income_data)
    total_expenses = sum(item['amount'] for item in expense_data)
    total_savings = total_income - total_expenses

    return render_template('dashboard.html',
                            income_data=income_data,
                            expense_data=expense_data,
                            total_income=total_income,
                            total_expenses=total_expenses,
                            total_savings=total_savings)


@app.route('/goal_planner')
def goal_planner_page():
    return render_template('goal_planner.html')


@app.route('/calculate_goal', methods=['POST'])
def calculate_goal():
    goal_name = request.form['goal_name']
    target_amount = float(request.form['target_amount'])
    monthly_saving = float(request.form['monthly_saving'])
    annual_rate = float(request.form['interest_rate'])

    monthly_rate = (annual_rate / 100) / 12

    n_months = math.log((target_amount * monthly_rate / monthly_saving) + 1) / math.log(1 + monthly_rate)

    months_needed = round(n_months)
    years_needed = round(months_needed / 12, 1)

    return render_template('goal_planner.html',
                            result=True,
                            goal_name=goal_name,
                            target_amount=target_amount,
                            monthly_saving=monthly_saving,
                            months=months_needed,
                            years=years_needed)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = db.users.find_one({"username": username})
        if existing_user:
            return render_template('signup.html', error="Username already taken")

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        db.users.insert_one({
            "username": username,
            "password": hashed_password
        })

        return redirect('/login')

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = db.users.find_one({"username": username})

        if user and bcrypt.check_password_hash(user['password'], password):
            session['username'] = username
            return redirect('/dashboard')
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')
@app.route('/insurance')
def insurance_page():
    if not is_logged_in():
        return redirect('/login')

    username = session['username']
    raw_policies = list(db.insurance.find({"username": username}))

    policies = []
    today = datetime.now()

    for policy in raw_policies:
        due_date = datetime.strptime(policy['due_date'], '%Y-%m-%d')
        days_left = (due_date - today).days

        policies.append({
            "type": policy['type'],
            "premium": policy['premium'],
            "due_date": policy['due_date'],
            "days_left": days_left
        })

    return render_template('insurance.html', policies=policies)


@app.route('/add_insurance', methods=['POST'])
def add_insurance():
    if not is_logged_in():
        return redirect('/login')

    insurance_type = request.form['type']
    premium = float(request.form['premium'])
    due_date = request.form['due_date']

    db.insurance.insert_one({
        "username": session['username'],
        "type": insurance_type,
        "premium": premium,
        "due_date": due_date
    })

    return redirect('/insurance')
@app.route('/advice')
def advice_page():
    if not is_logged_in():
        return redirect('/login')

    username = session['username']

    income_data = list(db.income.find({"username": username}))
    expense_data = list(db.expenses.find({"username": username}))
    insurance_data = list(db.insurance.find({"username": username}))

    total_income = sum(item['amount'] for item in income_data)
    total_expenses = sum(item['amount'] for item in expense_data)
    total_savings = total_income - total_expenses

    tips = []

    if total_income > 0:
        expense_ratio = (total_expenses / total_income) * 100
        savings_ratio = (total_savings / total_income) * 100

        if expense_ratio > 90:
            tips.append({"type": "danger", "message": "You're spending almost all your income. Try to cut down on non-essential expenses."})

        if savings_ratio < 10:
            tips.append({"type": "warning", "message": f"Your savings rate is only {round(savings_ratio,1)}%. Financial experts recommend saving at least 20% of your income."})
        elif savings_ratio > 30:
            tips.append({"type": "success", "message": f"Great job! You're saving {round(savings_ratio,1)}% of your income."})

        # Check spending by category
        category_totals = {}
        for item in expense_data:
            cat = item['category']
            category_totals[cat] = category_totals.get(cat, 0) + item['amount']

        for cat, amount in category_totals.items():
            if total_expenses > 0 and (amount / total_expenses) * 100 > 40:
                tips.append({"type": "warning", "message": f"You're spending {round((amount/total_expenses)*100,1)}% of your expenses on '{cat}'. Consider reducing this."})

    else:
        tips.append({"type": "warning", "message": "You haven't added any income yet. Add your income to get personalized advice."})

    if len(insurance_data) == 0:
        tips.append({"type": "warning", "message": "You don't have any insurance policies tracked. Consider adding health/life insurance for financial protection."})

    return render_template('advice.html', tips=tips, total_income=total_income, total_expenses=total_expenses, total_savings=total_savings)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)