from django.shortcuts import render, redirect
from account.models import Account
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from decimal import Decimal
from main_app.models import Transaction

@login_required
def search_users_acct_number(request):
    account = Account.objects.all()
    query = request.POST.get("account_number")
    
    if query:
        account = account.filter(
            Q(account_number=query)|
            Q(account_id=query)
        ).distinct()
    
    context = {
        "account" : account,
        "query" : query,
    }
    return render(request, "transfer/search-user-by-acct.html", context)

def amount_transfer(request, account_number):
    try:
        account = Account.objects.get(account_number=account_number)
    except:
        messages.warning(request, "Account does not exist.")
        return redirect("main_app:search-acct")
    
    context = {
        "account" : account,
    }
    return render(request, "transfer/amount-transfer.html", context)

def amount_transfer_process(request, account_number):
    account = Account.objects.get(account_number=account_number) # Get recipient's account number
    sender = request.user # Logged-in user
    recipient = account.user
    
    sender_account = request.user.account # Logged-in user's account
    recipient_account = account
    
    if request.method == "POST":
        amount = request.POST.get("amount-send")
        description = request.POST.get("description")
        
        if sender_account.account_balance >= Decimal(amount):
            new_transaction = Transaction.objects.create(
                user=request.user,
                amount=amount,
                description=description,
                recipient=recipient,
                sender=sender,
                sender_account=sender_account,
                recipient_account=recipient_account,
                status="Processing",
                transaction_type="Transfer",
            )
            new_transaction.save()
            
            # Get the id of the recently created transaction
            transaction_id = new_transaction.transaction_id
            return redirect("main_app:transfer-confirmation", account.account_number, transaction_id)
        else:
            messages.warning(request, "Insufficient funds.")
            return redirect("main_app:amount-transfer", account.account_number)
    else:
        messages.warning(request, "An error occurred. Try again later.")
        return redirect("account:account")

def transfer_confirmation(request, account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
        transaction = Transaction.objects.get(transaction_id=transaction_id)
    except:
        messages.warning(request, "Transaction does not exist.")
        return redirect("account:account")
    
    context = {
        "account":account,
        "transaction":transaction,
    }
    
    return render(request, "transfer/transfer-confirmation.html", context)

def transfer_process(request, account_number, transaction_id):
    account = Account.objects.get(account_number=account_number)
    transaction = Transaction.objects.get(transaction_id=transaction_id)
    
    sender = request.user
    recipient = account.user
    
    sender_account = request.user.account
    recipient_account = account
    
    completed = False
    
    if request.method == "POST":
        pin_number = request.POST.get("pin-number")
        
        if pin_number == sender_account.pin_number:
            transaction.status = "Completed"
            transaction.save()
            
            # Subtract transaction amount from sender's balance, save & update sender's account balance
            sender_account.account_balance -= transaction.amount
            sender_account.save()
            
            # Add transaction amount from sender's balance, save & update recipient's account balance
            recipient_account.account_balance += transaction.amount
            recipient_account.save()
            
            messages.success(request, "Transfer Successful!")
            return redirect("main_app:transfer-completed", account.account_number, transaction.transaction_id)
        
        else:
            messages.warning(request, "Incorrect Pin. Please try again.")
            return redirect("main_app:transfer-confirmation", account.account_number, transaction.transaction_id)
    else:
        messages.warning(request, "An error occurred. Try again later.")
        return redirect("account:account")

def transfer_completed(request, account_number, transaction_id):
    try:
        account = Account.objects.get(account_number=account_number)
        transaction = Transaction.objects.get(transaction_id=transaction_id)
    except:
        messages.warning(request, "Transaction does not exist.")
        return redirect("account:account")
    
    context = {
        "account":account,
        "transaction":transaction,
    }
    
    return render(request, "transfer/transfer-completed.html", context)