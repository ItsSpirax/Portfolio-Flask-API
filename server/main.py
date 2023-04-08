# Import
import json
import asyncio
import os
import requests
from discord import Webhook, Embed
from discord_webhook import DiscordWebhook, DiscordEmbed
import aiohttp
from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Flask, request, redirect, abort, jsonify, send_file
from flask_cors import CORS
from bs4 import BeautifulSoup

# Init
app = Flask(__name__)
CORS(app)

# Variables
user_list = ip_list = {}


# Functions
def captcha_verify(response, remoteip):
    return json.loads(
        requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": os.environ["RECAPTCHA_API_KEY"],
                "response": response,
                "remoteip": remoteip,
            },
        ).content
    )["success"]


def send_discord_webhook(
        webhook_url,
        title,
        description,
        color="39d874",
        username="Website - Adith",
        avatar_url="https://adith.ml/assets/favicon/favicon-32x32.png",
):
    embed = DiscordEmbed(
        title=title,
        description=description,
        color=color,
    )
    webhook = DiscordWebhook(url=webhook_url, username=username, avatar_url=avatar_url)
    webhook.add_embed(embed)
    webhook.execute()

async def update_leaderboard(score: int, username: str, message_id: int):
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(os.environ["LEADERBOARD_WEBHOOK_URL"], session=session)
        try:
            webhook_msg = await webhook.fetch_message(message_id)
            users = [x.split(". ")[1] for x in webhook_msg.embeds[0].fields[0].value.split("\n")]
            scores = [int(x) for x in webhook_msg.embeds[0].fields[1].value.split("\n")]
            if username in users:
                index = users.index(username)
                if int(scores[index]) < score:
                    scores[index] = score
            else:
                users.append(username)
                scores.append(score)
            users = [x for _, x in sorted(zip(scores, users), reverse=True)]
            scores = sorted(scores, reverse=True)
            users = [f"{i+1}. {x}" for i, x in enumerate(users)]
            if len(users) > 10:
                users.pop()
                scores.pop()
            newEmbed = Embed(title="**Stacker Leaderboard**", description="[**Click to Play!**](https://adith.ml/stacker)", color=0x3498DB)
            newEmbed.set_thumbnail(url="https://adith.ml/images/stack.png")
            newEmbed.add_field(name="**Username**", value="\n".join(users), inline=True)
            newEmbed.add_field(name="**Score**", value="\n".join([str(x) for x in scores]), inline=True)
            newEmbed.set_footer(text="Last Updated")
            newEmbed.timestamp = datetime.now(tz=ZoneInfo('Asia/Kolkata'))
            await webhook.edit_message(message_id, embed=newEmbed)
        except Exception as e:
            if str(e) == "404 Not Found (error code: 10008): Unknown Message":
                newEmbed = Embed(title="**Stacker Leaderboard**", description="[**Click to Play!**](https://adith.ml/stacker)", color=0x3498DB)
                newEmbed.set_thumbnail(url="https://adith.ml/images/stack.png")
                newEmbed.add_field(name="**Username**", value=f"1. {username}", inline=True)
                newEmbed.add_field(name="**Score**", value=score, inline=True)
                newEmbed.set_footer(text="Last Updated")
                newEmbed.timestamp = datetime.now(tz=ZoneInfo('Asia/Kolkata'))
                await webhook.send(embed=newEmbed, username="Stacker", avatar_url="https://adith.ml/images/favicon/favicon-32x32.png")
            else:
                print(e)

headers = {
    'authority': 'www.carwale.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'en-US,en-IN;q=0.9,en;q=0.8',
    'cache-control': 'max-age=0',
    'dnt': '1',
    'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
}

def search_cars(budget, bs, seat):
    req = requests.get("https://www.carwale.com/new/search/result/?fuel=5&bs=" + bs + "&budget=" + budget + "&seat=" + seat, headers = headers)
    escapes = ''.join([chr(char) for char in range(1, 32)])
    translator = str.maketrans('', '', escapes)
    soup = BeautifulSoup(req.text, 'html.parser')
    cars = soup.find_all("a", class_="href-title")
    price = soup.find_all("span", class_="new-price2")
    temp = 0
    dict = {}
    for i in range(len(cars)):
        car = cars[i].get_text().translate(translator)
        img = soup.find_all("img", alt = car)
        ratings = soup.find_all("img", class_= "text-bottom")
        final_rating = 0
        for x in range(0 + (5 * temp) , 5 + (5 * temp)):
            if ratings[x]['src'] == "https://imgd.aeplcdn.com/0x0/images/ratings/1.png":
                final_rating += 1
            elif ratings[x]['src'] == "https://imgd.aeplcdn.com/0x0/images/ratings/half.png":
                final_rating += 0.5
        dict[car] = [price[i].get_text(), img[0]['src'], str(final_rating) + " / 5"]
        temp += 1
    return dict

@app.route("/api/v1/search", methods=["POST"])
def search():
    return search_cars(request.json["budget"], request.json["bodystyle"], request.json["seats"])

# Web Request Routes
@app.route("/", methods=["GET"])
def home():
    return redirect("https://adith.ml", code=301)


@app.route("/favicon.ico", methods=["GET"])
def favicon():
    return send_file("media/favicon.ico")


