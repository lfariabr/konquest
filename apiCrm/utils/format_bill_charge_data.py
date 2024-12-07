def format_bill_charge_data(raw_bill_charge):
    quote = raw_bill_charge['quote']
    return {
        'quote_id': quote['id'],
        'customer_id': quote['customer']['id'],
        'customer_name': quote['customer']['name'],
        'customer_taxvat': quote['customer'].get('taxvat', 'N/A'),
        'customer_email': quote['customer'].get('email', ''),
        'store_name': raw_bill_charge['store']['name'],
        'total_amount': quote['bill']['total'],
        'installments': quote['bill'].get('installmentsQuantity', 'N/A'),
        'paid_at': raw_bill_charge.get('paidAt', 'N/A'),
        'due_at': raw_bill_charge.get('dueAt', 'N/A'),
        'is_paid': raw_bill_charge['isPaid'],
        'payment_method': raw_bill_charge['paymentMethod']['name'],
        'status': quote['status'],
        'quote_items': "; ".join([f"{item['description']} (Qty: {item['quantity']}, Amount: {item['amount']})" for item in quote['bill']['items']])
    }