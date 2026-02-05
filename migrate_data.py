import os
import pandas as pd
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 1. Setup a temporary app context
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'dokan.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 2. Define Models locally (Must match the new models.py exactly)
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

def migrate():
    with app.app_context():
        # Create DB folder if not exists
        if not os.path.exists('instance'):
            os.makedirs('instance')
        
        # Reset Database (Drop all to ensure clean schema)
        db.drop_all()
        db.create_all()
        print("Database initialized.")

        # Migrate Inventory
        if os.path.exists('data/inventory.csv'):
            df = pd.read_csv('data/inventory.csv')
            # Clean column names just in case (strip spaces)
            df.columns = df.columns.str.strip()
            
            for _, row in df.iterrows():
                # Note: We explicitly set 'id' from the CSV
                p = Product(
                    id=int(row['id']),
                    name=row['name'],
                    category=row['category'],
                    stock=int(row['stock']),
                    price=float(row['price']),
                    expiry_date=row['expiry_date'],
                    supplier=row['supplier']
                )
                db.session.add(p)
            print(f"Migrated {len(df)} products.")

        # Migrate Sales
        if os.path.exists('data/sales.csv'):
            df = pd.read_csv('data/sales.csv')
            df.columns = df.columns.str.strip()
            
            for _, row in df.iterrows():
                s = Sale(
                    item_id=int(row['item_id']),
                    date=row['date'],
                    sales=int(row['sales'])
                )
                db.session.add(s)
            print(f"Migrated {len(df)} sales.")

        # Migrate Transactions
        if os.path.exists('data/transactions.csv'):
            df = pd.read_csv('data/transactions.csv')
            df.columns = df.columns.str.strip()
            
            for _, row in df.iterrows():
                t = Transaction(
                    transaction_id=int(row['transaction_id']),
                    item_id=int(row['item_id'])
                )
                db.session.add(t)
            print(f"Migrated {len(df)} transactions.")

        db.session.commit()
        print("Migration complete! Data is now in instance/dokan.db")

if __name__ == '__main__':
    migrate()