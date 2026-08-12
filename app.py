from flask import Flask, render_template, request, redirect, session, send_file, flash, jsonify
from pymongo import MongoClient
from parser_engine import process_dataframe
from transaction_service import process_transactions, save_transactions
from statement_reader import read_statement
from statement_analysis import analyze_statement_data
from bson import ObjectId
from column_mapper import normalize_columns
from datetime import datetime
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from email_utils import generate_otp, send_otp_email
from datetime import datetime
from calculations import calculate_months_needed
from werkzeug.utils import secure_filename
from pypdf import PdfReader, PdfWriter
import tempfile
import os
import math
import certifi
import pandas as pd
def make_json_safe(value):

    

    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, dict):
        return {
            key: make_json_safe(val)
            for key, val in value.items()
        }

    if isinstance(value, list):
        return [
            make_json_safe(item)
            for item in value
        ]

    return value
from io import BytesIO
from flask import send_file
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from reportlab.platypus import KeepTogether


load_dotenv()

app = Flask(__name__)

app.config["PROFILE_FOLDER"] = "static/uploads/profiles"
app.config["STATEMENT_FOLDER"] = "static/uploads/statements"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
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

    username = session["username"]

    income_data = list(
        db.income.find({"username": username})
    )

    total_income = sum(
        item["amount"] for item in income_data
    )

    current_month = datetime.now().strftime("%B")

    monthly_income = sum(
        item["amount"]
        for item in income_data
        if item["month"] == current_month
    )

    total_entries = len(income_data)

    return render_template(

        "income.html",

        income_data=income_data,

        total_income=total_income,

        monthly_income=monthly_income,

        total_entries=total_entries

    )


@app.route('/add_income', methods=['POST'])
def add_income():

    if not is_logged_in():
        return redirect('/login')

    source = request.form['source'].strip()

    amount = float(request.form['amount'])

    # Month always save in proper format
    month = request.form['month'].strip().title()

    db.income.insert_one({
        "username": session['username'],
        "source": source,
        "amount": amount,
        "month": month
    })

    return redirect('/income')


@app.route('/expenses')
def expenses_page():

    if not is_logged_in():
        return redirect('/login')

    username = session["username"]

    expense_data = list(
        db.expenses.find({"username": username})
    )

    total_expenses = sum(
        item["amount"] for item in expense_data
    )

    current_month = datetime.now().strftime("%B")

    monthly_expenses = sum(
        item["amount"]
        for item in expense_data
        if item["month"] == current_month
    )

    total_entries = len(expense_data)

    return render_template(

        "expenses.html",

        expense_data=expense_data,

        total_expenses=total_expenses,

        monthly_expenses=monthly_expenses,

        total_entries=total_entries

    )


