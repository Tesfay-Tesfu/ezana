import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import stripe
from config import Config
from models import db, Service, Booking, Review, FAQ, Policy, UsefulLink, Subscriber, Admin, Setting, BlockedDate, HeroSlide
from forms import (BookingForm, ReviewForm, SubscribeForm, ServiceForm, FAQForm,
                   UsefulLinkForm, AdminLoginForm, HeroSlideForm, SocialMediaForm)
from flask_mail import Mail, Message

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
app.config.from_object(Config)

# Handle PostgreSQL URL conversion
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

# Initialize extensions
db.init_app(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

stripe.api_key = app.config['STRIPE_SECRET_KEY']

# Ensure upload folder exists
UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------- Helper Functions ----------
def send_booking_notification(booking):
    try:
        msg = Message(
            subject=f"New Booking from {booking.full_name}",
            recipients=[app.config['ADMIN_EMAIL']]
        )
        msg.body = f"""
        New booking received:
        Name: {booking.full_name}
        Email: {booking.email}
        Phone: {booking.phone}
        Services: {', '.join(booking.services) if booking.services else 'N/A'}
        Event Date: {booking.event_date}
        Guests: {booking.guest_count}
        Message: {booking.message}
        """
        mail.send(msg)
    except Exception as e:
        print(f"Admin email failed: {e}")

def send_customer_confirmation(booking):
    try:
        msg = Message(
            subject="Booking Confirmation - Ezana Services",
            recipients=[booking.email]
        )
        msg.body = f"""
Dear {booking.full_name},

Thank you for booking with Ezana Services. We have received your booking request and will contact you shortly.

Booking details:
- Services: {', '.join(booking.services)}
- Event Date: {booking.event_date}
- Number of Guests: {booking.guest_count}
- Your message: {booking.message}

If you have any questions, please contact us at {app.config['ADMIN_EMAIL']}.

Best regards,
Ezana Services Team
"""
        mail.send(msg)
    except Exception as e:
        print(f"Customer email failed: {e}")

def get_settings():
    settings = {}
    for s in Setting.query.all():
        settings[s.key] = s.value
    return settings

def get_blocked_dates():
    blocked = BlockedDate.query.all()
    return [b.date.strftime('%Y-%m-%d') for b in blocked]

# ---------- User Loader ----------
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# ---------- Context Processors ----------
@app.context_processor
def inject_settings():
    return dict(settings=get_settings())

@app.context_processor
def inject_now():
    return {'now': datetime.now}

# ---------- Initialize Database ----------
with app.app_context():
    db.create_all()
    
    # Default settings with contact info
    default_settings = {
        'company_name': 'Ezana Services',
        'address': '7513 Maple Avenue, Silver Spring, MD 20912',
        'phone': '+1 (571) 842-2447',
        'email': 'ezana@info.com',
        'business_hours': 'Monday - Sunday: 8:00 AM - 10:00 PM',
        'map_embed_url': 'https://www.google.com/maps/embed/v1/place?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&q=7513+Maple+Avenue,Silver+Spring,MD+20912',
        'facebook_url': 'https://www.facebook.com/tesfayphysics',
        'youtube_url': 'https://www.youtube.com/watch?v=Wa-uqVEd41Q',
        'social_facebook': 'https://www.facebook.com/share/1K48egkVLT/',
        'social_instagram': 'https://www.instagram.com/p/CxRJI8MI5kL/?img_index=1&igsh=MTJyeDN3dWUyemV0Zw==',
        'social_tiktok': 'https://www.tiktok.com/@evayordi1?_r=1&_t=ZG-93aiKt1AGGX',
        'social_youtube': 'https://youtube.com/@yordibeauty-w3k?si=gnVylZO_gh-B_cNQ',
        'social_linkedin': '',
        'social_twitter': ''
    }
    for key, value in default_settings.items():
        if not db.session.get(Setting, key):
            db.session.add(Setting(key=key, value=value))

    # Default policies
    policy_types = ['privacy', 'terms', 'cancellation', 'cookie']
    policy_titles = {
        'privacy': 'Privacy Policy',
        'terms': 'Terms and Conditions',
        'cancellation': 'Cancellation Policy',
        'cookie': 'Cookie Policy'
    }
    for ptype in policy_types:
        if not Policy.query.filter_by(type=ptype).first():
            db.session.add(Policy(
                title=policy_titles[ptype],
                content=f"<h2>{policy_titles[ptype]}</h2><p>Default content for {ptype}. Please update in admin.</p>",
                type=ptype
            ))

    # Sample FAQs
    sample_faqs = [
        {"question": "How do I book a service?", "answer": "You can book a service by visiting our Booking page and filling out the form. We'll get back to you within 24 hours.", "order": 1},
        {"question": "What payment methods do you accept?", "answer": "We accept all major credit cards, PayPal, and bank transfers.", "order": 2},
        {"question": "Can I cancel my booking?", "answer": "Yes, cancellations are allowed up to 48 hours before the event. Please see our Cancellation Policy for details.", "order": 3},
        {"question": "Do you offer discounts for multiple services?", "answer": "Yes, we offer package deals. Contact us for a custom quote.", "order": 4}
    ]
    for faq in sample_faqs:
        if not FAQ.query.filter_by(question=faq["question"]).first():
            db.session.add(FAQ(
                question=faq["question"],
                answer=faq["answer"],
                display_order=faq["order"]
            ))

    # Sample services
    sample_services = [
        {
            "title": "Event Planning",
            "subtitle": "Full-service event coordination",
            "description": "From intimate gatherings to large celebrations, we handle every detail.",
            "features": ["Venue selection", "Vendor management", "Timeline coordination", "On-site supervision"],
            "box_color": "#2E8B57"
        },
        {
            "title": "Cultural Consulting",
            "subtitle": "Authentic cultural experiences",
            "description": "Learn about Ethiopian traditions, customs, and ceremonies.",
            "features": ["Custom workshops", "Cultural presentations", "Traditional etiquette training"],
            "box_color": "#228B22"
        },
        {
            "title": "Language Services",
            "subtitle": "Translation & interpretation",
            "description": "Professional language support for any occasion.",
            "features": ["Document translation", "Live interpretation", "Language classes"],
            "box_color": "#32CD32"
        }
    ]
    if Service.query.count() == 0:
        for s in sample_services:
            service = Service(
                title=s["title"],
                subtitle=s["subtitle"],
                description=s["description"],
                features=s["features"],
                box_color=s["box_color"]
            )
            db.session.add(service)

    # Sample hero slides - 5 beautiful Unsplash images
    sample_slides = [
        {
            "title": "Experience Authentic Cultural Events",
            "subtitle": "Ezana Service brings you the finest diversified services",
            "image_url": "https://images.unsplash.com/photo-1465495976277-4387d4b0b4c6?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80",
            "button_text": "Book Now",
            "button_link": "/booking",
            "display_order": 1
        },
        {
            "title": "Professional Event Planning",
            "subtitle": "From intimate gatherings to large celebrations",
            "image_url": "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80",
            "button_text": "Learn More",
            "button_link": "/services",
            "display_order": 2
        },
        {
            "title": "Cultural Workshops & Training",
            "subtitle": "Learn about Ethiopian traditions and customs",
            "image_url": "https://images.unsplash.com/photo-1527529482837-4698179dc6ce?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80",
            "button_text": "Explore",
            "button_link": "/services",
            "display_order": 3
        },
        {
            "title": "Language Translation Services",
            "subtitle": "Professional translation and interpretation",
            "image_url": "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80",
            "button_text": "Get Started",
            "button_link": "/booking",
            "display_order": 4
        },
        {
            "title": "Traditional Ceremonies",
            "subtitle": "Experience authentic Ethiopian celebrations",
            "image_url": "https://images.unsplash.com/photo-1530103043960-7215ed5c69c7?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80",
            "button_text": "Discover",
            "button_link": "/booking",
            "display_order": 5
        }
    ]
    if HeroSlide.query.count() == 0:
        for slide in sample_slides:
            hero_slide = HeroSlide(**slide)
            db.session.add(hero_slide)

    db.session.commit()

# ---------- Public Routes ----------
@app.route('/')
def index():
    services = Service.query.order_by(Service.id).all()
    reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).limit(6).all()
    hero_slides = HeroSlide.query.filter_by(is_active=True).order_by(HeroSlide.display_order).all()
    return render_template('index.html', services=services, reviews=reviews, hero_slides=hero_slides)

