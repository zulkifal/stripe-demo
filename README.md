# stripe-demo - accepting a card payment

# Design

### Overview
The core part of the app relies on `cart` API. The app exposes a user's cart using `GET` and `POST` HTTP methods on `/cart` path.

`cart` is a map object, shown below, stored on the server side using [Flask session](https://flask.palletsprojects.com/en/1.1.x/api/#sessions). These sessions are persistent for 365 days.

```
{'items': {
            'item_id1': {'price': xx, 'qty': xx},
            'item_id2': {'price': xx, 'qty': xx},
            .
            .
            .
            'item_id(n-1)': {'price': xx, 'qty': xx},
            'item_idn': {'price': xx, 'qty': xx}
          }
}





# cart interaction on home page

# 1. empty cart
+-----------+               +------------------+
|           |  GET /cart    |                  |
|   client  +-------------->+     server       |
|           |               |                  |
+----+------+               +---------+--------+
     ^                                |
     |                                |
     +--------------------------------+
               {"items":{}}



# 2. mutate cart
+------------+                                                         +-------------------+
|            |            POST /cart                                   |                   |
|   client   +-------------------------------------------------------->+     server        |
|            | body: {"items":{                                        |                   |
+-----+------+                  "item1":{"price": xx, "qty": xx},      +----------+--------+
      ^                         "item2":{"price": xx, "qty": xx}                  |
      |                       }                                                   |
      |              }                                                            |
      |                                                                           |
      +---------------------------------------------------------------------------+
                                     OK

# 3. mutated cart sent back on next request
+-----------+               +------------------+
|           |  GET /cart    |                  |
|   client  +-------------->+     server       |
|           |               |                  |
+----+------+               +---------+--------+
     ^                                |
     |                                |
     +--------------------------------+
          {"items":{
                     "item1":{"price": xx, "qty": xx},
                     "item2":{"price": xx, "qty": xx}
                   }
          }
```
A new `cart` is initialized for a user visiting the home page for the first time (or if they have cleared their cookies, or using a different web browser). To make any change to the `cart's` state, the `js` on the client side fetches the whole `cart`, modifies it, and then tries to update it using `POST /cart` request. These post requests can be retried safely and are idempotent. There is potential for two different tabs in a browser over-writing each other's changes. But the latest state of the `cart` is visible to end user on `checkout` page and can be safely corrected.

`checkout` page shows the contents of the `cart` along with expected amount that needs to be paid. This app is using Stripe's [Payment Intent API](https://stripe.com/docs/api/payment_intents). Upon confirmation of the payment, a message is displayed with total amount charged and the [payment-intent id](https://stripe.com/docs/api/payment_intents/object#payment_intent_object-id). An overview of the complete checkout process is shown below:

```
# checkout page interactions

# 1. client sends POST /create-payment-intent to server, along with possible data such as currency/mode of payment
# 2. server calculates total amount, and creates a payment intent using idempotency_key
# 3. server receives {PaymentIntent, clientSecret}
# 4. server sends clientSecret for payment completion, and publishable_key for stripe js client initialization
# 5. client sends POST /v1/payment_intents/:id/confirm to stripe API along with payment method, such as card
# 6. transaction is completed

        +--------------+                                 +-----------------+
        |              | 1. POST /create-payment-intent  |                 |   3. {PaymentIntent, clientSecret}
+------->    client    +-------------------------------->+    server       <------------------------+
|       |              +------------+                    |                 |                        |
|       +-----+--------+            |                    +----+---+--------+                        |
|             ^                     |                         |   |                                 |
|             |                     |                         |   |                                 |
|   4. {      +-----------------------------------------------+   | 2. POST /v1/payment_intents     |
|        "client_secret":XX,        |                             v                                 |
|        "publishable_key":XX       |                    +--------+--------+                        |
|      }                            |                    |                 |                        |
|                                   |                    |    Stripe API   |                        |
|                                   +---+--------------->+                 +------------------------+
|                                       |                |                 |
|                                       +                +-----------------+
|                            5. POST /v1/payment_intents/:id/confirm|
|                                                                   |
+-------------------------------------------------------------------+
                           6. Success
```



### Idempotency
The app is using [Payment Intent API's](https://stripe.com/docs/api/payment_intents) [idempotency_key](https://stripe.com/docs/api/idempotent_requests?lang=curl) feature. A `cart` is a mutable object, and a UUID (kept on server side) is attached/updated to it on every mutation. The mutations to the `cart` object are driven by client side `js` that sends `POST /cart` requests. Once the end user is ready to make the payment and goes to `checkout` page, the payment intent is created using `cart's` current UUID as `idempotency_key`. The `publishable key` and `client secret` are sent back by the app to `js` in the user's browser. There are several scenarios that can occur from here:

1. The user completes/confirms the payment, the confirmation of payment is shown, payment intent's status is set to `succeeded` and webhooks/polling can be used to process the order. The `cart` is emptied, so that repeated visits to `checkout` don't cause creation of multiple payment intents.
2. The payment fails, and user is asked to try a different payment method.
3. If user doesn't make the payment and closes the `checkout` tab, they can safely visit `checkout` page as the `cart` is kept on the server side and its UUID hasn't changed. The app will attempt to create a new payment intent, though, but using same UUID as `idempotency_key` will not cause a new payment intent to be created.
4. The user goes back to `home` page without making the payment, and adds/removes an item in the cart. The mutated `cart` will have a new UUID, and a new payment-intent will be created on `checkout` page. The old payment-intent stays in `requires_payment_method` status and expires after certain time.

### Total calculation
Sending transparent `cart` data between client and server can be dangerous. Before creating a payment intent, the total amount to be charged is calculated using server side logic. In this version of the app, the client is only allowed to set the `qty` for each item is `cart` unconditionally.

```
def calculate_order_amount(items):
    """
        Calculating the total order amount on the server side. It is, however, important to note that the prices for
        each item need to be validated using the data the server can trust (a db or a map).
    """
    price = {"item1": 5, "item2": 10, "item3": 15, "item4": 7}
    total = 0
    if "cart" in session:
        for key, val in session["cart"].items():
            total += price[key] * val["qty"]
    return total * 100
```

### Possible Issues/Improvements

1. We are still relying on the client side `js` to set the `currency` of the payment. The server should have the logic to better handle that.
2. Passing the whole `cart` object between client/server can be slow for larger `carts`.
3. We shouldn't really update the `cart's` UUID on each `POST` request. The better logic could be that we only update UUID if state has been actually mutated.


# How to run

### Requirements

- Python 3
- MacOS/Unix

### Steps
1. Clone this repo

2. Create `.env` file using `example.env` in the root directory of this repo.

```
cp example.env .env
```

3. Udpdate `.env` with your API keys from Stripe [Developer Dashboard](https://stripe.com/docs/development#api-keys). You will need a Stripe account.

```
STRIPE_PUBLISHABLE_KEY=<replace-with-your-publishable-key>
STRIPE_SECRET_KEY=<replace-with-your-secret-key>
```

4. Create and activate a new virtual environment

```
python3 -m venv venv
source venv/bin/activate
```

5. Install dependencies

```
pip install -r requirements.txt
```

6. Export and run the application

```
python server.py
```

7. Go to `localhost:5000/` in your browser to see the demo

8. To accept traffic on all available IPs, replace `app.run()` in `server.py` with `app.run(host="0.0.0.0")` and re-run.
