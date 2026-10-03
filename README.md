# ☕ Cafe Chatbot

A web-based chatbot that helps cafe customers [browse the menu, ask questions, and place orders] through a simple chat interface.

**Live demo:**

## Features
- Answers questions about menu items and prices
- Takes and saves customer orders
- Clean, responsive chat UI
- Menu managed through an easy-to-edit `menu.json` file

## Tech Stack
- **Backend:** Python, [Flask]
- **Frontend:** HTML, CSS, JavaScript
- **Data:** JSON files for menu and orders


## How It Works
The user sends a message from the chat UI (`script.js`), which calls the Python backend (`app.py`). The backend [looks up the menu / calls the AI model], builds a reply, and saves orders to `data/orders.json`.

## Getting Started
1. Clone the repo
```bash
   git clone https://github.com/YOUR-USERNAME/cafe-chatbot.git
   cd cafe-chatbot
```
2. Install dependencies
```bash
   pip install -r requirements.txt
```
3. Create a `.env` file (see `.env.example`) and add your key
4. Run the app
```bash
   python app.py
```
5. Open `http://localhost:5000`

## Future Improvements
- Store orders in a database instead of JSON
- Add order status tracking
- Add payment integration

## Author
**Muskan**