@app.route('/services')
def services():
    services = Service.query.order_by(Service.id).all()
    return render_template('services.html', services=services)

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    form = BookingForm()
    services = Service.query.all()
    form.services.choices = [(s.title, s.title) for s in services]
    
    blocked_dates = get_blocked_dates()

    if form.validate_on_submit():
        if form.event_date.data:
            date_str = form.event_date.data.strftime('%Y-%m-%d')
            if date_str in blocked_dates:
                flash(f'Sorry, {date_str} is not available. Please choose another date.', 'danger')
                return render_template('booking.html', form=form, blocked_dates=blocked_dates)

        booking = Booking(
            full_name=form.full_name.data,
            email=form.email.data,
            phone=form.phone.data,
            services=form.services.data,
            event_date=form.event_date.data,
            guest_count=form.guest_count.data,
            message=form.message.data
        )
        db.session.add(booking)
        db.session.commit()
        send_booking_notification(booking)
        send_customer_confirmation(booking)
        flash('Your booking request has been sent!', 'success')
        return redirect(url_for('booking'))
    
    return render_template('booking.html', form=form, blocked_dates=blocked_dates)

@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    form = ReviewForm()
    if form.validate_on_submit():
        review = Review(
            client_name=form.client_name.data,
            rating=form.rating.data,
            comment=form.comment.data
        )
        db.session.add(review)
        db.session.commit()
        flash('Thank you for your review! It will appear after approval.', 'success')
        return redirect(url_for('reviews'))
    reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).all()
    return render_template('reviews.html', form=form, reviews=reviews)

