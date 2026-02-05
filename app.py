from flask import Flask, render_template, request, redirect, url_for, jsonify
import csv
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from validators import ValidationError, validate_inventory_item, sanitize_for_csv
from cache_utils import SimpleCache

app = Flask(__name__)

# Inject the Secret Key securely (No longer hardcoded!)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Inject the Database URL securely
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

db = SQLAlchemy(app)

CSV_FILE = 'data/inventory.csv'
TRANSACTIONS_FILE = 'data/transactions.csv'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    stock = db.Column(db.Integer)
    price = db.Column(db.Float)
    expiry_date = db.Column(db.String(20))
    supplier = db.Column(db.String(100))

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(20))
    sales = db.Column(db.Integer)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer)
    item_id = db.Column(db.Integer)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(20))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---

@app.route('/')
def home():
    # If user is already logged in, go straight to inventory
    if current_user.is_authenticated:
        return redirect(url_for('inventory'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            logger.warning(f"Registration attempt failed: User '{username}' already exists.")
            return "User already exists! <a href='/register'>Try again</a>"
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"New user registered: {username}")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            # CHANGED: Redirect to 'inventory' instead of 'dashboard'
            return redirect(url_for('inventory'))
        
        logger.warning(f"Failed login attempt for user: {username}")
        return "Invalid credentials! <a href='/login'>Try again</a>"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    user = current_user.username
    logout_user()
    logger.info(f"User logged out: {user}")
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    products = Product.query.all()
    sales = Sale.query.all()
    
    total_products = len(products)
    total_sales_count = len(sales)
    low_stock_items = [p for p in products if p.stock < 10]
    
    return render_template('dashboard.html', 
                           products=products, 
                           sales=sales, 
                           total_products=total_products, 
                           total_sales_count=total_sales_count,
                           low_stock_items=low_stock_items)

@app.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if request.method == 'POST':
        try:
            # Validate all inventory item fields
            validated_item = validate_inventory_item(request.form)

            # Sanitize values for CSV storage
            item = {
                'id': sanitize_for_csv(validated_item['id']),
                'name': sanitize_for_csv(validated_item['name']),
                'category': sanitize_for_csv(validated_item['category']),
                'stock': sanitize_for_csv(validated_item['stock']),
                'price': sanitize_for_csv(validated_item['price']),
                'expiry_date': sanitize_for_csv(validated_item['expiry_date']),
                'supplier': sanitize_for_csv(validated_item['supplier'])
            }

            # Edit/Update Logic
            data = read_csv(CSV_FILE)
            updated = False
            for i, row in enumerate(data):
                if row['id'] == item['id']:
                    data[i] = item  # Update existing
                    updated = True
                    break

            if not updated:
                data.append(item)  # Add new
                flash(f"Product '{item['name']}' added successfully!", "success")
            else:
                flash(f"Product '{item['name']}' updated successfully!", "success")

            write_csv(CSV_FILE, data)
            cache.invalidate_all() # Invalidate cache on update
            return redirect(url_for('inventory'))

        except ValidationError as e:
            flash(e.message, "error")
            items = read_csv(CSV_FILE)
            return render_template('inventory.html', items=items, edit_item=None)
        except Exception as e:
            flash("An unexpected error occurred. Please try again.", "error")
            items = read_csv(CSV_FILE)
            return render_template('inventory.html', items=items, edit_item=None)

    products = Product.query.all()
    items = [{'id': p.id, 'name': p.name, 'category': p.category, 'stock': p.stock, 
              'price': p.price, 'expiry_date': p.expiry_date, 'supplier': p.supplier} for p in products]

    return render_template('inventory.html', items=items, edit_item=None)

@app.route('/edit_product/<item_id>')
@login_required
def edit_product(item_id):
    product = Product.query.get(item_id)
    if not product:
        return redirect(url_for('inventory'))
        
    item_to_edit = {'id': product.id, 'name': product.name, 'category': product.category, 'stock': product.stock, 
                    'price': product.price, 'expiry_date': product.expiry_date, 'supplier': product.supplier}
    
    all_products = Product.query.all()
    items = [{'id': p.id, 'name': p.name, 'category': p.category, 'stock': p.stock, 
              'price': p.price, 'expiry_date': p.expiry_date, 'supplier': p.supplier} for p in all_products]

    return render_template('inventory.html', items=items, edit_item=item_to_edit)

@app.route('/delete/<item_id>')
@login_required
def delete_item(item_id):
    product = Product.query.get(item_id)
    if product:
        db.session.delete(product)
        db.session.commit()
    return redirect(url_for('inventory'))

@app.route('/billing', methods=['GET', 'POST'])
@login_required
@cache.cached(ttl=60)
def dashboard():
    items = read_csv(CSV_FILE)
    
    # Initialize with empty default values
    sales_forecast = {}
    stockout_predictions = []
    suggestions = []
    
    # Try to load AI insights (optional - graceful degradation if dependencies missing)
    try:
        from ai.sales_forecast import predict_sales
        sales_forecast = predict_sales(items)
    except (ImportError, Exception) as e:
        flash(f"Sales forecast unavailable: {str(e)}", "warning")
    
    try:
        from ai.stockout_predictor import predict_stockout
        stockout_predictions = predict_stockout(items)
    except (ImportError, Exception) as e:
        flash(f"Stockout predictions unavailable: {str(e)}", "warning")
    
    try:
        from ai.recommender import recommend_products
        suggestions = recommend_products(items)
    except (ImportError, Exception) as e:
        flash(f"Product recommendations unavailable: {str(e)}", "warning")
    
    return render_template('dashboard.html', 
                         items=items,
                         sales_forecast=sales_forecast,
                         stockout_predictions=stockout_predictions,
                         suggestions=suggestions)

    products = Product.query.all()
    return render_template('billing.html', products=products)

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def billing():
    return render_template('billing.html')

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    sentiment = None
    if request.method == 'POST':
        feedback_text = request.form.get('feedback', '').strip()
        if feedback_text:
            try:
                from ai.sentiment_analyzer import analyze_feedback
                sentiment = analyze_feedback(feedback_text)
            except (ImportError, Exception) as e:
                flash(f"Sentiment analysis unavailable: {str(e)}", "warning")
                sentiment = "Unable to analyze (missing dependencies)"
    
    return render_template('feedback.html', sentiment=sentiment)

@app.route('/api/inventory')
@login_required
def api_inventory():
    """API endpoint to get inventory data for billing page"""
    items = read_csv(CSV_FILE)
    return jsonify(items)


@app.route('/api/checkout', methods=['POST'])
@login_required
def api_checkout():
    """
    API endpoint to process checkout:
    - Updates inventory.csv (decreases stock)
    - Logs sale in transactions.csv
    """
    try:
        data = request.get_json()
        items = data.get('items', [])
        customer_name = data.get('customer_name', 'Unknown')
        
        if not items:
            return jsonify({'success': False, 'error': 'No items in cart'}), 400
        
        # Read current inventory
        inventory = read_csv(CSV_FILE)
        
        # Validate stock availability first
        for cart_item in items:
            item_id = str(cart_item.get('id'))
            qty = int(cart_item.get('qty', 0))
            
            inv_item = next((i for i in inventory if str(i['id']) == item_id), None)
            if not inv_item:
                return jsonify({'success': False, 'error': f'Item ID {item_id} not found'}), 400
            
            if int(inv_item['stock']) < qty:
                return jsonify({'success': False, 'error': f'Not enough stock for {inv_item["name"]}'}), 400
        
        # Generate new transaction ID
        transactions = read_csv(TRANSACTIONS_FILE)
        if transactions:
            max_trans_id = max(int(t['transaction_id']) for t in transactions)
            new_trans_id = max_trans_id + 1
        else:
            new_trans_id = 1
        
        # Update inventory and create transaction records
        new_transactions = []
        for cart_item in items:
            item_id = str(cart_item.get('id'))
            qty = int(cart_item.get('qty', 0))
            
            # Update inventory stock
            for inv_item in inventory:
                if str(inv_item['id']) == item_id:
                    inv_item['stock'] = int(inv_item['stock']) - qty
                    break
            
            # Add transaction record (one per item in the bill)
            new_transactions.append({
                'transaction_id': new_trans_id,
                'item_id': item_id
            })
        
        # Write updated inventory
        write_csv(CSV_FILE, inventory)
        
        # Append new transactions
        transactions.extend(new_transactions)
        write_csv(TRANSACTIONS_FILE, transactions)
        
        cache.invalidate_all() # Invalidate cache on new transaction
        
        return jsonify({
            'success': True, 
            'message': 'Checkout successful',
            'transaction_id': new_trans_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)