@app.route('/add_expense', methods=['POST'])
def add_expense():
    if not is_logged_in():
        return redirect('/login')

    category = request.form['category'].strip()
    amount = request.form['amount']
    month = request.form['month'].strip()

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

    username = session["username"]

    # =====================================================
    # SAFE NUMBER
    # =====================================================

    def safe_float(value):

        try:

            if value is None:
                return 0.0

            if isinstance(value, str):

                value = (
                    value
                    .replace(",", "")
                    .replace("₹", "")
                    .replace("Rs.", "")
                    .replace("Rs", "")
                    .strip()
                )

                if value == "":
                    return 0.0

            number = float(value)

            # NaN / Infinity protection
            if math.isnan(number) or math.isinf(number):
                return 0.0

            return number

        except (ValueError, TypeError):

            return 0.0

    # =====================================================
    # CURRENT MONTH
    # =====================================================

    current_month = datetime.now().strftime("%B")

    current_year = datetime.now().year

    # =====================================================
    # BUDGET
    # =====================================================

    budget_doc = db.budget.find_one({
        "username": username,
        "month": current_month
    })

    if budget_doc:

        budget_amount = safe_float(
            budget_doc.get("budget", 0)
        )

    else:

        budget_amount = 0.0

    # =====================================================
    # MANUAL INCOME
    # =====================================================

    income_data = list(
        db.income.find({
            "username": username
        })
    )

    # =====================================================
    # MANUAL EXPENSE
    # =====================================================

    expense_data = list(
        db.expenses.find({
            "username": username
        })
    )

    # =====================================================
    # IMPORTED BANK TRANSACTIONS
    # =====================================================

    bank_transactions = list(
        db.transactions.find({
            "username": username
        })
    )

    # =====================================================
    # MANUAL TOTAL INCOME
    # =====================================================

    manual_income = 0.0

    for item in income_data:

        manual_income += safe_float(
            item.get("amount", 0)
        )

    # =====================================================
    # MANUAL TOTAL EXPENSE
    # =====================================================

    manual_expenses = 0.0

    for item in expense_data:

        manual_expenses += safe_float(
            item.get("amount", 0)
        )

    # =====================================================
    # BANK TOTAL INCOME
    #
    # Credit = Money received
    # =====================================================

    bank_income = 0.0

    for transaction in bank_transactions:

        bank_income += safe_float(
            transaction.get("credit", 0)
        )

    # =====================================================
    # BANK TOTAL EXPENSE
    #
    # Debit = Money spent
    # =====================================================

    bank_expenses = 0.0

    for transaction in bank_transactions:

        bank_expenses += safe_float(
            transaction.get("debit", 0)
        )

    # =====================================================
    # FINAL TOTALS
    # =====================================================

    total_income = (
        manual_income +
        bank_income
    )

    total_expenses = (
        manual_expenses +
        bank_expenses
    )

    total_savings = (
        total_income -
        total_expenses
    )

    # =====================================================
    # REMAINING BUDGET
    # =====================================================

    remaining_budget = (
        budget_amount -
        total_expenses
    )

    # =====================================================
    # MONTHLY MANUAL INCOME
    # =====================================================

    monthly_manual_income = 0.0

    for item in income_data:

        if item.get("month") == current_month:

            monthly_manual_income += safe_float(
                item.get("amount", 0)
            )

    # =====================================================
    # MONTHLY MANUAL EXPENSE
    # =====================================================

    monthly_manual_expenses = 0.0

    for item in expense_data:

        if item.get("month") == current_month:

            monthly_manual_expenses += safe_float(
                item.get("amount", 0)
            )

    # =====================================================
    # MONTHLY BANK TRANSACTIONS
    # =====================================================

    monthly_bank_income = 0.0
    monthly_bank_expenses = 0.0

    for transaction in bank_transactions:

        date_value = str(
            transaction.get("date", "")
        ).strip()

        transaction_date = None

        # -----------------------------------------------
        # Try different bank date formats
        # -----------------------------------------------

        date_formats = [
            "%d-%b-%y",
            "%d-%b-%Y",
            "%d/%m/%Y",
            "%d/%m/%y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d-%m-%y"
        ]

        for date_format in date_formats:

            try:

                transaction_date = datetime.strptime(
                    date_value,
                    date_format
                )

                break

            except ValueError:

                continue

        # -----------------------------------------------
        # Check current month
        # -----------------------------------------------

        if transaction_date:

            if (
                transaction_date.month
                == datetime.now().month
                and
                transaction_date.year
                == current_year
            ):

                monthly_bank_income += safe_float(
                    transaction.get("credit", 0)
                )

                monthly_bank_expenses += safe_float(
                    transaction.get("debit", 0)
                )

    # =====================================================
    # FINAL MONTHLY TOTALS
    # =====================================================

    monthly_income = (
        monthly_manual_income +
        monthly_bank_income
    )

    monthly_expenses = (
        monthly_manual_expenses +
        monthly_bank_expenses
    )

    monthly_savings = (
        monthly_income -
        monthly_expenses
    )

    # =====================================================
    # FINANCIAL HEALTH SCORE
    # =====================================================

    score = 0

    if total_income > 0:

        savings_ratio = (
            total_savings /
            total_income
        ) * 100

        expense_ratio = (
            total_expenses /
            total_income
        ) * 100

        # Savings score
        if savings_ratio >= 30:

            score += 40

        elif savings_ratio >= 20:

            score += 30

        elif savings_ratio >= 10:

            score += 20

        else:

            score += 10

        # Expense score
        if expense_ratio <= 50:

            score += 30

        elif expense_ratio <= 70:

            score += 20

        else:

            score += 10

    # =====================================================
    # INSURANCE SCORE
    # =====================================================

    insurance_count = db.insurance.count_documents({
        "username": username
    })

    if insurance_count > 0:

        score += 20

    # Base score
    score += 10

    if score > 100:

        score = 100

    # =====================================================
    # RECENT TRANSACTIONS
    # =====================================================

    recent_transactions = []

    # =====================================================
    # MANUAL INCOME
    # =====================================================

    for item in income_data:

        recent_transactions.append({

            "type": "Income",

            "title": item.get(
                "source",
                "Income"
            ),

            "amount": safe_float(
                item.get("amount", 0)
            ),

            "month": item.get(
                "month",
                ""
            )
        })

    # =====================================================
    # MANUAL EXPENSE
    # =====================================================

    for item in expense_data:

        recent_transactions.append({

            "type": "Expense",

            "title": item.get(
                "category",
                "Expense"
            ),

            "amount": safe_float(
                item.get("amount", 0)
            ),

            "month": item.get(
                "month",
                ""
            )
        })

    # =====================================================
    # BANK TRANSACTIONS
    # =====================================================

    for transaction in bank_transactions:

        debit = safe_float(
            transaction.get("debit", 0)
        )

        credit = safe_float(
            transaction.get("credit", 0)
        )

        description = transaction.get(
            "description",
            "Bank Transaction"
        )

        date = transaction.get(
            "date",
            ""
        )

        # -----------------------------------------------
        # BANK CREDIT
        # -----------------------------------------------

        if credit > 0:

            recent_transactions.append({

                "type": "Income",

                "title": description,

                "amount": credit,

                "month": date
            })

        # -----------------------------------------------
        # BANK DEBIT
        # -----------------------------------------------

        if debit > 0:

            recent_transactions.append({

                "type": "Expense",

                "title": description,

                "amount": debit,

                "month": date
            })

    # =====================================================
    # LATEST 10 TRANSACTIONS
    # =====================================================

    recent_transactions = (
        recent_transactions[::-1][:10]
    )

    # =====================================================
    # DEBUG
    # =====================================================

    print("\n========== DASHBOARD TOTALS ==========")

    print("Manual Income   :", manual_income)
    print("Bank Income     :", bank_income)

    print("Manual Expenses :", manual_expenses)
    print("Bank Expenses   :", bank_expenses)

    print("TOTAL INCOME    :", total_income)
    print("TOTAL EXPENSES  :", total_expenses)
    print("TOTAL SAVINGS   :", total_savings)

    print("======================================\n")

    # =====================================================
    # RENDER DASHBOARD
    # =====================================================

    return render_template(

        "dashboard.html",

        income_data=income_data,

        expense_data=expense_data,

        bank_transactions=bank_transactions,

        total_income=total_income,

        total_expenses=total_expenses,

        total_savings=total_savings,

        financial_score=score,

        recent_transactions=recent_transactions,

        current_month=current_month,

        monthly_income=monthly_income,

        monthly_expenses=monthly_expenses,

        monthly_savings=monthly_savings,

        budget_amount=budget_amount,

        remaining_budget=remaining_budget
    )
