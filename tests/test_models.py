from main import User, ChoreType

def test_password_hashing():
    u = User(username='test', role='parent')
    u.set_password('cat')
    assert u.check_password('cat')
    assert not u.check_password('dog')

def test_chore_type_limits():
    # Create a chore with specific limits
    # Sunday=0, Monday=1, ... Saturday=6
    chore = ChoreType(
        name='Test Chore',
        description='Test',
        value=1.0,
        sunday_limit=0,   # Unlimited
        monday_limit=1,
        tuesday_limit=2,
        wednesday_limit=0,
        thursday_limit=0,
        friday_limit=0,
        saturday_limit=0
    )
    
    assert chore.get_limit_for_day(0) == 0  # Sunday
    assert chore.get_limit_for_day(1) == 1  # Monday
    assert chore.get_limit_for_day(2) == 2  # Tuesday

def test_chore_type_abbreviations():
    chore = ChoreType(
        name='Test Chore',
        description='Test',
        value=1.0,
        sunday_limit=1,
        monday_limit=0,
        tuesday_limit=1,
        wednesday_limit=0,
        thursday_limit=1,
        friday_limit=0,
        saturday_limit=1
    )
    # S (Sun), T (Tue), Th (Thu), S (Sat)
    # Days: S, M, T, W, Th, F, S
    # Limits: 1, 0, 1, 0, 1, 0, 1
    # Expected: S T Th S (without spaces) -> "STThS"
    
    assert chore.get_day_abbreviations() == "STThS"
