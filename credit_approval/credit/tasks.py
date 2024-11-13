import pandas as pd
from celery import shared_task
from .models import Customer, Loan

@shared_task
def ingest_customer_data(file_path):
    data = pd.read_excel(file_path)
    for _, row in data.iterrows():
        Customer.objects.update_or_create(
            customer_id=row['Customer ID'],  # Matches 'Customer ID' in Excel
            defaults={
                'first_name': row['First Name'],         # Matches 'First Name' in Excel
                'last_name': row['Last Name'],           # Matches 'Last Name' in Excel                      # Matches 'Age' in Excel
                'phone_number': row['Phone Number'],     # Matches 'Phone Number' in Excel
                'monthly_salary': row['Monthly Salary'], # Matches 'Monthly Salary' in Excel
                'approved_limit': row['Approved Limit'], # Matches 'Approved Limit' in Excel
                'current_debt': row.get('current_debt', 0) or 0  # Uses 'current_debt' if found, else 0
            }
        )

@shared_task
def ingest_loan_data(file_path):
    data = pd.read_excel(file_path)
    for _, row in data.iterrows():
        customer = Customer.objects.get(customer_id=row['Customer ID'])  # Matches 'Customer ID' in Excel
        Loan.objects.update_or_create(
            loan_id=row['Loan ID'],                      # Matches 'Loan ID' in Excel
            customer=customer,
            defaults={
                'loan_amount': row['Loan Amount'],       # Matches 'Loan Amount' in Excel
                'tenure': row['Tenure'],                 # Matches 'Tenure' in Excel
                'interest_rate': row['Interest Rate'],   # Matches 'Interest Rate' in Excel
                'monthly_repayment': row['Monthly payment'],  # Matches 'Monthly payment' in Excel
                'emis_paid_on_time': row['EMIs paid on Time'],  # Matches 'EMIs paid on Time' in Excel
                'start_date': row['Date of Approval'],   # Matches 'Date of Approval' in Excel
                'end_date': row['End Date'],             # Matches 'End Date' in Excel
            }
        )
