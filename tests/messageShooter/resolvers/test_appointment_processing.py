import pytest
from django.utils import timezone
from datetime import timedelta
from messageShooter.resolvers.get_counter import bulk_get_counter_appointment
from messageShooter.resolvers.get_appointment_to_contact import convert_appointment_to_contact
from messageShooter.resolvers.get_message import get_message_for_interval
from core.models.message import Message
from core.models.contact import Contact
from apiCrm.models.appointment import Appointment
from core.models.user import kUser

@pytest.fixture
def test_user():
    return kUser.objects.create(
        name="Test User",
        email="test@example.com",
        password="password123"
    )

@pytest.fixture
def appointment_messages(test_user):
    messages = []
    # Reminder messages
    messages.append(Message.objects.create(
        text="Tomorrow appointment reminder",
        relationship_tag="Reminder",
        counter=1,
        contact_type="Appointment",
        user=test_user,
        title="Reminder Message"
    ))
    messages.append(Message.objects.create(
        text="Today appointment reminder",
        relationship_tag="Reminder",
        counter=0,
        contact_type="Appointment",
        user=test_user,
        title="Reminder Message"
    ))

    # Missed appointment messages
    messages.append(Message.objects.create(
        text="You missed your appointment",
        relationship_tag="Falta",
        counter=0,
        contact_type="Appointment",
        user=test_user,
        title="Missed Appointment"
    ))

    # Cancelled appointment messages
    messages.append(Message.objects.create(
        text="Appointment cancelled",
        relationship_tag="Cancelado",
        counter=0,
        contact_type="Appointment",
        user=test_user,
        title="Cancelled Appointment"
    ))
    return messages

@pytest.fixture
def test_appointments(test_user):
    now = timezone.now()
    appointments = []
    for i in range(6):
        status = "Agendado"
        if i == 4:
            status = "Falta"
        elif i == 5:
            status = "Cancelado"
            
        apt = Appointment.objects.create(
            id_crm=f"TEST{i}",
            customer_name=f"Test Customer {i}",
            customer_phone=f"1199999{i:04d}",
            store_name="JARDINS",
            status_label=status,
            appointment_date=now + timedelta(days=i),
            createdby_created_at=now
        )
        appointments.append(apt)
    return appointments

