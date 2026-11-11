import ssl, urllib.request, json

TOKEN = "9182824243:AAFDAJBmFd0m4hPcZH4k0Skqryzj3g5g8aE"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
data = json.loads(urllib.request.urlopen(url, context=ctx).read().decode())

seen = set()
for u in data.get("result", []):
    msg = u.get("message") or u.get("channel_post") or u.get("my_chat_member") or {}
    chat = msg.get("chat")
    if chat and chat["id"] not in seen:
        seen.add(chat["id"])
        print(chat["id"], "|", chat.get("title") or chat.get("first_name"), "|", chat["type"])

if not seen:
    print("خالی بود. یک پیام در گروه بفرست و دوباره اجرا کن.")