@app.route('/goal_planner')
def goal_planner_page():

    if not is_logged_in():
        return redirect('/login')

    username = session["username"]

    goals = list(
        db.goals.find({"username": username})
    )

    return render_template(
        "goal_planner.html",
        goals=goals
    )
@app.route('/add_goal', methods=['POST'])
def add_goal():

    if not is_logged_in():
        return redirect('/login')

    db.goals.insert_one({

        "username": session["username"],

        "goal_name": request.form["goal_name"],

        "target_amount": float(request.form["target_amount"]),

        "saved_amount": float(request.form["saved_amount"]),

        "target_date": request.form["target_date"]

    })

    flash("Goal added successfully!", "success")

    return redirect('/goal_planner')


@app.route('/calculate_goal', methods=['POST'])
def calculate_goal():

    goal_name = request.form['goal_name']

    target_amount = float(request.form['target_amount'])

    monthly_saving = float(request.form['monthly_saving'])

    investment_type = request.form['investment_type']

    interest_rate = float(request.form['interest_rate'])

    months_needed = calculate_months_needed(
        target_amount,
        monthly_saving,
        interest_rate
    )

    years = int(months_needed // 12)

    remaining_months = int(months_needed % 12)

    days = int((months_needed - int(months_needed)) * 30)

    total_invested = monthly_saving * months_needed

    interest_earned = max(0, total_invested - target_amount)

    return render_template(

        'goal_planner.html',

        result=True,

        goal_name=goal_name,

        target_amount=target_amount,

        monthly_saving=monthly_saving,

        investment_type=investment_type,

        interest_rate=interest_rate,

        years=years,

        months=remaining_months,

        days=days,

        total_invested=round(total_invested, 2),

        interest_earned=round(interest_earned, 2)

    )
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        fullname = request.form['fullname']
        mobile = request.form['mobile']
        confirm_password = request.form['confirm_password']

        existing_user = db.users.find_one({
             "$or": [
               {"username": username},
               {"email": email},
               {"mobile": mobile}
       ]
})

        if existing_user:
            return render_template(
        "signup.html",
        error="Username, Email or Mobile already exists."
    )

        otp = generate_otp()
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Temporarily store pending signup info
        db.pending_signups.delete_many({"email": email})  # remove any old attempts
        db.pending_signups.insert_one({
    "fullname": fullname,
    "username": username,
    "password": hashed_password,
    "email": email,
    "mobile": mobile,
    "otp": otp
})

        send_otp_email(email, otp)

        session['pending_email'] = email
        return redirect('/verify_otp')

    return render_template('signup.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        email = session.get('pending_email')

        pending_user = db.pending_signups.find_one({"email": email})

        if pending_user and pending_user['otp'] == entered_otp:

            db.users.insert_one({
                "fullname": pending_user["fullname"],
                "username": pending_user["username"],
                "password": pending_user["password"],
                "email": pending_user["email"],
                "mobile": pending_user["mobile"]
            })

            db.pending_signups.delete_one({"email": email})
            session.pop("pending_email", None)

            return redirect('/login')

        else:
            return render_template(
                'verify_otp.html',
                error="Incorrect OTP. Please try again."
            )

    return render_template('verify_otp.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        login_input = request.form['username']
        password = request.form['password']

        user = db.users.find_one({
            "$or": [
                {"username": login_input},
                {"email": login_input},
                {"mobile": login_input}
            ]
        })

        if user and bcrypt.check_password_hash(user['password'], password):
            session['username'] = user['username']
            return redirect('/dashboard')

        return render_template(
            'login.html',
            error="Invalid username, email, mobile number or password."
        )

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

    company = request.form['company'].strip()
    policy_number = request.form['policy_number'].strip()
    insurance_type = request.form['type'].strip()
    coverage = float(request.form['coverage'])
    premium = float(request.form['premium'])
    due_date = request.form['due_date']
    nominee = request.form['nominee'].strip()

    db.insurance.insert_one({

        "username": session['username'],

        "company": company,

        "policy_number": policy_number,

        "type": insurance_type,

        "coverage": coverage,

        "premium": premium,

        "due_date": due_date,

        "nominee": nominee

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
@app.route('/reports')
def reports():

    if not is_logged_in():
        return redirect('/login')

    username = session['username']

    selected_month = request.args.get("month")

    if selected_month:

        income_data = list(db.income.find({
            "username": username,
            "month": selected_month
        }))

        expense_data = list(db.expenses.find({
            "username": username,
            "month": selected_month
        }))

    else:

        income_data = list(db.income.find({
            "username": username
        }))

        expense_data = list(db.expenses.find({
            "username": username
        }))

    total_income = sum(item["amount"] for item in income_data)
    total_expenses = sum(item["amount"] for item in expense_data)
    total_savings = total_income - total_expenses

    return render_template(
        "reports.html",
        income_data=income_data,
        expense_data=expense_data,
        total_income=total_income,
        total_expenses=total_expenses,
        total_savings=total_savings,
        selected_month=selected_month
    )
@app.route("/budget", methods=["GET", "POST"])
def budget():

    if not is_logged_in():
        return redirect("/login")

    username = session["username"]

    if request.method == "POST":

        month = request.form["month"]
        amount = float(request.form["budget"])

        db.budget.update_one(
            {
                "username": username,
                "month": month
            },
            {
                "$set": {
                    "budget": amount
                }
            },
            upsert=True
        )

        flash("Budget Saved Successfully!", "success")

        return redirect("/budget")

    budgets = list(
        db.budget.find(
            {"username": username}
        )
    )

    return render_template(
        "budget.html",
        budgets=budgets
    )
@app.route("/download_report")
def download_report():

    if not is_logged_in():
        return redirect("/login")

    username = session["username"]

    current_month = datetime.now().strftime("%B")

    # Budget
    budget_doc = db.budget.find_one({
        "username": username,
        "month": current_month
    })

    budget_amount = budget_doc["budget"] if budget_doc else 0

    # Fetch Data
    income_data = list(db.income.find({"username": username}))
    expense_data = list(db.expenses.find({"username": username}))

    # Totals
    total_income = sum(item["amount"] for item in income_data)
    total_expenses = sum(item["amount"] for item in expense_data)
    total_savings = total_income - total_expenses
    remaining_budget = budget_amount - total_expenses

    # Financial Score
    score = 0

    if total_income > 0:

        savings_ratio = (total_savings / total_income) * 100
        expense_ratio = (total_expenses / total_income) * 100

        if savings_ratio >= 30:
            score += 40
        elif savings_ratio >= 20:
            score += 30
        elif savings_ratio >= 10:
            score += 20
        else:
            score += 10

        if expense_ratio <= 50:
            score += 30
        elif expense_ratio <= 70:
            score += 20
        else:
            score += 10

    insurance_count = db.insurance.count_documents({
        "username": username
    })

    if insurance_count > 0:
        score += 20

    score += 10

    if score > 100:
        score = 100

    # PDF Buffer
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=24,
        textColor=colors.HexColor("#0B6E4F"),
        spaceAfter=20
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#0B6E4F"),
        spaceAfter=12
    )

    story = []

    logo = Image("static/images/logo.png")
    logo.drawHeight = 1.2 * inch
    logo.drawWidth = 1.2 * inch
    logo.hAlign = "CENTER"

    story.append(logo)
    story.append(Spacer(1, 0.2 * inch))

    story.append(
        Paragraph(
            "FINANCE TRACKER",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Professional Financial Report",
            heading_style
        )
    )

    story.append(
        Paragraph(
            f"<b>User :</b> {username}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"<b>Generated :</b> {datetime.now().strftime('%d %B %Y %I:%M %p')}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 0.25 * inch))
    # -----------------------------
    # Financial Summary
    # -----------------------------

    story.append(
        Paragraph(
            "Financial Summary",
            heading_style
        )
    )

    summary_data = [
        ["Category", "Amount"],
        ["Total Income", f"Rs {total_income:,.2f}"],
        ["Total Expenses", f"Rs {total_expenses:,.2f}"],
        ["Total Savings", f"Rs {total_savings:,.2f}"],
        ["Budget", f"Rs {budget_amount:,.2f}"],
        ["Remaining Budget", f"Rs {remaining_budget:,.2f}"]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[220, 180]
    )

    summary_table.setStyle(
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0B6E4F")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ])
    )

    story.append(summary_table)

    story.append(Spacer(1, 0.30 * inch))

    # -----------------------------
    # Income History
    # -----------------------------

    story.append(
        Paragraph(
            "Income History",
            heading_style
        )
    )

    income_table_data = [
        ["Source", "Month", "Amount"]
    ]

    for item in income_data:

        income_table_data.append([
            item["source"],
            item["month"],
            f"Rs{item['amount']:,.2f}"
        ])

    income_table = Table(
        income_table_data,
        colWidths=[170, 120, 110]
    )

    income_table.setStyle(
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.green),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ])
    )

    story.append(income_table)

    story.append(Spacer(1, 0.30 * inch))
     # -----------------------------
    # Expense History
    # -----------------------------

    story.append(
        Paragraph(
            "Expense History",
            heading_style
        )
    )

    expense_table_data = [
        ["Category", "Month", "Amount"]
    ]

    for item in expense_data:

        expense_table_data.append([
            item["category"],
            item["month"],
            f"Rs {item['amount']:,.2f}"
        ])

    expense_table = Table(
        expense_table_data,
        colWidths=[170, 120, 110]
    )

    expense_table.setStyle(
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.red),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ])
    )

    story.append(expense_table)

    story.append(Spacer(1, 0.30 * inch))

    # -----------------------------
    # Financial Health
    # -----------------------------

    story.append(
        Paragraph(
            "Financial Health Score",
            heading_style
        )
    )

    if score >= 80:
        status = "Excellent Financial Health"
        score_color = colors.green
    elif score >= 60:
        status = "Good Financial Health"
        score_color = colors.orange
    else:
        status = "Needs Improvement"
        score_color = colors.red

    health_table = Table(
        [
            ["Score", f"{score}/100"],
            ["Status", status]
        ],
        colWidths=[180, 220]
    )

    health_table.setStyle(
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), score_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ])
    )

    story.append(health_table)

    story.append(Spacer(1, 0.40 * inch))

    # Footer

    story.append(
        Paragraph(
            "<b>Generated by Finance Tracker</b>",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            "Thank you for using Finance Tracker.",
            styles["Normal"]
        )
    )

    # Build PDF

    doc.build(story)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Finance_Report.pdf",
        mimetype="application/pdf"
    )