@app.route('/faq')
def faq():
    faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.display_order).all()
    return render_template('faq.html', faqs=faqs)

@app.route('/policies/<type>')
def policies(type):
    policy = Policy.query.filter_by(type=type).first()
    return render_template('policies.html', policy=policy, type=type)

@app.route('/links')
def links():
    links = UsefulLink.query.filter_by(is_active=True).order_by(UsefulLink.display_order).all()
    return render_template('links.html', links=links)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    form = SubscribeForm()
    if form.validate_on_submit():
        email = form.email.data
        if not Subscriber.query.filter_by(email=email).first():
            sub = Subscriber(email=email)
            db.session.add(sub)
            db.session.commit()
            flash('Thank you for subscribing!', 'success')
        else:
            flash('Email already subscribed.', 'info')
    return redirect(request.referrer or url_for('index'))

# ---------- Admin Routes ----------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.check_password(form.password.data):
            login_user(admin, remember=form.remember.data)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('admin/login.html', form=form)

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    service_count = Service.query.count()
    booking_count = Booking.query.count()
    review_count = Review.query.filter_by(is_approved=False).count()
    return render_template('admin/dashboard.html',
                           recent_bookings=recent_bookings,
                           service_count=service_count,
                           booking_count=booking_count,
                           pending_reviews=review_count)

# ---- Contact Settings ----
@app.route('/admin/contact-settings', methods=['GET', 'POST'])
@login_required
def admin_contact_settings():
    if request.method == 'POST':
        # Update contact settings
        contact_fields = ['company_name', 'address', 'phone', 'email', 'business_hours', 'map_embed_url']
        
        for field in contact_fields:
            value = request.form.get(field, '')
            setting = Setting.query.get(field)
            if setting:
                setting.value = value
            else:
                setting = Setting(key=field, value=value)
                db.session.add(setting)
        
        db.session.commit()
        flash('Contact information updated successfully!', 'success')
        return redirect(url_for('admin_contact_settings'))
    
    # Load current settings
    settings = get_settings()
    return render_template('admin/contact_settings.html', settings=settings)

# ---- Services Management ----
@app.route('/admin/services')
@login_required
def admin_services():
    services = Service.query.order_by(Service.id).all()
    return render_template('admin/services.html', services=services)

@app.route('/admin/services/new', methods=['GET', 'POST'])
@login_required
def admin_service_new():
    form = ServiceForm()
    if form.validate_on_submit():
        image_url = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{datetime.utcnow().timestamp()}{ext}"
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('static', filename=f'uploads/{filename}')
        elif form.image_url.data:
            image_url = form.image_url.data
        
        features = [f.strip() for f in form.features.data.split(',') if f.strip()]
        service = Service(
            title=form.title.data,
            subtitle=form.subtitle.data,
            description=form.description.data,
            image_url=image_url,
            features=features,
            box_color=form.box_color.data
        )
        db.session.add(service)
        db.session.commit()
        flash('Service added successfully', 'success')
        return redirect(url_for('admin_services'))
    return render_template('admin/service_form.html', form=form, service=None)

