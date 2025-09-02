from flask import Flask, render_template, request, session, redirect, url_for, send_file, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import pandas as pd
from datetime import datetime
import ai_core 
import io
import os
from forms import LoginForm, RegistrationForm
from models import db, bcrypt, User # <-- MODIFIED: Import from models.py

# --- Flask App Initialization & Configuration ---
app = Flask(__name__)
app.secret_key = 'your_super_secret_key_for_hackathon'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Initialize Extensions with the App ---
db.init_app(app)
bcrypt.init_app(app)

# --- Login Manager Setup ---
login_manager = LoginManager(app)
login_manager.login_view = 'login' 
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- App Configuration ---
DATA_DIR = 'data'

# --- Authentication Routes ---
@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user) # Log the user in automatically
        flash(f'Welcome, {user.username}! Your account has been successfully created.', 'success')
        return redirect(url_for('index')) # Redirect to the main page
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Main Application Route (Now Protected) ---
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        if 'run_strategic' in request.form:
            if 'strategic_file' not in request.files or request.files['strategic_file'].filename == '':
                flash('Please upload a historical data file to train the strategic models.', 'warning')
                return redirect(url_for('index'))
            
            s_file = request.files['strategic_file']
            s_filepath = os.path.join(DATA_DIR, 'historical_data.csv')
            s_file.save(s_filepath)

            try:
                hist_df = pd.read_csv(s_filepath)
                products_in_file = hist_df['product_name'].unique().tolist()
            except Exception as e:
                flash(f"Could not read product list from file: {e}", "danger")
                return redirect(url_for('index'))

            success, message = ai_core.train_strategic_models()
            if not success:
                flash(f'Error during strategic model training: {message}', 'danger')
                return redirect(url_for('index'))
            
            ai_core.load_models()
            if not ai_core.MODELS['stock'] or not ai_core.MODELS['waste']:
                 flash('Strategic models trained but failed to load. Cannot generate forecast.', 'danger')
                 return redirect(url_for('index'))
            target_month = int(request.form['month'])
            target_year = int(request.form['year'])
            predictions = ai_core.run_strategic_prediction(products_in_file, target_month, target_year)
            session['strategic_df'] = predictions.to_json()
            session['strategic_month'] = target_month
            session['strategic_year'] = target_year
            chart_data = {'labels': predictions['Product'].tolist(), 'stock': predictions['Recommended Stock (Units)'].tolist(), 'waste': predictions['Predicted Waste (Units)'].tolist()}
            total_stock = predictions['Recommended Stock (Units)'].sum()
            total_waste = predictions['Predicted Waste (Units)'].sum()
            waste_percentage = (total_waste / total_stock * 100) if total_stock > 0 else 0
            return render_template('strategic_results.html', month=target_month, year=target_year, chart_data=chart_data, total_stock=f"{total_stock:,}", total_waste=f"{total_waste:,}", waste_percentage=f"{waste_percentage:.1f}", results_table=predictions.to_html(classes='table table-hover text-center', index=False))
        elif 'run_tactical' in request.form:
            if 'tactical_file' not in request.files or request.files['tactical_file'].filename == '':
                flash('Please upload a tactical training data file.', 'warning')
                return redirect(url_for('index'))
            
            t_file = request.files['tactical_file']
            t_filepath = os.path.join(DATA_DIR, 'tactical_training_data.csv')
            t_file.save(t_filepath)
            success, message = ai_core.train_tactical_model()
            if not success:
                flash(f'Error during tactical model training: {message}', 'danger')
                return redirect(url_for('index'))
            if 'inventory_file' not in request.files or request.files['inventory_file'].filename == '':
                flash('Training successful, but please also upload an inventory file for analysis.', 'warning')
                return redirect(url_for('index'))
            
            ai_core.load_models()
            if not ai_core.MODELS['sell_through']:
                flash('Tactical model trained but failed to load. Cannot get daily actions.', 'danger')
                return redirect(url_for('index'))
            
            inventory_file = request.files['inventory_file']
            try:
                inventory_df = pd.read_csv(inventory_file.stream)
                sale_items, donation_items = ai_core.run_tactical_analysis(inventory_df.copy())
                total_waste_prevented = donation_items['current_stock'].sum() + sale_items['current_stock'].sum()
                total_revenue_recovered = sale_items['recovered_revenue'].sum()
                co2_saved = total_waste_prevented * 0.5
                water_saved = total_waste_prevented * 25
                potential_meals = int(donation_items['current_stock'].sum() * 2.5)
                return render_template('tactical_results.html', 
                                       sale_items=sale_items.to_dict('records'), 
                                       donation_items=donation_items.to_dict('records'), 
                                       co2_saved=f"{co2_saved:.1f}", 
                                       water_saved=f"{water_saved:,.0f}", 
                                       revenue_recovered=f"${total_revenue_recovered:,.2f}", 
                                       potential_meals=f"~{potential_meals:,}")
            except Exception as e:
                flash(f"An error occurred while processing the inventory file: {e}", "danger")
                return redirect(url_for('index'))
    current_year = datetime.now().year
    return render_template('index.html', current_year=current_year)

@app.route('/download_po')
@login_required
def download_po():
    strategic_df_json = session.get('strategic_df', None)
    if strategic_df_json is None:
        flash("No strategic forecast found in session. Please run a forecast first.", "warning")
        return redirect(url_for('index'))
    df = pd.read_json(strategic_df_json)
    month = session.get('strategic_month')
    year = session.get('strategic_year')
    po_df = df[['Product', 'Recommended Stock (Units)']]
    output = io.BytesIO()
    po_df.to_csv(output, index=False)
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name=f'purchase_order_{month}_{year}.csv')

if __name__ == '__main__':
    # You may need to create the database from a separate script or the terminal first
    with app.app_context():
        db.create_all()
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(ai_core.MODEL_DIR, exist_ok=True)
    app.run(debug=True, port=5004)