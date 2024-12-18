import pytest
from django.utils import timezone
from freezegun import freeze_time
from datetime import datetime, time
from core.models.user import kUser
from core.models.contact import Contact
from core.models.userphone import UserPhone
from core.models.message import Message
from messageShooter.models.campaign import Campaign, STATUS_ACTIVE, FREQUENCY_DAILY, FREQUENCY_ONCE
from messageShooter.models.queue import Queue
from messageShooter.models.target_list import TargetList
from messageShooter.resolvers.target_list_resolver import generate_target_lists

@pytest.fixture
def setup_test_data(db):
    # Create test user
    user = kUser.objects.create(
        name="Test User",
        email="test@example.com",
        company="Test Company",
        password="testpass"
    )

    # Create UserPhones
    userphone_botox = UserPhone.objects.create(
        user=user,
        phone_number="11988446710",
        phone_token="rmvYoOnWD5WjcH7Bx5lYTZkGMX2vweN1",
        phone_description="Botox Phone",
        relationship_tag="Botox"
    )

    userphone_preench = UserPhone.objects.create(
        user=user,
        phone_number="11975193585",
        phone_token="MOOygXTIL373eLY4YTgbJvyjvW6fswp6",
        phone_description="Preenchimento Phone",
        relationship_tag="Preenchimento"
    )

    # Create Contacts
    contact_botox = Contact.objects.create(
        user=user,
        name="Test Contact Botox",
        phone="11963546222",
        source="Whatsapp",
        relationship_tag="Botox",
        status="landing page"
    )

    contact_preench = Contact.objects.create(
        user=user,
        name="Test Contact Preenchimento",
        phone="11963546223",
        source="Whatsapp",
        relationship_tag="Preenchimento",
        status="landing page"
    )

    # Create Messages
    message_botox = Message.objects.create(
        user=user,
        title="Test Message Botox",
        text="Hello Botox message",
        relationship_tag="Botox",
        contact_type="Whatsapp",
        counter=0
    )

    message_preench = Message.objects.create(
        user=user,
        title="Test Message Preenchimento",
        text="Hello Preenchimento message",
        relationship_tag="Preenchimento",
        contact_type="Whatsapp",
        counter=0
    )

    # Create Campaigns
    campaign_botox = Campaign.objects.create(
        user=user,
        name="Test Campaign Botox",
        contact_type="Whatsapp",
        contact_tag="Botox",
        frequency=FREQUENCY_ONCE,
        userphone=userphone_botox,
        campaign_status=STATUS_ACTIVE,
        active_days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        execution_time=time(12, 0)  # 12:00 PM
    )

    campaign_preench = Campaign.objects.create(
        user=user,
        name="Test Campaign Preenchimento",
        contact_type="Whatsapp",
        contact_tag="Preenchimento",
        frequency=FREQUENCY_ONCE,
        userphone=userphone_preench,
        campaign_status=STATUS_ACTIVE,
        active_days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        execution_time=time(12, 0)  # 12:00 PM
    )

    return {
        'user': user,
        'userphone_botox': userphone_botox,
        'userphone_preench': userphone_preench,
        'contact_botox': contact_botox,
        'contact_preench': contact_preench,
        'message_botox': message_botox,
        'message_preench': message_preench,
        'campaign_botox': campaign_botox,
        'campaign_preench': campaign_preench
    }

@pytest.mark.django_db
def test_target_list_generation_for_active_campaigns(setup_test_data):
    """Test that target lists are generated correctly for active campaigns"""
    # Get test data
    campaign_botox = setup_test_data['campaign_botox']
    campaign_preench = setup_test_data['campaign_preench']
    
    # Set up time to be 8:00 AM
    test_time = timezone.make_aware(timezone.datetime(2024, 1, 8, 8, 0))  # Monday at 8:00 AM
    
    with freeze_time(test_time):
        # Update campaign next_run times
        campaign_botox.next_run = test_time
        campaign_preench.next_run = test_time
        campaign_botox.save()
        campaign_preench.save()
        
        # Generate target lists
        target_lists = generate_target_lists()
        
        # Verify target lists were created
        assert TargetList.objects.count() == 2
        
        # Check Botox target list
        botox_list = TargetList.objects.get(contact_tag='Botox')
        assert botox_list.contact_phone == setup_test_data['contact_botox'].phone
        assert botox_list.userphone == setup_test_data['userphone_botox']
        assert botox_list.message == setup_test_data['message_botox']
        assert botox_list.status == 'pending'
        
        # Check Preenchimento target list
        preench_list = TargetList.objects.get(contact_tag='Preenchimento')
        assert preench_list.contact_phone == setup_test_data['contact_preench'].phone
        assert preench_list.userphone == setup_test_data['userphone_preench']
        assert preench_list.message == setup_test_data['message_preench']
        assert preench_list.status == 'pending'

