# iPhone Store - Django E-commerce Application

A comprehensive online store for selling iPhones of all types from iPhone 6 to iPhone 17, featuring all available colors, storage options, and conditions.

## Features

### 🛍️ Shopping Experience
- **Complete iPhone Catalog**: All models from iPhone 6 to iPhone 17
- **Extensive Product Variations**: Multiple colors, storage options, and conditions (New/Refurbished/Used)
- **Advanced Search & Filtering**: Search by model, color, storage, condition, and price range
- **Shopping Cart**: Session-based cart with add/remove/update functionality
- **Product Details**: Detailed product pages with specifications and related products

### 👥 User Authentication
- **Customer Registration**: Easy account creation with email verification
- **Secure Login**: Username/password authentication with session management
- **User Profiles**: Personal profile management with order history
- **Role-Based Access**: Different permissions for customers and admin users

### 🔐 Admin Security
- **Admin-Only Uploads**: Only administrators can upload product images
- **Restricted Product Management**: Only superusers can add/modify/delete products
- **Staff Permissions**: Staff users can view admin panel but limited modifications
- **User Management**: Admin can manage user accounts and permissions

### 🎨 Modern UI/UX
- **Responsive Design**: Mobile-first Bootstrap 5 design
- **Beautiful Interface**: Modern gradients, animations, and hover effects
- **User-Friendly Navigation**: Intuitive browsing and filtering with authentication tabs
- **Real-time Cart Updates**: Dynamic cart count updates

### ⚙️ Technical Features
- **Django Framework**: Built with Django 4.2.7
- **Database**: SQLite with comprehensive models
- **Admin Interface**: Full admin panel for product management
- **Session Management**: Secure session-based shopping cart
- **Image Upload**: Product image support with media handling

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Quick Start

1. **Clone/Download the project** to your local directory

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run database migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Populate sample data**:
   ```bash
   python manage.py populate_iphones
   ```
   This will create:
   - 42 iPhone models (iPhone 6 to iPhone 17)
   - 28 color options
   - 2,121+ product variations

5. **Create admin user**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

7. **Access the application**:
   - **Store Frontend**: http://127.0.0.1:8000/
   - **Admin Panel**: http://127.0.0.1:8000/admin/

### Production media uploads (HCode)

Uploaded product images are stored on disk, not in the database. `MEDIA_URL` remains `/media/`; `MEDIA_ROOT` defaults to the project `media` directory and can be set to an absolute path on a persistent HCode volume. The app expects the storage to retain the existing relative paths such as `iphone_images/` and `iphone_covers/`.

In production, configure HCode's web server to map `/media/` to `MEDIA_ROOT`, and ensure the web server can read the files and the Django process can write uploads. The storage must persist across releases, restarts, and instance replacement. Preserve and transfer existing media files with their directory structure before changing storage; database file names are relative to `MEDIA_ROOT`.

If HCode cannot map media URLs directly, set `SERVE_MEDIA_FILES=true` to enable Django's low-traffic fallback for `/media/`. This fallback is disabled by default; direct web-server or persistent object-storage serving is preferred for production.

### Test Users
The following test accounts have been created for demonstration:

**Customer Account:**
- Username: `testuser`
- Password: `testpass123`
- Can: Register, login, view products, use cart, manage profile

**Staff Account:**
- Username: `staffuser` 
- Password: `staffpass123`
- Can: Access admin panel, view products, limited modifications

**Superuser Account:**
- Username: `admin`
- Password: [set during setup]
- Can: Full admin access, upload images, manage all products and users

## Project Structure

```
iphonestore/
├── iphonestore/          # Main Django project settings
│   ├── settings.py       # Project configuration
│   ├── urls.py          # Main URL routing
│   └── wsgi.py         # WSGI configuration
├── store/               # Main application
│   ├── models.py        # Database models (iPhone, Product, Cart)
│   ├── views.py         # View logic and controllers
│   ├── urls.py          # App URL routing
│   ├── admin.py         # Admin interface configuration
│   ├── templates/       # HTML templates
│   ├── static/          # CSS, JavaScript, images
│   └── management/      # Django management commands
│       └── commands/
│           └── populate_iphones.py
├── media/               # User uploaded images
├── staticfiles/         # Collected static files
├── db.sqlite3          # SQLite database
└── manage.py           # Django management script
```

## Database Models

### iPhoneModel
- iPhone model information (iPhone 6 to iPhone 17)
- Release year, display size, storage options
- Model descriptions

### Color
- Available colors for iPhones
- Hex codes for UI display
- 28 color options including special editions

### iPhoneProduct
- Individual product variations
- Links model, color, storage, and condition
- Pricing, stock quantity, images
- Active/inactive status

### Cart & CartItem
- Session-based shopping cart
- Quantity management
- Price calculations

## Features in Detail

### Product Catalog
- **42 iPhone Models**: From iPhone 6 (2014) to iPhone 17 (2025)
- **28 Colors**: Including Space Gray, Gold, Rose Gold, Titanium variants
- **7 Storage Options**: 32GB to 2TB
- **3 Conditions**: New, Refurbished, Used
- **Smart Pricing**: Dynamic pricing based on model year, storage, and condition

### Search & Filtering
- **Text Search**: Search by model name, color, or storage
- **Model Filter**: Filter by specific iPhone model
- **Color Filter**: Filter by available colors
- **Storage Filter**: Filter by storage capacity
- **Condition Filter**: Filter by product condition
- **Sort Options**: Newest, Price (Low to High), Price (High to Low), Name

### Shopping Cart
- **Session-Based**: Cart persists across browser sessions
- **Real-time Updates**: Cart count updates automatically
- **Quantity Management**: Add, update, or remove items
- **Stock Validation**: Prevents adding out-of-stock items
- **Price Calculation**: Automatic total calculation

### Admin Interface
- **Product Management**: Add/edit products with images
- **Stock Management**: Update quantities and availability
- **Order Management**: View cart contents and user sessions
- **Bulk Operations**: Efficient management of large catalogs

## Customization

### Adding New Products
1. Access admin panel at `/admin/`
2. Navigate to "iPhone products"
3. Add new products with model, color, storage, and condition
4. Set pricing and stock quantities
5. Upload product images

### Customizing Colors
1. Edit `store/models.py` Color model choices
2. Run migrations: `python manage.py makemigrations` and `python manage.py migrate`
3. Re-run populate command: `python manage.py populate_iphones`

### Modifying Pricing Logic
Edit the `calculate_price` method in `store/management/commands/populate_iphones.py`

## Development Commands

```bash
# Start development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Populate sample data
python manage.py populate_iphones

# Collect static files (for production)
python manage.py collectstatic
```

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Security Features

- CSRF Protection
- Session Security
- SQL Injection Protection
- XSS Protection
- Image Upload Validation

## Performance Features

- Database Indexing
- Efficient Querying
- Image Optimization
- Static File Caching
- Session Management

## Future Enhancements

- User Authentication
- Order Processing
- Payment Integration
- Product Reviews
- Wishlist Feature
- Email Notifications
- Analytics Integration
- Multi-language Support

## Support

For issues or questions:
1. Check the Django documentation
2. Review the admin panel for data management
3. Verify static files are properly collected
4. Check browser console for JavaScript errors

## License

This project is for educational and demonstration purposes.

---

**Admin Credentials** (if not changed):
- Username: admin
- Password: [set during setup]

**Server URL**: http://127.0.0.1:8000/
**Admin URL**: http://127.0.0.1:8000/admin/
#   F i p h o n e s t o r e  
 