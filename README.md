![author](https://github.com/user-attachments/assets/c817770e-d071-480b-9f40-48bc65a8e98a)
![home](https://github.com/user-attachments/assets/23959be4-5f66-4e48-ae8d-72c0cb4e2599)
![member](https://github.com/user-attachments/assets/e413e9d9-6f51-41b4-8378-ddd83e80fe1f)
![email](https://github.com/user-attachments/assets/818fd2d1-5249-408f-b7ee-4a44718cf3df)
![story](https://github.com/user-attachments/assets/4e893e82-bfd0-432f-90a9-66a57814d6a6)
![noti](https://github.com/user-attachments/assets/0838263f-0c67-4434-ba93-6dd6f7244e6d)
![message](https://github.com/user-attachments/assets/1de3d4ff-5a1f-46a0-8abf-532476db62c3)
![d-17](https://github.com/user-attachments/assets/e2b5d850-a808-42cd-8dc2-447d7a0a1e9e)
🐍 dj_SocialaMedia

A Django backend for a social media application — RESTful API with user authentication, posts, story features, and notifications.

📌 Backend only — designed as API for mobile/web clients

🚀 Features

✔ User Authentication (Signup / Login / Logout)
✔ Profiles & Custom User Fields
✔ CRUD Posts & Stories
✔ Likes / Follows / Comments Endpoints
✔ Notifications & Real‑Time Updates (if implemented)
✔ Token‑based Auth (JWT / DRF Simple JWT)
✔ Docker‑ready development environment

(Adjust features to match what your repo actually implements)

📋 Table of Contents

👉 Demo

🛠️ Setup & Installation

🧠 Usage

📦 API Endpoints

🧪 Testing

🤝 Contributing

📝 License

📫 Contact

🎥 Demo

(If you have a demo or API docs link, insert here)

🛠️ Setup & Installation
⚡ Requirements

Python 3.10+

Django 4.x

Django REST Framework

Docker & Docker‑Compose (optional)

Install dependencies:

git clone https://github.com/abdelrahman-abobakr164/dj_SocialaMedia.git
cd dj_SocialaMedia
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
pip install -r requirements.txt

Create .env (environment file):

SECRET_KEY=your_secret_key
DEBUG=True
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASS=your_db_password

Run migrations:

python manage.py migrate
python manage.py createsuperuser

Start server:

python manage.py runserver
🧠 Usage

Access API at:

http://127.0.0.1:8000/api/

Auth endpoints (JWT):

POST /api/auth/login/
POST /api/auth/register/
POST /api/auth/logout/

Resource endpoints (example routes — update to match your routes):

GET    /api/posts/
POST   /api/posts/
GET    /api/profiles/{id}/
📦 API Endpoints
Endpoint	Method	Description
/api/auth/register/	POST	Register new user
/api/auth/login/	POST	Login user
/api/posts/	GET	List all posts
/api/posts/	POST	Create new post
/api/profiles/<id>/	GET	Get user profile
/api/stories/	GET	List stories

(Add or remove as necessary to reflect your actual API)

🧪 Testing

You can run tests locally:

python manage.py test
🤝 Contributing

Contributions are welcome!

Fork repo

Create a feature branch

Commit your changes

Open a Pull Request