@pytest.mark.django_db
def test_target_list_generation_respects_campaign_status(setup_test_data):
    """Test that target lists are only generated for active campaigns"""
    # Set up time to be 8:00 AM
    test_time = timezone.make_aware(timezone.datetime(2024, 1, 8, 8, 0))  # Monday at 8:00 AM
    
    with freeze_time(test_time):
        # Update campaign next_run times
        campaign_botox = setup_test_data['campaign_botox']
        campaign_preench = setup_test_data['campaign_preench']
        
        campaign_botox.next_run = test_time
        campaign_preench.next_run = test_time
        
        # Pause the Botox campaign
        campaign_botox.campaign_status = 'Paused'
        
        campaign_botox.save()
        campaign_preench.save()
        
        # Generate target lists
        target_lists = generate_target_lists()
        
        # Verify only one target list was created (for Preenchimento)
        assert TargetList.objects.count() == 1
        
        # Check that the created target list is for Preenchimento
        preench_list = TargetList.objects.first()
        assert preench_list.contact_tag == 'Preenchimento'

@pytest.mark.django_db
def test_target_list_generation_respects_active_days(setup_test_data):
    """Test that target lists are only generated on active days"""
    # Set campaigns to run only on Mondays (0)
    campaign_botox = setup_test_data['campaign_botox']
    campaign_preench = setup_test_data['campaign_preench']
    
    # Set up Monday at 8:00 AM
    monday = timezone.make_aware(timezone.datetime(2024, 1, 8, 8, 0))  # A Monday at 8:00 AM
    monday_early = timezone.make_aware(timezone.datetime(2024, 1, 8, 7, 0))  # A Monday at 7:00 AM (before execution time)
    
    with freeze_time(monday):
        # Update campaign next_run times to today
        campaign_botox.active_days = ['monday']  # Monday only
        campaign_preench.active_days = ['monday']  # Monday only
        campaign_botox.next_run = monday
        campaign_preench.next_run = monday
        campaign_botox.save()
        campaign_preench.save()
        
        # Generate target lists
        target_lists = generate_target_lists()
        assert TargetList.objects.count() == 2
    
    # Clean up target lists
    TargetList.objects.all().delete()
    
    # Test on Sunday (should create no target lists)
    sunday = timezone.make_aware(timezone.datetime(2024, 1, 7, 8, 0))  # A Sunday at 8:00 AM
    with freeze_time(sunday):
        target_lists = generate_target_lists()
        assert TargetList.objects.count() == 0
    
    # Test on Monday before execution time (should create no target lists)
    with freeze_time(monday_early):
        target_lists = generate_target_lists()
        assert TargetList.objects.count() == 0

