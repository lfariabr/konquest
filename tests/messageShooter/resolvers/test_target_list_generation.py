import pytest
from django.utils import timezone
from core.models.user import kUser
from core.models.contact import Contact
from core.models.userphone import UserPhone
from core.models.message import Message
from messageShooter.models.campaign import Campaign, FREQUENCY_DAILY, FREQUENCY_ONCE
from messageShooter.models.target_list import TargetList
from messageShooter.resolvers.target_list_resolver import generate_target_lists
from freezegun import freeze_time
import datetime

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
        phone="11963546222",
        source="Whatsapp",
        relationship_tag="Preenchimento",
        status="landing page"
    )

    # Create Messages
    message_botox = Message.objects.create(
        user=user,
        title="Botox Message 0",
        text="Hello message Botox 0",
        relationship_tag="Botox",
        contact_type="Whatsapp",
        counter=0
    )

    message_preench = Message.objects.create(
        user=user,
        title="Preenchimento Message 0",
        text="Hello message Preenchimento 0",
        relationship_tag="Preenchimento",
        contact_type="Whatsapp",
        counter=0
    )

    # Set up a base time for campaign creation
    now = timezone.now()
    execution_time = datetime.time(8, 0)  # 8:00 AM

    # Create Campaigns
    campaign_botox = Campaign.objects.create(
        user=user,
        name="Botox Campaign",
        contact_type="Whatsapp",
        contact_tag="Botox",
        frequency=FREQUENCY_DAILY,
        userphone=userphone_botox,
        execution_time=execution_time,
        active_days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'],  # Using day names
        campaign_status="Active",
        next_run=timezone.datetime.combine(now.date(), execution_time, tzinfo=now.tzinfo)
    )

    campaign_preench = Campaign.objects.create(
        user=user,
        name="Preenchimento Campaign",
        contact_type="Whatsapp",
        contact_tag="Preenchimento",
        frequency=FREQUENCY_DAILY,
        userphone=userphone_preench,
        execution_time=execution_time,
        active_days=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'],  # Using day names
        campaign_status="Active",
        next_run=timezone.datetime.combine(now.date(), execution_time, tzinfo=now.tzinfo)
    )

    return {
        'campaign_botox': campaign_botox,
        'campaign_preench': campaign_preench,
        'contact_botox': contact_botox,
        'contact_preench': contact_preench,
        'message_botox': message_botox,
        'message_preench': message_preench,
        'userphone_botox': userphone_botox,
        'userphone_preench': userphone_preench,
        'user': user
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
        # Update campaign next_run times
        campaign_botox = setup_test_data['campaign_botox']
        campaign_preench = setup_test_data['campaign_preench']
        
        campaign_botox.next_run = test_time
        campaign_preench.next_run = test_time
        campaign_botox.save()
        campaign_preench.save()
        
        # Generate target lists
        target_lists = generate_target_lists()
        assert TargetList.objects.count() == 2
        
        # Import and run the queue setup function
        from setup_queue import move_target_lists_to_queue
        move_target_lists_to_queue()
        
        # Verify queue items were created
        from messageShooter.models.queue import Queue
        assert Queue.objects.count() == 2
        
        # Check that target lists were moved to processing status
        for target_list in TargetList.objects.all():
            assert target_list.status == 'processing'
        
        # Check queue items properties
        for queue_item in Queue.objects.all():
            assert queue_item.status == 'pending'
            assert queue_item.target_list is not None
            assert queue_item.target_list.contact is not None
            assert queue_item.message is not None
            assert queue_item.userphone is not None
            assert queue_item.scheduled_time is not None
            # Priority should match target list priority
            assert queue_item.priority == queue_item.target_list.priority

@pytest.mark.django_db
def test_duplicate_contact_handling(setup_test_data):
    """Test that only one target list is created per phone number, using the earliest contact"""
    user = setup_test_data['user']

    # Clean up any existing contacts with the Botox tag
    Contact.objects.filter(relationship_tag="Botox").delete()

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
        counter=0,
        user=user,
        contact_type="Whatsapp"
    )

    # Create campaign with execution_time in the past
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

    # Verify only one target list was created (deduplication working)
    target_lists = TargetList.objects.filter(campaign=campaign)
    assert target_lists.count() == 1, "Should create only one target list for duplicate phone numbers"
    
    # Verify the earliest contact was used
    target_list = target_lists.first()
    assert target_list.contact == contact1, "Should use the earliest contact for the target list"
    
    # Verify the contact's creation date
    assert target_list.contact.created_at == contact1.created_at, "Should use the contact with earliest creation date"

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
        counter=0,
        user=user,
        contact_type="Whatsapp"
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
def test_target_list_generation_with_missing_message(setup_test_data):
    """Test that contacts are skipped when no message exists for their counter"""
    user = setup_test_data['user']
    
    # Clean up any existing contacts with the Botox tag
    Contact.objects.filter(relationship_tag="Botox").delete()
    Message.objects.filter(relationship_tag="Botox").delete()  # Also clean up messages
    
    # Create a contact
    contact = Contact.objects.create(
        user=user,
        name="Test Contact",
        phone="11999999999",
        source="Whatsapp",
        relationship_tag="Botox",
        status="landing page"
    )
    
    # Create campaign without creating a message
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
    
    # Verify no target lists were created
    target_lists = TargetList.objects.filter(campaign=campaign)
    assert target_lists.count() == 0, "Should not create target list when message is missing"
    
    # Verify the counts
    assert created == 0, "Should not create any target lists"
    assert skipped == 1, "Should skip the contact due to missing message"
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
        counter=0,
        user=user,
        contact_type=None  # Explicitly set to None
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
    assert message.contact_type == "Whatsapp", "Message contact_type should be updated"
    
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
            counter=0,  # All messages have counter 0 since they're new contacts
            user=user,
            contact_type="Whatsapp"
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