@app.route('/admin/services/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def admin_service_edit(id):
    service = Service.query.get_or_404(id)
    form = ServiceForm(obj=service)
    
    if form.validate_on_submit():
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{datetime.utcnow().timestamp()}{ext}"
            form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            service.image_url = url_for('static', filename=f'uploads/{filename}')
        elif form.image_url.data:
            service.image_url = form.image_url.data
        
        service.title = form.title.data
        service.subtitle = form.subtitle.data
        service.description = form.description.data
        service.features = [f.strip() for f in form.features.data.split(',') if f.strip()]
        service.box_color = form.box_color.data
        db.session.commit()
        flash('Service updated', 'success')
        return redirect(url_for('admin_services'))
    
    form.features.data = ', '.join(service.features) if service.features else ''
    return render_template('admin/service_form.html', form=form, service=service)

@app.route('/admin/services/<int:id>/delete', methods=['POST'])
@login_required
def admin_service_delete(id):
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted', 'success')
    return redirect(url_for('admin_services'))

# ---- Reviews Management ----
@app.route('/admin/reviews')
@login_required
def admin_reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=reviews)

@app.route('/admin/reviews/<int:id>/approve', methods=['POST'])
@login_required
def admin_review_approve(id):
    review = Review.query.get_or_404(id)
    review.is_approved = True
    db.session.commit()
    flash('Review approved', 'success')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/reviews/<int:id>/delete', methods=['POST'])
@login_required
def admin_review_delete(id):
    review = Review.query.get_or_404(id)
    db.session.delete(review)
    db.session.commit()
    flash('Review deleted', 'success')
    return redirect(url_for('admin_reviews'))

# ---- FAQs ----
@app.route('/admin/faqs')
@login_required
def admin_faqs():
    faqs = FAQ.query.order_by(FAQ.display_order).all()
    form = FAQForm()
    return render_template('admin/faqs.html', faqs=faqs, form=form)

@app.route('/admin/faqs/new', methods=['POST'])
@login_required
def admin_faq_new():
    form = FAQForm()
    if form.validate_on_submit():
        faq = FAQ(
            question=form.question.data,
            answer=form.answer.data,
            display_order=form.display_order.data
        )
        db.session.add(faq)
        db.session.commit()
        flash('FAQ added', 'success')
    return redirect(url_for('admin_faqs'))

@app.route('/admin/faqs/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def admin_faq_edit(id):
    faq = FAQ.query.get_or_404(id)
    form = FAQForm(obj=faq)
    if form.validate_on_submit():
        faq.question = form.question.data
        faq.answer = form.answer.data
        faq.display_order = form.display_order.data
        db.session.commit()
        flash('FAQ updated successfully', 'success')
        return redirect(url_for('admin_faqs'))
    return render_template('admin/faq_form.html', form=form, faq=faq)

@app.route('/admin/faqs/<int:id>/delete', methods=['POST'])
@login_required
def admin_faq_delete(id):
    faq = FAQ.query.get_or_404(id)
    db.session.delete(faq)
    db.session.commit()
    flash('FAQ deleted', 'success')
    return redirect(url_for('admin_faqs'))

# ---- Policies ----
@app.route('/admin/policies', methods=['GET', 'POST'])
@login_required
def admin_policies():
    privacy = Policy.query.filter_by(type='privacy').first()
    terms = Policy.query.filter_by(type='terms').first()
    cancellation = Policy.query.filter_by(type='cancellation').first()
    cookie = Policy.query.filter_by(type='cookie').first()
    if request.method == 'POST':
        privacy_content = request.form.get('privacy_content', '')
        terms_content = request.form.get('terms_content', '')
        cancellation_content = request.form.get('cancellation_content', '')
        cookie_content = request.form.get('cookie_content', '')

        if privacy:
            privacy.content = privacy_content
        else:
            privacy = Policy(title='Privacy Policy', content=privacy_content, type='privacy')
            db.session.add(privacy)

        if terms:
            terms.content = terms_content
        else:
            terms = Policy(title='Terms of Service', content=terms_content, type='terms')
            db.session.add(terms)

        if cancellation:
            cancellation.content = cancellation_content
        else:
            cancellation = Policy(title='Cancellation Policy', content=cancellation_content, type='cancellation')
            db.session.add(cancellation)

        if cookie:
            cookie.content = cookie_content
        else:
            cookie = Policy(title='Cookie Policy', content=cookie_content, type='cookie')
            db.session.add(cookie)

        db.session.commit()
        flash('Policies updated', 'success')
        return redirect(url_for('admin_policies'))
    return render_template('admin/policies.html', privacy=privacy, terms=terms, cancellation=cancellation, cookie=cookie)

# ---- Useful Links ----
@app.route('/admin/links')
@login_required
def admin_links():
    links = UsefulLink.query.order_by(UsefulLink.display_order).all()
    form = UsefulLinkForm()
    return render_template('admin/links.html', links=links, form=form)

@app.route('/admin/links/new', methods=['POST'])
@login_required
def admin_link_new():
    form = UsefulLinkForm()
    if form.validate_on_submit():
        link = UsefulLink(
            title=form.title.data,
            url=form.url.data,
            icon=form.icon.data,
            display_order=form.display_order.data
        )
        db.session.add(link)
        db.session.commit()
        flash('Link added', 'success')
    return redirect(url_for('admin_links'))

@app.route('/admin/links/<int:id>/delete', methods=['POST'])
@login_required
def admin_link_delete(id):
    link = UsefulLink.query.get_or_404(id)
    db.session.delete(link)
    db.session.commit()
    flash('Link deleted', 'success')
    return redirect(url_for('admin_links'))

# ---- Bookings ----
@app.route('/admin/bookings')
@login_required
def admin_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings)

