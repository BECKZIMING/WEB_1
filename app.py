from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import pdfplumber
import os

app = Flask(__name__)

# Set up the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transactions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define a database model for transactions
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(100))
    description = db.Column(db.String(200))
    amount = db.Column(db.Float)

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'

    if file:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                lines = text.split('\n')

                # Logic to extract transactions
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 3:
                        date, description, amount = parts[0], ' '.join(parts[1:-1]), parts[-1]
                        try:
                            amount = float(amount.replace(',', '').replace('$', ''))
                        except ValueError:
                            continue

                        # Save to the database
                        transaction = Transaction(date=date, description=description, amount=amount)
                        db.session.add(transaction)
            db.session.commit()

        return '''
            <h1>Data from PDF saved!</h1>
            <a href="/" style="display: inline-block; margin-top: 20px; padding: 10px 20px; 
                background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">
                Return to Home
            </a>
            <a href="/transactions" style="display: inline-block; margin-top: 20px; padding: 10px 20px; 
                background-color: #2196F3; color: white; text-decoration: none; border-radius: 5px;">
                View Transactions
            </a>
        '''

@app.route('/transactions')
def view_transactions():
    transactions = Transaction.query.all()
    output = '<h1>Saved Transactions:</h1>'
    for transaction in transactions:
        output += f'<p>{transaction.date} - {transaction.description} - ${transaction.amount}</p>'
    
    output += '''
        <br>
        <a href="/" style="display: inline-block; margin-top: 20px; padding: 10px 20px; 
            background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">
            Return to Home
        </a>
    '''
    return output

if __name__ == '__main__':
    # Run the Flask app on the port defined by the PORT environment variable, default to 8080 if not set
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
