// A reference to Stripe.js
var stripe;

var orderData = {
  currency: "aud"
};

fetch('/cart')
  .then(function (res) {
    if (res.status == 200) {
      return res.json();
    }
  })
  .then((data) => render_cart(data))


// Disable the button until we have Stripe set up on the page
document.querySelector("button").disabled = true;

fetch("/create-payment-intent", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(orderData)
})
  .then(function (result) {
    return result.json();
  })
  .then(function (data) {
    return setupElements(data);
  })
  .then(function ({ stripe, card, clientSecret }) {
    document.querySelector("button").disabled = false;

    // Handle form submission.
    var form = document.getElementById("payment-form");
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      // Initiate payment when the submit button is clicked
      pay(stripe, card, clientSecret);
    });
  });

// Set up Stripe.js and Elements to use in checkout form
var setupElements = function (data) {
  stripe = Stripe(data.publishableKey);
  var elements = stripe.elements();
  var style = {
    base: {
      color: "#32325d",
      fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
      fontSmoothing: "antialiased",
      fontSize: "16px",
      "::placeholder": {
        color: "#aab7c4"
      }
    },
    invalid: {
      color: "#fa755a",
      iconColor: "#fa755a"
    }
  };

  var card = elements.create("card", { style: style });
  card.mount("#card-element");

  return {
    stripe: stripe,
    card: card,
    clientSecret: data.clientSecret
  };
};

/*
 * Calls stripe.confirmCardPayment which creates a pop-up modal to
 * prompt the user to enter extra authentication details without leaving your page
 */
var pay = function (stripe, card, clientSecret) {
  changeLoadingState(true);

  // Initiate the payment.
  // If authentication is required, confirmCardPayment will automatically display a modal
  stripe
    .confirmCardPayment(clientSecret, {
      payment_method: {
        card: card
      }
    })
    .then(function (result) {
      if (result.error) {
        // Show error to your customer
        showError(result.error.message);
      } else {
        // The payment has been processed!
        emptyCart();
        render_cart({ "items": {} })
        orderComplete(clientSecret);
      }
    });
};

/* ------- Post-payment helpers ------- */
var emptyCart = function () {
  // Empty cart after successful payment
  data = { "items": {} }
  fetch('/cart', {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  })
    .then((res) => res.json())
};

var render_cart = function (cart_obj) {
  let total = 0;
  let cart_html = '<h2>Cart</h2><hr/>';
  items = cart_obj["items"];
  for (key in items) {
    total += items[key]["price"] * items[key]["qty"];
    cart_html += `<div>${key}</div>`;
    cart_html += `<div>Price: ${items[key]["price"]}</div>`;
    cart_html += `<div>Quantity: ${items[key]["qty"]}</div>`;
    cart_html += `<hr/>`;
  }
  cart_html += `<div>Total: ${total}</div>`;
  cart_html += `<div class="font-weight-bold mt-4">cart: ${JSON.stringify(cart_obj)}</div>`;
  document.getElementById('cart').innerHTML = `${cart_html}`;
}

/* Shows a success / error message when the payment is complete */
var orderComplete = function (clientSecret) {
  // Just for the purpose of the sample, show the PaymentIntent response object
  stripe.retrievePaymentIntent(clientSecret).then(function (result) {
    var paymentIntent = result.paymentIntent;
    var amount = paymentIntent.amount;
    var currency = paymentIntent.currency;
    var paymentIntentId = paymentIntent.id;
    var paymentIntentJson = JSON.stringify(paymentIntent, null, 2);

    document.querySelector(".sr-payment-form").classList.add("hidden");
    document.querySelector("pre").textContent = `
Payment has been accepted.

Amount: ${amount / 100}
Currency: ${currency}
PaymentIntent Id = ${paymentIntentId}
    `;

    document.querySelector(".sr-result").classList.remove("hidden");
    setTimeout(function () {
      document.querySelector(".sr-result").classList.add("expand");
    }, 200);

    changeLoadingState(false);
  });
};

var showError = function (errorMsgText) {
  changeLoadingState(false);
  var errorMsg = document.querySelector(".sr-field-error");
  errorMsg.textContent = errorMsgText;
  setTimeout(function () {
    errorMsg.textContent = "";
  }, 4000);
};

// Show a spinner on payment submission
var changeLoadingState = function (isLoading) {
  if (isLoading) {
    document.querySelector("button").disabled = true;
    document.querySelector("#spinner").classList.remove("hidden");
    document.querySelector("#button-text").classList.add("hidden");
  } else {
    document.querySelector("button").disabled = false;
    document.querySelector("#spinner").classList.add("hidden");
    document.querySelector("#button-text").classList.remove("hidden");
  }
};