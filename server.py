#! /usr/bin/env python3.6

"""
server.py
Stripe Sample.
Python 3.6 or newer required.
"""
import datetime
import stripe
import json
import os
import uuid

from flask import Flask, render_template, jsonify, request, session, send_from_directory
from dotenv import load_dotenv, find_dotenv

# Setup Stripe python client library
load_dotenv(find_dotenv())
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
app = Flask(__name__)
app.secret_key = 'super secret key' #session secret key
app.permanent_session_lifetime = datetime.timedelta(days=365) # session data to be persisted for given timedelta


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico')

@app.route('/cart', methods=['GET'])
def get_cart():
    if not 'cart' in session:
        session['cart'] = {}
        session['idempotency_key'] = str(uuid.uuid1())
    return jsonify({'items': session['cart']})

@app.route('/cart', methods=['POST'])
def update_cart():
    data = json.loads(request.data)
    print(data)
    session['cart'] = data['items']
    session['idempotency_key'] = str(uuid.uuid1())
    return jsonify({'items': session['cart']})

@app.route('/checkout', methods=['GET'])
def get_checkout_page():
    # Display checkout page
    return render_template('checkout.html')


def calculate_order_amount(items):
    total =  0
    if 'cart' in session:
      for key, val in session['cart'].items():
        total += val["price"] * val["qty"]
    return total * 100


@app.route('/create-payment-intent', methods=['POST'])
def create_payment():
    data = json.loads(request.data)
    amount = calculate_order_amount(session)
    if amount <= 0:
      return jsonify(error="Cart Empty or Negative price/quantity Values"), 400
    try:
      intent = stripe.PaymentIntent.create(
          amount=amount,
          currency=data['currency'],
          idempotency_key=session['idempotency_key']
      )
    except stripe.error.APIConnectionError as e:
      return jsonify(error=str(e)), 503
    except Exception as e:
      print(e)
      return jsonify(error=str(e)), 503
    
    try:
        # Send publishable key and PaymentIntent details to client
        return jsonify({'publishableKey': os.getenv('STRIPE_PUBLISHABLE_KEY'), 'clientSecret': intent.client_secret})
    except Exception as e:
        return jsonify(error=str(e)), 403

if __name__ == '__main__':
    app.run(debug=True)