@app.route('/admin/bookings/<int:id>/status', methods=['POST'])
@login_required
def admin_booking_status(id):
    booking = Booking.query.get_or_404(id)
    new_status = request.form.get('status')
    if new_status in ['pending', 'confirmed', 'cancelled']:
        booking.status = new_status
        db.session.commit()
        flash('Booking status updated', 'success')
    else:
        flash('Invalid status', 'danger')
    return redirect(url_for('admin_bookings'))

# ---- Blocked Dates ----
@app.route('/admin/blocked-dates')
@login_required
def admin_blocked_dates():
    blocked = BlockedDate.query.order_by(BlockedDate.date).all()
    return render_template('admin/blocked_dates.html', blocked=blocked)

@app.route('/admin/blocked-dates/add', methods=['POST'])
@login_required
def admin_blocked_date_add():
    date_str = request.form.get('date')
    reason = request.form.get('reason')
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        if BlockedDate.query.filter_by(date=date).first():
            flash('Date already blocked', 'warning')
        else:
            blocked = BlockedDate(date=date, reason=reason)
            db.session.add(blocked)
            db.session.commit()
            flash('Date blocked', 'success')
    except ValueError:
        flash('Invalid date format', 'danger')
    return redirect(url_for('admin_blocked_dates'))

@app.route('/admin/blocked-dates/<int:id>/delete', methods=['POST'])
@login_required
def admin_blocked_date_delete(id):
    blocked = BlockedDate.query.get_or_404(id)
    db.session.delete(blocked)
    db.session.commit()
    flash('Date unblocked', 'success')
    return redirect(url_for('admin_blocked_dates'))

# ---- Hero Slides Management ----
@app.route('/admin/hero-slides')
@login_required
def admin_hero_slides():
    slides = HeroSlide.query.order_by(HeroSlide.display_order).all()
    return render_template('admin/hero_slides.html', slides=slides)

@app.route('/admin/hero-slides/new', methods=['GET', 'POST'])
@login_required
def admin_hero_slide_new():
    form = HeroSlideForm()
    if form.validate_on_submit():
        image_url = None
        
        if form.image_file.data:
            filename = secure_filename(form.image_file.data.filename)
            name, ext = os.path.splitext(filename)
            filename = f"hero_{name}_{datetime.utcnow().timestamp()}{ext}"
            form.image_file.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('static', filename=f'uploads/{filename}')
        elif form.image_url.data:
            image_url = form.image_url.data
        else:
            flash('Please provide either an image file or image URL', 'danger')
            return render_template('admin/hero_slide_form.html', form=form, slide=None)
        
        slide = HeroSlide(
            title=form.title.data,
            subtitle=form.subtitle.data,
            image_url=image_url,
            button_text=form.button_text.data,
            button_link=form.button_link.data,
            display_order=form.display_order.data,
            is_active=form.is_active.data
        )
        db.session.add(slide)
        db.session.commit()
        flash('Hero slide added successfully', 'success')
        return redirect(url_for('admin_hero_slides'))
    return render_template('admin/hero_slide_form.html', form=form, slide=None)

