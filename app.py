import os
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, BooleanField, SelectField, FloatField, TextAreaField, DateTimeLocalField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional
from sqlalchemy import func
from dotenv import load_dotenv

# Load env variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key-for-dev')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///foodbridge.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect(app)

# ------------------------------------------------------------------------------
# MODELS
# ------------------------------------------------------------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'donor', 'claimant', 'admin'
    phone = db.Column(db.String(20))
    organization = db.Column(db.String(100))
    area = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    listings = db.relationship('Listing', backref='donor', lazy=True, foreign_keys='Listing.donor_id')
    claims = db.relationship('Claim', backref='claimant', lazy=True, foreign_keys='Claim.claimant_id')

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    quantity_kg = db.Column(db.Float, nullable=False)
    expiry_time = db.Column(db.DateTime, nullable=False)
    pickup_start = db.Column(db.String(50))
    pickup_end = db.Column(db.String(50))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    area = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    claims = db.relationship('Claim', backref='listing', lazy=True)
    impact_log = db.relationship('ImpactLog', backref='listing', uselist=False, lazy=True)
    
    @property
    def is_expired(self):
        return self.expiry_time < datetime.utcnow()
        
    @property
    def urgency(self):
        now = datetime.utcnow()
        delta = self.expiry_time - now
        if delta < timedelta(hours=2):
            return 'critical'
        elif delta < timedelta(hours=6):
            return 'urgent'
        return 'normal'