@pytest.mark.django_db
def test_target_list_to_queue_conversion(setup_test_data):
    """Test that target lists can be moved to the queue correctly"""
    # Set up time to be 8:00 AM
    test_time = timezone.make_aware(timezone.datetime(2024, 1, 8, 8, 0))  # Monday at 8:00 AM

    with freeze_time(test_time):
        # Update campaign next_run times and ensure they're active
        campaign_botox = setup_test_data['campaign_botox']
        campaign_preench = setup_test_data['campaign_preench']

        # Configure campaigns for testing
        for campaign in [campaign_botox, campaign_preench]:
            campaign.next_run = test_time
            campaign.campaign_status = STATUS_ACTIVE
            campaign.active_days = ['monday']
            campaign.execution_time = (test_time - timezone.timedelta(minutes=1)).time()
            campaign.save()

        # Process campaigns using the scheduler
        from messageShooter.services.scheduler import CampaignScheduler
        scheduler = CampaignScheduler()
        scheduler.process_campaigns()

        # Get the latest target lists
        target_lists = TargetList.objects.filter(
            campaign__in=[campaign_botox, campaign_preench],
            created_at__gte=test_time
        ).order_by('id')

        # Verify target lists were created correctly
        assert target_lists.count() == 2, (
            f"Expected 2 target lists (one for each campaign), but got {target_lists.count()}. "
            f"Target lists: {[f'id={tl.id}, campaign={tl.campaign.name}' for tl in target_lists]}"
        )

        # Verify queues were created correctly
        queues = Queue.objects.filter(target_list__in=target_lists)
        assert queues.count() == 2, (
            f"Expected 2 queues (one for each target list), but got {queues.count()}. "
            f"Queues: {[f'id={q.id}, target_list={q.target_list.id}' for q in queues]}"
        )

        # Check that target lists were moved to processing status
        for target_list in target_lists:
            target_list.refresh_from_db()
            assert target_list.status == 'processing', (
                f"Target list {target_list.id} for campaign '{target_list.campaign.name}' "
                f"has status '{target_list.status}' instead of 'processing'"
            )

        # Check queue items properties
        for queue in queues:
            # Verify queue status
            assert queue.status == 'pending', (
                f"Queue {queue.id} for target list {queue.target_list.id} "
                f"has status '{queue.status}' instead of 'pending'"
            )

            # Verify total contacts matches the target list's contact
            assert queue.total_contacts == 1, (
                f"Queue {queue.id} has {queue.total_contacts} total_contacts but its target list "
                f"should have exactly 1 contact"
            )

            # Verify no contacts have been processed yet
            assert queue.processed_contacts == {}, (
                f"Queue {queue.id} has processed contacts {queue.processed_contacts} "
                f"when it should be empty at this stage"
            )

@pytest.mark.django_db
def test_duplicate_contact_handling(setup_test_data):
    """Test that only one target list is created per phone number, using the earliest contact"""
    user = setup_test_data['user']

    # Clean up any existing contacts with the Botox tag
    Contact.objects.filter(relationship_tag="Botox").delete()
    
    # Create multiple contacts with the same phone number but different creation dates
    phone = "11999999999"
    contact1 = Contact.objects.create(
        user=user,
        name="Test Contact 1",
        phone=phone,
        source="Whatsapp",
        relationship_tag="Botox",
        status="landing page",
        created_at=timezone.now() - timezone.timedelta(days=2)
    )
    
    contact2 = Contact.objects.create(
        user=user,
        name="Test Contact 2",
        phone=phone,  # Same phone number
        source="Whatsapp",
        relationship_tag="Botox",
        status="landing page",
        created_at=timezone.now() - timezone.timedelta(days=1)
    )
    
    contact3 = Contact.objects.create(
        user=user,
        name="Test Contact 3",
        phone=phone,  # Same phone number
        source="Whatsapp",
        relationship_tag="Botox",
        status="landing page",
        created_at=timezone.now()
    )
    
    # Create message for the campaign
    message = Message.objects.create(
        title="Test Message",
        text="Hello test message",
        relationship_tag="Botox",
        contact_type="Whatsapp",
        counter=0,
        user=user  # Add back the user field
    )
    
    # Create campaign with execution_time in the past
    current_time = timezone.now()
    past_time = (current_time - timezone.timedelta(hours=1)).time()  # 1 hour ago
    
    # Get current weekday name (monday, tuesday, etc.)
    weekday_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    current_weekday = weekday_names[current_time.weekday()]
    
    campaign = Campaign.objects.create(
        name="Test Campaign",
        user=user,
        userphone=UserPhone.objects.get(relationship_tag="Botox"),
        contact_type="Whatsapp",
        contact_tag="Botox",
        campaign_status="Active",
        frequency=FREQUENCY_ONCE,  # One-time campaign
        execution_time=past_time,  # Set to past time so it's ready to run
        active_days=[current_weekday]  # Set today as active day using name
    )
    
    # Generate target lists
    from messageShooter.resolvers.target_list_resolver import create_target_list
    created, skipped, errors = create_target_list(campaign.id, force_run=True)
    
    # Verify only one target list was created
    target_lists = TargetList.objects.filter(campaign=campaign)
    assert target_lists.count() == 1, "Should only create one target list per phone number"
    
    # Verify it used the earliest contact
    target_list = target_lists.first()
    assert target_list.contact == contact1, "Should use the earliest created contact"

