import requests
import json
import uuid
import os
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)  
CORS(app)

api_key = os.getenv("API_KEY")
app.config['API_KEY'] = api_key 
# Load menu 
with open("menu.json") as f:
    menu = json.load(f)

sessions = {}

ORDERS_FILE = "orders.json"


def get_session(user_id):
    if user_id not in sessions:
        sessions[user_id] = {
            "cart": [],           # list of {name, price, qty}
            "state": None,       
            "name": None,
            "table": None,
        }
    return sessions[user_id]

def reset_session(user_id):
    sessions[user_id] = {
        "cart": [],
        "state": None,
        "name": None,
        "table": None,
    }

def find_dish(text):
    text = text.lower()

    
    for item in menu:
        if item["name"].lower() in text:
            return item

    
    for item in menu:
        words = item["name"].lower().split()
        if any(word in text for word in words if len(word) > 3):
            return item

    
    text_words = text.split()
    for item in menu:
        item_words = item["name"].lower().split()
        for tw in text_words:
            for iw in item_words:
                if len(tw) > 3 and len(iw) > 3:
                    if iw.startswith(tw[:4]) or tw.startswith(iw[:4]):
                        return item

    return None

def add_to_cart(session, dish, qty=1):
    for entry in session["cart"]:
        if entry["name"] == dish["name"]:
            entry["qty"] += qty
            return
    session["cart"].append({"name": dish["name"], "price": dish["price"], "qty": qty})

def cart_summary(cart):
    if not cart:
        return "Your cart is empty 🛒"
    lines = ["🛒 *Your Cart:*\n"]
    total = 0
    for i, item in enumerate(cart, 1):
        subtotal = item["price"] * item["qty"]
        total += subtotal
        lines.append(f"  {i}. {item['name']} x{item['qty']}  ₹{subtotal}")
    lines.append(f"\n💰 Total: ₹{total}")
    return "\n".join(lines)

def save_order(session, order_id):
    order = {
        "order_id":   order_id,
        "timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer":   session["name"],
        "table":      session["table"],
        "items":      session["cart"],
        "total":      sum(i["price"] * i["qty"] for i in session["cart"]),
    }

    # Load existing orders
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r") as f:
            all_orders = json.load(f)
    else:
        all_orders = []

    all_orders.append(order)

    with open(ORDERS_FILE, "w") as f:
        json.dump(all_orders, f, indent=2)

    return order

#Routes 

@app.route('/')
def home():
    return "Server is running 🚀"