class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    claimant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, confirmed, cancelled
    notes = db.Column(db.Text)
    claimed_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class ImpactLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    claimant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    kg_rescued = db.Column(db.Float, nullable=False)
    co2_saved_kg = db.Column(db.Float, nullable=False)
    meals_enabled = db.Column(db.Integer, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ------------------------------------------------------------------------------
# FORMS
# ------------------------------------------------------------------------------

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('donor', 'Donor (I have food)'), ('claimant', 'Claimant (I need food)')], validators=[DataRequired()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    organization = StringField('Organization (Optional)', validators=[Optional(), Length(max=100)])

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

class ListingForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('cooked_food', 'Cooked Food'),
        ('raw_produce', 'Raw Produce'),
        ('packaged', 'Packaged Goods'),
        ('bakery', 'Bakery Items'),
        ('dairy', 'Dairy Products'),
        ('beverages', 'Beverages'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    quantity_kg = FloatField('Quantity (kg)', validators=[DataRequired()])
    expiry_time = DateTimeLocalField('Expiry Date & Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    pickup_start = StringField('Pickup Window Start', validators=[DataRequired()])
    pickup_end = StringField('Pickup Window End', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    area = StringField('Area/Neighborhood', validators=[DataRequired()])

# ------------------------------------------------------------------------------
# DECORATORS & HELPERS
# ------------------------------------------------------------------------------

def donor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'donor':
            abort(403)
        return f(*args, **kwargs)
    return decorated

def claimant_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'claimant':
            abort(403)
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated

def mark_expired_listings():
    now = datetime.utcnow()
    expired_listings = Listing.query.filter(Listing.expiry_time < now, Listing.status == 'active').all()
    for listing in expired_listings:
        listing.status = 'expired'
    if expired_listings:
        db.session.commit()

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

def get_impact_stats():
    stats = db.session.query(
        func.sum(ImpactLog.kg_rescued).label('total_kg'),
        func.sum(ImpactLog.meals_enabled).label('total_meals'),
        func.sum(ImpactLog.co2_saved_kg).label('total_co2'),
        func.count(ImpactLog.id).label('rescues_count')
    ).first()
    return {
        'kg_rescued': stats.total_kg or 0,
        'meals_enabled': stats.total_meals or 0,
        'co2_saved': stats.total_co2 or 0,
        'rescues_count': stats.rescues_count or 0
    }

# ------------------------------------------------------------------------------
# CLI COMMANDS
# ------------------------------------------------------------------------------

@app.cli.command("seed-db")
def seed_db():
    db.create_all()
    
    if User.query.filter_by(email='admin@foodbridge.com').first():
        print("Database already seeded.")
        return
        
    print("Seeding database...")
    
    # Create Users
    admin = User(email='admin@foodbridge.com', password_hash=bcrypt.generate_password_hash('admin123').decode('utf-8'), name='Admin User', role='admin')
    donor1 = User(email='donor1@test.com', password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'), name='Spice Garden Restaurant', role='donor', organization='Spice Garden')
    donor2 = User(email='donor2@test.com', password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'), name='Fresh Mart Grocery', role='donor', organization='Fresh Mart')
    claimant1 = User(email='claimant1@test.com', password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'), name='Hope NGO', role='claimant', organization='Hope Foundation')
    claimant2 = User(email='claimant2@test.com', password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'), name='City Food Bank', role='claimant', organization='City Food Bank')
    
    db.session.add_all([admin, donor1, donor2, claimant1, claimant2])
    db.session.commit()
    
    now = datetime.utcnow()
    
    # Create Listings
    l1 = Listing(donor_id=donor1.id, title='Surplus Curry and Rice', description='10 portions of vegetable curry and rice. Cooked today.', category='cooked_food', quantity_kg=5.0, expiry_time=now + timedelta(hours=3), pickup_start='14:00', pickup_end='16:00', address='123 Spice St', city='Metro', area='Downtown', status='active')
    l2 = Listing(donor_id=donor2.id, title='Assorted Vegetables', description='Slightly bruised but perfectly edible carrots and potatoes.', category='raw_produce', quantity_kg=12.5, expiry_time=now + timedelta(hours=48), pickup_start='09:00', pickup_end='18:00', address='45 Market Rd', city='Metro', area='Westside', status='active')
    l3 = Listing(donor_id=donor1.id, title='Leftover Bread', description='Baguettes and rolls from yesterday.', category='bakery', quantity_kg=3.0, expiry_time=now + timedelta(hours=1), pickup_start='12:00', pickup_end='13:00', address='123 Spice St', city='Metro', area='Downtown', status='active')
    l4 = Listing(donor_id=donor2.id, title='Milk Cartons', description='Near expiry milk cartons.', category='dairy', quantity_kg=10.0, expiry_time=now + timedelta(hours=12), pickup_start='10:00', pickup_end='20:00', address='45 Market Rd', city='Metro', area='Westside', status='active')
    l5 = Listing(donor_id=donor1.id, title='Catering Leftovers', description='Mixed food from a corporate event.', category='cooked_food', quantity_kg=20.0, expiry_time=now - timedelta(hours=1), pickup_start='08:00', pickup_end='10:00', address='123 Spice St', city='Metro', area='Downtown', status='expired')
    l6 = Listing(donor_id=donor2.id, title='Packaged Snacks', description='Boxes of crackers.', category='packaged', quantity_kg=15.0, expiry_time=now + timedelta(days=5), pickup_start='09:00', pickup_end='17:00', address='45 Market Rd', city='Metro', area='Westside', status='completed')
    
    db.session.add_all([l1, l2, l3, l4, l5, l6])
    db.session.commit()
    
    # Create Claim & Impact for l6
    c1 = Claim(listing_id=l6.id, claimant_id=claimant1.id, status='confirmed', claimed_at=now - timedelta(days=1), completed_at=now)
    db.session.add(c1)
    
    il1 = ImpactLog(listing_id=l6.id, donor_id=donor2.id, claimant_id=claimant1.id, kg_rescued=15.0, co2_saved_kg=15.0 * 2.5, meals_enabled=int(15.0 * 2), recorded_at=now)
    db.session.add(il1)
    db.session.commit()
    
    print("Database seeded successfully.")

# ------------------------------------------------------------------------------
# ROUTES - AUTH
# ------------------------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email is already registered. Please log in.', 'danger')
            return redirect(url_for('login'))
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password_hash=hashed_pw,
            role=form.role.data,
            phone=form.phone.data,
            organization=form.organization.data
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('auth/register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.is_active and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login successful.', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ------------------------------------------------------------------------------
# ROUTES - LISTINGS
# ------------------------------------------------------------------------------

@app.route('/')
def index():
    mark_expired_listings()
    impact_stats = get_impact_stats()
    recent_listings = Listing.query.filter_by(status='active').order_by(Listing.created_at.desc()).limit(3).all()
    return render_template('index.html', impact_stats=impact_stats, recent_listings=recent_listings)

@app.route('/browse')
def browse():
    mark_expired_listings()
    query = Listing.query.filter_by(status='active')
    
    category = request.args.get('category')
    area = request.args.get('area')
    urgency = request.args.get('urgency')
    search_q = request.args.get('q')
    
    if category:
        query = query.filter_by(category=category)
    if area:
        query = query.filter(Listing.area.ilike(f'%{area}%'))
    if search_q:
        query = query.filter(db.or_(Listing.title.ilike(f'%{search_q}%'), Listing.description.ilike(f'%{search_q}%')))
        
    listings = query.order_by(Listing.expiry_time.asc()).all()
    
    # Filter by urgency (computed property)
    if urgency:
        listings = [l for l in listings if l.urgency == urgency]
        
    return render_template('listings/browse.html', listings=listings)

@app.route('/listings/new', methods=['GET', 'POST'])
@login_required
@donor_required
def create_listing():
    form = ListingForm()
    if form.validate_on_submit():
        listing = Listing(
            donor_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            quantity_kg=form.quantity_kg.data,
            expiry_time=form.expiry_time.data,
            pickup_start=form.pickup_start.data,
            pickup_end=form.pickup_end.data,
            address=form.address.data,
            city=form.city.data,
            area=form.area.data
        )
        db.session.add(listing)
        db.session.commit()
        flash('Listing created successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('listings/create.html', form=form)

@app.route('/listings/<int:id>')
def listing_detail(id):
    listing = db.session.get(Listing, id)
    if not listing:
        abort(404)
    return render_template('listings/detail.html', listing=listing)

@app.route('/listings/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@donor_required
def edit_listing(id):
    listing = db.session.get(Listing, id)
    if not listing:
        abort(404)
    if listing.donor_id != current_user.id:
        abort(403)
    if listing.status != 'active':
        flash('Cannot edit a listing that is no longer active.', 'danger')
        return redirect(url_for('listing_detail', id=listing.id))
        
    form = ListingForm()
    if form.validate_on_submit():
        listing.title = form.title.data
        listing.description = form.description.data
        listing.category = form.category.data
        listing.quantity_kg = form.quantity_kg.data
        listing.expiry_time = form.expiry_time.data
        listing.pickup_start = form.pickup_start.data
        listing.pickup_end = form.pickup_end.data
        listing.address = form.address.data
        listing.city = form.city.data
        listing.area = form.area.data
        db.session.commit()
        flash('Listing updated successfully!', 'success')
        return redirect(url_for('listing_detail', id=listing.id))
    elif request.method == 'GET':
        form.title.data = listing.title
        form.description.data = listing.description
        form.category.data = listing.category
        form.quantity_kg.data = listing.quantity_kg
        form.expiry_time.data = listing.expiry_time
        form.pickup_start.data = listing.pickup_start
        form.pickup_end.data = listing.pickup_end
        form.address.data = listing.address
        form.city.data = listing.city
        form.area.data = listing.area
        
    return render_template('listings/edit.html', form=form, listing=listing)

@app.route('/listings/<int:id>/delete', methods=['POST'])
@login_required
@donor_required
def delete_listing(id):
    listing = db.session.get(Listing, id)
    if not listing or listing.donor_id != current_user.id:
        abort(403)
    if listing.status == 'active':
        db.session.delete(listing)
        db.session.commit()
        flash('Listing deleted.', 'success')
    else:
        flash('Cannot delete this listing.', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/listings/<int:id>/claim', methods=['POST'])
@login_required
@claimant_required
def claim_listing(id):
    # Transactional Claim to prevent double claiming
    try:
        listing = db.session.query(Listing).with_for_update().get(id)
        if not listing:
            abort(404)
        if listing.status != 'active' or listing.is_expired:
            flash('This listing is no longer available.', 'danger')
            return redirect(url_for('browse'))
            
        listing.status = 'claimed'
        claim = Claim(listing_id=listing.id, claimant_id=current_user.id, status='pending')
        db.session.add(claim)
        db.session.commit()
        flash('You have successfully claimed this food! Please pick it up during the specified window.', 'success')
        return redirect(url_for('listing_detail', id=listing.id))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('listing_detail', id=id))

@app.route('/listings/<int:id>/confirm', methods=['POST'])
@login_required
@donor_required
def confirm_pickup(id):
    listing = db.session.get(Listing, id)
    if not listing or listing.donor_id != current_user.id:
        abort(403)
    if listing.status != 'claimed':
        flash('Invalid action.', 'danger')
        return redirect(url_for('listing_detail', id=listing.id))
        
    claim = Claim.query.filter_by(listing_id=listing.id, status='pending').first()
    if claim:
        claim.status = 'confirmed'
        claim.completed_at = datetime.utcnow()
        listing.status = 'completed'
        
        # Create impact log
        meals = int(listing.quantity_kg * 2)
        co2 = listing.quantity_kg * 2.5
        impact = ImpactLog(
            listing_id=listing.id,
            donor_id=listing.donor_id,
            claimant_id=claim.claimant_id,
            kg_rescued=listing.quantity_kg,
            co2_saved_kg=co2,
            meals_enabled=meals
        )
        db.session.add(impact)
        db.session.commit()
        flash('Pickup confirmed! Impact tracked.', 'success')
    return redirect(url_for('listing_detail', id=listing.id))

@app.route('/listings/<int:id>/cancel-claim', methods=['POST'])
@login_required
def cancel_claim(id):
    listing = db.session.get(Listing, id)
    if not listing:
        abort(404)
        
    claim = Claim.query.filter_by(listing_id=listing.id, status='pending').first()
    if not claim:
        flash('No active claim found.', 'danger')
        return redirect(url_for('listing_detail', id=listing.id))
        
    if current_user.id not in [listing.donor_id, claim.claimant_id]:
        abort(403)
        
    claim.status = 'cancelled'
    listing.status = 'active'
    db.session.commit()
    flash('Claim cancelled. Listing is active again.', 'info')
    return redirect(url_for('listing_detail', id=listing.id))

# ------------------------------------------------------------------------------
# ROUTES - DASHBOARD & MISC
# ------------------------------------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'donor':
        return redirect(url_for('donor_dashboard'))
    elif current_user.role == 'claimant':
        return redirect(url_for('claimant_dashboard'))
    elif current_user.role == 'admin':
        return redirect(url_for('admin'))
    abort(403)

@app.route('/dashboard/donor')
@login_required
@donor_required
def donor_dashboard():
    listings = Listing.query.filter_by(donor_id=current_user.id).order_by(Listing.created_at.desc()).all()
    impact = db.session.query(
        func.sum(ImpactLog.kg_rescued).label('kg_rescued'),
        func.sum(ImpactLog.meals_enabled).label('meals_enabled'),
        func.sum(ImpactLog.co2_saved_kg).label('co2_saved')
    ).filter(ImpactLog.donor_id == current_user.id).first()
    return render_template('dashboard/donor.html', listings=listings, impact=impact)

@app.route('/dashboard/claimant')
@login_required
@claimant_required
def claimant_dashboard():
    claims = Claim.query.filter_by(claimant_id=current_user.id).order_by(Claim.claimed_at.desc()).all()
    impact = db.session.query(
        func.sum(ImpactLog.kg_rescued).label('kg_rescued'),
        func.sum(ImpactLog.meals_enabled).label('meals_enabled'),
        func.sum(ImpactLog.co2_saved_kg).label('co2_saved')
    ).filter(ImpactLog.claimant_id == current_user.id).first()
    return render_template('dashboard/claimant.html', claims=claims, impact=impact)

@app.route('/impact')
def impact():
    stats = get_impact_stats()
    
    # Top Donors
    top_donors = db.session.query(
        User.name, User.organization, func.sum(ImpactLog.kg_rescued).label('total_kg')
    ).join(ImpactLog, User.id == ImpactLog.donor_id).group_by(User.id).order_by(func.sum(ImpactLog.kg_rescued).desc()).limit(5).all()
    
    # Top Claimants
    top_claimants = db.session.query(
        User.name, User.organization, func.sum(ImpactLog.kg_rescued).label('total_kg')
    ).join(ImpactLog, User.id == ImpactLog.claimant_id).group_by(User.id).order_by(func.sum(ImpactLog.kg_rescued).desc()).limit(5).all()
    
    return render_template('impact.html', stats=stats, top_donors=top_donors, top_claimants=top_claimants)

@app.route('/admin')
@login_required
@admin_required
def admin():
    users = User.query.order_by(User.created_at.desc()).all()
    user_count = len(users)
    listing_count = Listing.query.count()
    claim_count = Claim.query.count()
    return render_template('admin.html', users=users, user_count=user_count, listing_count=listing_count, claim_count=claim_count)

# ------------------------------------------------------------------------------
# ERROR HANDLERS
# ------------------------------------------------------------------------------

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
