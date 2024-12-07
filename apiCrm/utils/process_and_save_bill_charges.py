from .serializers import BillChargeSerializer
from apiCrm.schemas.bill_charges_type import BillChargeType

def process_and_save_bill_charges(bill_charges_data):
    bill_charges_list = []
    for raw_bill_charge in bill_charges_data:
        formatted_bill_charge = format_bill_charge_data(raw_bill_charge)
        serializer = BillChargeSerializer(data=formatted_bill_charge)
        if serializer.is_valid():
            serializer.save()
            bill_charges_list.append(BillChargeType(**serializer.validated_data))
        else:
            print(f"Failed to save bill charge: {serializer.errors}")
    return bill_charges_list