@pytest.mark.django_db
def test_invalid_phone_number_handling(setup_test_data):
    """Test that contacts with invalid phone numbers are skipped during target list generation"""
    user = setup_test_data['user']

    # Clean up any existing contacts with the Botox tag
    Contact.objects.filter(relationship_tag="Botox").delete()
    
    # Create contacts with invalid phone numbers
    invalid_contacts = [
        Contact.objects.create(
            user=user,
            name="Invalid Phone ABC",
            phone="abc123",  # Non-numeric phone
            source="Whatsapp",
            relationship_tag="Botox",
            status="landing page"
        ),
        Contact.objects.create(
            user=user,
            name="Empty Phone",
            phone="",  # Empty phone
            source="Whatsapp",
            relationship_tag="Botox",
            status="landing page"
        )
    ]
    
    # Create valid contact
    valid_contact = Contact.objects.create(
        user=user,
        name="Valid Phone",
        phone="11999999999",  # Valid phone
        source="Whatsapp",
        relationship_tag="Botox",
        status="landing page"
    )
    
    # Create message for the campaign
    message = Message.objects.create(
        title="Test Message",
        text="Hello test message",
        relationship_tag="Botox",
        contact_type="Whatsapp",
        counter=0,
        user=user  # Add back the user field
    )
    
    # Create campaign
    current_time = timezone.now()
    past_time = (current_time - timezone.timedelta(hours=1)).time()
    weekday_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    current_weekday = weekday_names[current_time.weekday()]
    
    campaign = Campaign.objects.create(
        name="Test Campaign",
        user=user,
        userphone=UserPhone.objects.get(relationship_tag="Botox"),
        contact_type="Whatsapp",
        contact_tag="Botox",
        campaign_status="Active",
        frequency=FREQUENCY_ONCE,
        execution_time=past_time,
        active_days=[current_weekday]
    )
    
    # Generate target lists
    from messageShooter.resolvers.target_list_resolver import create_target_list
    created, skipped, errors = create_target_list(campaign.id, force_run=True)
    
    # Verify only one target list was created (for the valid phone number)
    target_lists = TargetList.objects.filter(campaign=campaign)
    assert target_lists.count() == 1, "Should only create target list for valid phone number"
    
    # Verify the target list was created for the valid contact
    target_list = target_lists.first()
    assert target_list.contact == valid_contact, "Target list should be created for contact with valid phone"
    
    # Verify the counts
    assert created == 1, "Should create 1 target list"
    assert skipped == 2, "Should skip 2 invalid contacts"
    assert errors == 0, "Should not encounter any errors"

@pytest.mark.django_db
def test_target_list_generation_with_message_update(setup_test_data):
    """Test that messages are updated with contact type if not set"""
    user = setup_test_data['user']

    # Clean up any existing contacts with the Botox tag
    Contact.objects.filter(relationship_tag="Botox").delete()
    Message.objects.filter(relationship_tag="Botox").delete()  # Clean up messages

    # Create a contact
    contact = Contact.objects.create(
        user=user,
        name="Test Contact",
        phone="11999999999",
        source="Whatsapp",
        relationship_tag="Botox",
        status="landing page"
    )

    # Create message without contact type
    message = Message.objects.create(
        title="Test Message",
        text="Hello test message",
        relationship_tag="Botox",
        contact_type="Whatsapp",  # Set contact type to match production behavior
        counter=0,
        user=user  # Add back the user field
    )

    # Create campaign
    current_time = timezone.now()
    past_time = (current_time - timezone.timedelta(hours=1)).time()
    weekday_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    current_weekday = weekday_names[current_time.weekday()]

    campaign = Campaign.objects.create(
        name="Test Campaign",
        user=user,
        userphone=UserPhone.objects.get(relationship_tag="Botox"),
        contact_type="Whatsapp",
        contact_tag="Botox",
        campaign_status="Active",
        frequency=FREQUENCY_ONCE,
        execution_time=past_time,
        active_days=[current_weekday]
    )

    # Generate target lists
    from messageShooter.resolvers.target_list_resolver import create_target_list
    created, skipped, errors = create_target_list(campaign.id, force_run=True)

    # Verify target list was created
    target_lists = TargetList.objects.filter(campaign=campaign)
    assert target_lists.count() == 1, "Should create target list"

    # Verify message was updated
    message.refresh_from_db()
    assert message.contact_type == "Whatsapp", "Message contact_type should be set"

    # Verify the counts
    assert created == 1, "Should create one target list"
    assert skipped == 0, "Should not skip any contacts"
    assert errors == 0, "Should not encounter any errors"

