from main import ChoreSubmission, Transaction, ChoreType, app

def test_index_redirect(client, auth):
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.location

def test_login_logout(client, auth, init_database):
    # Test login
    response = auth.login('parent', 'password')
    assert response.status_code == 200
    assert b'Parent Dashboard' in response.data
    
    # Test logout
    response = auth.logout()
    assert response.status_code == 200
    assert b'Login' in response.data

def test_child_dashboard_access(client, auth, init_database):
    # Parent should not access child dashboard
    auth.login('parent', 'password')
    response = client.get('/child/dashboard', follow_redirects=True)
    assert b'Access denied. Child account required.' in response.data
    auth.logout()

    # Child should access child dashboard
    auth.login('child', 'password')
    response = client.get('/child/dashboard')
    assert response.status_code == 200
    # The title in the template is "My Chores", not "Child Dashboard"
    assert b'My Chores' in response.data

def test_submit_chore(client, auth, init_database):
    auth.login('child', 'password')
    
    # Get the chore type ID dynamically
    with app.app_context():
        chore = ChoreType.query.filter_by(name='Clean Room').first()
        chore_id = chore.id
    
    response = client.post('/child/submit_chore', data={
        f'chore_{chore_id}_count': '1',
        f'chore_{chore_id}_notes': 'Done!'
    }, follow_redirects=True)
    
    # Check for success message (HTML escaped quotes)
    assert b'Chore &#34;Clean Room&#34; submitted!' in response.data
    
    # Verify submission in DB
    with app.app_context():
        submission = ChoreSubmission.query.first()
        assert submission is not None
        assert submission.status == 'pending'
        assert submission.notes == 'Done!'

def test_parent_approve_chore(client, auth, init_database):
    # First, submit a chore as child
    auth.login('child', 'password')
    
    with app.app_context():
        chore = ChoreType.query.filter_by(name='Clean Room').first()
        chore_id = chore.id

    client.post('/child/submit_chore', data={f'chore_{chore_id}_count': '1'}, follow_redirects=True)
    auth.logout()
    
    # Login as parent
    auth.login('parent', 'password')
    
    # Get submission ID
    with app.app_context():
        submission = ChoreSubmission.query.first()
        submission_id = submission.id
        
    # Approve it
    response = client.post(f'/parent/approve_submission/{submission_id}', follow_redirects=True)
    assert b'Chore approved!' in response.data
    
    # Verify transaction and status
    with app.app_context():
        submission = ChoreSubmission.query.get(submission_id)
        assert submission.status == 'approved'
        
        transaction = Transaction.query.filter_by(type='chore').first()
        assert transaction is not None
        assert transaction.amount == 5.0  # Value of Clean Room

def test_add_fine(client, auth, init_database):
    auth.login('parent', 'password')
    
    response = client.post('/parent/add_fine', data={
        'description': 'Bad behavior',
        'amount': '2.00'
    }, follow_redirects=True)
    
    assert b'Fine added successfully!' in response.data
    
    with app.app_context():
        fine = Transaction.query.filter_by(type='fine').first()
        assert fine is not None
        assert fine.amount == 2.0
        assert fine.description == 'Bad behavior'

def test_add_payment(client, auth, init_database):
    auth.login('parent', 'password')
    
    response = client.post('/parent/add_payment', data={
        'amount': '10.00'
    }, follow_redirects=True)
    
    assert b'Payment recorded!' in response.data
    
    with app.app_context():
        payment = Transaction.query.filter_by(type='payment').first()
        assert payment is not None
        assert payment.amount == 10.0
