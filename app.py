import os
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# --- Database Configuration ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'dokan.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
            return "User already exists! <a href='/register'>Try again</a>"
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
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
        return "Invalid credentials! <a href='/login'>Try again</a>"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
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
            stock = int(request.form['stock'])
            price = float(request.form['price'])
            if stock < 0 or price < 0:
                return "Error: Stock and Price cannot be negative!"
        except ValueError:
            return "Error: Invalid number format!"

        item_id = request.form.get('id')
        
        if item_id: # Update Existing
            product = Product.query.get(item_id)
            if product:
                product.name = request.form['name']
                product.category = request.form['category']
                product.stock = stock
                product.price = price
                product.expiry_date = request.form['expiry_date']
                product.supplier = request.form['supplier']
        else: # Add New
            new_product = Product(
                name=request.form['name'],
                category=request.form['category'],
                stock=stock,
                price=price,
                expiry_date=request.form['expiry_date'],
                supplier=request.form['supplier']
            )
            db.session.add(new_product)
        
        db.session.commit()
        return redirect(url_for('inventory'))

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
def billing():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity'))
        
        product = Product.query.get(product_id)
        
        if product and product.stock >= quantity:
            product.stock -= quantity
            
            new_sale = Sale(
                item_id=product.id,
                sales=quantity,
                date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            db.session.add(new_sale)
            
            new_trans = Transaction(
                transaction_id=101,
                item_id=product.id
            )
            db.session.add(new_trans)
            
            db.session.commit()
            flash("Sale successful!", "success")
        else:
            flash("Error: Not enough stock!", "error")
            
        return redirect(url_for('billing'))

    products = Product.query.all()
    return render_template('billing.html', products=products)

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            new_feedback = Feedback(
                user_id=current_user.id,
                message=message,
                date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            db.session.add(new_feedback)
            db.session.commit()
            flash("Feedback sent!", "success")
            return redirect(url_for('dashboard'))
            
    try:
        return render_template('feedback.html')
    except:
        return "Feedback Page Under Construction (Template Missing)"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)