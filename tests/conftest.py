import pytest
from main import app, db, User, ChoreType

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test_secret_key'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

@pytest.fixture
def auth(client):
    return AuthActions(client)

class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, username='parent', password='password'):
        return self._client.post(
            '/login',
            data={'username': username, 'password': password},
            follow_redirects=True
        )

    def logout(self):
        return self._client.get('/logout', follow_redirects=True)

@pytest.fixture
def init_database(client):
    # Create a parent user
    parent = User(username='parent', role='parent')
    parent.set_password('password')
    
    # Create a child user
    child = User(username='child', role='child')
    child.set_password('password')
    
    # Create a chore type
    chore = ChoreType(
        name='Clean Room',
        description='Clean your room',
        value=5.0,
        sunday_limit=1, monday_limit=1, tuesday_limit=1,
        wednesday_limit=1, thursday_limit=1, friday_limit=1, saturday_limit=1
    )
    
    db.session.add(parent)
    db.session.add(child)
    db.session.add(chore)
    db.session.commit()
    
    yield db
