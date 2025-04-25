import requests
from decouple import config
from django.http import JsonResponse

WEBHOOK_DISCORD = config('WEBHOOK_DISCORD')

def send_discord_message(message):
    url = WEBHOOK_DISCORD
    data = {"content": message}
    response = requests.post(url, json=data)
    return response.status_code

def connect_clicked(request):
    if request.method == "POST":
        send_discord_message("🔗 CONNECT button clicked on Home page!")
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "Invalid method"}, status=405)