@app.route('/profile')
def profile():

    if not is_logged_in():
        return redirect('/login')

    username = session["username"]

    user = db.users.find_one({
        "username": username
    })

    income_data = list(db.income.find({"username": username}))
    expense_data = list(db.expenses.find({"username": username}))

    total_income = sum(item["amount"] for item in income_data)
    total_expenses = sum(item["amount"] for item in expense_data)
    total_savings = total_income - total_expenses

    return render_template(
        "profile.html",
        user=user,
        total_income=total_income,
        total_expenses=total_expenses,
        total_savings=total_savings
    )
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():

    if not is_logged_in():
        return redirect('/login')

    username = session["username"]

    user = db.users.find_one({
        "username": username
    })

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        mobile = request.form["mobile"]

        db.users.update_one(

            {"username": username},

            {
                "$set": {
                    "fullname": fullname,
                    "email": email,
                    "mobile": mobile
                }
            }

        )

        flash("Profile Updated Successfully!", "success")

        return redirect("/profile")

    return render_template(
        "edit_profile.html",
        user=user
    )
@app.route("/change_password", methods=["GET", "POST"])
def change_password():

    if not is_logged_in():
        return redirect("/login")

    # Open the page
    if request.method == "GET":
        return render_template("change_password.html")

    username = session["username"]

    current_password = request.form["current_password"]
    new_password = request.form["new_password"]
    confirm_password = request.form["confirm_password"]

    user = db.users.find_one({
        "username": username
    })

    if not bcrypt.check_password_hash(
        user["password"],
        current_password
    ):
        flash("Current password is incorrect!", "danger")
        return redirect("/change_password")

    if new_password != confirm_password:
        flash("New passwords do not match!", "warning")
        return redirect("/change_password")

    hashed_password = bcrypt.generate_password_hash(
        new_password
    ).decode("utf-8")

    db.users.update_one(
        {"username": username},
        {
            "$set": {
                "password": hashed_password
            }
        }
    )

    flash("Password changed successfully!", "success")

    return redirect("/change_password")