@app.route('/admin/hero-slides/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def admin_hero_slide_edit(id):
    slide = HeroSlide.query.get_or_404(id)
    form = HeroSlideForm(obj=slide)
    
    if form.validate_on_submit():
        if form.image_file.data:
            filename = secure_filename(form.image_file.data.filename)
            name, ext = os.path.splitext(filename)
            filename = f"hero_{name}_{datetime.utcnow().timestamp()}{ext}"
            form.image_file.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            slide.image_url = url_for('static', filename=f'uploads/{filename}')
        elif form.image_url.data:
            slide.image_url = form.image_url.data
        
        slide.title = form.title.data
        slide.subtitle = form.subtitle.data
        slide.button_text = form.button_text.data
        slide.button_link = form.button_link.data
        slide.display_order = form.display_order.data
        slide.is_active = form.is_active.data
        db.session.commit()
        flash('Hero slide updated successfully', 'success')
        return redirect(url_for('admin_hero_slides'))
    
    return render_template('admin/hero_slide_form.html', form=form, slide=slide)

@app.route('/admin/hero-slides/<int:id>/delete', methods=['POST'])
@login_required
def admin_hero_slide_delete(id):
    slide = HeroSlide.query.get_or_404(id)
    db.session.delete(slide)
    db.session.commit()
    flash('Hero slide deleted', 'success')
    return redirect(url_for('admin_hero_slides'))

# ---- Social Media Settings ----
@app.route('/admin/social-media', methods=['GET', 'POST'])
@login_required
def admin_social_media():
    form = SocialMediaForm()
    
    if request.method == 'POST' and form.validate():
        social_links = {
            'facebook': form.facebook.data,
            'instagram': form.instagram.data,
            'twitter': form.twitter.data,
            'linkedin': form.linkedin.data,
            'youtube': form.youtube.data,
            'tiktok': form.tiktok.data
        }
        
        for key, value in social_links.items():
            setting = Setting.query.get(f'social_{key}')
            if setting:
                setting.value = value or ''
            else:
                setting = Setting(key=f'social_{key}', value=value or '')
                db.session.add(setting)
        
        db.session.commit()
        flash('Social media links updated', 'success')
        return redirect(url_for('admin_social_media'))
    
    # Load existing values
    form.facebook.data = Setting.query.get('social_facebook').value if Setting.query.get('social_facebook') else ''
    form.instagram.data = Setting.query.get('social_instagram').value if Setting.query.get('social_instagram') else ''
    form.twitter.data = Setting.query.get('social_twitter').value if Setting.query.get('social_twitter') else ''
    form.linkedin.data = Setting.query.get('social_linkedin').value if Setting.query.get('social_linkedin') else ''
    form.youtube.data = Setting.query.get('social_youtube').value if Setting.query.get('social_youtube') else ''
    form.tiktok.data = Setting.query.get('social_tiktok').value if Setting.query.get('social_tiktok') else ''
    
    return render_template('admin/social_media.html', form=form)

# ---- Settings ----
@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if request.method == 'POST':
        for key, value in request.form.items():
            setting = Setting.query.get(key)
            if setting:
                setting.value = value
            else:
                setting = Setting(key=key, value=value)
                db.session.add(setting)
        db.session.commit()
        flash('Settings saved', 'success')
        return redirect(url_for('admin_settings'))
    settings = get_settings()
    return render_template('admin/settings.html', settings=settings)

# ---------- Temporary Admin Setup Route (REMOVE AFTER FIRST USE) ----------
@app.route('/setup-admin', methods=['GET', 'POST'])
def setup_admin():
    if Admin.query.count() > 0:
        return "Admin already exists. Please use the login page.", 403
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            admin = Admin(username=username)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            return "Admin created successfully! You can now <a href='/admin/login'>login here</a>."
    
    return '''
    <form method="post" style="max-width: 400px; margin: 50px auto; padding: 20px; border: 1px solid #ccc; border-radius: 5px;">
        <h2>Create Admin Account</h2>
        <div style="margin-bottom: 15px;">
            <label>Username:</label>
            <input type="text" name="username" required style="width: 100%; padding: 8px;">
        </div>
        <div style="margin-bottom: 15px;">
            <label>Password:</label>
            <input type="password" name="password" required style="width: 100%; padding: 8px;">
        </div>
        <button type="submit" style="background: #2E8B57; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">Create Admin</button>
    </form>
    '''

# ---------- Create Initial Admin (Command Line) ----------
@app.cli.command("create-admin")
def create_admin():
    import getpass
    username = input("Enter admin username: ").strip()
    password = getpass.getpass("Enter admin password: ").strip()
    if not username or not password:
        print("Username and password required.")
        return
    if Admin.query.filter_by(username=username).first():
        print(f"Admin '{username}' already exists.")
        return
    admin = Admin(username=username)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f"Admin '{username}' created successfully.")

if __name__ == '__main__':
    app.run(debug=True)
