# Reemio Recommendation Frontend

A beautiful, modern frontend for showcasing the Reemio recommendation system.

## Features

- **Personalized Homepage**: AI-powered product recommendations for each user
- **Similar Products**: View products similar to any item you're interested in
- **Cart Recommendations**: Get suggestions for items that complement your cart
- **Frequently Bought Together**: See what other customers purchase together
- **Smooth Animations**: Polished UI with delightful interactions
- **Responsive Design**: Works beautifully on desktop and mobile

## Quick Start

1. Make sure your FastAPI backend is running on `http://localhost:8000`

2. Open `index.html` in your browser:
   ```bash
   open index.html
   ```

   Or use a simple HTTP server:
   ```bash
   python -m http.server 8080
   ```
   Then visit `http://localhost:8080`

## Features Showcase

### User Switching
Switch between different users (Alice, Bob, Charlie) to see personalized recommendations for each user profile.

### Product Interactions
- Click on any product to view similar items
- Add items to cart with one click
- View cart recommendations based on your selections
- See frequently bought together suggestions

### Shopping Cart
- Slide-out cart sidebar
- Add/remove items easily
- See total price update in real-time
- Get recommendations based on cart contents
- Complete checkout with interaction tracking

## API Integration

The frontend connects to these API endpoints:

- `GET /api/v1/recommendations/homepage` - Homepage recommendations
- `GET /api/v1/recommendations/product/{id}` - Similar products
- `GET /api/v1/recommendations/cart` - Cart-based recommendations
- `GET /api/v1/recommendations/frequently-bought-together/{id}` - Co-purchase suggestions
- `POST /api/v1/interactions` - Track user interactions

## Customization

### API URL
Change the API base URL in `app.js`:
```javascript
const API_BASE_URL = 'http://localhost:8000/api/v1';
```

### Styling
Modify CSS variables in `styles.css` to customize colors, spacing, and more:
```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    ...
}
```

## Tech Stack

- Vanilla JavaScript (no frameworks needed)
- Modern CSS with CSS Grid and Flexbox
- SVG icons
- Fetch API for backend communication

## Browser Support

Works on all modern browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