@app.route("/upload_profile", methods=["POST"])
def upload_profile():

    if not is_logged_in():
        return redirect("/login")

    if "profile_pic" not in request.files:
        flash("No file selected.", "danger")
        return redirect("/profile")

    file = request.files["profile_pic"]

    if file.filename == "":
        flash("Please choose an image.", "warning")
        return redirect("/profile")

    filename = secure_filename(file.filename)

    filepath = os.path.join(
     app.config["PROFILE_FOLDER"],
    filename
    )

    file.save(filepath)

    db.users.update_one(
        {"username": session["username"]},
        {
            "$set": {
                "profile_pic": filename
            }
        }
    )

    flash("Profile picture updated successfully!", "success")

    return redirect("/profile")
@app.route("/search")
def search():

    if not is_logged_in():
        return jsonify([])

    username = session["username"]

    keyword = request.args.get("q", "").strip()

    if keyword == "":
        return jsonify([])

    keyword = keyword.lower()

    results = []

    # Income Search
    incomes = db.income.find({"username": username})

    for item in incomes:

        title = str(item.get("source", ""))

        if keyword in title.lower():

            results.append({
                "type": "Income",
                "name": title
            })

    # Expense Search
    expenses = db.expenses.find({"username": username})

    for item in expenses:

        title = str(item.get("category", ""))

        if keyword in title.lower():

            results.append({
                "type": "Expense",
                "name": title
            })

    return jsonify(results[:8])
