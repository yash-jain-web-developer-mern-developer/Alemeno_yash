from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Customer, Loan
from .serializers import CustomerSerializer, LoanSerializer
import decimal

@api_view(['POST'])
def register_customer(request):
    if request.method == 'POST':
        try:
            monthly_salary = request.data['monthly_income']
            # Calculate approved limit using the formula
            approved_limit = round(36 * monthly_salary, -5)  # Round to nearest lakh
            customer = Customer.objects.create(
                first_name=request.data['first_name'],
                last_name=request.data['last_name'],
                phone_number=request.data['phone_number'],
                monthly_salary=monthly_salary,
                approved_limit=approved_limit,
                current_debt=0  # Start with no debt
            )
            serializer = CustomerSerializer(customer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except KeyError:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)




from openpyxl import load_workbook  # Assuming you use openpyxl for reading Excel files

# Function to calculate credit score based on the loan history
def calculate_credit_score(customer):
    # Reading loan data from the Excel file
    wb = load_workbook('loan_data.xlsx')
    sheet = wb.active
    credit_score = 0
    current_year = 2024  # Set the current year as 2024
    
    # Past Loans Paid on Time (emulating data here)
    loans = Loan.objects.filter(customer=customer)
    on_time_loans = loans.filter(emis_paid_on_time=1).count()
    total_loans = loans.count()

    # Loan Activity in Current Year (current_year-based loan activity)
    loan_activity = loans.filter(start_date__year=current_year).count()

    # Total Loan Volume (sum of loan amounts)
    loan_volume = sum(loan.loan_amount for loan in loans)

    # If the sum of current loans exceeds the approved limit, score = 0
    if customer.current_debt > customer.approved_limit:
        return 0

    # Calculate a basic credit score based on the factors
    credit_score = (on_time_loans * 20) + (total_loans * 10) + (loan_activity * 15) - (loan_volume / 10000) - (customer.current_debt / 1000)
    return credit_score

@api_view(['POST'])
def check_loan_eligibility(request):
    if request.method == 'POST':
        customer_id = request.data['customer_id']
        try:
            customer = Customer.objects.get(customer_id=customer_id)
            credit_score = calculate_credit_score(customer)

            # Check if the current debt exceeds the approved limit
            if customer.current_debt > customer.approved_limit:
                return Response({"approval": False, "message": "Current debt exceeds approved limit"}, status=status.HTTP_400_BAD_REQUEST)

            # Determine loan approval based on credit score
            approval = False
            corrected_interest_rate = request.data['interest_rate']

            if credit_score > 50:
                approval = True
            elif 50 >= credit_score > 30:
                approval = True
                corrected_interest_rate = max(12, request.data['interest_rate'])
            elif 30 >= credit_score > 10:
                approval = True
                corrected_interest_rate = max(16, request.data['interest_rate'])
            else:
                approval = False

            # Compound interest scheme for monthly repayment
            loan_amount = request.data['loan_amount']
            interest_rate = corrected_interest_rate / 100  # Convert to decimal
            tenure = request.data['tenure']
            monthly_installment = loan_amount * (interest_rate * (1 + interest_rate)**tenure) / ((1 + interest_rate)**tenure - 1)

            # Return response
            response_data = {
                "customer_id": customer_id,
                "approval": approval,
                "interest_rate": request.data['interest_rate'],
                "corrected_interest_rate": corrected_interest_rate,
                "tenure": tenure,
                "monthly_installment": monthly_installment
            }

            return Response(response_data, status=status.HTTP_200_OK)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)






@api_view(['POST'])
def create_loan(request):
    if request.method == 'POST':
        try:
            customer = Customer.objects.get(customer_id=request.data['customer_id'])
            credit_score = calculate_credit_score(customer)

            if credit_score < 30:
                return Response({"message": "Loan not approved due to low credit score"}, status=status.HTTP_400_BAD_REQUEST)

            # Compound interest calculation for monthly repayment
            loan_amount = request.data['loan_amount']
            interest_rate = request.data['interest_rate'] / 100
            tenure = request.data['tenure']
            monthly_installment = loan_amount * (interest_rate * (1 + interest_rate)**tenure) / ((1 + interest_rate)**tenure - 1)

            loan = Loan.objects.create(
                customer=customer,
                loan_amount=loan_amount,
                interest_rate=request.data['interest_rate'],
                tenure=tenure,
                monthly_repayment=monthly_installment,
                emis_paid_on_time=0,  # Initial value
                start_date=request.data['start_date'],
                end_date=request.data['end_date']
            )

            return Response({
                "loan_id": loan.loan_id,
                "customer_id": loan.customer.customer_id,
                "loan_approved": True,
                "message": "Loan approved successfully",
                "monthly_installment": monthly_installment
            }, status=status.HTTP_201_CREATED)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)



@api_view(['GET'])
def view_loan(request, loan_id):
    # Use filter to get all loans with the specified loan_id
    loans = Loan.objects.filter(loan_id=loan_id)
    
    if loans.exists():
        # Prepare the response data by iterating over each loan
        response_data = []
        for loan in loans:
            customer = loan.customer
            loan_data = {
                "loan_id": loan.loan_id,
                "customer": {
                    "id": customer.customer_id,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "phone_number": customer.phone_number,
                    
                },
                "loan_amount": loan.loan_amount,
                "interest_rate": loan.interest_rate,
                "monthly_installment": loan.monthly_repayment,
                "tenure": loan.tenure
            }
            response_data.append(loan_data)

        return Response(response_data, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Loans not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def view_loans_by_customer(request, customer_id):
    try:
        customer = Customer.objects.get(customer_id=customer_id)
        loans = Loan.objects.filter(customer=customer)
        loan_data = []

        for loan in loans:
            loan_data.append({
                "loan_id": loan.loan_id,
                "loan_amount": loan.loan_amount,
                "interest_rate": loan.interest_rate,
                "monthly_installment": loan.monthly_repayment,
                "repayments_left": loan.tenure - loan.emis_paid_on_time
            })
        
        return Response(loan_data, status=status.HTTP_200_OK)
    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
