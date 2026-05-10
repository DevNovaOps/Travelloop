# Travelloop ✈️

Travelloop is an innovative, AI-powered travel planning and management platform designed to simplify how users organize, budget, and experience their trips.

## Features ✨

*   **AI-Powered Trip Planning**: Get intelligent, dynamic trip suggestions and personalized itineraries powered by the Groq API (llama-3.1-8b-instant).
*   **Comprehensive Dashboard**: A sleek, modern dashboard to view upcoming trips, recent activities, and essential metrics.
*   **Invoice & Expense Management**: Easily manage travel expenses and keep track of your budget with our integrated billing features.
*   **Secure Payments**: Seamlessly process payments with integrations for both Stripe and Razorpay.
*   **Community & Notes**: Share experiences and keep personal travel notes organized.
*   **Responsive UI**: A premium, dynamic frontend design featuring modern aesthetics, smooth gradients, and glassmorphism elements.

## Tech Stack 🛠️

*   **Backend**: Python, Django
*   **Database**: MySQL
*   **Frontend**: HTML5, Vanilla CSS, JavaScript
*   **AI Integration**: Groq API
*   **Payments**: Stripe, Razorpay

## Setup & Installation 🚀

### Prerequisites
* Python 3.11+
* MySQL Server
* Git

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/DevNovaOps/Travelloop.git
    cd Travelloop
    ```

2.  **Set up a virtual environment:**
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    *   Windows: `.\venv\Scripts\activate`
    *   macOS/Linux: `source venv/bin/activate`

3.  **Install dependencies:**
    *(If a `requirements.txt` file exists)*
    ```bash
    pip install -r requirements.txt
    ```

4.  **Database Configuration:**
    Ensure MySQL is running. Create a database named `travelloop`. By default, the app expects:
    *   **User:** `root`
    *   **Password:** `dev@2006`
    *   **Port:** `3306`

5.  **Environment Variables:**
    To use external services, you'll need to set the following environment variables (or add them using a tool like `python-dotenv`):
    ```env
    EMAIL_HOST_USER=your_email@gmail.com
    EMAIL_HOST_PASSWORD=your_app_password

    GROQ_API_KEY=your_groq_api_key

    RAZORPAY_KEY_ID=your_razorpay_key_id
    RAZORPAY_KEY_SECRET=your_razorpay_key_secret

    STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
    STRIPE_SECRET_KEY=your_stripe_secret_key
    ```

6.  **Run Migrations:**
    ```bash
    cd travelloop
    python manage.py migrate
    ```

7.  **Run the Server:**
    ```bash
    python manage.py runserver
    ```
    The application will be accessible at `http://127.0.0.0:8000`.

## Project Structure 📁
*   `travelloop/core/` - Main application logic, models, and views.
*   `travelloop/templates/` - HTML templates for the frontend views.
*   `travelloop/static/` - Static assets (CSS, JS, Images).
*   `travelloop/media/` - User-uploaded files.

## License 📄
This project is proprietary. All rights reserved.
