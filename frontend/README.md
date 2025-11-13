# RecipeHub Frontend

Static HTML/CSS/JavaScript frontend for the RecipeHub recipe aggregation application.

## Files

### HTML Pages
- `login.html` - Login and sign up page
- `index.html` - Main recipe discovery page with search and filters
- `recipe-detail.html` - Individual recipe detail page

### Stylesheets
- `css/styles.css` - All styles for the application

### JavaScript
- `js/login.js` - Tab switching and form handling for login page
- `js/recipes.js` - Recipe data, rendering, filtering, and search functionality

### Assets
- `assets/` - Folder for images, icons, and other static assets
- `design-screenshots/` - Original Figma design screenshots

## How to Use

### View Locally

Simply open any HTML file in a web browser:

```bash
# Open login page
open login.html

# Open main recipes page
open index.html

# Open recipe detail page
open recipe-detail.html
```

Or use a local web server:

```bash
# Using Python 3
python3 -m http.server 8080

# Then visit http://localhost:8080
```

### Features

**Login Page**
- Tab switching between Login and Sign Up
- Form validation
- Demo mode (any credentials work)

**Recipes Page**
- Display recipe cards in a grid
- Search by recipe name, cuisine, or source
- Filter by cuisine, category, time, and author
- Click cards to view recipe details

**Recipe Detail Page**
- Large hero image
- Recipe metadata (time, servings, source)
- Ingredients list
- Step-by-step instructions

## Design

Based on Figma design with:
- Orange primary color (#FF6B35)
- Beige/cream background (#F5F1E8)
- Clean, modern card-based layout
- Responsive design for mobile and desktop

## Notes

- This is a static frontend prototype
- Recipe data is hardcoded in `js/recipes.js`
- Not yet connected to Django backend
- Images use placeholder.com for demonstration