@app.route('/chat', methods=["POST"])
def chat():
    data        = request.json
    user_message = data["message"].strip().lower()
    user_id     = data.get("user_id", "user")   
    session     = get_session(user_id)
    state       = session["state"]

    #Greeting 
    if any(w in user_message for w in ["hi", "hello", "hey"]):
        reset_session(user_id)
        menu_text = "☕ Welcome to our Café!\n\n📋 Here's our menu:\n\n"
        for item in menu:
            menu_text += f"🍽️ {item['name']}\n💰 ₹{item['price']}   ⭐ {item['rating']}\n\n"
        menu_text += "\nJust tell me what you'd like to order! 😊"
        return jsonify({"reply": menu_text})


    if state == "awaiting_name":
        session["name"] = user_message.title()
        session["state"] = "awaiting_table"
        return jsonify({"reply": f"Nice to meet you, {session['name']}! 😊\nWhat's your table number?"})

    
    if state == "awaiting_table":
        session["table"] = user_message
        session["state"] = "awaiting_confirm"
        summary = cart_summary(session["cart"])
        return jsonify({
            "reply": (
                f"{summary}\n\n"
                f"📋 Name: {session['name']}\n"
                f"🪑 Table: {session['table']}\n\n"
                "Shall I confirm your order? Type **yes** to place it or **no** to cancel."
            )
        })

    #confirmation 
    if state == "awaiting_confirm":
        if "yes" in user_message:
            order_id = "ORD-" + str(uuid.uuid4())[:8].upper()
            order    = save_order(session, order_id)
            total    = order["total"]
            name     = session["name"]
            table    = session["table"]
            reset_session(user_id)
            return jsonify({
                "reply": (
                    f"🎉 Order Placed Successfully!\n\n"
                    f"🆔 Order ID : {order_id}\n"
                    f"👤 Name     : {name}\n"
                    f"🪑 Table    : {table}\n"
                    f"💰 Total    : ₹{total}\n\n"
                    f"⏳ Your order will be ready soon. Thank you! ☕"
                )
            })
        else:
            reset_session(user_id)
            return jsonify({"reply": "Order cancelled. No worries! Let me know if you'd like to start over. 😊"})

    #Add item to cart
    if any(w in user_message for w in ["add", "order", "i want", "i'll have", "give me", "get me"]):
        dish = find_dish(user_message)
        if dish:
            add_to_cart(session, dish)
            summary = cart_summary(session["cart"])
            return jsonify({
                "reply": (
                    f"✅ *{dish['name']}* added to your cart!\n\n"
                    f"{summary}\n\n"
                    "Add more items or type **checkout** to place your order."
                )
            })
        else:
            return jsonify({"reply": "I couldn't find that item. Could you check the name and try again? 😊"})

    #View cart
    if any(w in user_message for w in ["cart", "my order", "what have i ordered"]):
        summary = cart_summary(session["cart"])
        if session["cart"]:
            return jsonify({"reply": f"{summary}\n\nType **checkout** to place your order or keep adding items!"})
        return jsonify({"reply": summary})

    # Remove item from cart
    if any(w in user_message for w in ["remove", "delete", "cancel item"]):
        dish = find_dish(user_message)
        if dish:
            session["cart"] = [i for i in session["cart"] if i["name"] != dish["name"]]
            return jsonify({"reply": f"❌ *{dish['name']}* removed from your cart.\n\n{cart_summary(session['cart'])}"})
        return jsonify({"reply": "I couldn't find that item in your cart. Please check the name."})

    #Checkout
    if any(w in user_message for w in ["checkout", "place order", "confirm order", "done ordering"]):
        if not session["cart"]:
            return jsonify({"reply": "Your cart is empty! Add some items first. 🛒"})
        session["state"] = "awaiting_name"
        return jsonify({"reply": "Great! Let's place your order. 🎉\nFirst, what's your name?"})

    
    if "pizza" in user_message:
        text = "🍕 Our Pizzas:\n\n"
        for item in menu:
            if "pizza" in item["name"].lower():
                text += f"{item['name']} — ₹{item['price']} ⭐{item['rating']}\n"
        text += '\nTo order, type: "Add [item name]"'
        return jsonify({"reply": text})

    if "pasta" in user_message:
        text = "🍝 Our Pastas:\n\n"
        for item in menu:
            if "pasta" in item["name"].lower():
                text += f"{item['name']} — ₹{item['price']} ⭐{item['rating']}\n"
        text += '\nTo order, type: "Add [item name]"'
        return jsonify({"reply": text})

    if "burger" in user_message:
        text = "🍔 Our Burgers:\n\n"
        for item in menu:
            if "burger" in item["name"].lower():
                text += f"{item['name']} — ₹{item['price']} ⭐{item['rating']}\n"
        text += '\nTo order, type: "Add [item name]"'
        return jsonify({"reply": text})

    if "drinks" in user_message:
        text = "🥤 Our Drinks:\n\n"
        for item in menu:
            if any(x in item["name"].lower() for x in ["coffee", "shake", "tea", "cola", "mojito", "latte", "espresso"]):
                text += f"{item['name']} — ₹{item['price']} ⭐{item['rating']}\n"
        text += '\nTo order, type: "Add [item name]"'
        return jsonify({"reply": text})

    # Full menu 
    if "menu" in user_message:
        menu_text = "📋 Full Menu:\n\n"
        for item in menu:
            menu_text += f"- {item['name']} ₹{item['price']} ⭐{item['rating']}\n"
        menu_text += '\nTo order, type: "Add [item name]"'
        return jsonify({"reply": menu_text})

    #Timings
    if "timing" in user_message:
        return jsonify({"reply": "We are open from 10 AM to 11 PM ⏰"})

    #WiFi
    if "wifi" in user_message:
        return jsonify({"reply": "Yes! Free WiFi available 📶\nPassword: cafe123"})

    #Offers
    if "offer" in user_message:
        return jsonify({"reply": (
            "🎉 Current Offers:\n\n"
            "🔥 Buy 1 Pizza Get 1 Free (on Margherita)\n"
            "🍔 Combo: Burger + Fries + Coke @ ₹199\n"
            "🥤 20% OFF on all Shakes (today only)\n"
            "☕ Free Coffee on orders above ₹299"
        )})

    #Direct dish lookup
    dish = find_dish(user_message)
    if dish:
        return jsonify({
            "reply": (
                f"🍽️ *{dish['name']}*\n"
                f"💰 ₹{dish['price']}  ⭐ {dish['rating']}\n\n"
                f'To order, type: "Add {dish["name"]}"'
            )
        })

    # AI 
    menu_text = "\n".join(f"{i['name']} - ₹{i['price']} - ⭐{i['rating']}" for i in menu)

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "z-ai/glm-4.5-air:free",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"You are a smart café assistant.\n\nMenu:\n{menu_text}\n\n"
                        "Recommend food based on user request. Keep answers short and friendly. "
                        'Always end with: To order, type "Add [item name]"'
                    )
                },
                {"role": "user", "content": user_message}
            ]
        })
    )

    result = response.json()
    reply  = result["choices"][0]["message"]["content"]
    return jsonify({"reply": reply})


if __name__ == '__main__':
    app.run(debug=True)