@app.route("/v1/ping", methods=["GET", "POST"])
def ping():
    return jsonify(message="200: Success")


@app.route("/v1/stacker", methods=["POST"])
def stacker():
    username = request.json["username"]
    score = request.json["score"]
    if username is not None and score is not None:
        if score == 0 or score > 99:
            return jsonify(message="200: Success")
        asyncio.run(update_leaderboard(score, username, 1093232528959213608))
        adblock = str(request.json["adblock"])
        width = request.json["width"]
        height = request.json["height"]
        color = request.json["color"]
        rotation = "Portrait"
        if  request.json["rotation"] in ["landscape-primary", "landscape-secondary", "landscape"] :
            rotation = "Landscape"
        try:
            battery = f"\n\n**Battery:** {request.json['battery']}\n**Charging:** {str(request.json['charging'])}"
        except:
            battery = ""
        user_agent = str(request.headers.get("User-Agent"))
        if user_agent in user_list:
            response = user_list[user_agent]
        else:
            response = requests.post(
                "https://api.whatismybrowser.com/api/v2/user_agent_parse",
                data=json.dumps({"user_agent": f"{user_agent}"}),
                headers={"X-API-KEY": os.environ["WHAT_IS_MY_BROWSER_API_KEY"]},
            )
            user_list[user_agent] = response
        json_response = json.loads(response.content)
        platform = json_response["parse"]["simple_software_string"]
        model = f"\n**Model:** {json_response['parse']['simple_operating_platform_string']}"
        if json_response["parse"]["simple_operating_platform_string"] is None:
            model = ""
        ip = str(request.headers.get("Cf-Connecting-Ip"))
        if ip in ip_list:
            response = ip_list[ip]
        else:
            response = requests.get(
                f"https://ipgeolocation.abstractapi.com/v1/?api_key={os.environ['ABSTRACT_API_KEY']}&ip_address={ip}"
            )
            ip_list[ip] = response
        json_response = json.loads(response.content)
        ip_country_code = json_response["country_code"]
        ip_location = f"{json_response['city']}, {json_response['region']}"
        ip_postal_code = json_response["postal_code"]
        ip_currency = json_response["currency"]["currency_name"]
        ip_timezone = f"{json_response['timezone']['name']} ({json_response['timezone']['abbreviation']})"
        ip_is_vpn = json_response["security"]["is_vpn"]
        ip_connection_type = json_response["connection"]["connection_type"]
        ip_org = json_response["connection"]["autonomous_system_organization"]
        vpn = ""
        if str(ip_is_vpn).lower() == "true":
            vpn = " (VPN)"
        embed = DiscordEmbed(
            title=f"{username}   (Score: {score})",
            description=f"**Platform:** {platform}{model}\n\n**Display:** {width} x {height} ({color} bit)\n"
                        f"**Orientation:** {rotation}{battery}\n",
            color="39d874",
        )
        embed.set_thumbnail(
            url=f"https://flagcdn.com/h240/{ip_country_code.lower()}.png"
        )
        embed.add_embed_field(name="IP:", value=ip)
        embed.add_embed_field(name="Location:", value=ip_location)
        embed.add_embed_field(name="Postal Code:", value=ip_postal_code)
        embed.add_embed_field(name="Currency:", value=ip_currency)
        embed.add_embed_field(name="Time Zone:", value=ip_timezone)
        embed.add_embed_field(name="Adblocker Enabled:", value=adblock)
        embed.add_embed_field(
            name="Connection Type:", value=f"{ip_connection_type}{vpn}"
        )
        embed.add_embed_field(name="Organization:", value=ip_org)
        webhook = DiscordWebhook(url=os.environ["DISCORD_WEBHOOK_STACKER_URL"], username="Website - Adith",
                                 avatar_url="https://adith.ml/assets/favicon/favicon-32x32.png")
        webhook.add_embed(embed)
        webhook.execute()
        return jsonify(message="200: Success")
    else:
        abort(400)


@app.route("/v1/SubmitForm", methods=["POST"])
def submitform():
    if captcha_verify(
            request.json["g-recaptcha-response"], request.headers.get("X-Forwarded-For")
    ):
        email = request.json["email"]
        comment = "```" + str(request.json["comment"]) + "```"
        if comment == "''''''":
            comment = ""
        send_discord_webhook(
            os.environ["DISCORD_WEBHOOK_CONTACT_FORM_URL"],
            request.json["name"],
            f"**Email:**\n```{email}```\n**Message:**\n{comment}",
        )
        return jsonify(message="200: Success")
    else:
        abort(403)


# Error Handlers
@app.errorhandler(400)
def bad_request():
    return jsonify(error="400: Bad Request"), 400


@app.errorhandler(401)
def unauthorized():
    return jsonify(error="401: Unauthorized"), 401


@app.errorhandler(403)
def forbidden():
    return jsonify(error="403: Forbidden"), 403


@app.errorhandler(404)
def page_not_found():
    return jsonify(error="404: Not Found"), 404


@app.errorhandler(405)
def method_not_allowed():
    return jsonify(error="405: Method Not Allowed"), 405


@app.errorhandler(500)
def server_error():
    return jsonify(error="500: Server Error"), 500


@app.errorhandler(505)
def not_supported():
    return jsonify(error="505: HTTP Not Supported"), 505