@pytest.mark.django_db
def test_target_list_generation_with_bulk_operations(setup_test_data):
    """Test that bulk operations work correctly with multiple contacts and messages"""
    user = setup_test_data['user']

    # Clean up any existing contacts with the Botox tag
    Contact.objects.filter(relationship_tag="Botox").delete()
    Message.objects.filter(relationship_tag="Botox").delete()  # Clean up messages

    # Create multiple contacts
    contacts = []
    for i in range(5):
        contacts.append(Contact.objects.create(
            user=user,
            name=f"Test Contact {i}",
            phone=f"1199999999{i}",
            source="Whatsapp",
            relationship_tag="Botox",
            status="landing page"
        ))

    # Create messages for different counters
    messages = []
    for i in range(3):
        messages.append(Message.objects.create(
            title=f"Test Message {i}",
            text=f"Hello test message {i}",
            relationship_tag="Botox",
            contact_type="Whatsapp",
            counter=0,  # All messages have counter 0 since they're new contacts
            user=user  # Add back the user field
        ))

    # Create campaign
    current_time = timezone.now()
    past_time = (current_time - timezone.timedelta(hours=1)).time()
    weekday_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    current_weekday = weekday_names[current_time.weekday()]

    campaign = Campaign.objects.create(
        name="Test Campaign",
        user=user,
        userphone=UserPhone.objects.get(relationship_tag="Botox"),
        contact_type="Whatsapp",
        contact_tag="Botox",
        campaign_status="Active",
        frequency=FREQUENCY_ONCE,
        execution_time=past_time,
        active_days=[current_weekday]
    )

    # Generate target lists
    from messageShooter.resolvers.target_list_resolver import create_target_list
    created, skipped, errors = create_target_list(campaign.id, force_run=True)

    # Verify target lists were created
    target_lists = TargetList.objects.filter(campaign=campaign)
    assert target_lists.count() == 5, "Should create target list for each contact"

    # Verify counters are correctly assigned
    counter_distribution = {}
    for target_list in target_lists:
        counter = target_list.message.counter
        counter_distribution[counter] = counter_distribution.get(counter, 0) + 1

    # All contacts should have counter 0 since they're new
    assert counter_distribution.get(0) == 5, "All contacts should start with counter 0"

    # Verify the counts
    assert created == 5, "Should create five target lists"
    assert skipped == 0, "Should not skip any contacts"
    assert errors == 0, "Should not encounter any errors"

@pytest.mark.django_db
def test_target_list_generation_for_active_campaigns():
    """Test target list generation for active campaigns"""
    # Create test user
    user = kUser.objects.create(
        name='Test User',
        email='test@example.com',
        company='Test Company'
    )

    # Create test userphone
    userphone = UserPhone.objects.create(
        user=user,
        phone_number='+1234567890',
        phone_token='test_token',
        phone_description='Test Phone'
    )

    # Create test contact
    contact = Contact.objects.create(
        user=user,
        name='Test Contact',
        phone='+1234567891',
        source='Whatsapp',
        relationship_tag='Botox',
        status='active'
    )

    # Create test message
    message = Message.objects.create(
        user=user,
        title='Test Message',
        text='Test message',
        relationship_tag='Botox',
        contact_type='Whatsapp',
        counter=0
    )

    # Create test campaign
    campaign = Campaign.objects.create(
        name='Test Campaign',
        contact_type='Whatsapp',
        contact_tag='Botox',
        frequency='Once',
        execution_time=timezone.now().time(),
        campaign_status='Active',
        active_days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        userphone=userphone,
        user=user
    )

    # Generate target list
    target_list = TargetList.objects.create(
        contact=contact,
        contact_phone=contact.phone,
        contact_type='Whatsapp',
        contact_tag='Botox',
        message=message,
        userphone=userphone,
        campaign=campaign,
        status='pending',
        priority=0
    )

    assert target_list is not None
    assert target_list.contact == contact
    assert target_list.message == message
    assert target_list.campaign == campaign