@pytest.mark.django_db
class TestAppointmentProcessing:
    def test_reminder_message_selection(self, appointment_messages, test_appointments):
        """Test message selection for reminders"""
        # Tomorrow's appointment
        msg = get_message_for_interval(
            contact_type="Appointment",
            relationship_tag="Reminder",
            appointment_status_label="Agendado",
            days_interval=1
        )
        assert msg.text == "Tomorrow appointment reminder"
        
        # Today's appointment
        msg = get_message_for_interval(
            contact_type="Appointment",
            relationship_tag="Reminder",
            appointment_status_label="Agendado",
            days_interval=0
        )
        assert msg.text == "Today appointment reminder"
        
        # No message for appointments too far in future
        msg = get_message_for_interval(
            contact_type="Appointment",
            relationship_tag="Reminder",
            appointment_status_label="Agendado",
            days_interval=5
        )
        assert msg is None

    def test_missed_appointment_messages(self, appointment_messages, test_appointments):
        """Test message selection for missed appointments"""
        msg = get_message_for_interval(
            contact_type="Appointment",
            relationship_tag="Falta",
            appointment_status_label="Falta",
            days_interval=-3
        )
        assert msg.text == "You missed your appointment"
        
        # Message for appointments too far in past
        msg = get_message_for_interval(
            contact_type="Appointment",
            relationship_tag="Falta",
            appointment_status_label="Falta",
            days_interval=-10
        )
        assert msg.text == "You missed your appointment"  # Still get message for old missed appointments

    def test_cancelled_appointment_messages(self, appointment_messages, test_appointments):
        """Test message selection for cancelled appointments"""
        msg = get_message_for_interval(
            contact_type="Appointment",
            relationship_tag="Cancelado",
            appointment_status_label="Cancelado",
            days_interval=3
        )
        assert msg.text == "Appointment cancelled"
        
        # Message for appointments far in past
        msg = get_message_for_interval(
            contact_type="Appointment",
            relationship_tag="Cancelado",
            appointment_status_label="Cancelado",
            days_interval=10
        )
        assert msg.text == "Appointment cancelled"  # Still get message for old cancelled appointments

    def test_appointment_counter_calculation(self, test_appointments, test_user, appointment_messages):
        """Test counter calculation for appointments"""
        phones = [apt.customer_phone for apt in test_appointments]
    
        # Test Reminder counters - should be 0 initially as no messages sent
        reminder_counters = bulk_get_counter_appointment(phones, "Reminder")
        for phone, counter in reminder_counters.items():
            assert counter == 0  # No messages sent yet

        # Test Missed appointment counters - should be 0 initially
        missed_counters = bulk_get_counter_appointment(phones, "Falta")
        for phone, counter in missed_counters.items():
            assert counter == 0  # No messages sent yet

        # Create a message log to simulate sent message
        from core.models.messagelog import MessageLogs
        from core.models.contact import Contact
        test_phone = phones[0]
        test_contact = Contact.objects.create(
            phone=test_phone,
            name="Test User",
            relationship_tag="Reminder",
            user=test_user
        )
        
        # Get a test message
        test_message = next(msg for msg in appointment_messages if msg.relationship_tag == "Reminder")
        
        MessageLogs.objects.create(
            contact=test_contact,
            relationship_tag="Reminder",
            status="sent",
            message=test_message,
            user=test_user,
            sent_at=timezone.now()
        )

        # Test counter after sending message
        updated_counters = bulk_get_counter_appointment([test_phone], "Reminder")
        assert updated_counters[test_phone] == 1  # One message sent

    def test_contact_creation_from_appointment(self, test_appointments, test_user):
        """Test contact creation from appointments"""
        apt = test_appointments[0]

        # Create WhatsApp contact with same phone
        whatsapp_contact = Contact.objects.create(
            phone=apt.customer_phone,
            name="WhatsApp User",
            source="WhatsApp",
            relationship_tag="Botox",
            is_appointment=False,
            user=test_user
        )

        # Convert appointment to contact
        apt_contact = convert_appointment_to_contact(apt, "Reminder", test_user)
        assert apt_contact is not None
        assert apt_contact.phone == apt.customer_phone
        assert apt_contact.name == apt.customer_name
        assert apt_contact.source == "Appointment"
        assert apt_contact.is_appointment
        assert apt_contact.appointment_id == apt.id_crm
        assert apt_contact.appointment_status == apt.status_label

    def test_appointment_contact_update(self, test_appointments, test_user):
        """Test updating existing appointment contacts"""
        apt = test_appointments[0]

        # Create existing appointment contact
        old_contact = Contact.objects.create(
            phone=apt.customer_phone,
            name="Old Name",
            source="Appointment",
            relationship_tag="Reminder",
            is_appointment=True,
            appointment_id=apt.id_crm,
            user=test_user
        )

        # Convert appointment again - should update existing
        new_contact = convert_appointment_to_contact(apt, "Reminder", test_user)
        assert new_contact.id == old_contact.id
        assert new_contact.name == "Old Name"  # Name should not change
        assert new_contact.appointment_status == apt.status_label
        assert new_contact.appointment_id == apt.id_crm

    def test_multiple_appointment_contacts(self, test_appointments, test_user):
        """Test handling multiple appointments for same phone"""
        now = timezone.now()
        # Create two appointments with same phone
        phone = "11999999999"
        apt1 = Appointment.objects.create(
            id_crm="TEST_A",
            customer_name="Test A",
            customer_phone=phone,
            store_name="JARDINS",
            status_label="Agendado",
            appointment_date=now + timedelta(days=1),
            createdby_created_at=now
        )
        apt2 = Appointment.objects.create(
            id_crm="TEST_B",
            customer_name="Test B",
            customer_phone=phone,
            store_name="JARDINS",
            status_label="Agendado",
            appointment_date=now + timedelta(days=2),
            createdby_created_at=now
        )

        # Convert both appointments
        contact1 = convert_appointment_to_contact(apt1, "Reminder", test_user)
        assert contact1 is not None
        assert contact1.name == "Test A"  # First contact gets the name
        
        contact2 = convert_appointment_to_contact(apt2, "Reminder", test_user)
        assert contact2 is not None
        assert contact2.id == contact1.id  # Same contact is returned
        assert contact2.name == "Test A"  # Name stays from first contact
        assert contact2.appointment_id == apt2.id_crm  # But appointment ID is updated

    def test_appointment_contact_with_multiple_tags(self, test_appointments, test_user):
        """Test same appointment contact with different tags"""
        apt = test_appointments[0]

        # Convert same appointment with different tags
        reminder = convert_appointment_to_contact(apt, "Reminder", test_user)
        reschedule = convert_appointment_to_contact(apt, "Reschedule", test_user)

        # Should be different contacts
        assert reminder.id != reschedule.id
        assert reminder.relationship_tag == "Reminder"
        assert reschedule.relationship_tag == "Reschedule"

    def test_appointment_status_change(self, test_appointments, test_user):
        """Test handling appointment status changes"""
        apt = test_appointments[0]

        # Create initial contact
        contact = convert_appointment_to_contact(apt, "Reminder", test_user)
        assert contact.appointment_status == "Agendado"

        # Update appointment status
        apt.status_label = "Falta"
        apt.save()

        # Convert again - should update status
        updated = convert_appointment_to_contact(apt, "Reminder", test_user)
        assert updated.id == contact.id
        assert updated.appointment_status == "Falta"

    def test_invalid_appointment_scenarios(self, appointment_messages, test_user):
        """Test handling of invalid appointment data"""
        now = timezone.now()
        
        # Test with missing required fields
        invalid_apt = Appointment.objects.create(
            id_crm="INVALID",
            customer_name="",  # Empty name
            customer_phone="",  # Empty phone
            store_name="JARDINS",
            status_label="Agendado",
            appointment_date=now,
            createdby_created_at=now
        )
        
        # Empty phone should still create contact
        contact = convert_appointment_to_contact(invalid_apt, "Reminder", test_user)
        assert contact is not None
        assert contact.phone == ""
        assert contact.name == ""
