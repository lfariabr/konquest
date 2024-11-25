import pytest
from django.utils import timezone
from core.models.user import kUser
from core.models.contact import Contact
from core.models.userphone import UserPhone
from core.models.message import Message
from messageShooter.models.campaign import Campaign, FREQUENCY_DAILY
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
        status="active"
    )

    contact_preench = Contact.objects.create(
        user=user,
        name="Test Contact Preenchimento",
        phone="11963546222",
        source="Whatsapp",
        relationship_tag="Preenchimento",
        status="active"
    )

    # Create Messages
    message_botox = Message.objects.create(
        user=user,
        title="Botox Message 0",
        text="Hello message Botox 0",
        relationship_tag="Botox",
        counter=0
    )

    message_preench = Message.objects.create(
        user=user,
        title="Preenchimento Message 0",
        text="Hello message Preenchimento 0",
        relationship_tag="Preenchimento",
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
        active_days=[0, 1, 2, 3, 4, 5],  # Monday to Saturday
        start_time=now,
        next_run=timezone.datetime.combine(now.date(), execution_time, tzinfo=now.tzinfo),
        sequential_order=[{'message_id': message_botox.id}]  # Add message sequence
    )

    campaign_preench = Campaign.objects.create(
        user=user,
        name="Preenchimento Campaign",
        contact_type="Whatsapp",
        contact_tag="Preenchimento",
        frequency=FREQUENCY_DAILY,
        userphone=userphone_preench,
        execution_time=execution_time,
        active_days=[0, 1, 2, 3, 4, 5],  # Monday to Saturday
        start_time=now,
        next_run=timezone.datetime.combine(now.date(), execution_time, tzinfo=now.tzinfo),
        sequential_order=[{'message_id': message_preench.id}]  # Add message sequence
    )

    return {
        'campaign_botox': campaign_botox,
        'campaign_preench': campaign_preench,
        'contact_botox': contact_botox,
        'contact_preench': contact_preench,
        'message_botox': message_botox,
        'message_preench': message_preench,
        'userphone_botox': userphone_botox,
        'userphone_preench': userphone_preench
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
        campaign_botox.active_days = [0]  # Monday only
        campaign_preench.active_days = [0]  # Monday only
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
            assert queue_item.contact is not None
            assert queue_item.message is not None
            assert queue_item.userphone is not None
            assert queue_item.scheduled_time is not None
            # Priority should match target list priority
            assert queue_item.priority == queue_item.target_list.priority
