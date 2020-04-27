# stripe-demo - accepting a card payment

## Requirements

- Python 3
- MacOS/Unix

## How to run

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