@app.route("/settings")
def settings():

    if not is_logged_in():
        return redirect("/login")

    return render_template("settings.html")
@app.route("/smart_analyzer")
def smart_analyzer():

    if not is_logged_in():
        return redirect("/login")

    return render_template(
        "smart_analyzer.html"
    )
@app.route("/analyze_statement", methods=["POST"])
def analyze_statement():

    # ============================================
    # STEP 1 - LOGIN CHECK
    # ============================================

    if not is_logged_in():
        return redirect("/login")

    # ============================================
    # STEP 2 - GET UPLOADED FILE
    # ============================================

    file = request.files.get("statement")

    if file is None or file.filename == "":
        flash(
            "Please upload a bank statement.",
            "warning"
        )
        return redirect("/smart_analyzer")

    # ============================================
    # STEP 3 - GET OPENING BALANCE
    # ============================================

    opening_balance = request.form.get(
        "opening_balance",
        "0"
    )

    try:

        opening_balance = float(
            opening_balance
        )

    except (ValueError, TypeError):

        opening_balance = 0.0

    # ============================================
    # STEP 4 - GET PDF PASSWORD
    # ============================================

    statement_password = request.form.get(
        "statement_password",
        ""
    ).strip()

    # ============================================
    # FILE PATH VARIABLES
    # ============================================

    filepath = None
    decrypted_filepath = None

    try:

        # ========================================
        # STEP 5 - SECURE FILE NAME
        # ========================================

        filename = secure_filename(
            file.filename
        )

        if not filename:

            flash(
                "Invalid file name.",
                "danger"
            )

            return redirect(
                "/smart_analyzer"
            )

        # ========================================
        # STEP 6 - CREATE UPLOAD FOLDER
        # ========================================

        os.makedirs(
            app.config["STATEMENT_FOLDER"],
            exist_ok=True
        )

        # ========================================
        # STEP 7 - CREATE FILE PATH
        # ========================================

        filepath = os.path.join(
            app.config["STATEMENT_FOLDER"],
            filename
        )

        # ========================================
        # STEP 8 - SAVE UPLOADED FILE
        # ========================================

        file.save(filepath)

        print(
            "\n========== STATEMENT PROCESSING =========="
        )

        print(
            "File:",
            filename
        )

        # ========================================
        # STEP 9 - PDF PASSWORD HANDLING
        # ========================================

        file_to_read = filepath

        if filename.lower().endswith(".pdf"):

            print(
                "PDF detected."
            )

            try:

                # --------------------------------
                # Open PDF
                # --------------------------------

                reader = PdfReader(
                    filepath
                )

                # --------------------------------
                # Check encryption
                # --------------------------------

                if reader.is_encrypted:

                    print(
                        "Password protected PDF detected."
                    )

                    # ----------------------------
                    # Password missing
                    # ----------------------------

                    if not statement_password:

                        flash(
                            "This PDF is password protected. Please enter the statement password.",
                            "warning"
                        )

                        return redirect(
                            "/smart_analyzer"
                        )

                    # ----------------------------
                    # Try password
                    # ----------------------------

                    decrypt_result = reader.decrypt(
                        statement_password
                    )

                    if decrypt_result == 0:

                        flash(
                            "Incorrect statement password. Please try again.",
                            "danger"
                        )

                        return redirect(
                            "/smart_analyzer"
                        )

                    print(
                        "PDF password verified successfully."
                    )

                    # ----------------------------
                    # Temporary decrypted file
                    # ----------------------------

                    decrypted_filename = (
                        "decrypted_" + filename
                    )

                    decrypted_filepath = os.path.join(
                        app.config["STATEMENT_FOLDER"],
                        decrypted_filename
                    )

                    # ----------------------------
                    # Create PDF writer
                    # ----------------------------

                    writer = PdfWriter()

                    for page in reader.pages:

                        writer.add_page(
                            page
                        )

                    # ----------------------------
                    # Save decrypted PDF
                    # ----------------------------

                    with open(
                        decrypted_filepath,
                        "wb"
                    ) as decrypted_file:

                        writer.write(
                            decrypted_file
                        )

                    file_to_read = (
                        decrypted_filepath
                    )

                    print(
                        "Decrypted PDF created successfully."
                    )

                else:

                    print(
                        "PDF is not password protected."
                    )

            except Exception as pdf_error:

                print(
                    "\n========== PDF ERROR =========="
                )

                print(
                    pdf_error
                )

                flash(
                    f"Unable to open PDF: {pdf_error}",
                    "danger"
                )

                return redirect(
                    "/smart_analyzer"
                )

        # ========================================
        # STEP 10 - READ STATEMENT
        # ========================================

        dataframe = read_statement(
            file_to_read
        )

        # ========================================
        # STEP 11 - PROCESS STATEMENT
        # ========================================

        transactions, bank = process_dataframe(
            dataframe,
            file_to_read,
            opening_balance=opening_balance
        )

        print(
            "\nDetected Bank:",
            bank
        )

        print(
            "Transactions extracted:",
            len(transactions)
        )

        # ========================================
        # STEP 12 - CLEAN TRANSACTIONS
        # ========================================

        clean_transactions = []

        for transaction in transactions:

            clean_transaction = {}

            # ------------------------------------
            # Make sure transaction is dictionary
            # ------------------------------------

            if not isinstance(
                transaction,
                dict
            ):

                continue

            # ------------------------------------
            # Clean every field
            # ------------------------------------

            for key, value in transaction.items():

                # -------------------------------
                # NEVER send MongoDB _id
                # -------------------------------

                if key == "_id":
                    continue

                # -------------------------------
                # ObjectId
                # -------------------------------

                if isinstance(
                    value,
                    ObjectId
                ):

                    value = str(
                        value
                    )

                # -------------------------------
                # Pandas / NumPy values
                # -------------------------------

                elif hasattr(
                    value,
                    "item"
                ):

                    try:

                        value = value.item()

                    except Exception:

                        value = str(
                            value
                        )

                # -------------------------------
                # Datetime
                # -------------------------------

                elif isinstance(
                    value,
                    datetime
                ):

                    value = value.isoformat()

                # -------------------------------
                # None
                # -------------------------------

                elif value is None:

                    value = ""

                # -------------------------------
                # Save value
                # -------------------------------

                clean_transaction[
                    key
                ] = value

            # ==================================
            # STANDARD FIELDS
            # ==================================

            # ----------------------------------
            # Date
            # ----------------------------------

            clean_transaction[
                "date"
            ] = str(
                clean_transaction.get(
                    "date",
                    ""
                )
            )

            # ----------------------------------
            # Description
            # ----------------------------------

            clean_transaction[
                "description"
            ] = str(
                clean_transaction.get(
                    "description",
                    ""
                )
            )

            # ----------------------------------
            # Debit
            # ----------------------------------

            try:

                clean_transaction[
                    "debit"
                ] = float(
                    clean_transaction.get(
                        "debit",
                        0
                    ) or 0
                )

            except (
                ValueError,
                TypeError
            ):

                clean_transaction[
                    "debit"
                ] = 0.0

            # ----------------------------------
            # Credit
            # ----------------------------------

            try:

                clean_transaction[
                    "credit"
                ] = float(
                    clean_transaction.get(
                        "credit",
                        0
                    ) or 0
                )

            except (
                ValueError,
                TypeError
            ):

                clean_transaction[
                    "credit"
                ] = 0.0

            # ----------------------------------
            # Balance
            # ----------------------------------

            try:

                clean_transaction[
                    "balance"
                ] = float(
                    clean_transaction.get(
                        "balance",
                        0
                    ) or 0
                )

            except (
                ValueError,
                TypeError
            ):

                clean_transaction[
                    "balance"
                ] = 0.0

            # ----------------------------------
            # Category
            # ----------------------------------

            clean_transaction[
                "category"
            ] = str(
                clean_transaction.get(
                    "category",
                    "OTHERS"
                )
            ).upper().strip()

            # ==================================
            # ADD CLEAN TRANSACTION
            # ==================================

            clean_transactions.append(
                clean_transaction
            )

        # ========================================
        # STEP 13 - SAVE TO MONGODB
        # ========================================

        if clean_transactions:

            save_transactions(
                db,
                session["username"],
                clean_transactions
            )

            print(
                "Transactions saved:",
                len(clean_transactions)
            )

        else:

            print(
                "No transactions found."
            )

        # ========================================
        # STEP 14 - FINAL JSON SAFE COPY
        # ========================================
        #
        # This is extra protection for Jinja
        # {{ transactions | tojson }}
        #
        # ========================================

        preview_transactions = []

        for transaction in clean_transactions:

            preview = {}

            for key, value in transaction.items():

                # --------------------------------
                # Never send _id
                # --------------------------------

                if key == "_id":
                    continue

                # --------------------------------
                # ObjectId
                # --------------------------------

                if isinstance(
                    value,
                    ObjectId
                ):

                    value = str(
                        value
                    )

                # --------------------------------
                # Datetime
                # --------------------------------

                elif isinstance(
                    value,
                    datetime
                ):

                    value = value.isoformat()

                # --------------------------------
                # Pandas / NumPy
                # --------------------------------

                elif hasattr(
                    value,
                    "item"
                ):

                    try:

                        value = value.item()

                    except Exception:

                        value = str(
                            value
                        )

                # --------------------------------
                # None
                # --------------------------------

                elif value is None:

                    value = ""

                # --------------------------------
                # JSON-safe value
                # --------------------------------

                preview[
                    key
                ] = value

            preview_transactions.append(
                preview
            )

        # ========================================
        # STEP 15 - SHOW TRANSACTION PREVIEW
        # ========================================

        return render_template(
            "transaction_preview.html",

            transactions=preview_transactions,

            clean_transactions=preview_transactions,

            bank=bank
        )

    # ============================================
    # ERROR HANDLING
    # ============================================

    except Exception as error:

        import traceback

        print(
            "\n========== STATEMENT ERROR =========="
        )

        traceback.print_exc()

        print(
            "=====================================\n"
        )

        flash(
            f"Error reading statement: {error}",
            "danger"
        )

        return redirect(
            "/smart_analyzer"
        )

    # ============================================
    # STEP 16 - DELETE TEMP DECRYPTED PDF
    # ============================================

    finally:

        if decrypted_filepath:

            try:

                if os.path.exists(
                    decrypted_filepath
                ):

                    os.remove(
                        decrypted_filepath
                    )

                    print(
                        "Temporary decrypted PDF deleted."
                    )

            except Exception as cleanup_error:

                print(
                    "Temporary file cleanup failed:",
                    cleanup_error
                )
@app.route("/import_transactions", methods=["POST"])
def import_transactions():

    # Check login
    if not is_logged_in():
        return redirect("/login")

    try:

        # Get transactions from form
        transactions_json = request.form.get(
            "transactions",
            "[]"
        )

        import json

        transactions = json.loads(
            transactions_json
        )

        # Check transactions
        if not transactions:

            flash(
                "No transactions found to import.",
                "warning"
            )

            return redirect("/smart_analyzer")

        # Save username
        username = session["username"]

        # Save transactions to MongoDB
        save_transactions(
            db=db,
            username=username,
            transactions=transactions
        )

        flash(
            f"{len(transactions)} transactions imported successfully!",
            "success"
        )

        return redirect("/dashboard")

    except Exception as error:

        print("\n========== IMPORT ERROR ==========")
        print(error)
        print("==================================\n")

        flash(
            f"Error importing transactions: {error}",
            "danger"
        )

        return redirect("/smart_analyzer")
@app.route("/statement_analysis")
def statement_analysis_page():

    if not is_logged_in():
        return redirect("/login")

    username = session["username"]

    analysis = analyze_statement_data(
        db,
        username
    )

    return render_template(
        "statement_analysis.html",
        analysis=analysis
    )
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)