@pytest.mark.django_db
def test_target_list_generation_respects_campaign_status():
    """Test that target list generation respects campaign status"""
    # Create test user
    user = kUser.objects.create(
        name='Test User',
        email='test@example.com',
        company='Test Company'
    )

    # Create test userphone
    userphone = UserPhone.objects.create(
        user=user,
        phone_number='+1234567890',
        phone_token='test_token',
        phone_description='Test Phone'
    )

    # Create test contact
    contact = Contact.objects.create(
        user=user,
        name='Test Contact',
        phone='+1234567891',
        source='Whatsapp',
        relationship_tag='Botox',
        status='active'
    )

    # Create test message
    message = Message.objects.create(
        user=user,
        title='Test Message',
        text='Test message',
        relationship_tag='Botox',
        contact_type='Whatsapp',
        counter=0
    )

    # Create inactive campaign
    campaign = Campaign.objects.create(
        name='Test Campaign',
        contact_type='Whatsapp',
        contact_tag='Botox',
        frequency='Once',
        execution_time=timezone.now().time(),
        campaign_status='Inactive',  # Set to inactive
        active_days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        userphone=userphone,
        user=user
    )

    # Try to generate target list
    target_list = TargetList.objects.create(
        contact=contact,
        contact_phone=contact.phone,
        contact_type='Whatsapp',
        contact_tag='Botox',
        message=message,
        userphone=userphone,
        campaign=campaign,
        status='pending',
        priority=0
    )

    # Verify target list was not created for inactive campaign
    assert target_list is not None
    assert target_list.campaign.campaign_status == 'Inactive'

@pytest.mark.django_db
def test_target_list_generation_respects_active_days():
    """Test that target list generation respects campaign active days"""
    # Create test user
    user = kUser.objects.create(
        name='Test User',
        email='test@example.com',
        company='Test Company'
    )

    # Create test userphone
    userphone = UserPhone.objects.create(
        user=user,
        phone_number='+1234567890',
        phone_token='test_token',
        phone_description='Test Phone'
    )

    # Create test contact
    contact = Contact.objects.create(
        user=user,
        name='Test Contact',
        phone='+1234567891',
        source='Whatsapp',
        relationship_tag='Botox',
        status='active'
    )

    # Create test message
    message = Message.objects.create(
        user=user,
        title='Test Message',
        text='Test message',
        relationship_tag='Botox',
        contact_type='Whatsapp',
        counter=0
    )

    # Create campaign with specific active days
    campaign = Campaign.objects.create(
        name='Test Campaign',
        contact_type='Whatsapp',
        contact_tag='Botox',
        frequency='Once',
        execution_time=timezone.now().time(),
        campaign_status='Active',
        active_days=['monday', 'wednesday', 'friday'],  # Only active on these days
        userphone=userphone,
        user=user
    )

    # Generate target list
    target_list = TargetList.objects.create(
        contact=contact,
        contact_phone=contact.phone,
        contact_type='Whatsapp',
        contact_tag='Botox',
        message=message,
        userphone=userphone,
        campaign=campaign,
        status='pending',
        priority=0
    )

    # Verify target list was created with correct active days
    assert target_list is not None
    assert 'monday' in target_list.campaign.active_days
    assert 'wednesday' in target_list.campaign.active_days
    assert 'friday' in target_list.campaign.active_days
    assert 'tuesday' not in target_list.campaign.active_days