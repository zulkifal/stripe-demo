"""
 Stripe Demo
"""
import datetime
import stripe
import json
import os
import uuid
import sys

from flask import Flask, render_template, jsonify, request, session, send_from_directory
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
app = Flask(__name__)

# session secret key
app.secret_key = "not so super secret key"
# session data to be persisted for 365 days
app.permanent_session_lifetime = datetime.timedelta(days=365)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"), "favicon.ico")


@app.route("/cart", methods=["GET"])
def get_cart():
    """
        Return latest cart kept in session, assign a new idempotency_key for initial cart.
    """
    if not "cart" in session:
        session["cart"] = {}
        session["idempotency_key"] = str(uuid.uuid1())
    return jsonify({"items": session["cart"]})


@app.route("/cart", methods=["POST"])
def update_cart():
    """
        Update and return latest cart kept in session, assign an new idempotency_key for every newer? version of cart.

        Definition of a new version of cart is overly simplistic, we are assigning new idempotency_key against
        every POST request, irrespective of whether cart's contents change or not. For a naive user, a POST request
        for cart is only generated when items are added/removed.
    """
    data = json.loads(request.data)
    # print(data)
    session["cart"] = data["items"]
    session["idempotency_key"] = str(uuid.uuid1())
    return jsonify({"items": session["cart"]})


@app.route("/checkout", methods=["GET"])
def get_checkout_page():
    # Display checkout page
    return render_template("checkout.html")


def calculate_order_amount(items):
    """
        Calculating the total order amount on the server side. It is, however, important to note that the prices for each
        item need to be validated using the data the server can trust (a db or a map).
    """
    price = {"item1": 5, "item2": 10, "item3": 15, "item4": 7}
    total = 0
    if "cart" in session:
        for key, val in session["cart"].items():
            total += price[key] * val["qty"]
    return total * 100


@app.route("/create-payment-intent", methods=["POST"])
def create_payment():
    """
        Create payment intent using cart's current version id/idempotency_key, in the local currency.
        More error checking needs to be performed on the server side regarding chosen currency.
    """
    data = json.loads(request.data)
    amount = calculate_order_amount(session)
    if amount <= 0:
        return jsonify(error="Cart Empty or Negative price/quantity Values"), 400
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=data["currency"],
            idempotency_key=session["idempotency_key"],
        )
    except stripe.error.APIConnectionError as e:
        return jsonify(error=str(e)), 503
    except Exception as e:
        print(e)
        return jsonify(error=str(e)), 503

    try:
        # Send publishable key and PaymentIntent details to client
        return jsonify(
            {
                "publishableKey": os.getenv("STRIPE_PUBLISHABLE_KEY"),
                "clientSecret": intent.client_secret,
            }
        )
    except Exception as e:
        return jsonify(error=str(e)), 403


if __name__ == "__main__":
    if len(sys.argv) == 2:
        app.run(host=sys.argv[1])
    else:
        app.run()
