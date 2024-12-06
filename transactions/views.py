from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
from rest_framework.parsers import FileUploadParser
from rest_framework import status
# Create your views here.

class XMLToExcelAPIView(APIView):
    # parser_classes = [FileUploadParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')  # Get the uploaded file

        if not file_obj:
            return Response({"error":"No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        tree = ET.parse(file_obj)
        root = tree.getroot()

        # Initialize transactions list
        transactions = []

        # Iterate through vouchers
        for voucher in root.findall(".//TALLYMESSAGE/VOUCHER"):
            vch_type = voucher.find("VOUCHERTYPENAME")
            vch_no = voucher.find("VOUCHERNUMBER").text if voucher.find("VOUCHERNUMBER") is not None else "NA"
            ref_date = voucher.find("REFERENCEDATE").text if voucher.find("REFERENCEDATE") is not None else "NA"
            date_str = voucher.find("DATE").text if voucher.find("DATE") is not None else "NA"

            # Convert date to day-month-year format
            if date_str != "NA":
                date_obj = datetime.strptime(date_str, "%Y%m%d")  # Parse the string into a datetime object
                formatted_date = date_obj.strftime("%d-%m-%Y")  # Format it as day-month-year
            else:
                formatted_date = "NA"

            if vch_type is not None and vch_type.text == "Receipt":
                # Base transaction details (Parent)
                transaction = {
                    "Date": formatted_date,
                    "Transaction Type": "Parent",
                    "Vch No.": vch_no,
                    "Ref No.": "NA",
                    "Ref Type": "NA",
                    "Ref Date": ref_date,
                    "Debtor": voucher.find("PARTYLEDGERNAME").text if voucher.find("PARTYLEDGERNAME") is not None else "NA",
                    "Particulars": voucher.find("PARTYLEDGERNAME").text if voucher.find("PARTYLEDGERNAME") is not None else "NA",
                    "Ref Amount": "NA",
                    "Amount": "NA",
                    "Vch Type": vch_type.text,
                    "Amount Verified": "NA"
                }

                # Append Parent transaction
                transactions.append(transaction)

                # Parent amount
                parent_amount = 0
                child_amount_sum = 0

                # Extract "Amount" for Parent
                parent_amount_elem = voucher.find(".//ALLLEDGERENTRIES.LIST/AMOUNT")
                if parent_amount_elem is not None:
                    parent_amount = float(parent_amount_elem.text)
                    transaction["Amount"] = str(parent_amount)

                # Process ledger entries (Child and Other Transactions)
                ledger_entries = voucher.findall(".//ALLLEDGERENTRIES.LIST")
                for ledger in ledger_entries:
                    bill_allocations_list= ledger.findall("BILLALLOCATIONS.LIST")
                    ledger_name = ledger.find("LEDGERNAME").text if ledger.find("LEDGERNAME") is not None else "NA"
                    ledger_amount = ledger.find("AMOUNT").text if ledger.find("AMOUNT") is not None else "NA"


                    for bill_allocations in bill_allocations_list:
                        if bill_allocations is not None and ledger_name !="Standard Chartered Bank" :
                            # Child Transaction
                            child_transaction = transaction.copy()
                            child_transaction["Transaction Type"] = "Child"
                            child_transaction["Ref No."] = bill_allocations.find("NAME").text if bill_allocations.find("NAME") is not None else "NA"
                            child_transaction["Ref Type"] = bill_allocations.find("BILLTYPE").text if bill_allocations.find("BILLTYPE") is not None else "NA"
                            child_transaction["Ref Amount"] = bill_allocations.find("AMOUNT").text if bill_allocations.find("AMOUNT") is not None else "NA"
                            child_transaction["Amount"]="NA"
                            child_transaction["Particulars"] = ledger_name

                            # Update child amount sum
                            if child_transaction["Ref Amount"] != "NA":
                                child_amount_sum += float(child_transaction["Ref Amount"])

                            # Use the Ref Date from the bill allocation, or fallback to voucher's Referenced Date
                            child_transaction["Ref Date"] = bill_allocations.find("DUEDATE").text if bill_allocations.find("DUEDATE") is not None else " "

                            # Append child transaction
                            transactions.append(child_transaction)

                    if ledger_name == "Standard Chartered Bank" and bill_allocations.find("BILLTYPE")!="Agst Ref":
                        # Other Transaction for Standard Chartered Bank
                        other_transaction = transaction.copy()
                        other_transaction["Transaction Type"] = "Other"
                        other_transaction["Debtor"] =ledger_name
                        other_transaction["Particulars"] = ledger_name
                        other_transaction["Ref Amount"] = "NA"
                        other_transaction["Amount"] = ledger_amount

                        # Append "Other" transaction
                        transactions.append(other_transaction)

                # Compute "Amount Verified" for Parent
                if parent_amount > 0:
                    transaction["Amount Verified"] = "Yes" if abs(parent_amount - child_amount_sum) < 1e-6 else "No"

                

        # Convert transactions list to DataFrame
        columns = [
            "Date", "Transaction Type", "Vch No.", "Ref No.", "Ref Type", "Ref Date",
            "Debtor", "Particulars", "Ref Amount", "Amount", "Vch Type","Amount Verified"
        ]
        df = pd.DataFrame(transactions, columns=columns)
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="Result.xlsx"'
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return response