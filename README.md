# MediSearch Bot 🏥

MediSearch is a comprehensive medicine ordering system that combines a Telegram bot interface with a web-based admin panel. The system allows users to search for medicines, place orders via Telegram, and enables administrators to manage orders through a clean web interface.

## 🌟 Features

### Telegram Bot
- 🔍 Smart medicine search by name, salt composition, or therapeutic class
- 🛒 Shopping cart functionality
- 📦 Order placement with delivery address
- 💊 Detailed medicine information including price, composition, and stock
- 🤖 User-friendly command interface

### Admin Panel
- 📊 Order management dashboard
- 🔄 Real-time order status updates
- 📅 Date-based order filtering
- 👤 Customer name search with autocomplete
- 💰 Revenue tracking for completed orders
- 📍 Delivery address tracking
- 📱 Responsive design

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Telegram Bot Token (get it from [@BotFather](https://t.me/botfather))

### Installation

1. Clone the repository:
bash
git clone https://github.com/yourusername/medisearch.git
cd medisearch

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
dataset_path=medicines.csv
```

5. Create required directories:
```bash
mkdir data
```

### 🏃‍♂️ Running the Application

1. Start the application:
```bash
python src/main.py
```

This will launch both:
- Telegram bot
- Admin web interface (default: http://localhost:5000)

## 📁 Project Structure

```
medisearch/
├── data/
│   ├── medicines.csv
│   └── orders.csv
├── src/
│   ├── templates/
│   │   ├── base.html
│   │   ├── orders.html
│   │   └── order_detail.html
│   ├── main.py
│   ├── bot.py
│   ├── web_interface.py
│   ├── product_db.py
│   └── ai_handler.py
├── requirements.txt
└── README.md
```

## 💻 Admin Interface

The admin interface provides:
- Order management with status updates (Pending/Completed/Cancelled)
- Detailed order information
- Customer filtering
- Date-based filtering
- Revenue tracking

Access the admin panel at: `http://localhost:5000`

## 🤖 Bot Commands

- `/start` - Start the bot and get welcome message
- `/help` - Display help information
- `/cart` - View shopping cart

## 🛠 Development

To update product quantities for testing:
```bash
python src/update_quantities.py data/medicines.csv --min 0 --max 25
```

## 🔐 Security

- Web interface uses Flask's session management
- Secure storage of bot token using environment variables
- Input validation and sanitization

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For support or queries, please create an issue in the repository.

