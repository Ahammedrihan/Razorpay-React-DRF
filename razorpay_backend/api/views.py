from django.shortcuts import render

import json
import environ
import razorpay

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Order
from .serializers import OrderSerializer

env = environ.Env()
environ.Env.read_env()

def start_payment(request):
    amount = request.data['amount']
    name = request.data['name']
    client = razorpay.Client(auth=(env('PUBLIC_KEY'),env('SECRET_KEY')))
    payment = client.order.create({"amount":int(amount)*100,
                                   "currency": "INR", 
                                   "payment_capture": "1"})
    order = Order.objects.create(order_product=name, 
                                 order_amount=amount,
                                 order_payment_id=payment['id'])
    serializer = OrderSerializer(order)

    data = {
        "payment": payment,
        "order": serializer.data
    }
    return Response(data)


def handle_payment_success(request):
    res = json.loads(request.data["response"])

    ord_id = ""
    raz_pay_id = ""
    raz_signature = ""

    for key in res.keys():
        if key == "razorpay_order_id":
            ord_id = res[key]
        elif key == "razorpay_payment_id":
            raz_pay_id = res[key]
        elif key == "razorpay_signature":
            raz_signature = res[key]

    order = Order.objects.get(order_payment_id=ord_id)

    data = {
        'razorpay_order_id': ord_id,
        'razorpay_payment_id': raz_pay_id,
        'razorpay_signature': raz_signature
    }
    client = razorpay.Client(auth=(env('PUBLIC_KEY'), env('SECRET_KEY')))
    check = client.utility.verify_payment_signature(data)

    if check is not None:
        print("Redirect to error url or error page")
        return Response({'error': 'Something went wrong'})
    order.isPaid = True
    order.save()

    res_data = {
        'message': 'payment successfully received!'
    }

    return Response(res_data)




